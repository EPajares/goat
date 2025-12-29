"""Feature count statistics calculation."""

import logging
from typing import Any

import duckdb

from goatlib.analysis.schemas.statistics import FeatureCountResult

logger = logging.getLogger(__name__)


def calculate_feature_count(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    where_clause: str = "TRUE",
    params: list[Any] | None = None,
) -> FeatureCountResult:
    """Count features in a table with optional filtering.

    Args:
        con: DuckDB connection
        table_name: Fully qualified table name (e.g., "lake.my_table")
        where_clause: SQL WHERE clause condition (default: "TRUE" for all rows)
        params: Optional query parameters for prepared statement

    Returns:
        FeatureCountResult with the count of matching features
    """
    query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
    logger.debug("Feature count query: %s with params: %s", query, params)

    if params:
        result = con.execute(query, params).fetchone()
    else:
        result = con.execute(query).fetchone()

    count = result[0] if result else 0
    return FeatureCountResult(count=count)
