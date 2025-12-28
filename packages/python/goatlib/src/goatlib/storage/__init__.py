"""Storage backends for GOAT.

This module provides storage abstractions for DuckLake (GeoParquet + PostgreSQL catalog).
"""

from goatlib.storage.ducklake import (
    CONNECTION_ERROR_PATTERNS,
    POSTGRES_KEEPALIVE_PARAMS,
    BaseDuckLakeManager,
    DuckLakePool,
    execute_query_with_retry,
    execute_with_retry,
    is_connection_error,
)

__all__ = [
    "BaseDuckLakeManager",
    "DuckLakePool",
    "CONNECTION_ERROR_PATTERNS",
    "POSTGRES_KEEPALIVE_PARAMS",
    "is_connection_error",
    "execute_with_retry",
    "execute_query_with_retry",
]
