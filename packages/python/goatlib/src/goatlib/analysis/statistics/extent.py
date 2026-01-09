"""Layer extent calculation."""

import logging
from typing import Any

import duckdb

from goatlib.analysis.schemas.statistics import ExtentResult

logger = logging.getLogger(__name__)


def calculate_extent(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    geometry_column: str = "geom",
    where_clause: str = "TRUE",
    params: list[Any] | None = None,
    source_crs: str = "EPSG:4326",
) -> ExtentResult:
    """Calculate the bounding box extent of features in a table.

    The extent is returned in WGS84 (EPSG:4326) coordinates.

    Args:
        con: DuckDB connection
        table_name: Fully qualified table name (e.g., "lake.my_table")
        geometry_column: Name of the geometry column (default: "geom")
        where_clause: SQL WHERE clause condition (default: "TRUE" for all rows)
        params: Optional query parameters for prepared statement
        source_crs: Source CRS of the geometry column (default: "EPSG:4326")

    Returns:
        ExtentResult with bbox [minx, miny, maxx, maxy] and feature count
    """
    # Query to get extent and count in one pass
    # Transform to WGS84 and calculate the bounding box
    # Use ST_Extent_Agg to aggregate the extent of all features
    query = f"""
        SELECT
            ST_XMin(ST_Extent_Agg(ST_Transform({geometry_column}, '{source_crs}', 'EPSG:4326'))) as minx,
            ST_YMin(ST_Extent_Agg(ST_Transform({geometry_column}, '{source_crs}', 'EPSG:4326'))) as miny,
            ST_XMax(ST_Extent_Agg(ST_Transform({geometry_column}, '{source_crs}', 'EPSG:4326'))) as maxx,
            ST_YMax(ST_Extent_Agg(ST_Transform({geometry_column}, '{source_crs}', 'EPSG:4326'))) as maxy,
            COUNT(*) as feature_count
        FROM {table_name}
        WHERE {where_clause}
    """
    logger.debug("Extent query: %s with params: %s", query, params)

    if params:
        result = con.execute(query, params).fetchone()
    else:
        result = con.execute(query).fetchone()

    if not result or result[4] == 0:
        return ExtentResult(bbox=None, feature_count=0)

    minx, miny, maxx, maxy, feature_count = result

    # Handle case where all values might be None (no valid geometries)
    if minx is None or miny is None or maxx is None or maxy is None:
        return ExtentResult(bbox=None, feature_count=feature_count)

    return ExtentResult(
        bbox=[float(minx), float(miny), float(maxx), float(maxy)],
        feature_count=feature_count,
    )
