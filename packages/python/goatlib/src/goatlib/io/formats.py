from enum import StrEnum
from typing import FrozenSet


class FileFormat(StrEnum):
    """Canonical enumeration of atomic file extensions (lower‑case)."""

    CSV = ".csv"
    XLSX = ".xlsx"
    GEOJSON = ".geojson"
    JSON = ".json"
    GPKG = ".gpkg"
    SHP = ".shp"
    ZIP = ".zip"  # usually zipped Shapefile
    KML = ".kml"
    PARQUET = ".parquet"
    TIF = ".tif"
    TIFF = ".tiff"


# -------------------------------------------------------------------------
# Grouped extension sets, reusing Enum members
# -------------------------------------------------------------------------
VECTOR_EXTS: FrozenSet[str] = frozenset(
    {
        FileFormat.GEOJSON,
        FileFormat.JSON,
        FileFormat.GPKG,
        FileFormat.SHP,
        FileFormat.ZIP,
        FileFormat.KML,
        FileFormat.PARQUET,
    }
)

TABULAR_EXTS: FrozenSet[str] = frozenset(
    {FileFormat.CSV, FileFormat.XLSX, FileFormat.PARQUET}
)
RASTER_EXTS: FrozenSet[str] = frozenset({FileFormat.TIF, FileFormat.TIFF})
ALL_EXTS: FrozenSet[str] = VECTOR_EXTS | TABULAR_EXTS | RASTER_EXTS
