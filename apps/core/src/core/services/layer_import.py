"""Layer import service using goatlib for conversion and DuckLake for storage.

This service replaces the old ogr2ogr-based pipeline with:
1. goatlib.io.IOConverter for file conversion to GeoParquet
2. ducklake_manager singleton for storage in DuckLake

Supported formats:
- Vector: GeoJSON, GPKG, Shapefile (ZIP), KML/KMZ
- Tabular: CSV, XLSX
- Remote: WFS services
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from core.core.config import settings
from core.schemas.job import Msg, MsgType
from core.storage.ducklake import ducklake_manager
from goatlib.io.converter import IOConverter
from goatlib.io.remote_source.wfs import from_wfs
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


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
class FileValidationResult:
    """Result of file validation using goatlib."""

    file_path: str
    data_types: dict[str, Any]
    msg: Msg
    feature_count: int | None = None
    geometry_type: str | None = None
    format: str | None = None


class LayerImporter:
    """Service for importing files into DuckLake storage.

    Uses goatlib IOConverter to convert any supported format to GeoParquet,
    then ingests into DuckLake.

    Example:
        importer = LayerImporter()
        result = importer.import_file(
            user_id=user_id,
            layer_id=layer_id,
            file_path="/path/to/data.geojson",
        )
    """

    def __init__(self: "LayerImporter") -> None:
        """Initialize the layer importer."""
        self.converter = IOConverter()
        self.ducklake = ducklake_manager

    def import_file(
        self: "LayerImporter",
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

        Raises:
            ValueError: If file format is not supported
            RuntimeError: If conversion or ingestion fails
        """
        logger.info(
            "Importing file: %s for user=%s layer=%s",
            file_path,
            user_id,
            layer_id,
        )

        # Create temp directory for intermediate parquet file
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

        # Build result
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
        self: "LayerImporter",
        user_id: UUID,
        layer_id: UUID,
        s3_key: str,
        target_crs: str = "EPSG:4326",
    ) -> LayerImportResult:
        """Import a file from S3 into DuckLake storage.

        Uses a presigned URL so goatlib can read via HTTP without S3 credentials.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            s3_key: S3 key (path within bucket)
            target_crs: Target CRS for reprojection

        Returns:
            LayerImportResult with table info
        """
        import os

        from core.services.s3 import s3_service

        # Extract original file extension from S3 key
        original_filename = os.path.basename(s3_key)
        source_format = os.path.splitext(original_filename)[1].lstrip(".").lower()
        logger.info("S3 import: key=%s original_format=%s", s3_key, source_format)

        # Generate presigned URL - goatlib reads as HTTP, no S3 creds needed
        logger.info("Generating presigned URL for: %s", s3_key)
        presigned_url = s3_service.generate_presigned_download_url(
            bucket_name=settings.S3_BUCKET_NAME,
            s3_key=s3_key,
            expires_in=3600,  # 1 hour should be enough for import
        )
        logger.info("Presigned URL generated, starting import...")

        result = self.import_file(
            user_id=user_id,
            layer_id=layer_id,
            file_path=presigned_url,
            target_crs=target_crs,
        )

        # Override source_format with original file extension (not "parquet")
        result.source_format = source_format

        logger.info("S3 import complete for: %s", s3_key)
        return result

    def import_from_wfs(
        self: "LayerImporter",
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

            # Get first result (or only result if single layer)
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

    def delete_layer(self: "LayerImporter", user_id: UUID, layer_id: UUID) -> bool:
        """Delete a layer from DuckLake storage.

        Args:
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            True if deleted, False if didn't exist
        """
        logger.info("Deleting layer: user=%s layer=%s", user_id, layer_id)
        return self.ducklake.delete_layer_table(user_id, layer_id)

    def get_layer_info(
        self: "LayerImporter", user_id: UUID, layer_id: UUID
    ) -> dict[str, Any]:
        """Get metadata about a layer in DuckLake.

        Args:
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            Dict with table_name, feature_count, columns, geometry info
        """
        return self.ducklake.get_layer_info(user_id, layer_id)

    def validate_file(self: "LayerImporter", file_path: str) -> DatasetMetadata:
        """Validate a file without importing it.

        Uses goatlib to check if the file can be converted.

        Args:
            file_path: Path to file to validate

        Returns:
            DatasetMetadata with file info

        Raises:
            ValueError: If file is not valid/supported
        """
        logger.info("Validating file: %s", file_path)

        with tempfile.TemporaryDirectory(prefix="goat_validate_") as temp_dir:
            temp_parquet = Path(temp_dir) / "validate.parquet"
            metadata = self.converter.to_parquet(
                src_path=file_path,
                out_path=str(temp_parquet),
            )
            return metadata

    def validate_file_with_metadata(
        self: "LayerImporter",
        file_path: str,
    ) -> FileValidationResult:
        """Validate a file and return metadata using goatlib.

        Args:
            file_path: Path to file to validate (local or remote)

        Returns:
            FileValidationResult with validation info

        Raises:
            ValueError: If file format is not supported or validation fails
        """
        logger.info("Validating file: %s", file_path)

        with tempfile.TemporaryDirectory(prefix="goat_validate_") as temp_dir:
            temp_parquet = Path(temp_dir) / "validate.parquet"

            # Convert to parquet to validate
            metadata = self.converter.to_parquet(
                src_path=file_path,
                out_path=str(temp_parquet),
            )

            # Read schema from parquet
            import duckdb

            con = duckdb.connect(":memory:")
            con.execute("INSTALL spatial; LOAD spatial;")

            schema_result = con.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{temp_parquet}')"
            ).fetchall()
            con.close()

            # Build simple data_types dict with column names and types
            columns = {col_name: col_type for col_name, col_type, *_ in schema_result}

            return FileValidationResult(
                file_path=file_path,
                data_types={"columns": columns},
                msg=Msg(type=MsgType.info, text="File is valid."),
                feature_count=metadata.feature_count,
                geometry_type=metadata.geometry_type,
                format=metadata.format,
            )

    def export_layer_to_parquet(
        self: "LayerImporter",
        user_id: UUID,
        layer_id: UUID,
        output_path: str,
        query: str | None = None,
    ) -> str:
        """Export a layer from DuckLake to a GeoParquet file.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            output_path: Path for output parquet file
            query: Optional WHERE clause for filtering

        Returns:
            Path to the exported parquet file

        Raises:
            ValueError: If layer doesn't exist or export fails
        """
        logger.info(
            "Exporting layer to parquet: user=%s layer=%s",
            user_id,
            layer_id,
        )

        # Export from DuckLake to parquet using export_to_format
        self.ducklake.export_to_format(
            user_id=user_id,
            layer_id=layer_id,
            output_path=output_path,
            output_format="PARQUET",
            where=query,
        )

        return output_path

    def export_layer(
        self: "LayerImporter",
        user_id: UUID,
        layer_id: UUID,
        output_path: str,
        output_format: str = "GPKG",
        target_crs: str | None = None,
        query: str | None = None,
        timeout_seconds: int = 300,
    ) -> str:
        """Export a layer from DuckLake to any supported format.

        Uses DuckDB spatial extension for format conversion from DuckLake.
        Supports timeout to prevent very long exports.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            output_path: Path for output file
            output_format: Output format (GPKG, GEOJSON, CSV, etc.)
            target_crs: Optional target CRS for reprojection
            query: Optional WHERE clause for filtering
            timeout_seconds: Timeout in seconds (default 300 = 5 minutes)

        Returns:
            Path to the exported file

        Raises:
            ValueError: If layer doesn't exist or export fails
            TimeoutError: If export exceeds timeout
        """
        logger.info(
            "Exporting layer: user=%s layer=%s format=%s timeout=%ds",
            user_id,
            layer_id,
            output_format,
            timeout_seconds,
        )

        # Export from DuckLake using DuckDB's ST_Write with timeout support
        self.ducklake.export_to_format_with_timeout(
            user_id=user_id,
            layer_id=layer_id,
            output_path=output_path,
            output_format=output_format,
            target_crs=target_crs,
            where=query,
            timeout_seconds=timeout_seconds,
        )

        return output_path


# Singleton instance for convenience
layer_importer = LayerImporter()
