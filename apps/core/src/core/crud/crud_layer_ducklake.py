"""CRUD operations for layers using DuckLake storage.

This module provides a clean implementation for layer import/export
using DuckLake (GeoParquet) as the data storage backend.

Architecture:
- PostgreSQL: Layer metadata (name, style, etc.) in customer.layer table
- DuckLake: Actual feature/table data as GeoParquet files
- goatlib: File conversion (any format → GeoParquet)

Table naming:
- Schema per user: lake.user_{user_id}
- Table per layer: t_{layer_id}
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import text

from core.core.config import settings
from core.core.job import CRUDFailedJob, job_init, run_background_or_immediately
from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.db.models.layer import (
    FeatureGeometryType,
    FeatureType,
    Layer,
    LayerType,
)
from core.schemas.layer import (
    IFeatureStandardCreateAdditionalAttributes,
    ILayerFromDatasetCreate,
    ITableCreateAdditionalAttributes,
)
from core.schemas.style import get_base_style
from core.services.layer_import import LayerImportResult, layer_importer
from core.utils import async_delete_dir, async_zip_directory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# Geometry type mapping
# =============================================================================

GEOMETRY_TYPE_MAP: dict[str, str] = {
    "POINT": "point",
    "MULTIPOINT": "point",
    "LINESTRING": "line",
    "MULTILINESTRING": "line",
    "POLYGON": "polygon",
    "MULTIPOLYGON": "polygon",
}


def map_geometry_type(duckdb_type: str | None) -> str | None:
    """Map DuckDB geometry type to our FeatureGeometryType enum value."""
    if not duckdb_type:
        return None
    return GEOMETRY_TYPE_MAP.get(duckdb_type.upper(), "polygon")


def build_extent_wkt(extent: dict[str, float]) -> str:
    """Build WKT MULTIPOLYGON from extent dict.

    Handles both naming conventions:
    - xmin/ymin/xmax/ymax (from DuckLakeManager)
    - min_x/min_y/max_x/max_y (alternative format)
    """
    # Support both key naming conventions
    min_x = extent.get("xmin") or extent.get("min_x")
    min_y = extent.get("ymin") or extent.get("min_y")
    max_x = extent.get("xmax") or extent.get("max_x")
    max_y = extent.get("ymax") or extent.get("max_y")

    return (
        f"MULTIPOLYGON((("
        f"{min_x} {min_y}, "
        f"{max_x} {min_y}, "
        f"{max_x} {max_y}, "
        f"{min_x} {max_y}, "
        f"{min_x} {min_y}"
        f")))"
    )


# =============================================================================
# Layer Import CRUD
# =============================================================================


class CRUDLayerImportDuckLake(CRUDFailedJob):
    """CRUD for importing layers into DuckLake storage.

    This class handles:
    1. File conversion via goatlib (any format → GeoParquet)
    2. Data ingestion into DuckLake
    3. Layer metadata creation in PostgreSQL

    Example:
        crud = CRUDLayerImportDuckLake(
            job_id=job_id,
            background_tasks=background_tasks,
            async_session=session,
            user_id=user_id,
        )
        result, layer_id = await crud.import_file(
            file_path="/path/to/data.geojson",
            layer_in=layer_create_schema,
        )
    """

    def __init__(
        self: "CRUDLayerImportDuckLake",
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: "AsyncSession",
        user_id: UUID,
    ) -> None:
        """Initialize the import CRUD.

        Args:
            job_id: Background job UUID for tracking
            background_tasks: FastAPI background tasks
            async_session: SQLAlchemy async session
            user_id: Owner user UUID
        """
        super().__init__(job_id, background_tasks, async_session, user_id)

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    async def import_file(
        self: "CRUDLayerImportDuckLake",
        file_path: str,
        layer_in: ILayerFromDatasetCreate,
        file_metadata: dict[str, Any] | None = None,
        project_id: UUID | None = None,
    ) -> tuple[dict[str, Any], UUID]:
        """Import a file into DuckLake and create layer metadata.

        This method is atomic: if any step fails, previously created resources
        are cleaned up (DuckLake table deleted, no layer row created).

        Args:
            file_path: Path to source file
            layer_in: Layer creation schema with name, folder_id, etc.
            file_metadata: Optional metadata from file validation
            project_id: Optional project to associate layer with

        Returns:
            Tuple of (result dict, layer_id)

        Raises:
            RuntimeError: If import fails at any step
        """
        logger.info(
            "Importing file to DuckLake: %s for user=%s",
            file_path,
            self.user_id,
        )

        import_result = None
        try:
            # Step 1: Import file to DuckLake via LayerImporter
            import_result = layer_importer.import_file(
                user_id=self.user_id,
                layer_id=layer_in.id,
                file_path=file_path,
                target_crs="EPSG:4326",
            )

            # Step 2: Create layer metadata in PostgreSQL
            layer_id = await self._create_layer_metadata(
                layer_in=layer_in,
                import_result=import_result,
                file_metadata=file_metadata,
                project_id=project_id,
            )
        except Exception as e:
            # Cleanup: delete DuckLake table if it was created
            if import_result is not None:
                try:
                    from core.storage.ducklake import ducklake_manager

                    ducklake_manager.delete_layer_table(self.user_id, layer_in.id)
                    logger.info(
                        "Cleaned up DuckLake table after failed import: %s",
                        layer_in.id,
                    )
                except Exception as cleanup_err:
                    logger.warning(
                        "Failed to cleanup DuckLake table %s: %s",
                        layer_in.id,
                        cleanup_err,
                    )
            raise RuntimeError(f"Layer import failed: {e}") from e

        # Step 3: Cleanup uploaded file directory
        # file_path is like: data/{user_id}/{dataset_id}/file.gpkg
        upload_dir = os.path.dirname(file_path)  # data/{user_id}/{dataset_id}
        user_upload_dir = os.path.dirname(upload_dir)  # data/{user_id}
        if upload_dir and os.path.isdir(upload_dir):
            await async_delete_dir(upload_dir)
            logger.info("Cleaned up upload directory: %s", upload_dir)
            # Also remove parent user folder if empty
            if user_upload_dir and os.path.isdir(user_upload_dir):
                try:
                    os.rmdir(user_upload_dir)  # Only removes if empty
                    logger.info(
                        "Cleaned up empty user upload directory: %s", user_upload_dir
                    )
                except OSError:
                    pass  # Not empty, that's fine

        result = {
            "msg": "Layer imported successfully",
            "layer_id": str(layer_id),
            "table_name": import_result.table_name,
            "feature_count": import_result.feature_count,
            "geometry_type": import_result.geometry_type,
        }

        logger.info("Layer import complete: %s", result)
        return result, layer_id

    @run_background_or_immediately(settings)
    @job_init()
    async def import_file_job(
        self: "CRUDLayerImportDuckLake",
        file_path: str,
        layer_in: ILayerFromDatasetCreate,
        file_metadata: dict[str, Any] | None = None,
        project_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Import file as a background job.

        Same as import_file but runs in background with job tracking.
        """
        result, _ = await self.import_file(
            file_path=file_path,
            layer_in=layer_in,
            file_metadata=file_metadata,
            project_id=project_id,
        )
        return result

    async def import_from_wfs(
        self: "CRUDLayerImportDuckLake",
        wfs_url: str,
        layer_in: ILayerFromDatasetCreate,
        wfs_layer_name: str | None = None,
        project_id: UUID | None = None,
    ) -> tuple[dict[str, Any], UUID]:
        """Import a layer from a WFS service.

        This method is atomic: if any step fails, previously created resources
        are cleaned up (DuckLake table deleted, no layer row created).

        Args:
            wfs_url: WFS service URL
            layer_in: Layer creation schema
            wfs_layer_name: Specific layer to import (None = first layer)
            project_id: Optional project to associate layer with

        Returns:
            Tuple of (result dict, layer_id)

        Raises:
            RuntimeError: If import fails at any step
        """
        logger.info("Importing from WFS: %s", wfs_url)

        import_result = None
        try:
            import_result = layer_importer.import_from_wfs(
                user_id=self.user_id,
                layer_id=layer_in.id,
                wfs_url=wfs_url,
                layer_name=wfs_layer_name,
                target_crs="EPSG:4326",
            )

            layer_id = await self._create_layer_metadata(
                layer_in=layer_in,
                import_result=import_result,
                file_metadata=None,
                project_id=project_id,
            )
        except Exception as e:
            # Cleanup: delete DuckLake table if it was created
            if import_result is not None:
                try:
                    from core.storage.ducklake import ducklake_manager

                    ducklake_manager.delete_layer_table(self.user_id, layer_in.id)
                    logger.info(
                        "Cleaned up DuckLake table after failed WFS import: %s",
                        layer_in.id,
                    )
                except Exception as cleanup_err:
                    logger.warning(
                        "Failed to cleanup DuckLake table %s: %s",
                        layer_in.id,
                        cleanup_err,
                    )
            raise RuntimeError(f"WFS import failed: {e}") from e

        return {
            "msg": "WFS layer imported successfully",
            "layer_id": str(layer_id),
            "table_name": import_result.table_name,
            "feature_count": import_result.feature_count,
        }, layer_id

    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------

    async def _create_layer_metadata(
        self: "CRUDLayerImportDuckLake",
        layer_in: ILayerFromDatasetCreate,
        import_result: LayerImportResult,
        file_metadata: dict[str, Any] | None,
        project_id: UUID | None,
    ) -> UUID:
        """Create layer metadata record in PostgreSQL.

        Args:
            layer_in: Layer creation input
            import_result: Result from DuckLake import
            file_metadata: Optional file validation metadata
            project_id: Optional project to link to

        Returns:
            Created layer UUID
        """
        # Build columns info from import result
        columns_info = {col["name"]: col["type"] for col in import_result.columns}

        # Build additional attributes based on layer type
        attrs = self._build_layer_attributes(
            import_result=import_result,
            columns_info=columns_info,
            file_metadata=file_metadata,
        )

        # Check/alter layer name if duplicate
        layer_in.name = await self._check_layer_name(
            layer_in=layer_in,
            project_id=project_id,
        )

        # Create layer model
        layer_model = Layer(
            **layer_in.model_dump(exclude_none=True),
            **attrs,
            job_id=self.job_id,
        )

        # Get size from DuckLake metadata
        layer_model.size = await self._get_layer_size(self.async_session, import_result)

        # Persist to database
        from core.crud.crud_layer import CRUDLayer

        layer: Layer = await CRUDLayer(Layer).create(
            db=self.async_session,
            obj_in=layer_model.model_dump(),
        )
        assert layer.id is not None

        # Link to project if specified
        if project_id:
            await crud_layer_project.create(
                async_session=self.async_session,
                layer_ids=[layer.id],
                project_id=project_id,
            )

        logger.info("Created layer metadata: id=%s name=%s", layer.id, layer.name)
        return layer.id

    def _build_layer_attributes(
        self: "CRUDLayerImportDuckLake",
        import_result: LayerImportResult,
        columns_info: dict[str, str],
        file_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build additional layer attributes from import result."""
        attrs: dict[str, Any] = {
            "user_id": self.user_id,
            "attribute_mapping": {},  # Empty - not used for DuckLake layers
            "properties": {},  # Will be set with style below if feature layer
        }

        # Get file type from metadata if available
        if file_metadata and "file_ending" in file_metadata:
            attrs["upload_file_type"] = file_metadata["file_ending"]
        elif import_result.source_format:
            attrs["upload_file_type"] = import_result.source_format

        # Determine if feature or table layer
        if import_result.geometry_type:
            geom_type = map_geometry_type(import_result.geometry_type)
            attrs["type"] = LayerType.feature
            attrs["feature_layer_type"] = FeatureType.standard
            attrs["feature_layer_geometry_type"] = geom_type

            # Set default style based on geometry type
            geom_type_enum = FeatureGeometryType(geom_type)
            attrs["properties"] = get_base_style(geom_type_enum)

            # Set extent
            if import_result.extent:
                attrs["extent"] = build_extent_wkt(import_result.extent)

            # Validate with schema
            attrs = IFeatureStandardCreateAdditionalAttributes(**attrs).model_dump()
        else:
            attrs["type"] = LayerType.table
            attrs = ITableCreateAdditionalAttributes(**attrs).model_dump()

        return attrs

    async def _check_layer_name(
        self: "CRUDLayerImportDuckLake",
        layer_in: ILayerFromDatasetCreate,
        project_id: UUID | None,
    ) -> str:
        """Check and alter layer name if duplicate exists."""
        from core.crud.crud_layer import CRUDLayer

        return await CRUDLayer(Layer).check_and_alter_layer_name(
            async_session=self.async_session,
            folder_id=layer_in.folder_id,
            layer_name=layer_in.name,
            project_id=project_id,
        )

    async def _get_layer_size(
        self: "CRUDLayerImportDuckLake",
        async_session: "AsyncSession",
        import_result: LayerImportResult,
    ) -> int:
        """Get layer size in bytes from DuckLake metadata.

        DuckLake stores file_size_bytes in the ducklake_table_stats table.
        This is more accurate and efficient than reading file sizes from disk.
        """
        user_schema = f"user_{str(import_result.user_id).replace('-', '')}"
        table_name = f"t_{str(import_result.layer_id).replace('-', '')}"

        # Query file_size_bytes from ducklake_table_stats via ducklake_table
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
        result = await async_session.execute(
            query,
            {"schema_name": user_schema, "table_name": table_name},
        )
        row = result.fetchone()
        return row.file_size_bytes if row else 0


# =============================================================================
# Layer Export CRUD
# =============================================================================


class CRUDLayerExportDuckLake:
    """CRUD for exporting layers from DuckLake storage.

    Exports layer data from DuckLake to various formats.
    """

    def __init__(
        self: "CRUDLayerExportDuckLake",
        layer_id: UUID,
        async_session: "AsyncSession",
        user_id: UUID,
    ) -> None:
        """Initialize the export CRUD.

        Args:
            layer_id: Layer UUID to export
            async_session: SQLAlchemy async session
            user_id: User UUID (for permissions/paths)
        """
        self.layer_id = layer_id
        self.user_id = user_id
        self.async_session = async_session
        self.export_dir = os.path.join(
            settings.DATA_DIR,
            str(self.user_id),
            str(self.layer_id),
        )

    async def export_to_file(
        self: "CRUDLayerExportDuckLake",
        output_format: str,
        file_name: str,
        target_crs: str | None = None,
        where_clause: str | None = None,
    ) -> str:
        """Export layer to a file.

        Args:
            output_format: Output format (geojson, gpkg, csv, etc.)
            file_name: Base name for output file
            target_crs: Optional target CRS for reprojection
            where_clause: Optional filter

        Returns:
            Path to exported file (or zip if multiple files)
        """
        logger.info(
            "Exporting layer %s to %s format",
            self.layer_id,
            output_format,
        )

        # Get layer metadata
        layer = await self._get_layer()

        # IMPORTANT: Use the layer owner's user_id for DuckLake lookup,
        # not the current user's user_id. DuckLake tables are stored as
        # lake.user_{OWNER_ID}.t_{LAYER_ID}
        owner_user_id = layer.user_id

        # Create export directory
        os.makedirs(self.export_dir, exist_ok=True)

        # Build output path
        output_path = os.path.join(
            self.export_dir,
            file_name,
            f"{file_name}.{output_format}",
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Export via LayerImporter
        layer_importer.export_layer(
            user_id=owner_user_id,
            layer_id=self.layer_id,
            output_path=output_path,
            output_format=output_format.upper(),
            target_crs=target_crs,
            query=where_clause,
        )

        # Create metadata file
        await self._create_metadata_file(layer, output_format, target_crs)

        # Zip the result
        zip_path = os.path.join(
            settings.DATA_DIR,
            str(self.user_id),
            f"{file_name}.zip",
        )
        await async_zip_directory(
            zip_path,
            os.path.join(self.export_dir, file_name),
        )

        # Cleanup
        await async_delete_dir(self.export_dir)

        return zip_path

    async def _get_layer(self: "CRUDLayerExportDuckLake") -> Layer:
        """Get layer metadata from PostgreSQL."""
        from core.crud.crud_layer import CRUDLayer

        return await CRUDLayer(Layer).get_internal(
            async_session=self.async_session,
            id=self.layer_id,
        )

    async def _create_metadata_file(
        self: "CRUDLayerExportDuckLake",
        layer: Layer,
        output_format: str,
        target_crs: str | None,
    ) -> None:
        """Create metadata.txt file for export."""
        metadata_path = os.path.join(self.export_dir, "metadata.txt")

        with open(metadata_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write(f"Layer Export: {layer.name}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Exported: {datetime.now().isoformat()}\n")
            f.write(f"Format: {output_format}\n")
            if target_crs:
                f.write(f"CRS: {target_crs}\n")
            f.write("-" * 60 + "\n")
            f.write(f"Name: {layer.name}\n")
            f.write(f"Description: {layer.description or 'N/A'}\n")
            f.write(f"Type: {layer.type}\n")
            if layer.tags:
                f.write(f"Tags: {', '.join(layer.tags)}\n")
            f.write(f"License: {layer.license or 'N/A'}\n")
            f.write(f"Attribution: {layer.attribution or 'N/A'}\n")
            f.write("=" * 60 + "\n")


# =============================================================================
# Layer Delete
# =============================================================================


async def delete_layer_ducklake(
    async_session: "AsyncSession",
    layer: Layer,
) -> None:
    """Delete layer data from DuckLake storage.

    Args:
        async_session: SQLAlchemy session (unused, kept for compatibility)
        layer: Layer model with user_id and id
    """
    logger.info("Deleting layer from DuckLake: %s", layer.id)
    layer_importer.delete_layer(user_id=layer.user_id, layer_id=layer.id)
