"""Aggregation statistics calculation."""

import logging
from typing import Any

import duckdb

from goatlib.analysis.schemas.statistics import (
    AggregationStatsItem,
    AggregationStatsResult,
    SortOrder,
    StatisticsOperation,
)

logger = logging.getLogger(__name__)


def calculate_aggregation_stats(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    operation: StatisticsOperation = StatisticsOperation.count,
    operation_column: str | None = None,
    group_by_column: str | None = None,
    where_clause: str = "TRUE",
    params: list[Any] | None = None,
    order: SortOrder = SortOrder.descendent,
    limit: int = 100,
) -> AggregationStatsResult:
    """Calculate aggregation statistics with optional grouping.

    Args:
        con: DuckDB connection
        table_name: Fully qualified table name (e.g., "lake.my_table")
        operation: Statistical operation (count, sum, mean, min, max)
        operation_column: Column to perform the operation on (required for sum, mean, min, max)
        group_by_column: Optional column to group results by
        where_clause: SQL WHERE clause condition (default: "TRUE" for all rows)
        params: Optional query parameters for prepared statement
        order: Sort order by operation value (ascendent or descendent)
        limit: Maximum number of grouped values to return

    Returns:
        AggregationStatsResult with items, total_items, and total_count
    """
    # Validate inputs
    if operation != StatisticsOperation.count and not operation_column:
        raise ValueError(
            f"operation_column is required for operation '{operation.value}'"
        )

    # Build the aggregation expression
    if operation == StatisticsOperation.count:
        if operation_column:
            agg_expr = f'COUNT("{operation_column}")'
        else:
            agg_expr = "COUNT(*)"
    elif operation == StatisticsOperation.sum:
        agg_expr = f'SUM("{operation_column}")'
    elif operation == StatisticsOperation.mean:
        agg_expr = f'AVG("{operation_column}")'
    elif operation == StatisticsOperation.min:
        agg_expr = f'MIN("{operation_column}")'
    elif operation == StatisticsOperation.max:
        agg_expr = f'MAX("{operation_column}")'
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    # Map order
    order_dir = "DESC" if order == SortOrder.descendent else "ASC"

    # Build the query
    if group_by_column:
        group_col = f'"{group_by_column}"'

        # Query for total count of rows
        count_query = f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {where_clause}
        """

        # Query for total number of distinct groups
        total_groups_query = f"""
            SELECT COUNT(DISTINCT {group_col})
            FROM {table_name}
            WHERE {where_clause}
        """

        # Query for aggregation with grouping
        data_query = f"""
            SELECT
                CAST({group_col} AS VARCHAR) AS grouped_value,
                {agg_expr} AS operation_value
            FROM {table_name}
            WHERE {where_clause}
            GROUP BY {group_col}
            ORDER BY operation_value {order_dir}, grouped_value
            LIMIT {limit}
        """
    else:
        # Query for total count of rows
        count_query = f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {where_clause}
        """

        # No grouping - just return single aggregation (no params needed)
        total_groups_query = None

        data_query = f"""
            SELECT
                NULL AS grouped_value,
                {agg_expr} AS operation_value
            FROM {table_name}
            WHERE {where_clause}
        """

    logger.debug("Aggregation stats query: %s with params: %s", data_query, params)

    # Execute queries
    if params:
        total_count_result = con.execute(count_query, params).fetchone()
        # total_groups_query may be None (no grouping) or have placeholders
        if total_groups_query:
            total_groups_result = con.execute(total_groups_query, params).fetchone()
        else:
            total_groups_result = (1,)  # Single result when no grouping
        data_result = con.execute(data_query, params).fetchall()
    else:
        total_count_result = con.execute(count_query).fetchone()
        if total_groups_query:
            total_groups_result = con.execute(total_groups_query).fetchone()
        else:
            total_groups_result = (1,)  # Single result when no grouping
        data_result = con.execute(data_query).fetchall()

    total_count = total_count_result[0] if total_count_result else 0
    total_items = total_groups_result[0] if total_groups_result else 0

    # Build result items
    items = [
        AggregationStatsItem(
            grouped_value=row[0],
            operation_value=float(row[1]) if row[1] is not None else 0.0,
        )
        for row in data_result
    ]

    return AggregationStatsResult(
        items=items,
        total_items=total_items,
        total_count=total_count,
    )
