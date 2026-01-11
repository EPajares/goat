"""Tile service for generating MVT tiles.

This service generates Mapbox Vector Tiles (MVT) using DuckDB's
native ST_AsMVT function.
"""

import logging
from typing import Optional

from goatlib.storage import build_filters

from geoapi.config import settings
from geoapi.dependencies import LayerInfo
from geoapi.ducklake_pool import ducklake_pool

logger = logging.getLogger(__name__)


class TileService:
    """Service for generating vector tiles."""

    def __init__(self) -> None:
        self.max_features = settings.MAX_FEATURES_PER_TILE
        self.extent = settings.DEFAULT_EXTENT
        self.buffer = settings.DEFAULT_TILE_BUFFER

    def get_tile(
        self,
        layer_info: LayerInfo,
        z: int,
        x: int,
        y: int,
        properties: Optional[list[str]] = None,
        cql_filter: Optional[dict] = None,
        bbox: Optional[list[float]] = None,
        limit: Optional[int] = None,
        columns: Optional[list[dict]] = None,
        geometry_column: str = "geometry",
    ) -> Optional[bytes]:
        """Generate MVT tile for a layer.

        Args:
            layer_info: Layer information from URL
            z, x, y: Tile coordinates
            properties: List of properties to include
            cql_filter: CQL2 filter dict with 'filter' and 'lang' keys
            bbox: Additional bbox filter
            limit: Maximum features
            columns: List of column dicts with 'name' and 'type' keys
            geometry_column: Name of the geometry column

        Returns:
            MVT tile bytes or None if empty
        """
        limit = min(limit or self.max_features, self.max_features)
        table = layer_info.full_table_name

        geom_col = geometry_column
        columns = columns or []

        # Build column type mapping
        col_types = {col["name"]: col.get("type", "VARCHAR") for col in columns}
        column_names = [col["name"] for col in columns]

        # MVT supported types (can be passed directly)
        mvt_supported_types = {
            "varchar",
            "text",
            "string",
            "float",
            "double",
            "real",
            "integer",
            "int",
            "int4",
            "int8",
            "bigint",
            "smallint",
            "tinyint",
            "boolean",
            "bool",
        }

        # Types that need casting to BIGINT (unsigned integers)
        unsigned_int_types = {"ubigint", "uinteger", "uint64", "uint32", "uhugeint"}

        # Types that cannot be included in MVT at all (even with casting)
        mvt_excluded_type_prefixes = {"struct", "map", "list", "union"}

        def is_excluded_type(col_type: str) -> bool:
            """Check if type must be excluded from MVT entirely."""
            type_lower = col_type.lower()
            # Exclude array types (e.g., VARCHAR[], INTEGER[])
            if type_lower.endswith("[]"):
                return True
            return any(type_lower.startswith(t) for t in mvt_excluded_type_prefixes)

        def get_cast_type(col_type: str) -> str | None:
            """Get the target type for casting, or None if no cast needed."""
            type_lower = col_type.lower()
            # Check unsigned integers FIRST (before substring match, since 'ubigint' contains 'int')
            if type_lower in unsigned_int_types:
                return "BIGINT"
            # Check if it's a supported type (no cast needed)
            if any(t in type_lower for t in mvt_supported_types):
                return None
            # Cast everything else to VARCHAR
            return "VARCHAR"

        # Check if 'id' column exists in the data
        has_id_column = "id" in column_names

        # Build property selection - must be explicit columns (no * in subqueries)
        if properties:
            # Use specified properties, excluding geometry
            prop_cols = [p for p in properties if p not in (geom_col,)]
            # Always include id if it exists in the table (for feature identification)
            if has_id_column and "id" not in prop_cols:
                prop_cols.append("id")
        elif column_names:
            # Use all available columns except geometry
            prop_cols = [c for c in column_names if c not in (geom_col,)]
        else:
            # No properties available
            prop_cols = []

        # Filter out columns with types that cannot be used in MVT at all
        prop_cols = [
            c for c in prop_cols if not is_excluded_type(col_types.get(c, "VARCHAR"))
        ]

        # Build select clause with casting for unsupported types
        select_parts = []
        for col in prop_cols:
            col_type = col_types.get(col, "VARCHAR")
            cast_type = get_cast_type(col_type)
            if cast_type:
                select_parts.append(f'CAST("{col}" AS {cast_type}) AS "{col}"')
            else:
                select_parts.append(f'"{col}"')
        select_props = ", ".join(select_parts) if select_parts else None

        # Build WHERE clause (additional filters beyond tile bounds)
        # Uses shared query builder for bbox and CQL filters
        filters = build_filters(
            bbox=bbox,
            cql_filter=cql_filter,
            geometry_column=geom_col,
            column_names=column_names,
            has_geometry=True,
        )
        extra_where_sql = filters.to_where_sql()
        params = filters.params

        # Build struct_pack arguments for ST_AsMVT
        # geometry is handled separately via ST_AsMVTGeom
        struct_fields = [
            f"geometry := ST_AsMVTGeom(ST_Transform(candidates.\"{geom_col}\", 'EPSG:4326', 'EPSG:3857', always_xy := true), ST_Extent(bounds.bbox3857))"
        ]

        # Add id field - use actual id if exists, otherwise use DuckLake's rowid
        if has_id_column:
            struct_fields.append('"id" := candidates."id"')
        else:
            # Use DuckLake's built-in rowid which is stable and globally unique
            struct_fields.append('"id" := candidates.rowid')

        for col in prop_cols:
            # Skip id since we handle it separately above
            if col != "id":
                struct_fields.append(f'"{col}" := candidates."{col}"')
        struct_pack_args = ", ".join(struct_fields)

        # Build MVT query following working pattern:
        # 1. bounds CTE: compute tile envelope in both projections
        # 2. candidates CTE: filter data using bbox (no ST_AsMVTGeom here)
        # 3. Final SELECT: ST_AsMVT with ST_AsMVTGeom inside struct_pack
        select_clause = f'"{geom_col}"'
        if select_props:
            select_clause += f", {select_props}"

        # Add rowid to select clause if no id column exists (for stable IDs)
        if not has_id_column:
            select_clause += ", rowid"

        # Check if table has bbox column for fast row group pruning
        # Support both legacy scalar columns ($minx, etc.) and GeoParquet 1.1 struct bbox
        has_scalar_bbox = all(
            c in column_names for c in ["$minx", "$miny", "$maxx", "$maxy"]
        )
        has_struct_bbox = "bbox" in column_names
        has_bbox_columns = has_scalar_bbox or has_struct_bbox

        if has_bbox_columns:
            # Fast path: use bbox columns for row group pruning
            # This is 10-100x faster because parquet can skip entire row groups
            # Prefer scalar columns (legacy) over struct bbox (GeoParquet 1.1)
            if has_scalar_bbox:
                bbox_filter = """"$minx" <= ST_XMax(bounds.bbox4326)
                      AND "$maxx" >= ST_XMin(bounds.bbox4326)
                      AND "$miny" <= ST_YMax(bounds.bbox4326)
                      AND "$maxy" >= ST_YMin(bounds.bbox4326)"""
            else:
                bbox_filter = """bbox.xmin <= ST_XMax(bounds.bbox4326)
                      AND bbox.xmax >= ST_XMin(bounds.bbox4326)
                      AND bbox.ymin <= ST_YMax(bounds.bbox4326)
                      AND bbox.ymax >= ST_YMin(bounds.bbox4326)"""

            query = f"""
                WITH bounds AS (
                    SELECT
                        ST_TileEnvelope({z}, {x}, {y}) AS bbox3857,
                        ST_Transform(ST_TileEnvelope({z}, {x}, {y}), 'EPSG:3857', 'EPSG:4326', always_xy := true) AS bbox4326
                ),
                candidates AS (
                    SELECT {select_clause}
                    FROM {table}, bounds
                    WHERE {bbox_filter}
                      AND ST_Intersects("{geom_col}", bounds.bbox4326){extra_where_sql}
                    QUALIFY ROW_NUMBER() OVER (ORDER BY random()) <= {limit}
                )
                SELECT ST_AsMVT(
                    struct_pack({struct_pack_args}),
                    'default'
                )
                FROM candidates, bounds
            """
        else:
            # Fallback: no bbox columns, use ST_Intersects only
            query = f"""
                WITH bounds AS (
                    SELECT
                        ST_TileEnvelope({z}, {x}, {y}) AS bbox3857,
                        ST_Transform(ST_TileEnvelope({z}, {x}, {y}), 'EPSG:3857', 'EPSG:4326', always_xy := true) AS bbox4326
                ),
                candidates AS (
                    SELECT {select_clause}
                    FROM {table}, bounds
                    WHERE ST_Intersects("{geom_col}", bounds.bbox4326){extra_where_sql}
                    QUALIFY ROW_NUMBER() OVER (ORDER BY random()) <= {limit}
                )
                SELECT ST_AsMVT(
                    struct_pack({struct_pack_args}),
                    'default'
                )
                FROM candidates, bounds
            """

        try:
            # Use pool's execute_with_retry for automatic connection handling
            # Apply query timeout to prevent blocking other requests
            result = ducklake_pool.execute_with_retry(
                query,
                params=params if params else None,
                max_retries=3,
                fetch_all=False,
                timeout=settings.QUERY_TIMEOUT,
            )

            if result and result[0]:
                return bytes(result[0])
            return None
        except TimeoutError:
            logger.warning("Tile query timeout: z=%d, x=%d, y=%d", z, x, y)
            raise
        except Exception as e:
            logger.error("Tile generation error: %s", e)
            raise


# Singleton instance
tile_service = TileService()
