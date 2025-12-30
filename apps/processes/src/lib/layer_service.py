"""Layer import/export service for Processes API.

This module provides layer import and export functionality using goatlib
for file conversion and DuckLake for storage.

Architecture:
- goatlib IOConverter: Converts any format to GeoParquet
- DuckLake (via goatlib BaseDuckLakeManager): Stores GeoParquet files
- PostgreSQL: Layer metadata in customer.layer table
"""

import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from goatlib.io.converter import IOConverter
from goatlib.io.remote_source.wfs import from_wfs
from goatlib.models.io import DatasetMetadata
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from lib.config import get_settings
from lib.db import (
    FeatureGeometryType,
    FeatureType,
    FileUploadType,
    Layer,
    LayerProjectLink,
    LayerType,
)
from lib.ducklake import get_ducklake_manager
from lib.s3 import get_s3_service

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class LayerImportResult:
    """Result of a layer import operation."""

    layer_id: UUID
    user_id: UUID
    table_name: str
    feature_count: int
    columns: list[dict[str, str]]
    geometry_type: str | None
    geometry_column: str | None
    extent: dict[str, float] | None
    source_format: str
    source_path: str


@dataclass
class LayerExportResult:
    """Result of a layer export operation."""

    layer_id: UUID
    s3_key: str
    download_url: str
    file_name: str
    file_size_bytes: int
    format: str


# =============================================================================
# Geometry Type Mapping
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
    """Map DuckDB geometry type to FeatureGeometryType enum value."""
    if not duckdb_type:
        return None
    return GEOMETRY_TYPE_MAP.get(duckdb_type.upper(), "polygon")


def build_extent_wkt(extent: dict[str, float]) -> str:
    """Build WKT MULTIPOLYGON from extent dict."""
    min_x = extent.get("xmin") or extent.get("min_x") or 0
    min_y = extent.get("ymin") or extent.get("min_y") or 0
    max_x = extent.get("xmax") or extent.get("max_x") or 0
    max_y = extent.get("ymax") or extent.get("max_y") or 0

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
# Base Style Generation
# =============================================================================


def get_base_style(geometry_type: FeatureGeometryType) -> Dict[str, Any]:
    """Get default style properties for a geometry type."""
    if geometry_type == FeatureGeometryType.point:
        return {
            "type": "circle",
            "paint": {
                "circle-radius": 5,
                "circle-color": "#3b82f6",
                "circle-stroke-width": 1,
                "circle-stroke-color": "#ffffff",
            },
        }
    elif geometry_type == FeatureGeometryType.line:
        return {
            "type": "line",
            "paint": {
                "line-color": "#3b82f6",
                "line-width": 2,
            },
        }
    else:  # polygon
        return {
            "type": "fill",
            "paint": {
                "fill-color": "#3b82f6",
                "fill-opacity": 0.5,
                "fill-outline-color": "#1e40af",
            },
        }


# =============================================================================
# Layer Importer
# =============================================================================


class LayerImporter:
    """Service for importing files into DuckLake storage.

    Uses goatlib IOConverter to convert any supported format to GeoParquet,
    then ingests into DuckLake.
    """

    def __init__(self) -> None:
        """Initialize the layer importer."""
        self.converter = IOConverter()
        self._ducklake = None

    @property
    def ducklake(self):
        """Lazy load DuckLake manager."""
        if self._ducklake is None:
            self._ducklake = get_ducklake_manager()
        return self._ducklake

    def import_file(
        self,
        user_id: UUID,
        layer_id: UUID,
        file_path: str,
        target_crs: str = "EPSG:4326",
    ) -> LayerImportResult:
        """Import a file into DuckLake storage.

        Args:
            user_id: User UUID (determines schema)
            layer_id: Layer UUID (determines table name)
            file_path: Path to source file (local, S3, or HTTP URL)
            target_crs: Target CRS for reprojection (default EPSG:4326)

        Returns:
            LayerImportResult with table info
        """
        logger.info(
            "Importing file: %s for user=%s layer=%s",
            file_path,
            user_id,
            layer_id,
        )

        with tempfile.TemporaryDirectory(prefix="goat_import_") as temp_dir:
            parquet_path = Path(temp_dir) / f"{layer_id}.parquet"

            # Step 1: Convert to GeoParquet using goatlib
            logger.info("Converting to GeoParquet: %s -> %s", file_path, parquet_path)
            metadata = self.converter.to_parquet(
                src_path=file_path,
                out_path=str(parquet_path),
                target_crs=target_crs,
            )
            logger.info("Conversion complete: %s", metadata.short_summary())

            # Step 2: Ingest into DuckLake
            logger.info("Ingesting into DuckLake: %s", parquet_path)
            table_info = self.ducklake.create_layer_from_parquet(
                user_id=user_id,
                layer_id=layer_id,
                parquet_path=str(parquet_path),
                target_crs=target_crs,
            )

        return LayerImportResult(
            layer_id=layer_id,
            user_id=user_id,
            table_name=table_info["table_name"],
            feature_count=table_info["feature_count"],
            columns=table_info["columns"],
            geometry_type=table_info.get("geometry_type"),
            geometry_column=table_info.get("geometry_column"),
            extent=table_info.get("extent"),
            source_format=metadata.format or "unknown",
            source_path=file_path,
        )

    def import_from_s3(
        self,
        user_id: UUID,
        layer_id: UUID,
        s3_key: str,
        target_crs: str = "EPSG:4326",
    ) -> LayerImportResult:
        """Import a file from S3 into DuckLake storage.

        Uses a presigned URL so goatlib can read via HTTP.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            s3_key: S3 key (path within bucket)
            target_crs: Target CRS for reprojection

        Returns:
            LayerImportResult with table info
        """
        settings = get_settings()
        s3_service = get_s3_service()

        # Extract original file extension from S3 key
        original_filename = os.path.basename(s3_key)
        source_format = os.path.splitext(original_filename)[1].lstrip(".").lower()
        logger.info("S3 import: key=%s original_format=%s", s3_key, source_format)

        # Generate presigned URL
        presigned_url = s3_service.generate_presigned_download_url(
            bucket_name=settings.S3_BUCKET_NAME,
            s3_key=s3_key,
            expires_in=3600,
        )
        logger.info("Presigned URL generated, starting import...")

        result = self.import_file(
            user_id=user_id,
            layer_id=layer_id,
            file_path=presigned_url,
            target_crs=target_crs,
        )

        # Override source_format with original file extension
        result.source_format = source_format

        logger.info("S3 import complete for: %s", s3_key)
        return result

    def import_from_wfs(
        self,
        user_id: UUID,
        layer_id: UUID,
        wfs_url: str,
        layer_name: str | None = None,
        target_crs: str = "EPSG:4326",
    ) -> LayerImportResult:
        """Import a layer from a WFS service into DuckLake storage.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            wfs_url: WFS service URL
            layer_name: Specific layer to import (None = first layer)
            target_crs: Target CRS for reprojection

        Returns:
            LayerImportResult with table info
        """
        logger.info("Importing from WFS: %s layer=%s", wfs_url, layer_name)

        with tempfile.TemporaryDirectory(prefix="goat_wfs_") as temp_dir:
            # Use goatlib WFS reader
            results = from_wfs(
                url=wfs_url,
                out_dir=temp_dir,
                layer=layer_name,
                target_crs=target_crs,
            )

            if not results or results == (None, None):
                raise ValueError(f"No data retrieved from WFS: {wfs_url}")

            # Get first result
            if isinstance(results, list):
                parquet_path, metadata = results[0]
            else:
                parquet_path, metadata = results

            # Ingest into DuckLake
            logger.info("Ingesting WFS data into DuckLake: %s", parquet_path)
            table_info = self.ducklake.create_layer_from_parquet(
                user_id=user_id,
                layer_id=layer_id,
                parquet_path=str(parquet_path),
                target_crs=target_crs,
            )

        return LayerImportResult(
            layer_id=layer_id,
            user_id=user_id,
            table_name=table_info["table_name"],
            feature_count=table_info["feature_count"],
            columns=table_info["columns"],
            geometry_type=table_info.get("geometry_type"),
            geometry_column=table_info.get("geometry_column"),
            extent=table_info.get("extent"),
            source_format="wfs",
            source_path=wfs_url,
        )

    def delete_layer(self, user_id: UUID, layer_id: UUID) -> bool:
        """Delete a layer from DuckLake storage.

        Args:
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            True if deleted, False if didn't exist
        """
        logger.info("Deleting layer: user=%s layer=%s", user_id, layer_id)
        return self.ducklake.delete_layer_table(user_id, layer_id)

    def export_layer(
        self,
        user_id: UUID,
        layer_id: UUID,
        output_path: str,
        output_format: str = "GPKG",
        target_crs: str | None = None,
        query: str | None = None,
        timeout_seconds: int = 300,
    ) -> str:
        """Export a layer from DuckLake to any supported format.

        Uses DuckDB's COPY TO with GDAL for exporting.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            output_path: Path for output file
            output_format: Output format (GPKG, GEOJSON, CSV, etc.)
            target_crs: Optional target CRS for reprojection
            query: Optional WHERE clause for filtering
            timeout_seconds: Timeout in seconds

        Returns:
            Path to the exported file
        """
        logger.info(
            "Exporting layer: user=%s layer=%s format=%s",
            user_id,
            layer_id,
            output_format,
        )

        table_name = self.ducklake.get_layer_table_name(user_id, layer_id)
        where_clause = f"WHERE {query}" if query else ""

        # Map format names to GDAL driver names
        format_map = {
            "GPKG": "GPKG",
            "GEOPACKAGE": "GPKG",
            "GEOJSON": "GeoJSON",
            "KML": "KML",
            "SHP": "ESRI Shapefile",
            "SHAPEFILE": "ESRI Shapefile",
            "CSV": "CSV",
            "PARQUET": "Parquet",
        }

        gdal_format = format_map.get(output_format.upper(), output_format.upper())

        with self.ducklake.connection() as con:
            # Use DuckDB's COPY TO with GDAL writer
            con.execute(f"""
                COPY (
                    SELECT * FROM {table_name}
                    {where_clause}
                ) TO '{output_path}' 
                WITH (FORMAT GDAL, DRIVER '{gdal_format}')
            """)

        logger.info("Export complete: %s", output_path)
        return output_path

    def update_layer_dataset(
        self,
        user_id: UUID,
        layer_id: UUID,
        s3_key: str | None = None,
        wfs_url: str | None = None,
        wfs_layer_name: str | None = None,
        target_crs: str = "EPSG:4326",
    ) -> LayerImportResult:
        """Update a layer's data from S3 file or WFS refresh.

        This is a complete dataset replacement:
        1. Delete existing DuckLake data
        2. Import fresh data from source

        Args:
            user_id: User UUID (owner)
            layer_id: Layer UUID to update
            s3_key: S3 key for file import (mutually exclusive with wfs_url)
            wfs_url: WFS URL for refresh (mutually exclusive with s3_key)
            wfs_layer_name: WFS layer name (only for WFS refresh)
            target_crs: Target CRS for reprojection

        Returns:
            LayerImportResult with updated table info

        Raises:
            ValueError: If neither s3_key nor wfs_url provided
        """
        if not s3_key and not wfs_url:
            raise ValueError("Either s3_key or wfs_url must be provided for update")

        logger.info(
            "Updating layer dataset: user=%s layer=%s s3_key=%s wfs_url=%s",
            user_id,
            layer_id,
            s3_key,
            wfs_url,
        )

        # Step 1: Delete existing DuckLake data
        try:
            self.delete_layer(user_id, layer_id)
            logger.info("Deleted existing layer data")
        except Exception as e:
            logger.warning("Failed to delete existing data (may not exist): %s", str(e))

        # Step 2: Import fresh data
        if wfs_url:
            logger.info("Refreshing from WFS: %s", wfs_url)
            return self.import_from_wfs(
                user_id=user_id,
                layer_id=layer_id,
                wfs_url=wfs_url,
                layer_name=wfs_layer_name,
                target_crs=target_crs,
            )
        else:
            logger.info("Updating from S3: %s", s3_key)
            return self.import_from_s3(
                user_id=user_id,
                layer_id=layer_id,
                s3_key=s3_key,
                target_crs=target_crs,
            )


# =============================================================================
# Database Operations
# =============================================================================


async def create_layer_record(
    async_session: AsyncSession,
    user_id: UUID,
    layer_id: UUID,
    job_id: UUID,
    folder_id: UUID,
    name: str,
    import_result: LayerImportResult,
    description: str | None = None,
    tags: list[str] | None = None,
    data_type: str | None = None,
    other_properties: Dict[str, Any] | None = None,
    project_id: UUID | None = None,
) -> Layer:
    """Create a Layer record in PostgreSQL after successful import.

    Args:
        async_session: SQLAlchemy async session
        user_id: Owner user ID
        layer_id: Layer UUID
        job_id: Job ID for tracking
        folder_id: Folder to place layer in
        name: Layer name
        import_result: Result from layer import
        description: Optional description
        tags: Optional tags
        data_type: Feature data type (wfs, mvt, etc.)
        other_properties: External service properties
        project_id: Optional project to link to

    Returns:
        Created Layer object
    """
    # Check for duplicate name and alter if needed
    name = await _check_and_alter_layer_name(async_session, folder_id, name, project_id)

    # Validate upload_file_type
    source_format = import_result.source_format
    try:
        upload_file_type = FileUploadType(source_format) if source_format else None
    except ValueError:
        logger.warning("Unknown upload_file_type '%s', setting to None", source_format)
        upload_file_type = None

    # Determine layer type and properties based on geometry
    if import_result.geometry_type:
        geom_type = map_geometry_type(import_result.geometry_type)
        layer_type = LayerType.feature.value
        feature_layer_type = FeatureType.standard.value
        feature_layer_geometry_type = geom_type
        properties = get_base_style(FeatureGeometryType(geom_type))
    else:
        layer_type = LayerType.table.value
        feature_layer_type = None
        feature_layer_geometry_type = None
        properties = None

    # Get layer size from DuckLake
    size = await _get_layer_size(async_session, import_result)

    # Create layer
    layer = Layer(
        id=layer_id,
        user_id=user_id,
        folder_id=folder_id,
        name=name,
        description=description,
        tags=tags,
        type=layer_type,
        feature_layer_type=feature_layer_type,
        feature_layer_geometry_type=feature_layer_geometry_type,
        data_type=data_type,
        other_properties=other_properties,
        properties=properties,
        size=size,
        upload_file_type=upload_file_type.value if upload_file_type else None,
        job_id=job_id,
    )

    async_session.add(layer)

    # Link to project if specified
    if project_id:
        link = LayerProjectLink(layer_id=layer_id, project_id=project_id)
        async_session.add(link)

    await async_session.commit()

    logger.info("Created layer: id=%s name=%s", layer_id, name)
    return layer


async def _check_and_alter_layer_name(
    async_session: AsyncSession,
    folder_id: UUID,
    layer_name: str,
    project_id: UUID | None = None,
) -> str:
    """Check if layer name exists and alter if needed.

    Adds numeric suffix like "name (1)" if name already exists.
    """
    # Query existing layer names in folder
    query = text("""
        SELECT name FROM customer.layer
        WHERE folder_id = :folder_id
        AND name LIKE :name_pattern
    """)
    result = await async_session.execute(
        query,
        {"folder_id": str(folder_id), "name_pattern": f"{layer_name}%"},
    )
    existing_names = {row[0] for row in result.fetchall()}

    if layer_name not in existing_names:
        return layer_name

    # Find next available suffix
    counter = 1
    while True:
        new_name = f"{layer_name} ({counter})"
        if new_name not in existing_names:
            return new_name
        counter += 1


async def _get_layer_size(
    async_session: AsyncSession,
    import_result: LayerImportResult,
) -> int:
    """Get layer size in bytes from DuckLake metadata."""
    user_schema = f"user_{str(import_result.user_id).replace('-', '')}"
    table_name = f"t_{str(import_result.layer_id).replace('-', '')}"

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


async def delete_layer_data(
    async_session: AsyncSession,
    user_id: UUID,
    layer_id: UUID,
) -> None:
    """Delete layer data from DuckLake storage.

    Args:
        async_session: SQLAlchemy session (unused, kept for consistency)
        user_id: User UUID
        layer_id: Layer UUID
    """
    importer = LayerImporter()
    importer.delete_layer(user_id=user_id, layer_id=layer_id)


# Singleton instance
layer_importer = LayerImporter()
