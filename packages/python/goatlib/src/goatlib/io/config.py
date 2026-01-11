"""Parquet configuration constants for consistent settings across goatlib.

These settings are used by:
- goatlib.io.parquet.write_optimized_parquet()
- goatlib.tools.base._get_duckdb_connection() (DuckLake settings)

Row Group Size Rationale:
    75K rows is a good balance between:
    - I/O efficiency: Larger groups = fewer seeks, better compression
    - Memory usage: Smaller groups = less memory during processing
    - Query selectivity: Smaller groups = more can be skipped with predicates
    - For spatial data with Hilbert sorting, this groups ~75K nearby features

Compression Rationale:
    ZSTD provides ~20-30% better compression than Snappy with similar speed.
    It's now well-supported in all major Parquet implementations.

Parquet V2 Rationale:
    V2 enables advanced encodings that significantly improve compression:
    - DELTA_BINARY_PACKED: For integers (timestamps, IDs)
    - DELTA_LENGTH_BYTE_ARRAY: For strings and binary (geometry WKB)
    - BYTE_STREAM_SPLIT: For floating point (coordinates)

    These encodings can reduce file sizes by 20-40% for typical GIS data.
"""

# Default row group size for Parquet files
# 50K-100K rows is the recommended range
PARQUET_ROW_GROUP_SIZE = 75000

# Default compression algorithm
PARQUET_COMPRESSION = "zstd"

# Parquet format version (1 or 2)
# V2 enables better encodings
PARQUET_VERSION = "2"
