"""Feature service for GeoJSON queries.

This service retrieves features from DuckLake as GeoJSON.
"""

import json
import logging
from typing import Any, Optional

from geoapi.cql_evaluator import cql2_to_duckdb_sql, parse_cql2_filter
from geoapi.dependencies import LayerInfo
from geoapi.ducklake import ducklake_manager

logger = logging.getLogger(__name__)


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

        # Build WHERE clause
        where_clauses: list[str] = []
        params: list[Any] = []

        # ID filter
        if ids:
            placeholders = ", ".join("?" for _ in ids)
            where_clauses.append(f'"id" IN ({placeholders})')
            params.extend(ids)

        # Bbox filter (only for layers with geometry)
        if bbox and has_geometry and geom_col:
            minx, miny, maxx, maxy = bbox
            bbox_wkt = f"POLYGON(({minx} {miny}, {minx} {maxy}, {maxx} {maxy}, {maxx} {miny}, {minx} {miny}))"
            where_clauses.append(f'ST_Intersects("{geom_col}", ST_GeomFromText(?))')
            params.append(bbox_wkt)

        # CQL filter
        if cql_filter and column_names:
            try:
                ast = parse_cql2_filter(
                    cql_filter["filter"],
                    cql_filter.get("lang", "cql2-json"),
                )
                cql_sql, cql_params = cql2_to_duckdb_sql(ast, column_names, geom_col)
                where_clauses.append(f"({cql_sql})")
                params.extend(cql_params)
            except Exception as e:
                logger.warning(f"CQL2 parse error: {e}")

        where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

        # Build ORDER BY clause
        order_clause = ""
        if sortby:
            if sortby.startswith("-"):
                order_clause = f'ORDER BY "{sortby[1:]}" DESC'
            elif sortby.startswith("+"):
                order_clause = f'ORDER BY "{sortby[1:]}" ASC'
            else:
                order_clause = f'ORDER BY "{sortby}" ASC'

        # Get total count
        count_query = f"SELECT COUNT(*) FROM {table} WHERE {where_sql}"
        logger.debug("Count query: %s with params: %s", count_query, params)
        try:
            with ducklake_manager.connection() as con:
                if params:
                    count_result = con.execute(count_query, params).fetchone()
                else:
                    count_result = con.execute(count_query).fetchone()
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
            with ducklake_manager.connection() as con:
                if params:
                    result = con.execute(query, params).fetchall()
                else:
                    result = con.execute(query).fetchall()

                # Get column names from description
                description = con.description
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

                    features.append(
                        {
                            "type": "Feature",
                            "id": str(feature_id) if feature_id else None,
                            "geometry": geometry,
                            "properties": row_dict,
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
            with ducklake_manager.connection() as con:
                result = con.execute(query, [feature_id]).fetchone()

                if not result:
                    return None

                # Get column names
                description = con.description
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

                return {
                    "type": "Feature",
                    "id": str(fid) if fid else None,
                    "geometry": geometry,
                    "properties": row_dict,
                }
        except Exception as e:
            logger.error(f"Feature by ID error: {e}", exc_info=True)
            return None


# Singleton instance
feature_service = FeatureService()
