"""Tile service for generating MVT tiles.

This service generates Mapbox Vector Tiles (MVT) using DuckDB's
native ST_AsMVT function.
"""

import logging
from typing import Any, Optional

from geoapi.config import settings
from geoapi.cql_evaluator import cql2_to_duckdb_sql, parse_cql2_filter
from geoapi.dependencies import LayerInfo
from geoapi.ducklake import ducklake_manager


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

        # MVT supported types
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

        def needs_cast(col_type: str) -> bool:
            """Check if type needs casting to VARCHAR for MVT."""
            type_lower = col_type.lower()
            return not any(t in type_lower for t in mvt_supported_types)

        # Build property selection - must be explicit columns (no * in subqueries)
        if properties:
            # Use specified properties, excluding geometry
            prop_cols = [p for p in properties if p not in (geom_col,)]
        elif column_names:
            # Use all available columns except geometry
            prop_cols = [c for c in column_names if c not in (geom_col,)]
        else:
            # No properties available
            prop_cols = []

        # Build select clause with casting for unsupported types
        select_parts = []
        for col in prop_cols:
            col_type = col_types.get(col, "VARCHAR")
            if needs_cast(col_type):
                select_parts.append(f'CAST("{col}" AS VARCHAR) AS "{col}"')
            else:
                select_parts.append(f'"{col}"')
        select_props = ", ".join(select_parts) if select_parts else None

        # Build WHERE clause (additional filters beyond tile bounds)
        extra_where_clauses = []
        params: list[Any] = []

        # Additional bbox filter
        if bbox:
            minx, miny, maxx, maxy = bbox
            bbox_wkt = f"POLYGON(({minx} {miny}, {minx} {maxy}, {maxx} {maxy}, {maxx} {miny}, {minx} {miny}))"
            extra_where_clauses.append(
                f'ST_Intersects("{geom_col}", ST_GeomFromText(?))'
            )
            params.append(bbox_wkt)

        # CQL2 filter
        if cql_filter and column_names:
            try:
                ast = parse_cql2_filter(
                    cql_filter["filter"],
                    cql_filter.get("lang", "cql2-json"),
                )
                cql_sql, cql_params = cql2_to_duckdb_sql(ast, column_names)
                extra_where_clauses.append(f"({cql_sql})")
                params.extend(cql_params)
            except Exception as e:
                # Log but don't fail on CQL parse errors
                logging.warning("CQL2 parse error: %s", e)

        # Combine tile bounds filter with extra filters
        extra_where_sql = (
            " AND " + " AND ".join(extra_where_clauses) if extra_where_clauses else ""
        )

        # Build struct_pack arguments for ST_AsMVT
        # geometry is handled separately via ST_AsMVTGeom
        struct_fields = [
            f"geometry := ST_AsMVTGeom(ST_Transform(candidates.\"{geom_col}\", 'EPSG:4326', 'EPSG:3857', always_xy := true), ST_Extent(bounds.bbox3857))"
        ]
        for col in prop_cols:
            struct_fields.append(f'"{col}" := candidates."{col}"')
        struct_pack_args = ", ".join(struct_fields)

        # Build MVT query following working pattern:
        # 1. bounds CTE: compute tile envelope in both projections
        # 2. candidates CTE: filter data using bbox (no ST_AsMVTGeom here)
        # 3. Final SELECT: ST_AsMVT with ST_AsMVTGeom inside struct_pack
        # Use QUALIFY for random sampling instead of LIMIT for better distribution
        select_clause = f'"{geom_col}"'
        if select_props:
            select_clause += f", {select_props}"

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
            with ducklake_manager.connection() as con:
                if params:
                    result = con.execute(query, params).fetchone()
                else:
                    result = con.execute(query).fetchone()

                if result and result[0]:
                    return bytes(result[0])
                return None
        except Exception as e:
            logging.error("Tile generation error: %s", e)
            raise


# Singleton instance
tile_service = TileService()
