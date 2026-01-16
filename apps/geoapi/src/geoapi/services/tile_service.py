"""Tile service for generating MVT tiles.

This service generates Mapbox Vector Tiles (MVT) using a hybrid approach:
1. PMTiles (static) - Pre-generated tiles for fast unfiltered access
2. Dynamic tiles - On-the-fly generation using DuckDB's ST_AsMVT for filtered requests

The service automatically routes requests to the appropriate source:
- If PMTiles exist AND no CQL filter is applied → serve from PMTiles
- Otherwise → generate dynamically from DuckLake
"""

import asyncio
import logging
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from goatlib.storage import build_filters
from pmtiles.reader import MmapSource
from pmtiles.reader import Reader as PMTilesReader

from geoapi.config import settings
from geoapi.dependencies import LayerInfo
from geoapi.ducklake_pool import ducklake_pool

logger = logging.getLogger(__name__)

# Web Mercator extent in meters (EPSG:3857)
WEB_MERCATOR_EXTENT = 20037508.342789244

# Thread pool for PMTiles I/O (file reads are blocking)
_pmtiles_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pmtiles")

# Thread pool for dynamic tile generation (DuckDB queries are blocking)
_dynamic_tile_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="dyntile")


def tile_to_bbox_4326(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Convert tile coordinates to EPSG:4326 (lon/lat) bounding box.

    Args:
        z: Zoom level
        x: Tile X coordinate
        y: Tile Y coordinate

    Returns:
        Tuple of (xmin, ymin, xmax, ymax) in EPSG:4326
    """
    n = 2**z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return (lon_min, lat_min, lon_max, lat_max)


def tile_to_bbox_3857(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Convert tile coordinates to EPSG:3857 (Web Mercator) bounding box.

    Args:
        z: Zoom level
        x: Tile X coordinate
        y: Tile Y coordinate

    Returns:
        Tuple of (xmin, ymin, xmax, ymax) in EPSG:3857
    """
    n = 2**z
    tile_size = 2 * WEB_MERCATOR_EXTENT / n
    x_min = -WEB_MERCATOR_EXTENT + x * tile_size
    x_max = -WEB_MERCATOR_EXTENT + (x + 1) * tile_size
    y_max = WEB_MERCATOR_EXTENT - y * tile_size
    y_min = WEB_MERCATOR_EXTENT - (y + 1) * tile_size
    return (x_min, y_min, x_max, y_max)


class TileService:
    """Service for generating vector tiles with hybrid PMTiles/dynamic support."""

    def __init__(self) -> None:
        self.max_features = settings.MAX_FEATURES_PER_TILE
        self.extent = settings.DEFAULT_EXTENT
        self.buffer = settings.DEFAULT_TILE_BUFFER
        self.ducklake_data_dir = Path(settings.DUCKLAKE_DATA_DIR)
        self.tiles_data_dir = Path(settings.TILES_DATA_DIR)
        # Track which PMTiles files exist (simple path cache)
        self._pmtiles_exists_cache: dict[str, bool] = {}

    def _get_pmtiles_path(self, layer_info: LayerInfo) -> Path:
        """Get the PMTiles file path for a layer.

        Args:
            layer_info: Layer information

        Returns:
            Path to PMTiles file
        """
        return (
            self.tiles_data_dir
            / layer_info.schema_name
            / f"{layer_info.table_name}.pmtiles"
        )

    def _pmtiles_exists(self, layer_info: LayerInfo) -> bool:
        """Check if PMTiles file exists for a layer.

        Uses caching to avoid repeated filesystem checks.

        Args:
            layer_info: Layer information

        Returns:
            True if PMTiles file exists
        """
        cache_key = f"{layer_info.schema_name}/{layer_info.table_name}"

        if cache_key not in self._pmtiles_exists_cache:
            pmtiles_path = self._get_pmtiles_path(layer_info)
            exists = pmtiles_path.exists()
            self._pmtiles_exists_cache[cache_key] = exists
            logger.debug(
                "PMTiles %s for %s", "available" if exists else "not found", cache_key
            )

        return self._pmtiles_exists_cache[cache_key]

    def invalidate_pmtiles_cache(self, schema_name: str, table_name: str) -> None:
        """Invalidate PMTiles cache for a layer.

        Call this when PMTiles are regenerated or deleted.

        Args:
            schema_name: Schema name (e.g., "user_abc123")
            table_name: Table name (e.g., "t_xyz789")
        """
        cache_key = f"{schema_name}/{table_name}"
        if cache_key in self._pmtiles_exists_cache:
            del self._pmtiles_exists_cache[cache_key]
            logger.debug("Invalidated PMTiles cache for %s", cache_key)

    def invalidate_all_pmtiles_cache(self) -> None:
        """Invalidate all PMTiles cache entries.

        Call this on service restart or when PMTiles storage changes.
        """
        self._pmtiles_exists_cache.clear()
        logger.debug("Invalidated all PMTiles cache")

    def _should_use_pmtiles(
        self,
        layer_info: LayerInfo,
        cql_filter: Optional[dict] = None,
        bbox: Optional[list[float]] = None,
    ) -> bool:
        """Determine if request should use PMTiles.

        PMTiles are used when:
        1. PMTiles file exists for the layer
        2. No CQL filter is applied (filters require dynamic generation)
        3. No additional bbox filter (tile bbox is implicit)

        Args:
            layer_info: Layer information
            cql_filter: Optional CQL filter
            bbox: Optional additional bbox filter

        Returns:
            True if PMTiles should be used
        """
        # If filters are applied, need dynamic generation
        if cql_filter or bbox:
            return False

        # Check if PMTiles exist
        return self._pmtiles_exists(layer_info)

    async def _get_tile_from_pmtiles(
        self, layer_info: LayerInfo, z: int, x: int, y: int
    ) -> Optional[tuple[bytes, bool]]:
        """Get tile data from PMTiles file using pmtiles library.

        Supports overzooming: if requested zoom > max_zoom, serves the
        corresponding parent tile at max_zoom.

        Runs in a thread pool since file I/O is blocking.

        Args:
            layer_info: Layer information
            z: Zoom level
            x: Tile X coordinate
            y: Tile Y coordinate

        Returns:
            Tuple of (tile_data, is_gzip_compressed) or None if tile not found
        """
        pmtiles_path = self._get_pmtiles_path(layer_info)

        def _read_tile() -> Optional[tuple[bytes, bool]]:
            """Synchronous tile read function."""
            try:
                with open(pmtiles_path, "rb") as f:
                    reader = PMTilesReader(MmapSource(f))
                    header = reader.header()

                    min_zoom = header.get("min_zoom", 0)
                    max_zoom = header.get("max_zoom", 22)

                    # Check if below min zoom
                    if z < min_zoom:
                        logger.debug(
                            "PMTiles zoom %d below min %d for %s",
                            z,
                            min_zoom,
                            pmtiles_path.name,
                        )
                        return b"", False  # Empty tile

                    # Overzoom support: if z > max_zoom, get the parent tile at max_zoom
                    actual_z, actual_x, actual_y = z, x, y
                    if z > max_zoom:
                        # Calculate parent tile coordinates at max_zoom
                        zoom_diff = z - max_zoom
                        actual_z = max_zoom
                        actual_x = x >> zoom_diff  # x // (2 ** zoom_diff)
                        actual_y = y >> zoom_diff  # y // (2 ** zoom_diff)
                        logger.debug(
                            "Overzooming: %d/%d/%d -> %d/%d/%d",
                            z,
                            x,
                            y,
                            actual_z,
                            actual_x,
                            actual_y,
                        )

                    # Get tile data - returns None if tile doesn't exist (sparse tile)
                    tile_data = reader.get(actual_z, actual_x, actual_y)

                    # Check if tiles are gzip compressed
                    tile_compression = header.get("tile_compression")
                    is_gzip = tile_compression and tile_compression.value == 2  # GZIP

                    # If tile is None but within zoom range, return empty tile
                    # (don't fall back to GeoParquet for sparse areas)
                    if tile_data is None:
                        return b"", False  # Empty MVT tile

                    return tile_data, is_gzip
            except Exception as e:
                logger.warning("PMTiles read error for %s: %s", pmtiles_path, e)
                return None

        # Run blocking I/O in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_pmtiles_executor, _read_tile)

    async def get_tile(
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
    ) -> Optional[tuple[bytes, bool]]:
        """Generate MVT tile for a layer.

        Uses PMTiles for unfiltered requests, GeoParquet for filtered requests.

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
            Tuple of (MVT tile bytes, is_gzip_compressed, source) or None if empty
            source is 'pmtiles' or 'geoparquet'
        """
        # If CQL filter or bbox is provided, use dynamic GeoParquet generation
        if cql_filter or bbox:
            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            tile_data = await loop.run_in_executor(
                _dynamic_tile_executor,
                lambda: self._generate_dynamic_tile(
                    layer_info=layer_info,
                    z=z,
                    x=x,
                    y=y,
                    properties=properties,
                    cql_filter=cql_filter,
                    bbox=bbox,
                    limit=limit,
                    columns=columns,
                    geometry_column=geometry_column,
                ),
            )
            if tile_data is None:
                return None
            return tile_data, False, "geoparquet"  # Dynamic tiles are not gzip compressed

        # Unfiltered request - use PMTiles only
        if not self._pmtiles_exists(layer_info):
            logger.warning(
                "No PMTiles for %s, tile not available",
                layer_info.table_name,
            )
            return None

        result = await self._get_tile_from_pmtiles(layer_info, z, x, y)
        if result is not None:
            tile_data, is_gzip = result
            logger.info(
                "Tile (PMTiles): %s z=%d/%d/%d",
                layer_info.table_name,
                z,
                x,
                y,
            )
            return tile_data, is_gzip, "pmtiles"

        # Tile not in PMTiles (outside zoom bounds)
        return None

    def _generate_dynamic_tile(
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
        """Generate MVT tile dynamically using DuckDB.

        Args:
            layer_info: Layer information from URL
            z, x, y: Tile coordinates
            properties: List of properties to include
            cql_filter: CQL2 filter dict
            bbox: Additional bbox filter
            limit: Maximum features
            columns: List of column dicts
            geometry_column: Name of the geometry column

        Returns:
            MVT tile bytes or None if empty
        """
        logger.info(
            "Tile (GeoParquet): %s z=%d/%d/%d",
            layer_info.table_name,
            z,
            x,
            y,
        )
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
            # Check unsigned integers FIRST (before substring match)
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

        # Filter out hidden fields (e.g., bbox columns) from client responses
        prop_cols = [c for c in prop_cols if c not in settings.HIDDEN_FIELDS]

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
            f'geometry := ST_AsMVTGeom(ST_Transform(candidates."{geom_col}", '
            f"'EPSG:4326', 'EPSG:3857', always_xy := true), ST_Extent(bounds.bbox3857))"
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
            #
            # Compute tile bounds in Python (pure math, no DB query needed!)
            # Tile bounds are deterministic from z/x/y coordinates.
            tile_xmin, tile_ymin, tile_xmax, tile_ymax = tile_to_bbox_4326(z, x, y)
            tile_xmin_3857, tile_ymin_3857, tile_xmax_3857, tile_ymax_3857 = (
                tile_to_bbox_3857(z, x, y)
            )

            # Prefer scalar columns (legacy) over struct bbox (GeoParquet 1.1)
            if has_scalar_bbox:
                bbox_filter = f""""$minx" <= {tile_xmax}
                      AND "$maxx" >= {tile_xmin}
                      AND "$miny" <= {tile_ymax}
                      AND "$maxy" >= {tile_ymin}"""
            else:
                bbox_filter = f"""bbox.xmin <= {tile_xmax}
                      AND bbox.xmax >= {tile_xmin}
                      AND bbox.ymin <= {tile_ymax}
                      AND bbox.ymax >= {tile_ymin}"""

            # Use pre-computed literal bounds everywhere - no ST_TileEnvelope in main query
            # This eliminates redundant geometry computations
            # Note: Using LIMIT instead of ORDER BY random() - with Hilbert-ordered data,
            # this gives spatially coherent results and is much faster (no sort needed)
            query = f"""
                WITH bounds AS (
                    SELECT
                        ST_MakeEnvelope({tile_xmin_3857}, {tile_ymin_3857}, {tile_xmax_3857}, {tile_ymax_3857}) AS bbox3857,
                        ST_MakeEnvelope({tile_xmin}, {tile_ymin}, {tile_xmax}, {tile_ymax}) AS bbox4326
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
