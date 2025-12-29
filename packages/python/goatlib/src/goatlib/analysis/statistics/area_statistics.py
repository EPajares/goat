"""Area statistics calculation."""

import logging
from typing import Any

import duckdb

from goatlib.analysis.schemas.statistics import AreaOperation, AreaStatisticsResult

logger = logging.getLogger(__name__)


def calculate_area_statistics(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    geometry_column: str,
    operation: AreaOperation = AreaOperation.sum,
    where_clause: str = "TRUE",
    params: list[Any] | None = None,
    source_crs: str = "EPSG:4326",
    target_crs: str = "EPSG:3857",
) -> AreaStatisticsResult:
    """Calculate area-based statistics for polygon features.

    Args:
        con: DuckDB connection
        table_name: Fully qualified table name (e.g., "lake.my_table")
        geometry_column: Name of the geometry column
        operation: Statistical operation to perform (sum, mean, min, max)
        where_clause: SQL WHERE clause condition (default: "TRUE" for all rows)
        params: Optional query parameters for prepared statement
        source_crs: Source coordinate reference system (default: EPSG:4326)
        target_crs: Target CRS for area calculation (default: EPSG:3857 for meters)

    Returns:
        AreaStatisticsResult with calculated statistics
    """
    geom_col = f'"{geometry_column}"'

    # Calculate area using ST_Transform to a projected CRS for accurate measurement
    area_expr = f"ST_Area(ST_Transform({geom_col}, '{source_crs}', '{target_crs}'))"

    # Build aggregation based on operation
    if operation == AreaOperation.sum:
        agg_expr = f"SUM({area_expr})"
    elif operation == AreaOperation.mean:
        agg_expr = f"AVG({area_expr})"
    elif operation == AreaOperation.min:
        agg_expr = f"MIN({area_expr})"
    elif operation == AreaOperation.max:
        agg_expr = f"MAX({area_expr})"
    else:
        agg_expr = f"SUM({area_expr})"

    query = f"""
        SELECT
            {agg_expr} AS result,
            SUM({area_expr}) AS total_area,
            COUNT(*) AS feature_count
        FROM {table_name}
        WHERE {where_clause}
    """
    logger.debug("Area statistics query: %s with params: %s", query, params)

    if params:
        result = con.execute(query, params).fetchone()
    else:
        result = con.execute(query).fetchone()

    if result:
        return AreaStatisticsResult(
            result=result[0],
            total_area=result[1],
            feature_count=result[2],
            unit="m²",
        )
    else:
        return AreaStatisticsResult(
            result=None,
            total_area=None,
            feature_count=0,
            unit="m²",
        )
