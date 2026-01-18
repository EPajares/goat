"""I/O utilities for GOAT data processing.

This module provides:
- IOConverter: Convert various formats to Parquet/GeoParquet
- Optimized Parquet writing with V2 format
- Optimized GeoParquet writing with Hilbert sorting and bbox columns
- File format detection and discovery
"""

from goatlib.io.config import (
    PARQUET_COMPRESSION,
    PARQUET_ROW_GROUP_SIZE,
    PARQUET_VERSION,
)
from goatlib.io.converter import IOConverter
from goatlib.io.ingest import convert_any
from goatlib.io.parquet import (
    verify_geoparquet_optimization,
    write_optimized_geoparquet,
    write_optimized_parquet,
)


# Lazy import for PMTiles to avoid requiring pmtiles package in all environments
# (e.g., print worker doesn't need pmtiles)
def __getattr__(name: str):
    if name in ("PMTilesConfig", "PMTilesGenerator"):
        from goatlib.io.pmtiles import PMTilesConfig, PMTilesGenerator

        return PMTilesConfig if name == "PMTilesConfig" else PMTilesGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "IOConverter",
    "convert_any",
    "write_optimized_parquet",
    "write_optimized_geoparquet",  # alias for backward compatibility
    "verify_geoparquet_optimization",
    # PMTiles generation (lazy loaded)
    "PMTilesConfig",
    "PMTilesGenerator",
    # Config constants
    "PARQUET_COMPRESSION",
    "PARQUET_ROW_GROUP_SIZE",
    "PARQUET_VERSION",
]
