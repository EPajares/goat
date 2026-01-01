"""Analytics service for synchronous statistics operations.

Uses goatlib statistics functions to compute analytics on DuckLake layers.
These are synchronous operations that return immediate results.
"""

import logging
from typing import Any

from goatlib.analysis.statistics import (
    AreaOperation,
    ClassBreakMethod,
    SortOrder,
    calculate_area_statistics,
    calculate_class_breaks,
    calculate_feature_count,
    calculate_unique_values,
)
from goatlib.storage import build_filters

from geoapi.dependencies import (
    _layer_id_to_table_name,
    get_schema_for_layer,
    normalize_layer_id,
)
from geoapi.ducklake import ducklake_manager

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

    def _build_where_clause(self, filter_expr: str | None) -> tuple[str, list[Any]]:
        """Build SQL WHERE clause from CQL2 filter.

        Args:
            filter_expr: CQL2 filter expression or None

        Returns:
            Tuple of (where_clause, params)
        """
        if not filter_expr:
            return "TRUE", []

        # Use goatlib's filter builder
        try:
            where_clause, params = build_filters(filter_expr)
            return where_clause or "TRUE", params or []
        except Exception as e:
            logger.warning("Failed to parse filter '%s': %s", filter_expr, e)
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
        where_clause, params = self._build_where_clause(filter_expr)

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
        where_clause, params = self._build_where_clause(filter_expr)

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
        where_clause, params = self._build_where_clause(filter_expr)

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
        where_clause, params = self._build_where_clause(filter_expr)

        # Map string to enum
        area_op = AreaOperation.sum
        if operation in AreaOperation.__members__:
            area_op = AreaOperation(operation)

        with ducklake_manager.connection() as con:
            result = calculate_area_statistics(
                con,
                table_name,
                geometry_column="geom",  # Standard geometry column name
                operation=area_op,
                where_clause=where_clause,
                params=params if params else None,
            )

        return result.model_dump()


# Singleton instance
analytics_service = AnalyticsService()
