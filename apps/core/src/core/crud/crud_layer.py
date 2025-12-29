# Standard library imports
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List
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
    run_background_or_immediately,
)
from core.core.layer import (
    CRUDLayerBase,
    FileUpload,
    OGRFileHandling,
    delete_layer_data,
)
from core.crud.base import CRUDBase
from core.db.models._link_model import (
    LayerOrganizationLink,
    LayerTeamLink,
)
from core.db.models.layer import Layer, LayerType
from core.db.models.organization import Organization
from core.db.models.role import Role
from core.db.models.team import Team
from core.schemas.error import (
    ColumnNotFoundError,
    LayerNotFoundError,
    OperationNotSupportedError,
    UnsupportedLayerTypeError,
)
from core.schemas.job import JobStatusType
from core.schemas.layer import (
    AreaStatisticsOperation,
    ComputeBreakOperation,
    ICatalogLayerGet,
    IFileUploadExternalService,
    IFileUploadMetadata,
    ILayerFromDatasetCreate,
    ILayerGet,
    IMetadataAggregate,
    IMetadataAggregateRead,
    IUniqueValue,
    MetadataGroupAttributes,
    UserDataGeomType,
    get_layer_schema,
    layer_update_class,
)
from core.utils import (
    async_delete_dir,
    build_where,
)

logger = logging.getLogger(__name__)


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

        # TODO: Feature count validation moved to geoapi - consider adding limit check there
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


class CRUDLayerDatasetUpdate(CRUDFailedJob):
    """CRUD class for updating the dataset of an existing layer in-place."""

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
        """Update layer dataset in-place (keeps same layer_id).

        Uses atomic swap approach:
        1. Convert file to parquet (goatlib)
        2. Create temp DuckLake table from parquet
        3. If successful: DROP old table, RENAME temp table
        4. If failed: DROP temp table, original data intact
        5. Update layer metadata
        """
        import tempfile
        from pathlib import Path

        from goatlib.io.converter import IOConverter

        from core.crud.crud_layer_ducklake import (
            build_extent_wkt,
            map_geometry_type,
        )
        from core.storage.ducklake import ducklake_manager

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Verify layer exists (will raise if not found)
        await layer.get_internal(
            async_session=self.async_session,
            id=existing_layer_id,
        )

        logger.info(
            "Updating layer dataset in-place: layer_id=%s",
            existing_layer_id,
        )

        # Step 1: Convert file to parquet using goatlib
        with tempfile.TemporaryDirectory(prefix="goat_update_") as temp_dir:
            parquet_path = Path(temp_dir) / f"{existing_layer_id}.parquet"

            converter = IOConverter()
            metadata = converter.to_parquet(
                src_path=file_metadata["file_path"],
                out_path=str(parquet_path),
                target_crs="EPSG:4326",
            )
            logger.info("Converted to parquet: %s", metadata.short_summary())

            # Step 2: Atomic replace in DuckLake
            # This creates temp table, drops old, renames - all in one transaction
            table_info = ducklake_manager.replace_layer_from_parquet(
                user_id=self.user_id,
                layer_id=existing_layer_id,
                parquet_path=str(parquet_path),
                target_crs="EPSG:4326",
            )

        # Step 3: Build updated attributes
        columns_info = {col["name"]: col["type"] for col in table_info["columns"]}

        update_attrs: Dict[str, Any] = {
            "attribute_mapping": columns_info,
            "job_id": self.job_id,
        }

        # Update geometry-related fields if geometry exists
        if table_info.get("geometry_type"):
            update_attrs["feature_layer_geometry_type"] = map_geometry_type(
                table_info["geometry_type"]
            )
            if table_info.get("extent"):
                update_attrs["extent"] = build_extent_wkt(table_info["extent"])

        # Update size from DuckLake metadata
        user_schema = f"user_{str(self.user_id).replace('-', '')}"
        table_name = f"t_{str(existing_layer_id).replace('-', '')}"
        query = text("""
            SELECT COALESCE(ts.file_size_bytes, 0) as file_size_bytes
            FROM ducklake.ducklake_table t
            JOIN ducklake.ducklake_schema s ON t.schema_id = s.schema_id
            JOIN ducklake.ducklake_table_stats ts ON t.table_id = ts.table_id
            WHERE s.schema_name = :schema_name
              AND t.table_name = :table_name
              AND t.end_snapshot IS NULL
              AND s.end_snapshot IS NULL
        """)
        result = await self.async_session.execute(
            query,
            {"schema_name": user_schema, "table_name": table_name},
        )
        row = result.fetchone()
        update_attrs["size"] = row.file_size_bytes if row else 0

        # Step 4: Update layer metadata in PostgreSQL
        await layer.update(
            async_session=self.async_session,
            id=existing_layer_id,
            layer_in=update_attrs,
        )

        # Step 5: Cleanup uploaded file directory
        upload_dir = os.path.dirname(file_metadata["file_path"])
        user_upload_dir = os.path.dirname(upload_dir)
        if upload_dir and os.path.isdir(upload_dir):
            await async_delete_dir(upload_dir)
            logger.info("Cleaned up upload directory: %s", upload_dir)
            if user_upload_dir and os.path.isdir(user_upload_dir):
                try:
                    os.rmdir(user_upload_dir)
                except OSError:
                    pass

        result = {
            "status": JobStatusType.finished.value,
            "msg": "Layer dataset updated successfully",
            "layer_id": str(existing_layer_id),
            "table_name": table_info["table_name"],
            "feature_count": table_info["feature_count"],
            "geometry_type": table_info.get("geometry_type"),
        }

        logger.info("Layer dataset update complete: %s", result)
        return result
