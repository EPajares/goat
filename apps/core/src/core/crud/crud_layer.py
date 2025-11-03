# Standard library imports
import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

# Third party imports
from fastapi import BackgroundTasks, HTTPException, status
from fastapi_pagination import Page
from fastapi_pagination import Params as PaginationParams
from geoalchemy2.elements import WKTElement
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

# Local application imports
from core.core.config import settings
from core.core.content import build_shared_with_object, create_query_shared_content
from core.core.job import (
    CRUDFailedJob,
    job_init,
    job_log,
    run_background_or_immediately,
)
from core.core.layer import (
    CRUDLayerBase,
    FileUpload,
    OGRFileHandling,
    delete_layer_data,
    delete_old_files,
)
from core.crud.base import CRUDBase
from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.db.models._link_model import (
    LayerOrganizationLink,
    LayerTeamLink,
)
from core.db.models.layer import FeatureGeometryType, FeatureType, Layer, LayerType
from core.db.models.organization import Organization
from core.db.models.role import Role
from core.db.models.team import Team
from core.schemas.error import (
    ColumnNotFoundError,
    LayerNotFoundError,
    NoCRSError,
    OperationNotSupportedError,
    UnsupportedLayerTypeError,
)
from core.schemas.job import JobStatusType
from core.schemas.layer import (
    AreaStatisticsOperation,
    ComputeBreakOperation,
    ICatalogLayerGet,
    IFeatureStandardCreateAdditionalAttributes,
    IFileUploadExternalService,
    IFileUploadMetadata,
    ILayerExport,
    ILayerFromDatasetCreate,
    ILayerGet,
    IMetadataAggregate,
    IMetadataAggregateRead,
    ITableCreateAdditionalAttributes,
    IUniqueValue,
    MetadataGroupAttributes,
    OgrDriverType,
    SupportedOgrGeomType,
    UserDataGeomType,
    get_layer_schema,
    layer_update_class,
)
from core.schemas.style import get_base_style
from core.schemas.toolbox_base import MaxFeatureCnt
from core.utils import (
    async_delete_dir,
    async_zip_directory,
    build_where,
    build_where_clause,
)


class CRUDLayer(CRUDLayerBase):
    """CRUD class for Layer."""

    async def label_cluster_keep(
        self, async_session: AsyncSession, layer: Layer
    ) -> None:
        """Label the rows that should be kept in case of vector tile clustering. Based on the logic to priotize features close to the centroid of an h3 grid of resolution 8."""

        # Build query to update the selected rows
        if layer.type == LayerType.feature:
            sql_query = f"""WITH to_update AS
            (
                SELECT id, CASE
                    WHEN row_number() OVER (PARTITION BY h3_group
                    ORDER BY ST_DISTANCE(ST_CENTROID(geom), ST_SETSRID(h3_cell_to_lat_lng(h3_group)::geometry, 4326))) = 1 THEN TRUE
                    ELSE FALSE
                END AS cluster_keep
                FROM {layer.table_name}
                WHERE layer_id = '{str(layer.id)}'
                ORDER BY h3_group, ST_DISTANCE(ST_CENTROID(geom), ST_SETSRID(h3_cell_to_lat_lng(h3_lat_lng_to_cell(ST_CENTROID(geom)::point, 8))::geometry, 4326))
            )
            UPDATE {layer.table_name} p
            SET cluster_keep = TRUE
            FROM to_update u
            WHERE p.id = u.id
            AND u.cluster_keep IS TRUE"""

            await async_session.execute(text(sql_query))
            await async_session.commit()

    async def get_internal(self, async_session: AsyncSession, id: UUID) -> Layer:
        """Gets a layer and make sure it is a internal layer."""

        layer: Layer | None = await self.get(async_session, id=id)
        if layer is None:
            raise LayerNotFoundError("Layer not found")
        if layer.type not in [LayerType.feature, LayerType.table]:
            raise UnsupportedLayerTypeError(
                "Layer is not a feature layer or table layer. The requested operation cannot be performed on these layer types."
            )
        return layer

    async def update(
        self,
        async_session: AsyncSession,
        id: UUID,
        layer_in: dict,
    ) -> Layer:
        # Get layer
        layer = await self.get(async_session, id=id)
        if layer is None:
            raise LayerNotFoundError(f"{Layer.__name__} not found")

        # Get the right Layer model for update
        schema = get_layer_schema(
            class_mapping=layer_update_class,
            layer_type=layer.type,
            feature_layer_type=layer.feature_layer_type,
        )

        # Populate layer schema
        layer_in = schema(**layer_in)

        layer = await CRUDBase(Layer).update(
            async_session, db_obj=layer, obj_in=layer_in
        )

        return layer

    async def delete(
        self,
        async_session: AsyncSession,
        id: UUID,
    ) -> None:
        layer = await CRUDBase(Layer).get(async_session, id=id)
        if layer is None:
            raise LayerNotFoundError(f"{Layer.__name__} not found")

        # Delete data if internal layer
        if layer.type in [LayerType.table.value, LayerType.feature.value]:
            # Delete layer data
            await delete_layer_data(async_session=async_session, layer=layer)

        # Delete layer metadata
        await CRUDBase(Layer).delete(
            db=async_session,
            id=id,
        )

        # Delete layer thumbnail
        if (
            layer.thumbnail_url
            and settings.THUMBNAIL_DIR_LAYER in layer.thumbnail_url
            and settings.TEST_MODE is False
        ):
            settings.S3_CLIENT.delete_object(
                Bucket=settings.AWS_S3_ASSETS_BUCKET,
                Key=layer.thumbnail_url.replace(settings.ASSETS_URL + "/", ""),
            )

    async def upload_file(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        source: UploadFile | IFileUploadExternalService,
        layer_type: LayerType,
    ) -> IFileUploadMetadata:
        """Fetch data if required, then validate using ogr2ogr."""

        dataset_id = uuid4()
        # Initialize OGRFileUpload
        file_upload = FileUpload(
            async_session=async_session,
            user_id=user_id,
            dataset_id=dataset_id,
            source=source,
        )

        # Save file
        timeout = 120
        try:
            file_path = await asyncio.wait_for(
                file_upload.save_file(),
                timeout,
            )
        except asyncio.TimeoutError:
            # Run failure function and perform cleanup
            await file_upload.save_file_fail()
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"File upload timed out after {timeout} seconds.",
            )
        except Exception as e:
            # Run failure function if exists
            await file_upload.save_file_fail()
            # Update job status simple to failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        # Initialize OGRFileHandling
        ogr_file_handling = OGRFileHandling(
            async_session=async_session,
            user_id=user_id,
            file_path=file_path,
        )

        # Validate file before uploading
        try:
            validation_result = await asyncio.wait_for(
                ogr_file_handling.validate(),
                timeout,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"File validation timed out after {timeout} seconds.",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        if validation_result.get("status") == "failed":
            # Run failure function if exists
            await file_upload.save_file_fail()
            # Update job status simple to failed
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=validation_result["msg"],
            )

        # Get file size in bytes
        if isinstance(source, UploadFile):
            original_position = source.file.tell()
            source.file.seek(0, 2)
            file_size = source.file.tell()
            source.file.seek(original_position)
        else:
            file_size = os.path.getsize(file_path)

        # Define metadata object
        metadata = IFileUploadMetadata(
            **validation_result,
            dataset_id=dataset_id,
            file_ending=os.path.splitext(
                source.filename if isinstance(source, UploadFile) else file_path
            )[-1][1:],
            file_size=file_size,
            layer_type=layer_type,
        )

        # Save metadata into user folder as json
        metadata_path = os.path.join(
            os.path.dirname(metadata.file_path), "metadata.json"
        )
        with open(metadata_path, "w") as f:
            # Convert dict to json
            json.dump(metadata.model_dump_json(), f)

        # Add layer_type and file_size to validation_result
        return metadata

    async def get_feature_layer_size(
        self, async_session: AsyncSession, layer: Layer
    ) -> int:
        """Get size of feature layer."""

        # Get size
        sql_query = f"""
            SELECT SUM(pg_column_size(p.*))
            FROM {layer.table_name} AS p
            WHERE layer_id = '{str(layer.id)}'
        """
        result: int = (await async_session.execute(text(sql_query))).fetchall()[0][0]
        return result

    async def get_feature_layer_extent(
        self, async_session: AsyncSession, layer: Layer
    ) -> WKTElement:
        """Get extent of feature layer."""

        # Get extent
        sql_query = f"""
            SELECT CASE WHEN ST_MULTI(ST_ENVELOPE(ST_Extent(geom))) <> 'ST_MultiPolygon'
            THEN ST_MULTI(ST_ENVELOPE(ST_Extent(ST_BUFFER(geom, 0.00001))))
            ELSE ST_MULTI(ST_ENVELOPE(ST_Extent(geom))) END AS extent
            FROM {layer.table_name}
            WHERE layer_id = '{str(layer.id)}'
        """
        result: WKTElement = (
            (await async_session.execute(text(sql_query))).fetchall()
        )[0][0]
        return result

    async def check_if_column_suitable_for_stats(
        self, async_session: AsyncSession, id: UUID, column_name: str, query: str | None
    ) -> Dict[str, Any]:
        # Check if layer is internal layer
        layer = await self.get_internal(async_session, id=id)

        # Ensure a valid ID and attribute mapping is available
        if layer.id is None or layer.attribute_mapping is None:
            raise ValueError(
                "ID or attribute mapping is not defined for this layer, unable to compute stats."
            )

        column_mapped = next(
            (
                key
                for key, value in layer.attribute_mapping.items()
                if value == column_name
            ),
            None,
        )

        if column_mapped is None:
            raise ColumnNotFoundError("Column not found")

        return {
            "layer": layer,
            "column_mapped": column_mapped,
            "where_query": build_where(
                id=layer.id,
                table_name=layer.table_name,
                query=query,
                attribute_mapping=layer.attribute_mapping,
            ),
        }

    async def get_unique_values(
        self,
        async_session: AsyncSession,
        id: UUID,
        column_name: str,
        order: str,
        query: str,
        page_params: PaginationParams,
    ) -> Page:
        # Check if layer is suitable for stats
        res_check = await self.check_if_column_suitable_for_stats(
            async_session=async_session, id=id, column_name=column_name, query=query
        )
        layer = res_check["layer"]
        column_mapped = res_check["column_mapped"]
        where_query = res_check["where_query"]
        # Map order
        order_mapped = {"descendent": "DESC", "ascendent": "ASC"}[order]

        # Build count query
        count_query = f"""
            SELECT COUNT(*) AS total_count
            FROM (
                SELECT {column_mapped}
                FROM {layer.table_name}
                WHERE {where_query}
                AND {column_mapped} IS NOT NULL
                GROUP BY {column_mapped}
            ) AS subquery
        """

        # Execute count query
        count_result = await async_session.execute(text(count_query))
        total_results = count_result.scalar_one()

        # Build data query
        data_query = f"""
        SELECT *
        FROM (

            SELECT JSONB_BUILD_OBJECT(
                'value', {column_mapped}, 'count', COUNT(*)
            )
            FROM {layer.table_name}
            WHERE {where_query}
            AND {column_mapped} IS NOT NULL
            GROUP BY {column_mapped}
            ORDER BY COUNT(*) {order_mapped}, {column_mapped}
        ) AS subquery
        LIMIT {page_params.size}
        OFFSET {(page_params.page - 1) * page_params.size}
        """

        # Execute data query
        data_result = await async_session.execute(text(data_query))
        result = data_result.fetchall()
        result = [IUniqueValue(**res[0]) for res in result]

        # Create Page object
        page = Page(
            items=result,
            total=total_results,
            page=page_params.page,
            size=page_params.size,
        )

        return page

    async def get_area_statistics(
        self,
        async_session: AsyncSession,
        id: UUID,
        operation: AreaStatisticsOperation,
        query: str,
    ) -> Dict[str, Any] | None:
        # Check if layer is internal layer
        layer = await self.get_internal(async_session, id=id)

        # Ensure a valid ID and attribute mapping is available
        if layer.id is None or layer.attribute_mapping is None:
            raise ValueError(
                "ID or attribute mapping is not defined for this layer, unable to compute stats."
            )

        # Where query
        where_query = build_where(
            id=layer.id,
            table_name=layer.table_name,
            query=query,
            attribute_mapping=layer.attribute_mapping,
        )

        # Ensure where query is valid
        if where_query is None:
            raise ValueError("Invalid where query for layer.")

        # Check if layer has polygon geoms
        if layer.feature_layer_geometry_type != UserDataGeomType.polygon.value:
            raise UnsupportedLayerTypeError(
                "Operation not supported. The layer does not contain polygon geometries. Pick a layer with polygon geometries."
            )

        # Check if feature count is exceeding the defined limit
        await crud_layer_project.check_exceed_feature_cnt(
            async_session=async_session,
            max_feature_cnt=MaxFeatureCnt.area_statistics.value,
            layer=layer,
            where_query=where_query,
        )
        where_query = "WHERE " + where_query

        # Call SQL function
        sql_query = text(f"""
            SELECT * FROM basic.area_statistics('{operation.value}', '{layer.table_name}', '{where_query.replace("'", "''")}')
        """)
        res = (
            await async_session.execute(
                sql_query,
            )
        ).fetchall()
        res_value: Dict[str, Any] | None = res[0][0] if res else None
        return res_value

    async def get_class_breaks(
        self,
        async_session: AsyncSession,
        id: UUID,
        operation: ComputeBreakOperation,
        query: str | None,
        column_name: str,
        stripe_zeros: bool | None = None,
        breaks: int | None = None,
    ) -> Dict[str, Any] | None:
        # Check if layer is suitable for stats
        res = await self.check_if_column_suitable_for_stats(
            async_session=async_session, id=id, column_name=column_name, query=query
        )

        args = res
        where_clause = res["where_query"]
        args["table_name"] = args["layer"].table_name
        # del layer from args
        del args["layer"]

        # Extend where clause
        column_mapped = res["column_mapped"]
        if stripe_zeros:
            where_extension = (
                f" AND {column_mapped} != 0"
                if where_clause
                else f"{column_mapped} != 0"
            )
            args["where"] = where_clause + where_extension

        # Define additional arguments
        if breaks:
            args["breaks"] = breaks

        # Choose the SQL query based on operation
        if operation == ComputeBreakOperation.quantile:
            sql_query = "SELECT * FROM basic.quantile_breaks(:table_name, :column_mapped, :where, :breaks)"
        elif operation == ComputeBreakOperation.equal_interval:
            sql_query = "SELECT * FROM basic.equal_interval_breaks(:table_name, :column_mapped, :where, :breaks)"
        elif operation == ComputeBreakOperation.standard_deviation:
            sql_query = "SELECT * FROM basic.standard_deviation_breaks(:table_name, :column_mapped, :where)"
        elif operation == ComputeBreakOperation.heads_and_tails:
            sql_query = "SELECT * FROM basic.heads_and_tails_breaks(:table_name, :column_mapped, :where, :breaks)"
        else:
            raise OperationNotSupportedError("Operation not supported")

        # Execute the query
        result = (await async_session.execute(text(sql_query), args)).fetchall()
        result_value: Dict[str, Any] | None = result[0][0] if result else None
        return result_value

    async def get_last_data_updated_at(
        self, async_session: AsyncSession, id: UUID, query: str
    ) -> datetime:
        """Get last updated at timestamp."""

        # Check if layer is internal layer
        layer = await self.get_internal(async_session, id=id)

        # Ensure a valid ID and attribute mapping is available
        if layer.id is None or layer.attribute_mapping is None:
            raise ValueError(
                "ID or attribute mapping is not defined for this layer, unable to compute stats."
            )

        where_query = build_where(
            id=layer.id,
            table_name=layer.table_name,
            query=query,
            attribute_mapping=layer.attribute_mapping,
        )

        # Get last updated at timestamp
        sql_query = f"""
            SELECT MAX(updated_at)
            FROM {layer.table_name}
            WHERE {where_query}
        """
        result: datetime = (await async_session.execute(text(sql_query))).fetchall()[0][
            0
        ]
        return result

    async def get_base_filter(
        self,
        user_id: UUID,
        params: ILayerGet | ICatalogLayerGet | IMetadataAggregate,
        attributes_to_exclude: List[str] = [],
        team_id: UUID | None = None,
        organization_id: UUID | None = None,
    ) -> List[Any]:
        """Get filter for get layer queries."""
        filters = []
        for key, value in params.dict().items():
            if (
                key
                not in (
                    "search",
                    "spatial_search",
                    "in_catalog",
                    *attributes_to_exclude,
                )
                and value is not None
            ):
                # Avoid adding folder_id in case team_id or organization_id is provided
                if key == "folder_id" and (team_id or organization_id):
                    continue

                # Convert value to list if not list
                if not isinstance(value, list):
                    value = [value]
                filters.append(getattr(Layer, key).in_(value))

        # Check if ILayer get then it is organization layers
        if isinstance(params, ILayerGet):
            if params.in_catalog is not None:
                if not team_id and not organization_id:
                    filters.append(
                        and_(
                            Layer.in_catalog == bool(params.in_catalog),
                            Layer.user_id == user_id,
                        )
                    )
                else:
                    filters.append(
                        and_(
                            Layer.in_catalog == bool(params.in_catalog),
                        )
                    )
            else:
                if not team_id and not organization_id:
                    filters.append(Layer.user_id == user_id)
        else:
            filters.append(Layer.in_catalog == bool(True))

        # Add search filter
        if params.search is not None:
            filters.append(
                or_(
                    func.lower(Layer.name).contains(params.search.lower()),
                    func.lower(Layer.description).contains(params.search.lower()),
                    func.lower(Layer.distributor_name).contains(params.search.lower()),
                )
            )
        if params.spatial_search is not None:
            filters.append(
                Layer.extent.ST_Intersects(
                    WKTElement(params.spatial_search, srid=4326)
                ),
            )
        return filters

    async def get_layers_with_filter(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        order_by: str,
        order: str,
        page_params: PaginationParams,
        params: ILayerGet | ICatalogLayerGet,
        team_id: UUID | None = None,
        organization_id: UUID | None = None,
    ) -> Page[BaseModel]:
        """Get layer with filter."""

        # Additional server side validation for feature_layer_type
        if params is None:
            params = ILayerGet()
        if (
            params.type is not None
            and params.feature_layer_type is not None
            and LayerType.feature not in params.type
        ):
            raise HTTPException(
                status_code=400,
                detail="Feature layer type can only be set when layer type is feature",
            )
        # Get base filter
        filters = await self.get_base_filter(
            user_id=user_id,
            params=params,
            team_id=team_id,
            organization_id=organization_id,
        )

        # Get roles
        roles = await CRUDBase(Role).get_all(
            async_session,
        )
        role_mapping = {role.id: role.name for role in roles}

        # Build query
        query = create_query_shared_content(
            Layer,
            LayerTeamLink,
            LayerOrganizationLink,
            Team,
            Organization,
            Role,
            filters,
            team_id=team_id,
            organization_id=organization_id,
        )

        # Build params and filter out None values
        builder_params = {
            k: v
            for k, v in {
                "order_by": order_by,
                "order": order,
            }.items()
            if v is not None
        }

        layers = await self.get_multi(
            async_session,
            query=query,
            page_params=page_params,
            **builder_params,
        )
        assert isinstance(layers, Page)
        layers_arr = build_shared_with_object(
            items=layers.items,
            role_mapping=role_mapping,
            team_key="team_links",
            org_key="organization_links",
            model_name="layer",
            team_id=team_id,
            organization_id=organization_id,
        )
        layers.items = layers_arr
        return layers

    async def metadata_aggregate(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        params: IMetadataAggregate,
    ) -> IMetadataAggregateRead:
        """Get metadata aggregate for layers."""

        if params is None:
            params = ILayerGet()

        # Loop through all attributes
        result = {}
        for attribute in params:
            key = attribute[0]
            if key in ("search", "spatial_search", "folder_id"):
                continue

            # Build filter for respective group
            filters = await self.get_base_filter(
                user_id=user_id, params=params, attributes_to_exclude=[key]
            )
            # Get attribute from layer
            group_by = getattr(Layer, key)
            sql_query = (
                select(group_by, func.count(Layer.id).label("count"))
                .where(and_(*filters))
                .group_by(group_by)
            )
            res = await async_session.execute(sql_query)
            res = res.fetchall()
            # Create metadata object
            metadata = [
                MetadataGroupAttributes(value=str(r[0]), count=r[1])
                for r in res
                if r[0] is not None
            ]
            result[key] = metadata

        return IMetadataAggregateRead(**result)


layer = CRUDLayer(Layer)


class CRUDLayerImport(CRUDFailedJob):
    """CRUD class for Layer import."""

    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id)
        self.temp_table_name = (
            f'{settings.USER_DATA_SCHEMA}."{str(self.job_id).replace("-", "")}"'
        )

    async def create_internal(
        self,
        layer_in: ILayerFromDatasetCreate,
        file_metadata: Dict[str, Any],
        attribute_mapping: Dict[str, Any],
        project_id: UUID | None = None,
    ) -> UUID:
        additional_attributes: Dict[str, Any] = {}
        # Get layer_id and size from import job
        additional_attributes["user_id"] = self.user_id
        # Create attribute mapping
        additional_attributes["attribute_mapping"] = attribute_mapping
        # Map original file type
        additional_attributes["upload_file_type"] = file_metadata["file_ending"]

        # Get default style if feature layer
        if file_metadata["data_types"].get("geometry"):
            geom_type = SupportedOgrGeomType[
                file_metadata["data_types"]["geometry"]["type"]
            ].value
            if not layer_in.properties:
                layer_in.properties = get_base_style(
                    feature_geometry_type=FeatureGeometryType[geom_type]
                )
            additional_attributes["type"] = LayerType.feature
            additional_attributes["feature_layer_type"] = FeatureType.standard
            additional_attributes["feature_layer_geometry_type"] = geom_type
            additional_attributes["extent"] = file_metadata["data_types"]["geometry"][
                "extent"
            ]
            additional_attributes = IFeatureStandardCreateAdditionalAttributes(
                **additional_attributes
            ).model_dump()
        else:
            additional_attributes["type"] = LayerType.table
            additional_attributes = ITableCreateAdditionalAttributes(
                **additional_attributes
            ).model_dump()

        # Check to update the layer name if it already exists
        layer_in.name = await CRUDLayer(Layer).check_and_alter_layer_name(
            async_session=self.async_session,
            folder_id=layer_in.folder_id,
            layer_name=layer_in.name,
            project_id=project_id,
        )

        # Populate layer_in with additional attributes
        layer_in = Layer(
            **layer_in.model_dump(exclude_none=True),
            **additional_attributes,
            job_id=self.job_id,
        )

        # Update size
        layer_in.size = await CRUDLayer(Layer).get_feature_layer_size(
            async_session=self.async_session, layer=layer_in
        )
        layer: Layer = await CRUDLayer(Layer).create(
            db=self.async_session,
            obj_in=layer_in.model_dump(),
        )
        assert layer.id is not None

        # Label cluster_keep
        if layer.type == LayerType.feature:
            await CRUDLayer(Layer).label_cluster_keep(self.async_session, layer)

        if project_id:
            # Add layer to project
            await crud_layer_project.create(
                async_session=self.async_session,
                layer_ids=[layer.id],
                project_id=project_id,
            )

        return layer.id

    async def import_file(
        self,
        file_metadata: Dict[str, Any],
        layer_in: ILayerFromDatasetCreate,
        project_id: UUID | None = None,
    ) -> Tuple[Dict[str, Any], UUID]:
        """Import file using ogr2ogr."""

        # Initialize OGRFileHandling
        ogr_file_upload = OGRFileHandling(
            async_session=self.async_session,
            user_id=self.user_id,
            file_path=file_metadata["file_path"],
        )

        # Create attribute mapping out of valid attributes
        attribute_mapping = {}
        for field_type, field_names in file_metadata["data_types"]["valid"].items():
            cnt = 1
            for field_name in field_names:
                if field_name == "id":
                    continue
                # Replace hyphens with an underscore as ogr2ogr also does this while importing the layer
                # TODO: Find a more robust way to sync changes made by ogr2ogr to field names and this attribute mapping
                attribute_mapping[field_type + "_attr" + str(cnt)] = field_name.replace(
                    "-", "_"
                )
                cnt += 1

        # Upload file to temporary table using ogr2ogr
        result = await ogr_file_upload.upload_ogr2ogr(
            temp_table_name=self.temp_table_name,
            job_id=self.job_id,
        )
        # Migrate temporary table to target table
        result = await ogr_file_upload.migrate_target_table(
            validation_result=file_metadata,
            attribute_mapping=attribute_mapping,
            temp_table_name=self.temp_table_name,
            layer_id=layer_in.id,
            job_id=self.job_id,
        )
        # Create layer metadata and thumbnail
        layer_id = await self.create_internal(
            layer_in=layer_in,
            file_metadata=file_metadata,
            attribute_mapping=attribute_mapping,
            project_id=project_id,
        )

        return result, layer_id

    @run_background_or_immediately(settings)
    @job_init()
    async def import_file_job(
        self,
        file_metadata: Dict[str, Any],
        layer_in: ILayerFromDatasetCreate,
        project_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Create a layer from a dataset file."""

        result, _ = await self.import_file(
            file_metadata=file_metadata,
            layer_in=layer_in,
            project_id=project_id,
        )
        return result


class CRUDLayerExport:
    """CRUD class for Layer import."""

    def __init__(self, id: UUID, async_session: AsyncSession, user_id: UUID) -> None:
        self.id = id
        self.user_id = user_id
        self.async_session = async_session
        self.folder_path = os.path.join(
            settings.DATA_DIR, str(self.user_id), str(self.id)
        )

    async def create_metadata_file(self, layer: Layer, layer_in: ILayerExport) -> None:
        last_data_updated_at = await CRUDLayer(Layer).get_last_data_updated_at(
            async_session=self.async_session, id=self.id, query=layer_in.query
        )
        # Write metadata to metadata.txt file
        with open(
            os.path.join(self.folder_path, layer_in.file_name, "metadata.txt"), "w"
        ) as f:
            # Write some heading
            f.write("############################################################\n")
            f.write(f"Metadata for layer {layer.name}\n")
            f.write("############################################################\n")
            f.write(f"Exported Coordinate Reference System: {layer_in.crs}\n")
            f.write(
                f"Exported File Type: {OgrDriverType[layer_in.file_type.value].value}\n"
            )
            f.write("############################################################\n")
            f.write(f"Last data update: {last_data_updated_at}\n")
            f.write(f"Last metadata update: {layer.updated_at}\n")
            f.write(f"Created at: {layer.created_at}\n")
            f.write(f"Exported at: {datetime.now()}\n")
            f.write("############################################################\n")
            f.write(f"Name: {layer.name}\n")
            f.write(f"Description: {layer.description}\n")
            if layer.tags:
                f.write(f"Tags: {', '.join(layer.tags)}\n")
            f.write(f"Lineage: {layer.lineage}\n")
            f.write(f"Positional Accuracy: {layer.positional_accuracy}\n")
            f.write(f"Attribute Accuracy: {layer.attribute_accuracy}\n")
            f.write(f"Completeness: {layer.completeness}\n")
            f.write(f"Upload Reference System: {layer.upload_reference_system}\n")
            f.write(f"Upload File Type: {layer.upload_file_type}\n")
            f.write(f"Geographical Code: {layer.geographical_code}\n")
            f.write(f"Language Code: {layer.language_code}\n")
            f.write(f"Distributor Name: {layer.distributor_name}\n")
            f.write(f"Distributor Email: {layer.distributor_email}\n")
            f.write(f"Distribution URL: {layer.distribution_url}\n")
            f.write(f"License: {layer.license}\n")
            f.write(f"Attribution: {layer.attribution}\n")
            f.write(f"Data Reference Year: {layer.data_reference_year}\n")
            f.write(f"Data Category: {layer.data_category}\n")
            f.write("############################################################")

    async def export_file(
        self,
        layer_in: ILayerExport,
    ) -> str:
        """Export file using ogr2ogr."""

        # Get layer
        layer = await CRUDLayer(Layer).get_internal(
            async_session=self.async_session, id=self.id
        )

        # Only feature and table layers can be exported
        if layer.type not in [LayerType.feature, LayerType.table]:
            raise UnsupportedLayerTypeError(
                "Layer is not a feature layer or table layer. Other layer types cannot be exported."
            )

        # Make sure that feature layer have CRS set
        if layer.type == LayerType.feature:
            if layer_in.crs is None:
                raise NoCRSError(
                    "CRS is required for feature layers. Please provide a CRS."
                )

        # Build SQL query for export
        # Build select query based on attribute mapping
        select_query = ""
        for key, value in layer.attribute_mapping.items():
            select_query += f'{key} AS "{value}", '

        # Add id and geom
        if layer.type == LayerType.feature:
            select_query = "id, " + select_query + "geom"
        else:
            select_query = "id, " + select_query
            select_query = select_query[:-2]

        # Build where query
        where_query = build_where(
            layer.id, layer.table_name, layer_in.query, layer.attribute_mapping
        )
        query = build_where_clause([where_query])
        sql_query = f"""
            SELECT {select_query}
            FROM {layer.table_name}
            {query}
        """
        # Build filepath
        file_path = os.path.join(
            self.folder_path,
            layer_in.file_name,
            f"{layer_in.file_name}." + layer_in.file_type,
        )

        # Delete files that are older then one hour
        await delete_old_files(3600)

        # Initialize OGRFileHandling
        ogr_file_handling = OGRFileHandling(
            async_session=self.async_session,
            user_id=self.user_id,
            file_path=file_path,
        )
        file_path = await ogr_file_handling.export_ogr2ogr(
            layer=layer,
            file_type=layer_in.file_type,
            file_name=layer_in.file_name,
            sql_query=sql_query,
            crs=layer_in.crs,
        )

        # Write data into metadata.txt file
        await self.create_metadata_file(layer=layer, layer_in=layer_in)

        # Zip result folder
        result_dir = os.path.join(
            settings.DATA_DIR, str(self.user_id), str(layer_in.file_name) + ".zip"
        )
        await async_zip_directory(
            result_dir, os.path.join(self.folder_path, layer_in.file_name)
        )

        # Delete folder
        await async_delete_dir(self.folder_path)

        return result_dir

    async def export_file_run(self, layer_in: ILayerExport) -> str:
        return await self.export_file(layer_in=layer_in)


class CRUDDataDelete(CRUDFailedJob):
    """CRUD class for Layer import."""

    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id)

    @job_log(job_step_name="data_delete_multi")
    async def delete_multi(
        self,
        async_session: AsyncSession,
        layers: list[Layer],
    ) -> Dict[str, Any]:
        for layer in layers:
            await delete_layer_data(async_session=async_session, layer=layer)
        return {
            "status": JobStatusType.finished.value,
            "msg": "Data was successfuly deleted.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def delete_multi_run(
        self,
        async_session: AsyncSession,
        layers: list[Layer],
    ) -> Dict[str, Any]:
        return await self.delete_multi(async_session=async_session, layers=layers)


class CRUDLayerDatasetUpdate(CRUDFailedJob):
    """CRUD class for updating the dataset of an existing layer and updating all layer project references."""

    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id)

    @run_background_or_immediately(settings)
    @job_init()
    async def update(
        self,
        existing_layer_id: UUID,
        file_metadata: dict,
        layer_in: ILayerFromDatasetCreate,
    ) -> Dict[str, Any]:
        """Update layer dataset."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        original_name = layer_in.name

        # Create a new layer with the updated dataset while transferring existing layer properties
        result, layer_id = await CRUDLayerImport(
            background_tasks=self.background_tasks,
            async_session=self.async_session,
            user_id=self.user_id,
            job_id=self.job_id,
        ).import_file(
            file_metadata=file_metadata,
            layer_in=layer_in,
        )

        # Update all layer project references with the new layer id
        await crud_layer_project.update_layer_id(
            async_session=self.async_session,
            layer_id=existing_layer_id,
            new_layer_id=layer_id,
        )

        # Delete the old layer
        await layer.delete(async_session=self.async_session, id=existing_layer_id)

        # Rename the new layer
        await layer.update(
            async_session=self.async_session,
            id=layer_id,
            layer_in={"name": original_name},
        )

        return result
