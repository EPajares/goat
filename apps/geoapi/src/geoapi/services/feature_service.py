"""Feature service for GeoJSON queries.

This service retrieves features from DuckLake as GeoJSON.
"""

import json
import logging
from typing import Any, Optional

from goatlib.storage import build_filters, build_order_clause

from geoapi.dependencies import LayerInfo
from geoapi.ducklake import ducklake_manager
from geoapi.ducklake_pool import execute_with_retry

logger = logging.getLogger(__name__)


def sanitize_string(value: Any) -> Any:
    """Sanitize string values to ensure valid UTF-8.

    Some data may contain invalid UTF-8 bytes (e.g., Latin-1 or Windows-1252).
    This function attempts to fix encoding issues.
    """
    if isinstance(value, bytes):
        # Try UTF-8 first, then fallback to latin-1
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("latin-1", errors="replace")
    elif isinstance(value, str):
        # Re-encode and decode to fix any invalid sequences
        try:
            # Encode to bytes and back to ensure valid UTF-8
            return value.encode("utf-8", errors="surrogatepass").decode(
                "utf-8", errors="replace"
            )
        except (UnicodeDecodeError, UnicodeEncodeError):
            return value.encode("latin-1", errors="replace").decode(
                "utf-8", errors="replace"
            )
    return value


def sanitize_properties(properties: dict[str, Any]) -> dict[str, Any]:
    """Sanitize all string values in properties dict."""
    return {k: sanitize_string(v) for k, v in properties.items()}


class FeatureService:
    """Service for querying features."""

    def get_features(
        self,
        layer_info: LayerInfo,
        limit: int = 10,
        offset: int = 0,
        bbox: Optional[list[float]] = None,
        properties: Optional[list[str]] = None,
        cql_filter: Optional[dict] = None,
        column_names: Optional[list[str]] = None,
        sortby: Optional[str] = None,
        ids: Optional[list[str]] = None,
        geometry_column: str = "geometry",
        has_geometry: bool = True,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get features from a layer.

        Args:
            layer_info: Layer information
            limit: Maximum features to return
            offset: Number of features to skip
            bbox: Bounding box filter [minx, miny, maxx, maxy]
            properties: List of properties to include
            cql_filter: CQL2 filter
            column_names: Available column names for validation
            sortby: Sort column (prefix with - for descending)
            ids: List of feature IDs to filter
            geometry_column: Name of the geometry column
            has_geometry: Whether the layer has a geometry column

        Returns:
            Tuple of (features, total_count)
        """
        table = layer_info.full_table_name
        geom_col = geometry_column if has_geometry else None

        # Build SELECT clause
        if properties:
            # Ensure id is always included
            props_set = set(properties) | {"id"}
            select_cols = ", ".join(f'"{p}"' for p in props_set if p != geom_col)
            if has_geometry and geom_col:
                select_clause = (
                    f'{select_cols}, ST_AsGeoJSON("{geom_col}") AS geom_json'
                )
            else:
                select_clause = select_cols
        else:
            if has_geometry and geom_col:
                select_clause = f'*, ST_AsGeoJSON("{geom_col}") AS geom_json'
            else:
                select_clause = "*"

        # Build WHERE clause using shared query builder
        filters = build_filters(
            bbox=bbox,
            cql_filter=cql_filter,
            ids=ids,
            geometry_column=geom_col or "geometry",
            column_names=column_names,
            has_geometry=has_geometry,
        )
        where_sql = filters.to_full_where()
        params = filters.params

        # Build ORDER BY clause
        order_clause = build_order_clause(sortby)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM {table} WHERE {where_sql}"
        logger.debug("Count query: %s with params: %s", count_query, params)
        try:
            count_result, _ = execute_with_retry(
                ducklake_manager,
                count_query,
                params if params else None,
                fetch_all=False,
            )
            total_count = count_result[0] if count_result else 0
        except Exception as e:
            logger.warning("Count query failed: %s", e)
            total_count = 0

        # Get features
        query = f"""
            SELECT {select_clause}
            FROM {table}
            WHERE {where_sql}
            {order_clause}
            LIMIT {limit} OFFSET {offset}
        """
        logger.debug("Feature query: %s with params: %s", query, params)

        features = []
        try:
            result, description = execute_with_retry(
                ducklake_manager, query, params if params else None, fetch_all=True
            )

            # Get column names from description
            col_names = [desc[0] for desc in description]

            for row in result:
                row_dict = dict(zip(col_names, row))

                # Extract geometry (only if layer has geometry)
                geometry = None
                if has_geometry and geom_col:
                    geom_json = row_dict.pop("geom_json", None)
                    geometry = json.loads(geom_json) if geom_json else None
                    # Remove raw geometry column if present
                    row_dict.pop(geom_col, None)

                # Get ID
                feature_id = row_dict.pop("id", None)

                # Sanitize string values to ensure valid UTF-8
                sanitized_props = sanitize_properties(row_dict)

                features.append(
                    {
                        "type": "Feature",
                        "id": str(feature_id) if feature_id else None,
                        "geometry": geometry,
                        "properties": sanitized_props,
                    }
                )
        except Exception as e:
            logger.error(f"Feature query error: {e}", exc_info=True)
            raise

        return features, total_count

    def get_feature_by_id(
        self,
        layer_info: LayerInfo,
        feature_id: str,
        properties: Optional[list[str]] = None,
        geometry_column: str = "geometry",
        has_geometry: bool = True,
    ) -> Optional[dict[str, Any]]:
        """Get a single feature by ID.

        Args:
            layer_info: Layer information
            feature_id: Feature ID
            properties: Properties to include
            geometry_column: Name of the geometry column
            has_geometry: Whether the layer has a geometry column

        Returns:
            Feature dict or None if not found
        """
        table = layer_info.full_table_name
        geom_col = geometry_column if has_geometry else None

        # Build SELECT clause
        if properties:
            props_set = set(properties) | {"id"}
            select_cols = ", ".join(f'"{p}"' for p in props_set if p != geom_col)
            if has_geometry and geom_col:
                select_clause = (
                    f'{select_cols}, ST_AsGeoJSON("{geom_col}") AS geom_json'
                )
            else:
                select_clause = select_cols
        else:
            if has_geometry and geom_col:
                select_clause = f'*, ST_AsGeoJSON("{geom_col}") AS geom_json'
            else:
                select_clause = "*"

        query = f"""
            SELECT {select_clause}
            FROM {table}
            WHERE "id" = ?
            LIMIT 1
        """

        try:
            result, description = execute_with_retry(
                ducklake_manager, query, [feature_id], fetch_all=False
            )

            if not result:
                return None

            # Get column names
            col_names = [desc[0] for desc in description]
            row_dict = dict(zip(col_names, result))

            # Extract geometry (only if layer has geometry)
            geometry = None
            if has_geometry and geom_col:
                geom_json = row_dict.pop("geom_json", None)
                geometry = json.loads(geom_json) if geom_json else None
                # Remove raw geometry column
                row_dict.pop(geom_col, None)

            # Get ID
            fid = row_dict.pop("id", None)

            # Sanitize string values to ensure valid UTF-8
            sanitized_props = sanitize_properties(row_dict)

            return {
                "type": "Feature",
                "id": str(fid) if fid else None,
                "geometry": geometry,
                "properties": sanitized_props,
            }
        except Exception as e:
            logger.error(f"Feature by ID error: {e}", exc_info=True)
            return None


# Singleton instance
feature_service = FeatureService()
