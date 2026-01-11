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

__all__ = [
    "IOConverter",
    "convert_any",
    "write_optimized_parquet",
    "write_optimized_geoparquet",  # alias for backward compatibility
    "verify_geoparquet_optimization",
    # Config constants
    "PARQUET_COMPRESSION",
    "PARQUET_ROW_GROUP_SIZE",
    "PARQUET_VERSION",
]
