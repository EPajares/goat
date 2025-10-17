# src/goatlib/io/ingest.py
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from goatlib.io.converter import IOConverter
from goatlib.io.discover import discover_inputs
from goatlib.io.formats import RASTER_EXTS, TABULAR_EXTS, VECTOR_EXTS, FileFormat
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


def convert_any(
    src_path: str | list[str],
    dest_dir: str | Path,
    geometry_col: str | None = None,
    target_crs: str | None = None,
    *,
    progress: bool = True,
    progress_style: str = "auto",
) -> list[tuple[Path, DatasetMetadata]]:
    """
    Convert any supported input to standardized outputs.

    Parameters
    ----------
    src_path : str | list[str]
        Source path(s)
    dest_dir : str | Path
        Destination directory
    geometry_col : str, optional
        Geometry column name
    target_crs : str, optional
        Target CRS for reprojection
    progress : bool, default=True
        Enable progress reporting
    progress_style : str, default="auto"
        Progress style: "rich", "callback", "silent", or "auto"

    Returns
    -------
    list[tuple[Path, DatasetMetadata]]
        List of (output_path, metadata) for all converted datasets
    """
    from goatlib.io.converter import IOConverter

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    # Resolve progress reporter
    progress_reporter = (
        _resolve_progress(progress, progress_style) if progress else None
    )

    converter = IOConverter(progress_reporter=progress_reporter)

    # Handle multiple source paths
    if isinstance(src_path, list):
        return _convert_multiple_sources(
            src_paths=src_path,
            converter=converter,
            dest_dir=dest,
            geometry_col=geometry_col,
            target_crs=target_crs,
            progress_reporter=progress_reporter,
        )

    # Single source path
    return _convert_single_source(
        src_path=src_path,
        converter=converter,
        dest_dir=dest,
        geometry_col=geometry_col,
        target_crs=target_crs,
        progress_reporter=progress_reporter,
    )


def _resolve_progress(progress: bool, progress_style: str):  # noqa: ANN202
    """Resolve progress parameter to ProgressReporter instance."""
    if not progress:
        return None

    from goatlib.utils.progress import create_progress_reporter

    return create_progress_reporter(progress_style)


def _convert_single_source(
    src_path: str,
    converter: IOConverter,
    dest_dir: Path,
    geometry_col: str | None,
    target_crs: str | None,
    progress_reporter,  # noqa: ANN001
) -> list[tuple[Path, DatasetMetadata]]:
    """Convert a single source path (which may contain multiple datasets)."""
    from goatlib.utils.progress import ProgressState

    if progress_reporter:
        progress_reporter.update(
            ProgressState(10, "Discovering input datasets", src_path)
        )

    # Discover inputs - this might create temp directories
    discovered = discover_inputs(src_path)
    if not discovered:
        raise ValueError(f"No convertible datasets found in {src_path}")

    outputs: list[tuple[Path, DatasetMetadata]] = []
    total_items = len(discovered)

    # Track temp directories that need cleanup
    temp_dirs_to_cleanup = set()

    try:
        for i, item in enumerate(discovered):
            try:
                if progress_reporter:
                    progress = 20 + (i / total_items) * 70
                    progress_reporter.update(
                        ProgressState(
                            progress,
                            f"Converting dataset {i+1}/{total_items}",
                            current_item=item,
                        )
                    )

                # Check if this is a temp file from discovery
                item_path = Path(item)
                if item_path.parent.name.startswith(
                    ("goatlib_zip_", "goatlib_remote_")
                ):
                    temp_dirs_to_cleanup.add(item_path.parent)

                output_path, metadata = _convert_single_item(
                    converter=converter,
                    item=item,
                    dest_dir=dest_dir,
                    geometry_col=geometry_col,
                    target_crs=target_crs,
                    progress_reporter=progress_reporter,
                )
                outputs.append((output_path, metadata))

            except Exception as e:
                logger.error("Failed to convert %s: %s", item, e)
                if progress_reporter:
                    progress_reporter.update(
                        ProgressState(0, f"Failed to convert {item}: {e}")
                    )
                raise

        if progress_reporter:
            progress_reporter.update(
                ProgressState(100, "Conversion completed", src_path)
            )

        return outputs

    finally:
        # Clean up all temp directories after conversion is complete
        for temp_dir in temp_dirs_to_cleanup:
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.debug("Cleaned up temp directory: %s", temp_dir)
                except Exception as e:
                    logger.warning(
                        "Failed to clean up temp directory %s: %s", temp_dir, e
                    )


def _convert_multiple_sources(
    src_paths: list[str],
    converter: IOConverter,
    dest_dir: Path,
    geometry_col: str | None,
    target_crs: str | None,
    progress_reporter,  # noqa: ANN001
) -> list[tuple[Path, DatasetMetadata]]:
    """Convert multiple source paths."""
    from goatlib.utils.progress import ProgressState

    all_outputs: list[tuple[Path, DatasetMetadata]] = []
    total_sources = len(src_paths)

    for i, src_path in enumerate(src_paths):
        if progress_reporter:
            progress = (i / total_sources) * 100
            progress_reporter.update(
                ProgressState(
                    progress,
                    f"Processing source {i+1}/{total_sources}",
                    current_item=src_path,
                )
            )

        try:
            outputs = _convert_single_source(
                src_path=src_path,
                converter=converter,
                dest_dir=dest_dir,
                geometry_col=geometry_col,
                target_crs=target_crs,
                progress_reporter=progress_reporter,
            )
            all_outputs.extend(outputs)
        except Exception as e:
            logger.error("Failed to convert %s: %s", src_path, e)
            if progress_reporter:
                progress_reporter.update(
                    ProgressState(
                        progress=progress, message=f"Failed to convert {src_path}: {e}"
                    )
                )
            # Continue with other sources instead of failing completely
            continue

    return all_outputs


def _convert_single_item(
    converter: IOConverter,
    item: str,
    dest_dir: Path,
    geometry_col: str | None,
    target_crs: str | None,
    progress_reporter,  # Type is resolved at runtime  # noqa: ANN001
) -> tuple[Path, DatasetMetadata]:
    """
    Convert a single discovered item to the appropriate format.
    """
    base_path = item.split("::")[0]
    suffix = Path(base_path).suffix.lower()
    stem = Path(base_path).stem

    # Handle WFS XML datasource
    if _is_wfs_xml_datasource(base_path):
        logger.info("Processing WFS XML datasource: %s", base_path)
        out = dest_dir / f"{stem}{FileFormat.PARQUET.value}"
        meta = converter.to_parquet(
            base_path,
            out,
            geometry_col=geometry_col,
            target_crs=target_crs,
            progress_reporter=progress_reporter,
        )
        return out, meta

    # Handle raster files
    if suffix in RASTER_EXTS:
        out = dest_dir / f"{stem}{FileFormat.TIF.value}"
        meta = converter.to_cog(
            item, out, target_crs=target_crs, progress_reporter=progress_reporter
        )
        return out, meta

    # Handle vector/tabular files and ZIP archives
    if (
        suffix in VECTOR_EXTS
        or suffix in TABULAR_EXTS
        or suffix == FileFormat.ZIP.value
    ):
        suffix_extra = _get_layer_suffix(item)
        out = dest_dir / f"{stem}{suffix_extra}{FileFormat.PARQUET.value}"
        meta = converter.to_parquet(
            item,
            out,
            geometry_col=geometry_col,
            target_crs=target_crs,
            progress_reporter=progress_reporter,
        )
        return out, meta

    # Unsupported format
    logger.warning("Skipping unsupported file: %s", item)
    raise ValueError(f"Unsupported file format: {suffix}")


def _is_wfs_xml_datasource(file_path: str) -> bool:
    """Check if a file is a WFS XML datasource."""
    path = Path(file_path)
    if path.suffix.lower() != ".xml" or not path.exists():
        return False

    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:200]
        return "<OGRWFSDataSource" in head
    except Exception:
        return False


def _get_layer_suffix(item: str) -> str:
    """Extract layer suffix from item path with ::layer syntax."""
    if "::" in item:
        layer_name = item.split("::")[1]
        # Sanitize layer name for filename
        sanitized = layer_name.replace("/", "_").replace("\\", "_")
        return f"_{sanitized}"
    return ""
