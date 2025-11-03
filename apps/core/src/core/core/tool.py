from typing import Any, Dict, List
from uuid import UUID

from fastapi import BackgroundTasks
from fastapi_pagination import Params as PaginationParams
from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from core.core.config import settings
from core.core.job import CRUDFailedJob
from core.core.statistics import StatisticsBase
from core.crud.crud_job import job as crud_job
from core.crud.crud_layer import layer as crud_layer
from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.crud.crud_project import project as crud_project
from core.db.models.layer import FeatureType, Layer, LayerType, ToolType
from core.schemas.common import CQLQueryObject, OrderEnum
from core.schemas.error import (
    AreaSizeError,
    FeatureCountError,
    GeometryTypeError,
    LayerExtentError,
    LayerProjectTypeError,
    LayerSizeError,
)
from core.schemas.job import JobType, Msg, MsgType
from core.schemas.layer import (
    ComputeBreakOperation,
    FeatureGeometryType,
    IFeatureLayerToolCreate,
    UserDataGeomType,
)
from core.schemas.project import (
    IFeatureStandardProjectRead,
    IFeatureStreetNetworkProjectRead,
    IFeatureToolProjectRead,
    ITableProjectRead,
)
from core.schemas.style import (
    custom_styles,
    get_base_style,
    get_tool_style_ordinal,
    get_tool_style_with_breaks,
)
from core.schemas.tool import IToolParam
from core.schemas.toolbox_base import (
    ColumnStatisticsOperation,
    DefaultResultLayerName,
    GeofenceTable,
    MaxFeatureCnt,
    MaxFeaturePolygonArea,
)
from core.utils import (
    build_where_clause,
    format_value_null_sql,
    get_random_string,
)


def assign_attribute(
    mapped_column: str, attribute_mapping: Dict[str, Any], attribute_value: Any
) -> Dict[str, Any]:
    base_attr = mapped_column.split("_")[0]
    attr1 = base_attr + "_attr1"
    if attr1 not in attribute_mapping:
        attribute_mapping[attr1] = attribute_value
    else:
        # Get attr of same name with max count
        count_attr = 1
        while (base_attr + f"_attr{count_attr}") in attribute_mapping:
            count_attr += 1
        attribute_mapping[base_attr + f"_attr{count_attr}"] = attribute_value
    return attribute_mapping


async def start_calculation(
    job_type: JobType,
    tool_class: type,
    crud_method: str,
    async_session: AsyncSession,
    user_id: UUID,
    background_tasks: BackgroundTasks,
    project_id: UUID,
    params: BaseModel,
    http_client: AsyncClient | None = None,
) -> Dict[str, Any]:
    # Create job and check if user can create a new job
    job = await crud_job.check_and_create(
        async_session=async_session,
        user_id=user_id,
        job_type=job_type,
        project_id=project_id,
    )

    # Instantiate the class
    if http_client is None:
        tool = tool_class(
            job_id=job.id,
            background_tasks=background_tasks,
            async_session=async_session,
            user_id=user_id,
            project_id=project_id,
        )
    else:
        tool = tool_class(
            job_id=job.id,
            background_tasks=background_tasks,
            async_session=async_session,
            user_id=user_id,
            project_id=project_id,
            http_client=http_client,
        )

    # Execute the CRUD method
    await getattr(tool, crud_method)(
        params=params,
    )

    return {"job_id": job.id}


class CRUDToolBase(StatisticsBase, CRUDFailedJob):
    def __init__(
        self,
        job_id: UUID | None,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id)
        self.project_id = project_id

    async def build_additional_spatial_filter(
        self,
        layer_project: IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | IFeatureStreetNetworkProjectRead
        | ITableProjectRead,
        layer_project_filter: IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | IFeatureStreetNetworkProjectRead,
    ) -> BaseModel:
        # Ensure spatial extent is available
        if layer_project_filter.extent is None:
            raise LayerExtentError(
                "The layer_project_filter does not have an extent defined."
            )

        # Add filter by extent to query
        coords = [
            [float(coord) for coord in point.split()]
            for point in layer_project_filter.extent[16:-3].split(", ")
        ]

        # Add spatial filter to query
        spatial_filter = {
            "op": "s_intersects",
            "args": [
                {"property": "geom"},
                {
                    "type": "Polygon",
                    "coordinates": [coords],
                },
            ],
        }
        if layer_project.query is None:
            query = {"cql": spatial_filter}
        else:
            query = {
                "cql": {"op": "and", "args": [layer_project.query.cql, spatial_filter]}
            }

        layer_project.query = CQLQueryObject(**query)
        return layer_project

    async def check_max_feature_cnt_aggregation(
        self,
        layers_project: Dict[str, Any],
        params: IToolParam,
    ) -> Dict[str, Any]:
        # Count exclusively features that are within the extent of the other layers
        source_layer_project = layers_project["source_layer_project_id"]
        aggregation_layer_project = layers_project.get("aggregation_layer_project_id")

        if aggregation_layer_project is None:
            await self.check_max_feature_cnt(
                layers_project=[source_layer_project],
                tool_type=params.tool_type,
            )
            return layers_project
        else:
            # Build array for layers to check
            layers_project_list = []
            source_layer_project = await self.build_additional_spatial_filter(
                layer_project=source_layer_project,
                layer_project_filter=aggregation_layer_project,
            )
            layers_project_list.append(source_layer_project)
            aggregation_layer_project = await self.build_additional_spatial_filter(
                layer_project=aggregation_layer_project,
                layer_project_filter=source_layer_project,
            )
            layers_project_list.append(aggregation_layer_project)

            # Check if the feature count is below the limit
            for layer_project in layers_project_list:
                cnt = (
                    await crud_layer_project.get_feature_cnt(
                        async_session=self.async_session,
                        layer_project=layer_project,
                    )
                )["filtered_count"]
                # Make sure that the count is below the limit for aggregation_point or aggregation_polygon
                if cnt > MaxFeatureCnt[params.tool_type.value].value:
                    raise FeatureCountError(
                        f"The operation cannot be performed on more than {MaxFeatureCnt[params.tool_type.value].value} features."
                    )
            return {
                "source_layer_project_id": source_layer_project,
                "aggregation_layer_project_id": aggregation_layer_project,
            }

    async def get_layers_project(self, params: BaseModel) -> Dict[str, Any]:
        # Get all params that have the name layer_project_id and build a dict using the variable name as key
        layer_project_ids = {}
        for key, value in params.model_dump().items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key.endswith("layer_project_id") and sub_value is not None:
                        layer_project_ids[sub_key] = sub_value
            elif key.endswith("layer_project_id") and value is not None:
                layer_project_ids[key] = value

        # Get all layers_project
        layers_project = {}
        for layer_name in layer_project_ids:
            # Get layer_project
            layer_project_id = layer_project_ids[layer_name]
            input_layer_types = params.input_layer_types
            layer_project = await crud_layer_project.get_internal(
                async_session=self.async_session,
                id=layer_project_id,
                project_id=self.project_id,
                expected_layer_types=input_layer_types[layer_name].layer_types,
                expected_geometry_types=input_layer_types[
                    layer_name
                ].feature_layer_geometry_types,
            )
            layers_project[layer_name] = layer_project

        # Adjust max_feature count for aggregation layers
        if params.tool_type in [ToolType.aggregate_point, ToolType.aggregate_polygon]:
            # Check max feature count based on the features within the extent of the other layers
            layers_project = await self.check_max_feature_cnt_aggregation(
                layers_project=layers_project,
                params=params,
            )
        else:
            # Check Max feature count for all layers
            await self.check_max_feature_cnt(
                layers_project=list(layers_project.values()),
                tool_type=params.tool_type,
            )

        # If geometry is of type polygon and tool type is in MaxFeaturePolygonArea
        for layer_project in layers_project.values():
            # Check for each feature layer of type polygon if the tool type is in MaxFeaturePolygonArea
            if layer_project.type == LayerType.feature:
                if (
                    layer_project.feature_layer_geometry_type
                    == FeatureGeometryType.polygon
                    and params.tool_type in MaxFeaturePolygonArea.__members__
                ):
                    # Check reference area size
                    await self.check_reference_area_size(
                        layer_project=layer_project,
                        tool_type=params.tool_type,
                    )

        return layers_project

    async def create_feature_layer_tool(
        self,
        layer_in: IFeatureLayerToolCreate,
        params: BaseModel,
    ) -> Dict[str, Any]:
        # Get project to put the new layer in the same folder as the project
        project = await crud_project.get(self.async_session, id=self.project_id)

        # Check layer name and alter if needed
        default_layer_name = layer_in.name
        new_layer_name = await crud_layer_project.check_and_alter_layer_name(
            async_session=self.async_session,
            folder_id=project.folder_id,
            layer_name=default_layer_name,
            project_id=self.project_id,
        )
        layer_in.name = new_layer_name

        # TODO: Compute properties dynamically
        properties = get_base_style(layer_in.feature_layer_geometry_type)
        layer = Layer(
            **layer_in.model_dump(exclude_none=True),
            folder_id=project.folder_id,
            user_id=self.user_id,
            type=LayerType.feature,
            feature_layer_type=FeatureType.tool,
            properties=properties,
        )

        # Get extent, size and properties
        layer.size = await crud_layer.get_feature_layer_size(
            async_session=self.async_session, layer=layer
        )
        layer.extent = str(
            await crud_layer.get_feature_layer_extent(
                async_session=self.async_session, layer=layer
            )
        )
        # Raise error if extent or size is None
        if layer.size is None:
            raise LayerSizeError("The layer size is None.")
        if layer.extent is None:
            raise LayerExtentError("The layer extent is None.")

        # Create layer
        layer = await crud_layer.create(
            db=self.async_session,
            obj_in=dict(layer),
        )
        await crud_layer.label_cluster_keep(
            async_session=self.async_session,
            layer=layer,
        )

        # Create style for layer
        # Request scale breaks in case of color_scale
        properties = None
        if DefaultResultLayerName(default_layer_name) in custom_styles:
            properties = custom_styles[DefaultResultLayerName(default_layer_name)]

        elif hasattr(params, "properties_base"):
            properties_base = params.properties_base[
                DefaultResultLayerName(default_layer_name)
            ]
            if (
                properties_base.get("color_scale") in ComputeBreakOperation.__members__
                and properties_base.get("color_field").get("type") == "number"
                and properties_base["color_field"]["name"]
                in (layer_in.attribute_mapping.values())
            ):
                # Get unique values for color field
                unique_values = await crud_layer.get_unique_values(
                    async_session=self.async_session,
                    id=layer.id,
                    column_name=properties_base["color_field"]["name"],
                    order=OrderEnum.descendent.value,
                    query=None,
                    page_params=PaginationParams(page=1, size=7),
                )
                if properties_base.get("breaks") is None:
                    # Get len propertes as breaks
                    breaks = len(unique_values.items)
                else:
                    # Get breaks from params if len is less then number of unique values
                    breaks = (
                        properties_base["breaks"]
                        if len(unique_values.items) > properties_base["breaks"]
                        else len(unique_values.items)
                    )

                if breaks > 2:
                    # Get unique unique scale breaks
                    operation = properties_base.get("color_scale")
                    # Get scale breaks
                    color_scale_breaks = await crud_layer.get_class_breaks(
                        async_session=self.async_session,
                        id=layer.id,
                        operation=ComputeBreakOperation(operation),
                        column_name=properties_base["color_field"]["name"],
                        stripe_zeros=True,
                        breaks=breaks,
                        query=None,
                    )
                    # Get unique breaks
                    breaks_arr = list(set(color_scale_breaks["breaks"]))
                    # Sort list
                    breaks_arr.sort()
                    # Remove of min or max in breaks
                    if color_scale_breaks["min"] in breaks_arr:
                        breaks_arr.remove(color_scale_breaks["min"])
                    if color_scale_breaks["max"] in breaks_arr:
                        breaks_arr.remove(color_scale_breaks["max"])
                    color_scale_breaks["breaks"] = breaks_arr
                    # Get properties
                    properties = get_tool_style_with_breaks(
                        feature_geometry_type=layer.feature_layer_geometry_type,
                        color_field=properties_base["color_field"],
                        color_scale_breaks=color_scale_breaks,
                        color_range_type=properties_base["color_range_type"],
                    )
            elif properties_base.get("color_scale") == "ordinal":
                # Check if layer has max nine unique values in color_field
                unique_values = await crud_layer.get_unique_values(
                    async_session=self.async_session,
                    id=layer.id,
                    column_name=properties_base["color_field"]["name"],
                    order=OrderEnum.descendent.value,
                    query=None,
                    page_params=PaginationParams(page=1, size=9),
                )
                # Get properties
                unique_values = [item.value for item in unique_values.items]
                properties = get_tool_style_ordinal(
                    feature_geometry_type=layer.feature_layer_geometry_type,
                    color_range_type=properties_base["color_range_type"],
                    color_field=properties_base["color_field"],
                    unique_values=unique_values,
                )

        if properties is None:
            properties = get_base_style(layer_in.feature_layer_geometry_type)

        # Update layer with properties and thumbnail
        layer = await crud_layer.update(
            async_session=self.async_session,
            id=layer.id,
            layer_in={"properties": properties},
        )

        # Label cluster_keep
        if layer.type == LayerType.feature:
            await crud_layer.label_cluster_keep(self.async_session, layer)

        # Add layer to project
        layer_project = await crud_layer_project.create(
            async_session=self.async_session,
            project_id=self.project_id,
            layer_ids=[layer.id],
        )

        return {"layer": layer, "layer_project": layer_project}

    async def check_max_feature_cnt(
        self,
        layers_project: List[BaseModel] | List[SQLModel] | List[dict],
        tool_type: ToolType,
    ) -> None:
        for layer_project in layers_project:
            # Check if BaseModel or SQLModel
            if isinstance(layer_project, BaseModel) or isinstance(
                layer_project, SQLModel
            ):
                feature_cnt = layer_project.filtered_count or layer_project.total_count
            elif isinstance(layer_project, dict):
                feature_cnt = layer_project.filtered_count or layer_project.total_count
            else:
                raise LayerProjectTypeError(
                    "The layer_project is not of type BaseModel, SQLModel or dict."
                )
            if feature_cnt > MaxFeatureCnt[tool_type.value].value:
                raise FeatureCountError(
                    f"The operation cannot be performed on more than {MaxFeatureCnt[tool_type.value].value} features."
                )

    async def check_reference_area_size(
        self,
        layer_project: BaseModel | SQLModel | Dict[str, Any],
        tool_type: ToolType,
    ) -> float:
        # Build where query for layer
        where_query = build_where_clause([layer_project.where_query])

        # Check if layer has polygon geoms
        if (
            layer_project.feature_layer_geometry_type.value
            != UserDataGeomType.polygon.value
        ):
            raise GeometryTypeError(
                "Operation not supported. The layer does not contain polygon geometries. Pick a layer with polygon geometries."
            )

        # Call SQL function
        sql_query = text("""
            SELECT *
            FROM basic.area_statistics(:operation, :table_name, :where_query)
        """)
        res = (
            await self.async_session.execute(
                sql_query,
                {
                    "operation": ColumnStatisticsOperation.sum.value,
                    "table_name": layer_project.table_name,
                    "where_query": where_query,
                },
            )
        ).fetchall()
        area: float = res[0][0]["sum"] / 1000000
        if area > MaxFeaturePolygonArea[tool_type.value].value:
            raise AreaSizeError(
                f"The operation cannot be performed on more than {MaxFeaturePolygonArea[tool_type.value].value} km2."
            )
        return area

    async def check_reference_area_geofence(
        self,
        layer_project: BaseModel | SQLModel | dict,
        tool_type: MaxFeaturePolygonArea,
    ) -> Msg:
        # Build where query for layer
        where_query = build_where_clause([layer_project.where_query])
        geofence_table = GeofenceTable[tool_type.value].value
        # Check if layer has polygon geoms
        sql = text(f"""
            WITH to_test AS
            (
                SELECT *
                FROM {layer_project.table_name}
                {where_query}
            )
            SELECT COUNT(*)
            FROM to_test t
            WHERE NOT EXISTS (
                SELECT 1
                FROM {geofence_table} AS g
                WHERE ST_WITHIN(t.geom, g.geom)
            )
        """)
        # Execute query
        cnt_not_within = await self.async_session.execute(sql)
        cnt_not_within = cnt_not_within.scalar()

        if cnt_not_within > 0:
            return Msg(
                type=MsgType.warning,
                text=f"{cnt_not_within} features are not within the geofence.",
            )
        return Msg(type=MsgType.info, text="All features are within the geofence.")

    async def check_reference_area(
        self, layer_project_id: int, tool_type: ToolType
    ) -> Dict[str, Any]:
        # Get layer project
        layer_project = await crud_layer_project.get_internal(
            async_session=self.async_session,
            id=layer_project_id,
            project_id=self.project_id,
            expected_layer_types=[LayerType.feature],
            expected_geometry_types=[FeatureGeometryType.polygon],
        )
        # Check if the feature count is below the limit
        await self.check_max_feature_cnt(
            layers_project=[layer_project], tool_type=tool_type
        )
        # Check if the reference area size is below the limit
        await self.check_reference_area_size(
            layer_project=layer_project, tool_type=tool_type
        )
        # Check if the reference area is within in geofence
        return {
            "msg": await self.check_reference_area_geofence(
                layer_project=layer_project, tool_type=tool_type
            ),
            "layer_project": layer_project,
        }

    # TODO: Remove if unused
    # async def check_column_same_type(
    #     self, layers_project: BaseModel, columns: list[str]
    # ) -> None:
    #     """Check if all columns are having the same type"""

    #     # Check if len layers_project and columns are the same
    #     if len(layers_project) != len(columns):
    #         raise ValueError("The number of columns and layers are not the same.")

    #     # Populate mapped_field_type array
    #     mapped_field_type = []
    #     for i in range(len(layers_project)):
    #         layer_project = layers_project[i]
    #         column = columns[i]

    #         # Get mapped field
    #         mapped_field = search_value(layer_project.attribute_mapping, column)
    #         mapped_field_type.append(mapped_field.split("_")[0])

    #     # Check if all mapped_field_type are the same
    #     if len(set(mapped_field_type)) != 1:
    #         raise ColumnTypeError("The columns are not having the same type.")

    async def create_temp_table_name(self, prefix: str) -> str:
        # Create temp table name
        table_suffix = str(self.job_id).replace("-", "")
        temp_table = f"temporal.{prefix}_{get_random_string(6)}_{table_suffix}"
        return temp_table

    async def create_distributed_polygon_table(
        self,
        layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead,
        scenario_id: UUID | None,
    ) -> str:
        # Create table name
        temp_polygons = await self.create_temp_table_name("polygons")

        # Create distributed polygon table using sql
        where_query_polygon = "WHERE " + layer_project.where_query.replace("'", "''")
        arr_columns = (
            f", {', '.join(list(layer_project.attribute_mapping.keys()))}"
            if layer_project.attribute_mapping
            else ""
        )

        await self.async_session.execute(
            text(f"""SELECT basic.create_distributed_polygon_table(
                '{layer_project.table_name}',
                {layer_project.id},
                '{arr_columns}',
                '{settings.CUSTOMER_SCHEMA}',
                {format_value_null_sql(scenario_id)},
                '{where_query_polygon}',
                30,
                '{temp_polygons}'
            )""")
        )
        # Commit changes
        await self.async_session.commit()
        return temp_polygons

    async def create_distributed_line_table(
        self,
        layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead,
        scenario_id: UUID | None,
    ) -> str:
        # Create temp table name for lines
        temp_lines = await self.create_temp_table_name("lines")

        # Create distributed line table using sql
        where_query_line = "WHERE " + layer_project.where_query.replace("'", "''")
        arr_columns = (
            f", {', '.join(list(layer_project.attribute_mapping.keys()))}"
            if layer_project.attribute_mapping
            else ""
        )

        await self.async_session.execute(
            text(f"""SELECT basic.create_distributed_line_table(
                '{layer_project.table_name}',
                {layer_project.id},
                '{arr_columns}',
                '{settings.CUSTOMER_SCHEMA}',
                {format_value_null_sql(scenario_id)},
                '{where_query_line}',
                '{temp_lines}'
            )""")
        )
        # Commit changes
        await self.async_session.commit()
        return temp_lines

    async def create_distributed_point_table(
        self,
        layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead,
        scenario_id: UUID | None,
    ) -> str:
        # Create temp table name for points
        temp_points = await self.create_temp_table_name("points")

        # Create distributed point table using sql
        where_query_point = "WHERE " + layer_project.where_query.replace("'", "''")
        arr_columns = (
            f", {', '.join(list(layer_project.attribute_mapping.keys()))}"
            if layer_project.attribute_mapping
            else ""
        )

        await self.async_session.execute(
            text(f"""SELECT basic.create_distributed_point_table(
                '{layer_project.table_name}',
                {layer_project.id},
                '{arr_columns}',
                '{settings.CUSTOMER_SCHEMA}',
                {format_value_null_sql(scenario_id)},
                '{where_query_point}',
                '{temp_points}'
            )""")
        )
        # Commit changes
        await self.async_session.commit()
        return temp_points

    async def create_temp_table_layer(
        self, layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead
    ) -> str:
        """Create a temp table for the layer_project."""

        temp_geometry_layer = await self.create_temp_table_name("layer")
        where_query = "WHERE " + layer_project.where_query
        sql_temp_geometry_layer = text(f"""
            CREATE TABLE {temp_geometry_layer} AS
            SELECT *
            FROM {layer_project.table_name}
            {where_query}
        """)
        await self.async_session.execute(sql_temp_geometry_layer)
        await self.async_session.commit()
        return temp_geometry_layer
