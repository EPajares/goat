# src/goatlib/io/remote_source/wfs.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple, Union

from goatlib.io.ingest import convert_any
from goatlib.io.remote_source.wfs_reader import WFSReader
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)

# Define result type for WFS operations
WfsResult = Union[
    List[Tuple[Path, DatasetMetadata]], Tuple[Path, DatasetMetadata], Tuple[None, None]
]


def from_wfs(
    url: str,
    out_dir: str | Path,
    *,
    layer: str | List[str] | None = None,
    target_crs: str | None = None,
    list_layers: bool = False,
    progress: bool = True,
    progress_style: str = "auto",
) -> WfsResult:
    """
    Read or inspect a WFS service and convert layers to Parquet/GeoParquet.
    """
    reader = WFSReader()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not reader.can_handle(url):
        raise ValueError(f"URL does not look like a WFS endpoint: {url}")

    # Fetch available layers
    layers = _fetch_wfs_layers(reader, url)

    if list_layers:
        _display_available_layers(layers)
        return None, None

    if not layers:
        raise RuntimeError("No layers found in WFS service.")

    # Determine and validate layers to process
    layers_to_process = _validate_and_filter_layers(layer, layers)

    if not layers_to_process:
        logger.warning("No valid layers found to process")
        return []

    # Convert layers
    return _convert_wfs_layers(
        reader=reader,
        url=url,
        layers=layers_to_process,
        out_dir=out_dir,
        target_crs=target_crs,
        progress=progress,
        progress_style=progress_style,
    )


def _fetch_wfs_layers(reader: WFSReader, url: str) -> List[str]:
    """Fetch available layers from WFS service."""
    try:
        return reader.get_layers(url)
    except RuntimeError as e:
        raise RuntimeError(f"Failed to fetch WFS layers from {url}") from e


def _display_available_layers(layers: List[str]) -> None:
    """Display available WFS layers to the user."""
    logger.info("Available WFS layers:")
    for layer_name in layers:
        logger.info("  • %s", layer_name)


def _validate_and_filter_layers(
    requested_layers: str | List[str] | None, available_layers: List[str]
) -> List[str]:
    """Validate requested layers against available layers."""
    if requested_layers is None:
        return available_layers

    if isinstance(requested_layers, str):
        selected_layers = [requested_layers]
    elif isinstance(requested_layers, list):
        selected_layers = requested_layers
    else:
        raise TypeError(
            "The 'layer' argument must be a string, list of strings, or None"
        )

    # Filter out non-existent layers with warnings
    valid_layers = []
    for layer_name in selected_layers:
        if layer_name in available_layers:
            valid_layers.append(layer_name)
        else:
            logger.warning("Layer '%s' not found in WFS service - skipping", layer_name)

    return valid_layers


def _convert_wfs_layers(
    reader: WFSReader,
    url: str,
    layers: List[str],
    out_dir: Path,
    target_crs: str | None,
    progress: bool = True,
    progress_style: str = "auto",
) -> WfsResult:
    """Convert WFS layers to Parquet/GeoParquet."""
    results: List[Tuple[Path, DatasetMetadata]] = []

    for layer_name in layers:
        try:
            layer_results = _convert_single_wfs_layer(
                reader=reader,
                url=url,
                layer_name=layer_name,
                out_dir=out_dir,
                target_crs=target_crs,
                progress=progress,
                progress_style=progress_style,
            )
            results.extend(layer_results)

        except Exception as e:
            logger.error("Failed to process WFS layer '%s': %s", layer_name, e)
            # Continue with next layer instead of failing completely

    # Return appropriate format based on number of results
    return _format_wfs_results(results, layers)


def _convert_single_wfs_layer(
    reader: WFSReader,
    url: str,
    layer_name: str,
    out_dir: Path,
    target_crs: str | None,
    progress: bool = True,
    progress_style: str = "auto",
) -> List[Tuple[Path, DatasetMetadata]]:
    """Convert a single WFS layer to Parquet/GeoParquet."""
    xml_path = None
    tmp_dir = None

    try:
        # Create WFS datasource XML file
        xml_path = reader.build_datasource(url, layer=layer_name)
        tmp_dir = xml_path.parent

        # Convert using the main conversion pipeline
        return convert_any(
            src_path=str(xml_path),
            dest_dir=out_dir,
            geometry_col=None,
            target_crs=target_crs,
            progress=progress,
            progress_style=progress_style,
        )

    finally:
        # Clean up temporary files
        _cleanup_wfs_temp_files(xml_path, tmp_dir)


def _cleanup_wfs_temp_files(xml_path: Path | None, tmp_dir: Path | None) -> None:
    """Clean up temporary WFS files and directories."""
    try:
        if xml_path and xml_path.exists():
            xml_path.unlink(missing_ok=True)

        if tmp_dir and tmp_dir.exists():
            # Remove directory if empty
            try:
                tmp_dir.rmdir()
            except OSError:
                # Directory not empty - leave for system cleanup
                logger.debug("Could not remove non-empty temp directory: %s", tmp_dir)
    except Exception as e:
        logger.warning("Failed to clean up WFS temp files: %s", e)


def _format_wfs_results(
    results: List[Tuple[Path, DatasetMetadata]], requested_layers: List[str]
) -> WfsResult:
    """Format results appropriately based on number of layers processed."""
    if len(requested_layers) == 1 and len(results) == 1:
        # Single layer → return single tuple for backward compatibility
        return results[0]
    else:
        return results
