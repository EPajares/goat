"""LayerExport Tool - Export layers to various file formats.

This tool exports layers from DuckLake to file formats like:
- GPKG (GeoPackage)
- GeoJSON
- CSV
- KML
- Shapefile

The exported file is uploaded to S3 and a presigned download URL is returned.

Usage:
    from goatlib.tools.layer_export import LayerExportParams, main

    result = main(LayerExportParams(
        user_id="...",
        layer_id="...",
        file_type="gpkg",
        file_name="my_export",
    ))
"""

import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Self

from pydantic import ConfigDict, Field

from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    SECTION_OPTIONS,
    SECTION_OUTPUT,
    ui_field,
    ui_sections,
)
from goatlib.tools.base import SimpleToolRunner
from goatlib.tools.schemas import ToolInputBase, ToolOutputBase

logger = logging.getLogger(__name__)


# Map user-friendly format names to GDAL driver names
FORMAT_MAP = {
    "gpkg": "GPKG",
    "geopackage": "GPKG",
    "geojson": "GeoJSON",
    "json": "GeoJSON",
    "kml": "KML",
    "shp": "ESRI Shapefile",
    "shapefile": "ESRI Shapefile",
    "csv": "CSV",
    "parquet": "Parquet",
}


class LayerExportParams(ToolInputBase):
    """Parameters for LayerExport tool."""

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            SECTION_OUTPUT,
            SECTION_OPTIONS,
        )
    )

    layer_id: str = Field(
        ...,
        description="ID of the layer to export",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            widget="layer-selector",
        ),
    )
    file_type: str = Field(
        ...,
        description="Output file format (gpkg, geojson, csv, kml, shp, parquet)",
        json_schema_extra=ui_field(
            section="output",
            field_order=1,
            widget="select",
            widget_options={
                "options": [
                    {"value": "gpkg", "label": "GeoPackage"},
                    {"value": "geojson", "label": "GeoJSON"},
                    {"value": "csv", "label": "CSV"},
                    {"value": "kml", "label": "KML"},
                    {"value": "shp", "label": "Shapefile"},
                    {"value": "parquet", "label": "Parquet"},
                ]
            },
        ),
    )
    file_name: str = Field(
        ...,
        description="Output filename (without extension)",
        json_schema_extra=ui_field(section="output", field_order=2),
    )
    crs: str | None = Field(
        None,
        description="Target CRS for reprojection (e.g., EPSG:4326)",
        json_schema_extra=ui_field(
            section="options",
            field_order=1,
            widget="crs-selector",
        ),
    )
    query: str | dict[str, Any] | None = Field(
        None,
        description="WHERE clause or CQL2 filter to filter features",
        json_schema_extra=ui_field(
            section="options",
            field_order=2,
            widget="sql-editor",
        ),
    )
    # user_id inherited from ToolInputBase


class LayerExportOutput(ToolOutputBase):
    """Output schema for LayerExport tool."""

    layer_id: str
    s3_key: str | None = None
    download_url: str | None = None
    file_name: str | None = None
    file_size_bytes: int | None = None
    format: str | None = None
    error: str | None = None


class LayerExportRunner(SimpleToolRunner):
    """Runner for LayerExport tool.

    Extends SimpleToolRunner for shared infrastructure (DuckDB, S3, settings, logging).
    """

    def _get_table_name(self: Self, layer_id: str, user_id: str) -> str:
        """Build DuckLake table name, looking up the actual layer owner.

        This correctly handles catalog/shared layers owned by other users.

        Args:
            layer_id: Layer UUID string
            user_id: Fallback user UUID if layer owner lookup fails

        Returns:
            Fully qualified table name: lake.user_{owner_id}.t_{layer_id}
        """
        # Look up the layer's actual owner
        layer_owner_id = self.get_layer_owner_id_sync(layer_id)
        if layer_owner_id is None:
            layer_owner_id = user_id  # Fallback to passed user_id

        user_schema = f"user_{layer_owner_id.replace('-', '')}"
        table_name = f"t_{layer_id.replace('-', '')}"
        return f"lake.{user_schema}.{table_name}"

    def _get_column_names(self: Self, table_name: str) -> list[str]:
        """Get column names for a table."""
        result = self.duckdb_con.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_schema || '.' || table_name = '{table_name.replace('lake.', '')}'"
        ).fetchall()
        return [row[0] for row in result]

    def _get_exportable_columns(self: Self, table_name: str) -> list[str]:
        """Get column names that can be exported to OGR formats.

        Excludes STRUCT and other complex types not supported by GDAL/OGR.

        Args:
            table_name: Full qualified table name (lake.schema.table)

        Returns:
            List of column names safe for OGR export
        """
        # Get columns with their types
        result = self.duckdb_con.execute(
            f"SELECT column_name, data_type FROM information_schema.columns "
            f"WHERE table_schema || '.' || table_name = '{table_name.replace('lake.', '')}'"
        ).fetchall()

        # Filter out STRUCT, MAP, and other complex types not supported by OGR
        unsupported_prefixes = ("STRUCT", "MAP", "UNION")
        exportable = []
        for col_name, col_type in result:
            if not col_type.upper().startswith(unsupported_prefixes):
                exportable.append(col_name)
            else:
                logger.debug(
                    "Excluding column '%s' with unsupported type '%s' from export",
                    col_name,
                    col_type,
                )

        return exportable

    def _convert_cql2_to_sql(
        self: Self, query: str | dict[str, Any] | None, table_name: str
    ) -> str | None:
        """Convert CQL2 filter dict to SQL WHERE clause.

        Args:
            query: SQL string or CQL2 filter dict
            table_name: Table name for column validation

        Returns:
            SQL WHERE clause string with parameters substituted, or None
        """
        if query is None:
            return None

        # If already a string, return as-is (raw SQL)
        if isinstance(query, str):
            return query

        # Convert CQL2 dict to SQL using shared utility
        try:
            from goatlib.storage import cql_to_where_clause

            column_names = self._get_column_names(table_name)
            # Use inline=True since COPY doesn't support parameterized queries
            return cql_to_where_clause(query, column_names, "geometry", inline=True)
        except Exception as e:
            logger.warning("Failed to convert CQL2 filter to SQL: %s", e)
            return None

    def _export_to_file(
        self: Self,
        layer_id: str,
        user_id: str,
        output_path: str,
        output_format: str,
        crs: str | None = None,
        query: str | dict[str, Any] | None = None,
    ) -> None:
        """Export layer from DuckLake to file.

        Args:
            layer_id: Layer UUID
            user_id: User UUID (fallback if layer owner lookup fails)
            output_path: Path for output file
            output_format: GDAL driver name (GPKG, GeoJSON, etc.)
            crs: Target CRS for reprojection (e.g., "EPSG:4326")
            query: WHERE clause filter (string or CQL2 dict)
        """
        table_name = self._get_table_name(layer_id, user_id)

        # Get columns that can be exported to OGR formats
        # (excludes STRUCT, MAP, and other unsupported types)
        exportable_columns = self._get_exportable_columns(table_name)

        # Build column selection, applying CRS transformation to geometry if needed
        # DuckDB ST_Transform requires both source and target CRS
        # Data is stored in EPSG:4326
        source_crs = "EPSG:4326"
        column_exprs = []
        for col in exportable_columns:
            if col == "geometry" and crs:
                # Transform geometry from source CRS to target CRS
                column_exprs.append(
                    f"ST_Transform(\"geometry\", '{source_crs}', '{crs}') AS \"geometry\""
                )
            else:
                column_exprs.append(f'"{col}"')
        columns_sql = ", ".join(column_exprs)

        # Convert CQL2 filter to SQL if needed
        sql_query = self._convert_cql2_to_sql(query, table_name)
        where_clause = f"WHERE {sql_query}" if sql_query else ""

        logger.info(
            "Exporting layer: table=%s, format=%s, output=%s, crs=%s",
            table_name,
            output_format,
            output_path,
            crs,
        )

        # Build GDAL COPY options
        # SRS sets the spatial reference metadata in the output file
        srs_option = f", SRS '{crs}'" if crs else ""

        # Use DuckDB's COPY TO with GDAL writer
        self.duckdb_con.execute(f"""
            COPY (
                SELECT {columns_sql} FROM {table_name}
                {where_clause}
            ) TO '{output_path}'
            WITH (FORMAT GDAL, DRIVER '{output_format}'{srs_option})
        """)

        logger.info("Export complete: %s", output_path)

    def _create_zip_with_metadata(
        self: Self,
        source_dir: str,
        zip_path: str,
        file_name: str,
        file_type: str,
        crs: str | None,
    ) -> None:
        """Create zip file with exported data and metadata.

        Args:
            source_dir: Directory containing exported file(s)
            zip_path: Output zip file path
            file_name: Base filename
            file_type: Export format
            crs: CRS used for export
        """
        # Create metadata file
        metadata_path = os.path.join(source_dir, "metadata.txt")
        with open(metadata_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write(f"GOAT Layer Export: {file_name}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Exported: {datetime.now().isoformat()}\n")
            f.write(f"Format: {file_type}\n")
            if crs:
                f.write(f"CRS: {crs}\n")
            f.write("=" * 60 + "\n")

        # Create zip
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)

    def _upload_to_s3(self: Self, file_path: str, user_id: str, file_name: str) -> str:
        """Upload file to S3 and return the S3 key.

        Args:
            file_path: Local file path
            user_id: User UUID for path prefix
            file_name: Filename for S3 key

        Returns:
            S3 key
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"users/{user_id}/exports/{file_name}_{timestamp}.zip"

        logger.info("Uploading to S3: %s", s3_key)

        with open(file_path, "rb") as f:
            self.s3_client.upload_fileobj(
                f,
                self.settings.s3_bucket_name,
                s3_key,
                ExtraArgs={"ContentType": "application/zip"},
            )

        logger.info("Upload complete: %s", s3_key)
        return s3_key

    def _generate_presigned_url(self: Self, s3_key: str, file_name: str) -> str:
        """Generate presigned download URL.

        Args:
            s3_key: S3 object key
            file_name: Filename for Content-Disposition header

        Returns:
            Presigned URL (valid for 24 hours)
        """
        # Use public S3 client to generate URLs accessible from outside the cluster
        # The s3_public_client MUST be configured with the public endpoint URL
        # (e.g., localhost:9000) for the signature to be valid when accessed from browser
        url = self.s3_public_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.settings.s3_bucket_name,
                "Key": s3_key,
                "ResponseContentDisposition": f'attachment; filename="{file_name}"',
            },
            ExpiresIn=86400,  # 24 hours
        )

        return url

    def run(self: Self, params: LayerExportParams) -> dict:
        """Run the layer export.

        Args:
            params: Export parameters

        Returns:
            LayerExportOutput as dict
        """
        if self.settings is None:
            raise RuntimeError("Settings not initialized. Call init_from_env() first.")

        logger.info(
            "Starting layer export: user=%s, layer=%s, format=%s",
            params.user_id,
            params.layer_id,
            params.file_type,
        )

        # Build wm_labels for Windmill job tracking
        wm_labels: list[str] = []
        if params.triggered_by_email:
            wm_labels.append(params.triggered_by_email)

        output = LayerExportOutput(
            layer_id=params.layer_id,
            name=params.file_name,
            folder_id="",
            user_id=params.user_id,
            format=params.file_type,
            wm_labels=wm_labels,
        )

        export_dir = None

        try:
            # Validate format
            gdal_format = FORMAT_MAP.get(params.file_type.lower())
            if not gdal_format:
                raise ValueError(
                    f"Unsupported format: {params.file_type}. "
                    f"Supported: {', '.join(FORMAT_MAP.keys())}"
                )

            # Create temp directory
            export_dir = tempfile.mkdtemp(prefix="goat_export_")
            output_dir = os.path.join(export_dir, params.file_name)
            os.makedirs(output_dir, exist_ok=True)

            # Export file
            output_path = os.path.join(
                output_dir, f"{params.file_name}.{params.file_type}"
            )
            self._export_to_file(
                layer_id=params.layer_id,
                user_id=params.user_id,
                output_path=output_path,
                output_format=gdal_format,
                crs=params.crs,
                query=params.query,
            )

            # Create zip
            zip_path = os.path.join(export_dir, f"{params.file_name}.zip")
            self._create_zip_with_metadata(
                source_dir=output_dir,
                zip_path=zip_path,
                file_name=params.file_name,
                file_type=params.file_type,
                crs=params.crs,
            )

            # Get file size
            file_size = os.path.getsize(zip_path)
            output.file_size_bytes = file_size

            # Upload to S3
            s3_key = self._upload_to_s3(
                file_path=zip_path,
                user_id=params.user_id,
                file_name=params.file_name,
            )
            output.s3_key = s3_key

            # Generate download URL
            download_url = self._generate_presigned_url(
                s3_key=s3_key,
                file_name=f"{params.file_name}.zip",
            )
            output.download_url = download_url
            output.file_name = f"{params.file_name}.zip"

            logger.info(
                "Layer export complete: layer=%s, size=%d bytes, s3_key=%s",
                params.layer_id,
                file_size,
                s3_key,
            )

        except Exception as e:
            output.error = str(e)
            logger.error("Layer export failed: %s", e)
            # Re-raise to mark job as failed in Windmill
            raise

        finally:
            # Cleanup temp files
            if export_dir and os.path.exists(export_dir):
                try:
                    shutil.rmtree(export_dir)
                except Exception as cleanup_error:
                    logger.warning("Failed to cleanup: %s", cleanup_error)

            self.cleanup()

        return output.model_dump()


def main(params: LayerExportParams) -> dict:
    """Windmill entry point for LayerExport.

    Args:
        params: Validated LayerExportParams

    Returns:
        LayerExportOutput as dict
    """
    runner = LayerExportRunner()
    runner.init_from_env()
    return runner.run(params)
