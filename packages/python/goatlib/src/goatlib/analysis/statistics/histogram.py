"""Histogram statistics calculation."""

import logging
from typing import Any

import duckdb

from goatlib.analysis.schemas.statistics import (
    ClassBreakMethod,
    HistogramBin,
    HistogramBreakMethod,
    HistogramResult,
    SortOrder,
)
from goatlib.analysis.statistics.class_breaks import calculate_class_breaks

logger = logging.getLogger(__name__)


def calculate_histogram(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    column: str,
    num_bins: int = 10,
    method: HistogramBreakMethod = HistogramBreakMethod.equal_interval,
    custom_breaks: list[float] | None = None,
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
        num_bins: Number of histogram bins/classes (default: 10)
        method: Binning method
        custom_breaks: Internal custom break points (used when method=custom_breaks)
        where_clause: SQL WHERE clause condition (default: "TRUE" for all rows)
        params: Optional query parameters for prepared statement
        order: Sort order of bins (ascendent or descendent)

    Returns:
        HistogramResult with bins, missing_count, and total_rows
    """
    if isinstance(method, str):
        try:
            method = HistogramBreakMethod(method)
        except ValueError:
            method = HistogramBreakMethod.equal_interval

    col = f'"{column}"'

    # Temporal columns are binned on their epoch value (time -> seconds of day,
    # date/timestamp -> unix seconds); the caller formats the numeric edges back.
    value_expr = col
    try:
        type_row = con.execute(
            f"SELECT lower(typeof({col})) FROM {table_name} "
            f"WHERE {where_clause} AND {col} IS NOT NULL LIMIT 1",
            params or [],
        ).fetchone()
        if type_row and type_row[0] and ("time" in type_row[0] or "date" in type_row[0]):
            value_expr = f"epoch({col})"
    except Exception:
        value_expr = col

    # First, get min, max, total count, and null count
    stats_query = f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT({value_expr}) AS non_null_count,
            MIN({value_expr}) AS min_val,
            MAX({value_expr}) AS max_val
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

    edges = _build_histogram_edges(
        con=con,
        table_name=table_name,
        column=column,
        min_val=float(min_val),
        max_val=float(max_val),
        num_bins=num_bins,
        method=method,
        custom_breaks=custom_breaks,
        where_clause=where_clause,
        params=params,
    )

    bins = _count_bins(
        con=con,
        table_name=table_name,
        value_expr=value_expr,
        edges=edges,
        where_clause=where_clause,
        params=params,
    )

    if order == SortOrder.descendent:
        bins = list(reversed(bins))

    return HistogramResult(
        bins=bins,
        missing_count=missing_count,
        total_rows=total_rows,
    )


def _build_histogram_edges(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    column: str,
    min_val: float,
    max_val: float,
    num_bins: int,
    method: HistogramBreakMethod,
    custom_breaks: list[float] | None,
    where_clause: str,
    params: list[Any] | None,
) -> list[float]:
    """Build sorted histogram bin edges [min, ..., max]."""
    # Internal break points (without min/max)
    internal_breaks: list[float] = []

    if method == HistogramBreakMethod.custom_breaks:
        internal_breaks = [
            float(value)
            for value in (custom_breaks or [])
            if min_val < float(value) < max_val
        ]
    elif method == HistogramBreakMethod.equal_interval:
        num_internal_breaks = max(num_bins - 1, 0)
        if num_internal_breaks > 0:
            # For integer columns, don't create more classes than possible integer values
            range_size = max_val - min_val
            if float(min_val).is_integer() and float(max_val).is_integer():
                max_possible_bins = int(range_size) + 1
                num_bins = min(num_bins, max_possible_bins)
                num_internal_breaks = max(num_bins - 1, 0)

            if num_internal_breaks > 0:
                interval = (max_val - min_val) / num_bins
                internal_breaks = [
                    min_val + interval * index
                    for index in range(1, num_internal_breaks + 1)
                ]
    else:
        # Map histogram methods to class breaks methods.
        if method == HistogramBreakMethod.quantile:
            class_method = ClassBreakMethod.quantile
        elif method == HistogramBreakMethod.standard_deviation:
            class_method = ClassBreakMethod.standard_deviation
        else:
            class_method = ClassBreakMethod.heads_and_tails

        num_internal_breaks = max(num_bins - 1, 0)
        if num_internal_breaks > 0:
            class_breaks_result = calculate_class_breaks(
                con=con,
                table_name=table_name,
                attribute=column,
                method=class_method,
                num_breaks=num_internal_breaks,
                where_clause=where_clause,
                params=params,
            )
            internal_breaks = [
                float(value)
                for value in class_breaks_result.breaks
                if min_val < float(value) < max_val
            ]

    # Final edges must include min and max and be strictly increasing.
    deduped_internal = sorted(set(internal_breaks))
    edges = [min_val, *deduped_internal, max_val]
    strictly_increasing = [edges[0]]
    for value in edges[1:]:
        if value > strictly_increasing[-1]:
            strictly_increasing.append(value)

    # Ensure at least one bin.
    if len(strictly_increasing) < 2:
        return [min_val, max_val]

    return strictly_increasing


def _count_bins(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    value_expr: str,
    edges: list[float],
    where_clause: str,
    params: list[Any] | None,
) -> list[HistogramBin]:
    """Count values for each bin edge interval."""
    col = value_expr
    base_params = params or []
    bins: list[HistogramBin] = []

    for index in range(len(edges) - 1):
        lower = float(edges[index])
        upper = float(edges[index + 1])
        is_last_bin = index == len(edges) - 2

        if is_last_bin:
            condition = f"{col} >= ? AND {col} <= ?"
        else:
            condition = f"{col} >= ? AND {col} < ?"

        query = f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {where_clause}
              AND {col} IS NOT NULL
              AND {condition}
        """

        count_params = [*base_params, lower, upper]
        count = int(con.execute(query, count_params).fetchone()[0])

        bins.append(
            HistogramBin(
                range=(round(lower, 6), round(upper, 6)),
                count=count,
            )
        )

    return bins
