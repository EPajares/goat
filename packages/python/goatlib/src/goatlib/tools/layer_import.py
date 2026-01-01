"""Layer import tool for Windmill.

Imports geospatial data from S3 or WFS into DuckLake storage.
Supports all formats that goatlib IOConverter handles (GeoPackage, Shapefile, GeoJSON, etc).
"""

import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from goatlib.io.converter import IOConverter
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LayerImportParams(ToolInputBase):
    """Parameters for layer import tool.

    Either s3_key or wfs_url must be provided.
    """

    # Layer metadata
    name: str | None = None  # Optional, will use filename if not provided
    description: str | None = None
    tags: list[str] | None = None

    # Import source (one of these must be provided)
    s3_key: str | None = None
    wfs_url: str | None = None
    wfs_layer_name: str | None = None

    # External layer properties (for WFS/external services)
    data_type: str | None = None
    other_properties: dict | None = None


class LayerImportRunner(BaseToolRunner[LayerImportParams]):
    """Layer import tool runner for Windmill.

    Imports files from S3 or WFS services into DuckLake storage.
    Unlike analysis tools, this creates "standard" feature layers (not "tool" layers).
    """

    tool_class = None  # No analysis tool - we handle import directly
    output_geometry_type = None  # Detected from data
    default_output_name = "Imported Layer"

    def __init__(self: Self) -> None:
        """Initialize layer import runner."""
        super().__init__()
        self._s3_client = None
        self._converter = None

    def get_feature_layer_type(self: Self, params: LayerImportParams) -> str:
        """Return 'standard' for imported layers (not 'tool').

        Args:
            params: Import parameters

        Returns:
            "standard" for user-imported data
        """
        return "standard"

    @property
    def converter(self: Self) -> IOConverter:
        """Lazy-load IOConverter."""
        if self._converter is None:
            self._converter = IOConverter()
        return self._converter

    def _get_s3_client(self: Self) -> Any:
        """Get or create S3 client (uses shared helper from ToolSettings)."""
        if self._s3_client is None:
            if self.settings is None:
                raise RuntimeError("Settings not initialized")
            self._s3_client = self.settings.get_s3_client()
        return self._s3_client

    def _import_from_s3(
        self: Self, s3_key: str, temp_dir: Path, output_path: Path
    ) -> DatasetMetadata:
        """Import file from S3 and convert to GeoParquet.

        Args:
            s3_key: S3 object key
            temp_dir: Temporary directory for downloaded file
            output_path: Path for output parquet file

        Returns:
            Dataset metadata from conversion
        """
        if self.settings is None:
            raise RuntimeError("Settings not initialized")

        logger.info(
            "S3 Settings: provider=%s, endpoint=%s, bucket=%s, region=%s",
            self.settings.s3_provider,
            self.settings.s3_endpoint_url,
            self.settings.s3_bucket_name,
            self.settings.s3_region_name,
        )
        logger.info("S3 Key: %s", s3_key)

        # Download file directly using boto3 (more reliable than presigned URLs)
        client = self._get_s3_client()
        filename = Path(s3_key).name
        local_file = temp_dir / filename

        logger.info(
            "Downloading s3://%s/%s to %s",
            self.settings.s3_bucket_name,
            s3_key,
            local_file,
        )
        client.download_file(self.settings.s3_bucket_name, s3_key, str(local_file))

        # Convert to GeoParquet using IOConverter
        metadata = self.converter.to_parquet(
            src_path=str(local_file),
            out_path=str(output_path),
            target_crs="EPSG:4326",
        )

        logger.info(
            "S3 import complete: %d features, format=%s",
            metadata.feature_count or 0,
            metadata.format,
        )
        return metadata

    def _import_from_wfs(
        self: Self,
        wfs_url: str,
        layer_name: str | None,
        temp_dir: Path,
        output_path: Path,
    ) -> DatasetMetadata:
        """Import layer from WFS service.

        Args:
            wfs_url: WFS service URL
            layer_name: Specific layer name (None = first layer)
            temp_dir: Temporary directory for intermediate files
            output_path: Path for output parquet file

        Returns:
            Dataset metadata from WFS import
        """
        logger.info("Importing from WFS: %s (layer=%s)", wfs_url, layer_name)

        # Import lazily to avoid GDAL dependency when not using WFS
        from goatlib.io.remote_source.wfs import from_wfs

        # Use goatlib WFS reader
        results = from_wfs(
            url=wfs_url,
            out_dir=str(temp_dir),
            layer=layer_name,
            target_crs="EPSG:4326",
        )

        if not results or results == (None, None):
            raise ValueError(f"No data retrieved from WFS: {wfs_url}")

        # Get first result (from_wfs can return list or tuple)
        if isinstance(results, list):
            parquet_path, metadata = results[0]
        else:
            parquet_path, metadata = results

        # Move to expected output path
        shutil.move(str(parquet_path), str(output_path))

        logger.info(
            "WFS import complete: %d features",
            metadata.feature_count or 0,
        )
        return metadata

    def process(
        self: Self, params: LayerImportParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Import data from S3 or WFS and convert to GeoParquet.

        Args:
            params: Import parameters
            temp_dir: Temporary directory for intermediate files

        Returns:
            Tuple of (output_parquet_path, metadata)

        Raises:
            ValueError: If neither s3_key nor wfs_url provided
        """
        if not params.s3_key and not params.wfs_url:
            raise ValueError("Either s3_key or wfs_url must be provided")

        output_path = temp_dir / "output.parquet"

        if params.wfs_url:
            metadata = self._import_from_wfs(
                wfs_url=params.wfs_url,
                layer_name=params.wfs_layer_name,
                temp_dir=temp_dir,
                output_path=output_path,
            )
            # Override source info
            metadata.format = "wfs"
        else:
            metadata = self._import_from_s3(
                s3_key=params.s3_key,  # type: ignore
                temp_dir=temp_dir,
                output_path=output_path,
            )
            # Extract original format from S3 key
            original_ext = os.path.splitext(params.s3_key)[1].lstrip(".")  # type: ignore
            if original_ext:
                metadata.format = original_ext.lower()

        return output_path, metadata

    def run(self: Self, params: LayerImportParams) -> dict:
        """Run layer import with custom output name handling.

        Overrides base to handle output_name from s3_key if not provided.

        Args:
            params: Import parameters

        Returns:
            Dict with layer metadata
        """
        # Set default output name from filename if not provided
        if not params.output_name and not params.name:
            if params.s3_key:
                # Extract filename without extension
                filename = os.path.basename(params.s3_key)
                params.output_name = os.path.splitext(filename)[0]
            elif params.wfs_url:
                params.output_name = params.wfs_layer_name or "WFS Import"

        # Use name field if output_name not set
        if not params.output_name and params.name:
            params.output_name = params.name

        return super().run(params)


def main(params: LayerImportParams) -> dict:
    """Windmill entry point for layer import tool."""
    runner = LayerImportRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
