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
from core.schemas.layer import ILayerFromDatasetCreate
from core.schemas.style import get_base_style
from core.services.layer_import import LayerImportResult, layer_importer
from core.utils import async_delete_dir, async_zip_directory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Export timeout in seconds
EXPORT_TIMEOUT_SECONDS = 30


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
        project_id: UUID | None = None,
    ) -> tuple[dict[str, Any], UUID]:
        """Import a file into DuckLake and create layer metadata.

        This method is atomic: if any step fails, previously created resources
        are cleaned up (DuckLake table deleted, no layer row created).

        Args:
            file_path: Path to source file
            layer_in: Layer creation schema with name, folder_id, etc.
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

            layer_id = await self._create_layer(
                layer_in=layer_in,
                import_result=import_result,
                project_id=project_id,
            )
        except Exception as e:
            self._cleanup_on_failure(layer_in.id, import_result, "file")
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
        project_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Import file as a background job.

        Same as import_file but runs in background with job tracking.
        """
        from core.schemas.job import JobStatusType

        result, _ = await self.import_file(
            file_path=file_path,
            layer_in=layer_in,
            project_id=project_id,
        )
        return {
            "status": JobStatusType.successful.value,
            "result": result,
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def import_from_s3_job(
        self: "CRUDLayerImportDuckLake",
        s3_key: str,
        layer_in: ILayerFromDatasetCreate,
        project_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Import file from S3 as a background job.

        Downloads file from S3 and imports using goatlib + DuckLake.

        Args:
            s3_key: S3 key for the file to import
            layer_in: Layer creation schema
            project_id: Optional project to link to

        Returns:
            Job result dict with status and layer info
        """
        from core.schemas.job import JobStatusType

        logger.info(
            "Importing from S3: %s for user=%s",
            s3_key,
            self.user_id,
        )

        import_result = None
        try:
            # Import directly from S3 using LayerImporter
            import_result = layer_importer.import_from_s3(
                user_id=self.user_id,
                layer_id=layer_in.id,
                s3_key=s3_key,
                target_crs="EPSG:4326",
            )

            layer_id = await self._create_layer(
                layer_in=layer_in,
                import_result=import_result,
                project_id=project_id,
            )
        except Exception as e:
            self._cleanup_on_failure(layer_in.id, import_result, "S3")
            raise RuntimeError(f"S3 import failed: {e}") from e

        result = {
            "msg": "Layer imported successfully from S3",
            "layer_id": str(layer_id),
            "table_name": import_result.table_name,
            "feature_count": import_result.feature_count,
            "geometry_type": import_result.geometry_type,
        }

        logger.info("S3 layer import complete: %s", result)
        return {
            "status": JobStatusType.successful.value,
            "result": result,
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def import_from_wfs_job(
        self: "CRUDLayerImportDuckLake",
        wfs_url: str,
        layer_in: ILayerFromDatasetCreate,
        wfs_layer_name: str | None = None,
        project_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Import from WFS as a background job.

        Args:
            wfs_url: WFS service URL
            layer_in: Layer creation schema
            wfs_layer_name: Specific layer to import (None = first layer)
            project_id: Optional project to link to

        Returns:
            Job result dict with status and layer info
        """
        from core.schemas.job import JobStatusType

        result, _ = await self.import_from_wfs(
            wfs_url=wfs_url,
            layer_in=layer_in,
            wfs_layer_name=wfs_layer_name,
            project_id=project_id,
        )
        return {
            "status": JobStatusType.successful.value,
            "result": result,
        }

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

            layer_id = await self._create_layer(
                layer_in=layer_in,
                import_result=import_result,
                project_id=project_id,
            )
        except Exception as e:
            self._cleanup_on_failure(layer_in.id, import_result, "WFS")
            raise RuntimeError(f"WFS import failed: {e}") from e

        return {
            "msg": "WFS layer imported successfully",
            "layer_id": str(layer_id),
            "table_name": import_result.table_name,
            "feature_count": import_result.feature_count,
        }, layer_id

    def _cleanup_on_failure(
        self: "CRUDLayerImportDuckLake",
        layer_id: UUID,
        import_result: LayerImportResult | None,
        source: str,
    ) -> None:
        """Delete DuckLake table if import failed after table creation."""
        if import_result is None:
            return
        try:
            from core.storage.ducklake import ducklake_manager

            ducklake_manager.delete_layer_table(self.user_id, layer_id)
            logger.info(
                "Cleaned up DuckLake table after failed %s import: %s", source, layer_id
            )
        except Exception as err:
            logger.warning("Failed to cleanup DuckLake table %s: %s", layer_id, err)

    async def _create_layer(
        self: "CRUDLayerImportDuckLake",
        layer_in: ILayerFromDatasetCreate,
        import_result: LayerImportResult,
        project_id: UUID | None,
    ) -> UUID:
        """Create Layer row in PostgreSQL after successful goatlib import."""
        from core.crud.crud_layer import CRUDLayer
        from core.db.models.layer import FileUploadType

        # Check/alter layer name if duplicate exists
        layer_name = await CRUDLayer(Layer).check_and_alter_layer_name(
            async_session=self.async_session,
            folder_id=layer_in.folder_id,
            layer_name=layer_in.name,
            project_id=project_id,
        )

        # Validate upload_file_type against enum, fallback to None if not valid
        source_format = import_result.source_format
        try:
            upload_file_type = FileUploadType(source_format) if source_format else None
        except ValueError:
            logger.warning(
                "Unknown upload_file_type '%s', setting to None", source_format
            )
            upload_file_type = None

        # Build layer data from import result
        layer_data = {
            **layer_in.model_dump(exclude_none=True),
            "name": layer_name,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "upload_file_type": upload_file_type,
        }

        # Set type based on geometry
        if import_result.geometry_type:
            geom_type = map_geometry_type(import_result.geometry_type)
            layer_data["type"] = LayerType.feature
            layer_data["feature_layer_type"] = FeatureType.standard
            layer_data["feature_layer_geometry_type"] = geom_type
            layer_data["properties"] = get_base_style(FeatureGeometryType(geom_type))
            if import_result.extent:
                layer_data["extent"] = build_extent_wkt(import_result.extent)
        else:
            layer_data["type"] = LayerType.table

        # Get size from DuckLake
        layer_data["size"] = await self._get_layer_size(
            self.async_session, import_result
        )

        # Create layer row
        layer: Layer = await CRUDLayer(Layer).create(
            db=self.async_session,
            obj_in=layer_data,
        )
        assert layer.id is not None

        # Link to project if specified
        if project_id:
            await crud_layer_project.create(
                async_session=self.async_session,
                layer_ids=[layer.id],
                project_id=project_id,
            )

        logger.info("Created layer: id=%s name=%s", layer.id, layer_name)
        return layer.id

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


class CRUDLayerExportDuckLake(CRUDFailedJob):
    """CRUD for exporting layers from DuckLake storage.

    Exports layer data from DuckLake to various formats.
    Supports both sync exports and background job exports with S3 upload.
    """

    def __init__(
        self: "CRUDLayerExportDuckLake",
        job_id: UUID | None,
        background_tasks: BackgroundTasks,
        async_session: "AsyncSession",
        user_id: UUID,
        layer_id: UUID,
    ) -> None:
        """Initialize the export CRUD.

        Args:
            job_id: Job UUID for tracking (None for sync exports)
            background_tasks: FastAPI background tasks
            async_session: SQLAlchemy async session
            user_id: User UUID (for permissions/paths)
            layer_id: Layer UUID to export
        """
        super().__init__(job_id, background_tasks, async_session, user_id)
        self.layer_id = layer_id
        self.export_dir = os.path.join(
            settings.DATA_DIR,
            str(self.user_id),
            str(self.layer_id),
        )

    @run_background_or_immediately(settings)
    @job_init()
    async def export_to_file_job(
        self: "CRUDLayerExportDuckLake",
        output_format: str,
        file_name: str,
        target_crs: str | None = None,
        where_clause: str | None = None,
    ) -> dict[str, Any]:
        """Export layer as a background job with S3 upload.

        Runs the export in background and uploads result to S3.

        Args:
            output_format: Output format (geojson, gpkg, csv, etc.)
            file_name: Base name for output file
            target_crs: Optional target CRS for reprojection
            where_clause: Optional filter

        Returns:
            Job result dict with s3_key for download
        """
        from core.schemas.job import JobStatusType
        from core.services.s3 import s3_service

        MAX_RETRIES = 3
        RETRY_DELAY_SECONDS = 1

        logger.info(
            "Starting export job for layer %s to %s format",
            self.layer_id,
            output_format,
        )

        zip_path = None
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Perform the export (creates zip file locally)
                zip_path = await self._export_to_file_internal(
                    output_format=output_format,
                    file_name=file_name,
                    target_crs=target_crs,
                    where_clause=where_clause,
                )
                # Success - break out of retry loop
                break

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                # Check if this is a retryable connection error
                is_retryable = any(
                    keyword in error_str
                    for keyword in ["ssl", "eof", "connection", "timeout", "network"]
                )

                if is_retryable and attempt < MAX_RETRIES:
                    import asyncio

                    logger.warning(
                        "Export attempt %d/%d failed with retryable error: %s. Retrying in %ds...",
                        attempt,
                        MAX_RETRIES,
                        str(e)[:200],
                        RETRY_DELAY_SECONDS,
                    )
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    continue
                else:
                    # Non-retryable error or max retries reached
                    raise

        if zip_path is None:
            raise RuntimeError(
                f"Export failed after {MAX_RETRIES} attempts: {last_error}"
            )

        # Generate S3 key for the export
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = s3_service.build_s3_key(
                settings.S3_BUCKET_PATH or "",
                "exports",
                str(self.user_id),
                f"{file_name}_{timestamp}.zip",
            )

            # Upload to S3
            import io

            with open(zip_path, "rb") as f:
                file_content = f.read()
                file_size = len(file_content)

            s3_service.upload_file(
                file_content=io.BytesIO(file_content),
                bucket_name=settings.S3_BUCKET_NAME or "goat",
                s3_key=s3_key,
                content_type="application/zip",
            )

            # Cleanup local file
            if os.path.exists(zip_path):
                os.remove(zip_path)
            # Remove parent dir if empty
            parent_dir = os.path.dirname(zip_path)
            if parent_dir and os.path.isdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                except OSError:
                    pass

            # Generate presigned download URL (valid for 24 hours)
            download_url = s3_service.generate_presigned_download_url(
                bucket_name=settings.S3_BUCKET_NAME or "goat",
                s3_key=s3_key,
                expires_in=86400,  # 24 hours
                filename=f"{file_name}.zip",
            )

            result_payload = {
                "s3_key": s3_key,
                "download_url": download_url,
                "file_name": f"{file_name}.zip",
                "file_size_bytes": file_size,
                "format": output_format,
                "layer_id": str(self.layer_id),
            }

            logger.info(
                "Export job completed. S3 key: %s, file_name: %s.zip",
                s3_key,
                file_name,
            )

            return {"status": JobStatusType.successful.value, "result": result_payload}

        except asyncio.TimeoutError:
            # Cleanup on timeout
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            raise RuntimeError(
                f"Export timed out after {EXPORT_TIMEOUT_SECONDS} seconds. "
                "The dataset may be too large for export."
            )
        except Exception as e:
            # Cleanup on failure
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            raise RuntimeError(f"Export failed: {e}") from e

    async def _export_to_file_internal(
        self: "CRUDLayerExportDuckLake",
        output_format: str,
        file_name: str,
        target_crs: str | None = None,
        where_clause: str | None = None,
    ) -> str:
        """Internal export logic - creates local zip file.

        The blocking DuckDB/GDAL export is run in a thread pool to avoid
        blocking the event loop. Uses DuckDB's interrupt() for timeout.

        Args:
            output_format: Output format (geojson, gpkg, csv, etc.)
            file_name: Base name for output file
            target_crs: Optional target CRS for reprojection
            where_clause: Optional filter

        Returns:
            Path to exported zip file
        """
        import asyncio

        logger.info(
            "Exporting layer %s to %s format (timeout: %ds)",
            self.layer_id,
            output_format,
            EXPORT_TIMEOUT_SECONDS,
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

        # Run the blocking export in a thread pool to avoid blocking the event loop
        # Timeout is handled at the DuckDB level via con.interrupt()
        await asyncio.to_thread(
            layer_importer.export_layer,
            user_id=owner_user_id,
            layer_id=self.layer_id,
            output_path=output_path,
            output_format=output_format.upper(),
            target_crs=target_crs,
            query=where_clause,
            timeout_seconds=EXPORT_TIMEOUT_SECONDS,
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

        # Cleanup export directory
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
