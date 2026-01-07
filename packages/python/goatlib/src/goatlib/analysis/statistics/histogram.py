"""Histogram statistics calculation."""

import logging
from typing import Any

import duckdb

from goatlib.analysis.schemas.statistics import (
    HistogramBin,
    HistogramResult,
    SortOrder,
)

logger = logging.getLogger(__name__)


def calculate_histogram(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    column: str,
    num_bins: int = 10,
    where_clause: str = "TRUE",
    params: list[Any] | None = None,
    order: SortOrder = SortOrder.ascendent,
) -> HistogramResult:
    """Calculate histogram for a numeric column.

    Uses DuckDB's FLOOR-based binning for efficient histogram calculation.

    Args:
        con: DuckDB connection
        table_name: Fully qualified table name (e.g., "lake.my_table")
        column: Numeric column to create histogram for
        num_bins: Number of histogram bins (default: 10)
        where_clause: SQL WHERE clause condition (default: "TRUE" for all rows)
        params: Optional query parameters for prepared statement
        order: Sort order of bins (ascendent or descendent)

    Returns:
        HistogramResult with bins, missing_count, and total_rows
    """
    col = f'"{column}"'

    # First, get min, max, total count, and null count
    stats_query = f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT({col}) AS non_null_count,
            MIN({col}) AS min_val,
            MAX({col}) AS max_val
        FROM {table_name}
        WHERE {where_clause}
    """

    logger.debug("Histogram stats query: %s with params: %s", stats_query, params)

    if params:
        stats_result = con.execute(stats_query, params).fetchone()
    else:
        stats_result = con.execute(stats_query).fetchone()

    if not stats_result:
        return HistogramResult(bins=[], missing_count=0, total_rows=0)

    total_rows, non_null_count, min_val, max_val = stats_result
    missing_count = total_rows - non_null_count

    # Handle edge cases
    if min_val is None or max_val is None or non_null_count == 0:
        return HistogramResult(
            bins=[], missing_count=missing_count, total_rows=total_rows
        )

    # If min equals max, return single bin
    if min_val == max_val:
        return HistogramResult(
            bins=[
                HistogramBin(
                    range=(float(min_val), float(max_val)),
                    count=non_null_count,
                )
            ],
            missing_count=missing_count,
            total_rows=total_rows,
        )

    # Adjust num_bins if there are fewer distinct values than bins
    # Also limit bins based on the range
    range_size = max_val - min_val
    if isinstance(min_val, int) and isinstance(max_val, int):
        # For integer columns, don't have more bins than the range
        max_possible_bins = int(range_size) + 1
        num_bins = min(num_bins, max_possible_bins)

    # Map order
    order_dir = "ASC" if order == SortOrder.ascendent else "DESC"

    # Calculate bin width
    bin_width = range_size / num_bins

    # Use FLOOR-based binning which is more portable
    # bin_number = LEAST(FLOOR((value - min) / bin_width), num_bins - 1) + 1
    histogram_query = f"""
        WITH bins AS (
            SELECT generate_series AS bin_number
            FROM generate_series(1, {num_bins})
        ),
        bucketed AS (
            SELECT
                LEAST(
                    FLOOR(({col} - {min_val}) / {bin_width})::INTEGER,
                    {num_bins - 1}
                ) + 1 AS bin_number
            FROM {table_name}
            WHERE {where_clause}
              AND {col} IS NOT NULL
        ),
        histogram AS (
            SELECT
                bin_number,
                COUNT(*) AS count
            FROM bucketed
            GROUP BY bin_number
        )
        SELECT
            bins.bin_number,
            ROUND(({min_val} + (bins.bin_number - 1) * {bin_width})::NUMERIC, 6) AS lower_bound,
            ROUND(({min_val} + bins.bin_number * {bin_width})::NUMERIC, 6) AS upper_bound,
            COALESCE(histogram.count, 0) AS count
        FROM bins
        LEFT JOIN histogram ON bins.bin_number = histogram.bin_number
        ORDER BY bins.bin_number {order_dir}
    """

    logger.debug("Histogram query: %s with params: %s", histogram_query, params)

    if params:
        result = con.execute(histogram_query, params).fetchall()
    else:
        result = con.execute(histogram_query).fetchall()

    # Build bins
    bins = [
        HistogramBin(
            range=(float(row[1]), float(row[2])),
            count=int(row[3]),
        )
        for row in result
    ]

    return HistogramResult(
        bins=bins,
        missing_count=missing_count,
        total_rows=total_rows,
    )
