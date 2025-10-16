from __future__ import annotations

from pathlib import Path
from typing import Tuple

from goatlib.io.converter import IOConverter
from goatlib.io.formats import RASTER_EXTS, TABULAR_EXTS, VECTOR_EXTS, FileFormat
from goatlib.models.io import DatasetMetadata


def convert_any(
    src_path: str,
    dest_dir: str | Path,
    geometry_col: str | None = None,
    target_crs: str | None = None,
) -> Tuple[Path, DatasetMetadata]:
    """
    Convert any supported dataset to Parquet/GeoParquet (vector, tabular)
    or Cloud‑Optimized GeoTIFF (raster).

    Returns (output_path, DatasetMetadata).

    Parameters
    ----------
    src_path : str
        Source dataset path or URI.
    dest_dir : str | Path
        Directory where converted output will be written.
    geometry_col : str | None, default None
        Geometry column name if known.
    target_crs : str | None, default None
        CRS to which vector geometries should be transformed.
        If None, input CRS is preserved.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    base = Path(src_path).stem
    suffix = Path(src_path).suffix.lower()
    conv = IOConverter()

    if suffix in RASTER_EXTS:
        out = dest / f"{base}{FileFormat.TIF.value}"
        meta = conv.to_cog(src_path, out, target_crs=target_crs)
    elif suffix in VECTOR_EXTS | TABULAR_EXTS or suffix == FileFormat.ZIP.value:
        out = dest / f"{base}{FileFormat.PARQUET.value}"
        meta = conv.to_parquet(
            src_path,
            out,
            geometry_col=geometry_col,
            target_crs=target_crs,
        )
    else:
        raise ValueError(f"Unsupported file extension: {suffix}")
    return out, meta
