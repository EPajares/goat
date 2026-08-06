"""Storage backends for GOAT.

This module provides storage abstractions for DuckLake (GeoParquet + PostgreSQL catalog).
"""

from goatlib.storage.cql_evaluator import (
    DuckDBCQLEvaluator,
    cql2_to_duckdb_sql,
    cql_to_where_clause,
    inline_params,
    parse_cql2_filter,
)
from goatlib.storage.ducklake import (
    CONNECTION_ERROR_PATTERNS,
    POSTGRES_KEEPALIVE_PARAMS,
    BaseDuckLakeManager,
    DuckLakePool,
    configure_baked_extensions,
    execute_query_with_retry,
    execute_with_retry,
    is_connection_error,
)
from goatlib.storage.pin_errors import is_pin_miss_error
from goatlib.storage.query_builder import (
    QueryFilters,
    build_bbox_filter,
    build_cql_filter,
    build_filters,
    build_id_filter,
    build_order_clause,
)
from goatlib.storage.snapshot_pin import SnapshotPin

__all__ = [
    # DuckLake
    "BaseDuckLakeManager",
    "DuckLakePool",
    "CONNECTION_ERROR_PATTERNS",
    "POSTGRES_KEEPALIVE_PARAMS",
    "is_connection_error",
    "configure_baked_extensions",
    "execute_with_retry",
    "execute_query_with_retry",
    # CQL Evaluator
    "DuckDBCQLEvaluator",
    "cql2_to_duckdb_sql",
    "cql_to_where_clause",
    "inline_params",
    "parse_cql2_filter",
    # Query Builder
    "QueryFilters",
    "build_bbox_filter",
    "build_cql_filter",
    "build_filters",
    "build_id_filter",
    "build_order_clause",
    # Snapshot Pin
    "SnapshotPin",
    "is_pin_miss_error",
]
