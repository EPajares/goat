# src/goatlib/io/remote_source/wfs_reader.py
from __future__ import annotations

import logging
import tempfile
import textwrap
from pathlib import Path
from typing import Dict, List, Optional

try:
    from osgeo import gdal, ogr
except ImportError:
    logging.error(
        "GDAL/OGR Python bindings are required for WFS support. "
        "Please install them (e.g., 'conda install gdal' or 'pip install GDAL')"
    )
    raise

logger = logging.getLogger(__name__)


class WFSReader:
    """
    Wrapper for OGC WFS services using GDAL/OGR WFS driver.

    Handles layer discovery and datasource preparation for DuckDB/ST_Read().
    """

    def __init__(self: WFSReader) -> None:
        """Initialize WFS reader and ensure GDAL drivers are registered."""
        self._ensure_gdal_initialized()

    def _ensure_gdal_initialized(self: WFSReader) -> None:
        """Ensure GDAL drivers are properly initialized."""
        try:
            ogr.RegisterAll()
        except Exception as e:
            logger.warning("Failed to register GDAL drivers: %s", e)

    def can_handle(self: WFSReader, url: str) -> bool:
        """
        Check if URL appears to be a WFS endpoint.

        Args:
            url: Service URL to check

        Returns:
            True if URL looks like a WFS endpoint
        """
        url_lower = url.lower()
        return (
            "service=wfs" in url_lower
            or "wfs" in url_lower
            or url_lower.endswith("/wfs")
        )

    def build_datasource(
        self: WFSReader,
        url: str,
        layer: Optional[str] = None,
        config: Optional[Dict[str, str]] = None,
    ) -> Path:
        """
        Create OGRWFSDataSource XML file for GDAL WFS driver.

        Args:
            url: WFS service endpoint URL
            layer: Specific layer to access, or None for all layers
            config: Additional GDAL configuration parameters

        Returns:
            Path to temporary XML datasource file

        Raises:
            ValueError: If URL is invalid
            IOError: If temporary file cannot be created
        """
        if not url or not isinstance(url, str):
            raise ValueError("Invalid WFS URL provided")

        # Build XML content
        xml_content = self._build_wfs_xml(url, layer, config or {})

        # Create temporary file
        return self._write_wfs_xml_file(xml_content, layer)

    def _build_wfs_xml(
        self: WFSReader, url: str, layer: Optional[str], config: Dict[str, str]
    ) -> str:
        """Build WFS datasource XML content."""
        layer_tag = f"  <Layer>{layer}</Layer>\n" if layer else ""

        config_tags = "".join(
            f"  <{key}>{value}</{key}>\n" for key, value in config.items()
        )

        xml_template = textwrap.dedent("""\
            <OGRWFSDataSource>
              <URL>{url}</URL>
            {config_tags}{layer_tag}</OGRWFSDataSource>
        """)

        return xml_template.format(
            url=url, config_tags=config_tags, layer_tag=layer_tag
        )

    def _write_wfs_xml_file(
        self: WFSReader, xml_content: str, layer: Optional[str]
    ) -> Path:
        """Write XML content to temporary file."""
        tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_wfs_"))

        if layer:
            # Sanitize layer name for filename
            safe_name = self._sanitize_filename(layer)
            filename = f"wfs_source_{safe_name}.xml"
        else:
            filename = "wfs_source.xml"

        xml_path = tmp_dir / filename
        xml_path.write_text(xml_content, encoding="utf-8")

        logger.debug("Created WFS datasource XML: %s", xml_path)
        return xml_path

    def _sanitize_filename(self: WFSReader, name: str) -> str:
        """Sanitize string for use in filename."""
        # Replace problematic characters with underscores
        return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)

    def get_layers(self: WFSReader, url: str) -> List[str]:
        """
        Retrieve available layer names from WFS service.

        Args:
            url: WFS service endpoint URL

        Returns:
            Sorted list of layer names

        Raises:
            RuntimeError: If WFS connection or layer discovery fails
        """
        if not self.can_handle(url):
            raise ValueError(f"URL does not appear to be a WFS endpoint: {url}")

        connection_string = f"WFS:{url}"

        try:
            datasource = self._open_wfs_datasource(connection_string)
            layer_names = self._extract_layer_names(datasource)
            return sorted(layer_names)

        except Exception as e:
            raise RuntimeError(
                f"Failed to get layers from WFS service {url}: {e}"
            ) from e

    def _open_wfs_datasource(self: WFSReader, connection_string: str) -> ogr.DataSource:
        """Open WFS datasource using GDAL driver."""
        driver = ogr.GetDriverByName("WFS")
        if not driver:
            raise RuntimeError("GDAL WFS driver is not available")

        datasource = driver.Open(connection_string, 0)  # 0 = read-only
        if datasource is None:
            error_msg = gdal.GetLastErrorMsg()
            raise RuntimeError(
                f"Failed to open WFS datasource. GDAL error: {error_msg or 'Unknown error'}"
            )

        return datasource

    def _extract_layer_names(self: WFSReader, datasource: ogr.DataSource) -> List[str]:
        """Extract layer names from GDAL datasource."""
        layer_names = []
        layer_count = datasource.GetLayerCount()

        for i in range(layer_count):
            layer = datasource.GetLayerByIndex(i)
            if layer:
                name = layer.GetName()
                if name:
                    layer_names.append(name)
                else:
                    logger.warning("Found layer with no name at index %d", i)

        # Explicit cleanup (good practice with GDAL objects)
        datasource = None

        return layer_names
