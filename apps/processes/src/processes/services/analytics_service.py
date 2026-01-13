"""Analytics service for synchronous statistics operations.

Uses goatlib statistics functions to compute analytics on DuckLake layers.
These are synchronous operations that return immediate results.
"""

import json
import logging
from typing import Any

from goatlib.analysis.statistics import (
    AreaOperation,
    ClassBreakMethod,
    SortOrder,
    StatisticsOperation,
    calculate_aggregation_stats,
    calculate_area_statistics,
    calculate_class_breaks,
    calculate_extent,
    calculate_feature_count,
    calculate_histogram,
    calculate_unique_values,
)
from goatlib.storage import build_cql_filter

from processes.dependencies import (
    _layer_id_to_table_name,
    get_schema_for_layer,
    normalize_layer_id,
)
from processes.ducklake import ducklake_manager

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for computing analytics on DuckLake layers."""

    def _get_table_name(self, collection: str) -> str:
        """Get the full DuckLake table name for a collection/layer ID.

        Args:
            collection: Layer ID (UUID format)

        Returns:
            Full table name like 'lake.user_xxx.t_layerid'
        """
        layer_id = normalize_layer_id(collection)
        schema_name = get_schema_for_layer(layer_id)
        table_name = _layer_id_to_table_name(layer_id)
        return f"lake.{schema_name}.{table_name}"

    def _get_column_names(self, table_name: str) -> list[str]:
        """Get column names for a table.

        Args:
            table_name: Full table name

        Returns:
            List of column names
        """
        with ducklake_manager.connection() as con:
            result = con.execute(f"DESCRIBE {table_name}").fetchall()
            return [row[0] for row in result]

    def _detect_geometry_column(self, table_name: str) -> str:
        """Detect the geometry column name for a table.

        Args:
            table_name: Full table name

        Returns:
            Geometry column name (defaults to 'geometry')
        """
        with ducklake_manager.connection() as con:
            result = con.execute(f"DESCRIBE {table_name}").fetchall()
            for row in result:
                col_name, col_type = row[0], row[1]
                if "GEOMETRY" in col_type.upper():
                    return col_name
        return "geometry"

    def _build_where_clause(
        self,
        filter_expr: str | None,
        table_name: str,
        geometry_column: str = "geometry",
    ) -> tuple[str, list[Any]]:
        """Build SQL WHERE clause from CQL2 filter.

        Args:
            filter_expr: CQL2 filter expression (JSON string) or None
            table_name: Full table name (for getting column names)
            geometry_column: Name of geometry column

        Returns:
            Tuple of (where_clause, params)
        """
        if not filter_expr:
            return "TRUE", []

        try:
            # Parse the filter JSON string
            if isinstance(filter_expr, str):
                filter_dict = json.loads(filter_expr)
            else:
                filter_dict = filter_expr

            # Get column names and detect geometry column from the table
            with ducklake_manager.connection() as con:
                result = con.execute(f"DESCRIBE {table_name}").fetchall()
                column_names = [row[0] for row in result]
                column_types = {row[0]: row[1] for row in result}

            # Detect geometry column name (could be 'geom', 'geometry', etc.)
            geometry_column = "geometry"  # default
            for col_name, col_type in column_types.items():
                if "geometry" in col_type.lower() or col_name.lower() in (
                    "geom",
                    "geometry",
                ):
                    geometry_column = col_name
                    break

            # Build CQL filter with proper structure
            cql_filter = {"filter": filter_dict, "lang": "cql2-json"}
            query_filters = build_cql_filter(
                cql_filter,
                column_names,
                geometry_column=geometry_column,
            )

            where_clause = query_filters.to_full_where(default="TRUE")
            params = query_filters.params

            logger.debug("CQL filter built: %s with params %s", where_clause, params)
            return where_clause, params

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse filter JSON '%s': %s", filter_expr, e)
            return "TRUE", []
        except Exception as e:
            logger.warning("Failed to build filter '%s': %s", filter_expr, e)
            return "TRUE", []

    def feature_count(
        self,
        collection: str,
        filter_expr: str | None = None,
    ) -> dict[str, Any]:
        """Count features in a collection.

        Args:
            collection: Layer ID
            filter_expr: Optional CQL2 filter

        Returns:
            Dict with 'count' key
        """
        table_name = self._get_table_name(collection)
        geometry_column = self._detect_geometry_column(table_name)
        where_clause, params = self._build_where_clause(
            filter_expr, table_name, geometry_column
        )

        with ducklake_manager.connection() as con:
            result = calculate_feature_count(
                con,
                table_name,
                where_clause=where_clause,
                params=params if params else None,
            )

        return result.model_dump()

    def unique_values(
        self,
        collection: str,
        attribute: str,
        order: str = "descendent",
        filter_expr: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get unique values for an attribute.

        Args:
            collection: Layer ID
            attribute: Column name
            order: Sort order ('ascendent' or 'descendent')
            filter_expr: Optional CQL2 filter
            limit: Maximum values to return
            offset: Pagination offset

        Returns:
            Dict with attribute, total, and values
        """
        table_name = self._get_table_name(collection)
        geometry_column = self._detect_geometry_column(table_name)
        where_clause, params = self._build_where_clause(
            filter_expr, table_name, geometry_column
        )

        # Map string to enum
        sort_order = SortOrder.descendent
        if order == "ascendent":
            sort_order = SortOrder.ascendent

        with ducklake_manager.connection() as con:
            result = calculate_unique_values(
                con,
                table_name,
                attribute,
                where_clause=where_clause,
                params=params if params else None,
                order=sort_order,
                limit=limit,
                offset=offset,
            )

        return result.model_dump()

    def class_breaks(
        self,
        collection: str,
        attribute: str,
        method: str = "quantile",
        breaks: int = 5,
        filter_expr: str | None = None,
        strip_zeros: bool = False,
    ) -> dict[str, Any]:
        """Calculate class breaks for a numeric attribute.

        Args:
            collection: Layer ID
            attribute: Numeric column name
            method: Classification method
            breaks: Number of breaks
            filter_expr: Optional CQL2 filter
            strip_zeros: Exclude zero values

        Returns:
            Dict with breaks, min, max, mean, std_dev
        """
        table_name = self._get_table_name(collection)
        geometry_column = self._detect_geometry_column(table_name)
        where_clause, params = self._build_where_clause(
            filter_expr, table_name, geometry_column
        )

        # Map string to enum
        break_method = ClassBreakMethod.quantile
        if method in ClassBreakMethod.__members__:
            break_method = ClassBreakMethod(method)

        with ducklake_manager.connection() as con:
            result = calculate_class_breaks(
                con,
                table_name,
                attribute,
                method=break_method,
                num_breaks=breaks,
                where_clause=where_clause,
                params=params if params else None,
                strip_zeros=strip_zeros,
            )

        return result.model_dump()

    def area_statistics(
        self,
        collection: str,
        operation: str = "sum",
        filter_expr: str | None = None,
    ) -> dict[str, Any]:
        """Calculate area statistics for polygon features.

        Args:
            collection: Layer ID
            operation: Statistical operation (sum, mean, min, max)
            filter_expr: Optional CQL2 filter

        Returns:
            Dict with result, total_area, feature_count, unit
        """
        table_name = self._get_table_name(collection)
        geometry_column = self._detect_geometry_column(table_name)
        where_clause, params = self._build_where_clause(
            filter_expr, table_name, geometry_column
        )

        # Map string to enum
        area_op = AreaOperation.sum
        if operation in AreaOperation.__members__:
            area_op = AreaOperation(operation)

        with ducklake_manager.connection() as con:
            result = calculate_area_statistics(
                con,
                table_name,
                geometry_column=geometry_column,
                operation=area_op,
                where_clause=where_clause,
                params=params if params else None,
            )

        return result.model_dump()

    def extent(
        self,
        collection: str,
        filter_expr: str | None = None,
    ) -> dict[str, Any]:
        """Calculate bounding box extent for features.

        Args:
            collection: Layer ID
            filter_expr: Optional CQL2 filter

        Returns:
            Dict with bbox [minx, miny, maxx, maxy] and feature_count
        """
        table_name = self._get_table_name(collection)
        geometry_column = self._detect_geometry_column(table_name)
        where_clause, params = self._build_where_clause(
            filter_expr, table_name, geometry_column
        )

        logger.info(
            "Extent query: table=%s, geom_col=%s, where=%s, params=%s",
            table_name,
            geometry_column,
            where_clause,
            params,
        )

        with ducklake_manager.connection() as con:
            result = calculate_extent(
                con,
                table_name,
                geometry_column=geometry_column,
                where_clause=where_clause,
                params=params if params else None,
            )
        return result.model_dump()

    def aggregation_stats(
        self,
        collection: str,
        operation: str = "count",
        operation_column: str | None = None,
        group_by_column: str | None = None,
        filter_expr: str | None = None,
        order: str = "descendent",
        limit: int = 100,
    ) -> dict[str, Any]:
        """Calculate aggregation statistics with optional grouping.

        Args:
            collection: Layer ID
            operation: Statistical operation (count, sum, mean, min, max)
            operation_column: Column to perform the operation on
            group_by_column: Optional column to group results by
            filter_expr: Optional CQL2 filter
            order: Sort order (ascendent or descendent)
            limit: Maximum number of grouped values to return

        Returns:
            Dict with items, total_items, and total_count
        """
        table_name = self._get_table_name(collection)
        where_clause, params = self._build_where_clause(filter_expr, table_name)

        # Map string to enum
        stats_op = StatisticsOperation.count
        if operation in StatisticsOperation.__members__:
            stats_op = StatisticsOperation(operation)

        sort_order = SortOrder.descendent
        if order == "ascendent":
            sort_order = SortOrder.ascendent

        with ducklake_manager.connection() as con:
            result = calculate_aggregation_stats(
                con,
                table_name,
                operation=stats_op,
                operation_column=operation_column,
                group_by_column=group_by_column,
                where_clause=where_clause,
                params=params if params else None,
                order=sort_order,
                limit=limit,
            )

        return result.model_dump()

    def histogram(
        self,
        collection: str,
        column: str,
        num_bins: int = 10,
        filter_expr: str | None = None,
        order: str = "ascendent",
    ) -> dict[str, Any]:
        """Calculate histogram for a numeric column.

        Args:
            collection: Layer ID
            column: Numeric column name
            num_bins: Number of histogram bins
            filter_expr: Optional CQL2 filter
            order: Sort order of bins (ascendent or descendent)

        Returns:
            Dict with bins, missing_count, and total_rows
        """
        table_name = self._get_table_name(collection)
        where_clause, params = self._build_where_clause(filter_expr, table_name)

        sort_order = SortOrder.ascendent
        if order == "descendent":
            sort_order = SortOrder.descendent

        with ducklake_manager.connection() as con:
            result = calculate_histogram(
                con,
                table_name,
                column=column,
                num_bins=num_bins,
                where_clause=where_clause,
                params=params if params else None,
                order=sort_order,
            )

        return result.model_dump()


# Singleton instance
analytics_service = AnalyticsService()
