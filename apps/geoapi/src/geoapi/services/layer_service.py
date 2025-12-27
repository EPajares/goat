"""Layer metadata service.

This service retrieves layer metadata from the DuckLake catalog
and PostgreSQL metadata tables.
"""

import logging
from typing import Any, Optional
from uuid import UUID

import asyncpg
from cachetools import TTLCache

from geoapi.config import settings
from geoapi.dependencies import LayerInfo

logger = logging.getLogger(__name__)

# Cache for layer metadata (5 minute TTL, max 1000 entries)
_metadata_cache: TTLCache[str, "LayerMetadata"] = TTLCache(maxsize=1000, ttl=300)


class LayerMetadata:
    """Layer metadata container."""

    def __init__(
        self,
        layer_id: str,
        name: str,
        geometry_type: Optional[str],
        bounds: list[float],
        columns: list[dict[str, Any]],
        srid: int = 4326,
        user_id: Optional[str] = None,
        geometry_column: Optional[str] = None,
    ) -> None:
        self.layer_id = layer_id
        self.user_id = user_id
        self.name = name
        self.geometry_type = geometry_type
        self.bounds = bounds
        self.columns = columns
        self.srid = srid
        self.geometry_column = geometry_column

    @property
    def column_names(self) -> list[str]:
        """Get list of column names."""
        return [col["name"] for col in self.columns]

    @property
    def has_geometry(self) -> bool:
        """Check if layer has geometry."""
        return self.geometry_type is not None

    @property
    def table_name(self) -> str:
        """Get the DuckLake table name (user_<user_id>.t_<layer_id>)."""
        if self.user_id:
            return f"user_{self.user_id}.t_{self.layer_id}"
        return f"t_{self.layer_id}"

    @property
    def schema_name(self) -> str:
        """Get the DuckLake schema name."""
        if self.user_id:
            return f"user_{self.user_id}"
        return "public"


class LayerService:
    """Service for layer metadata operations."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        """Initialize connection pool."""
        self._pool = await asyncpg.create_pool(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=2,
            max_size=10,
        )

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()

    async def get_metadata_by_id(self, layer_id: UUID) -> Optional[LayerMetadata]:
        """Get layer metadata by UUID.

        Args:
            layer_id: Layer UUID

        Returns:
            LayerMetadata if found, None otherwise
        """
        if not self._pool:
            raise RuntimeError("LayerService not initialized")

        layer_id_str = str(layer_id).replace("-", "")

        # Check cache first
        if layer_id_str in _metadata_cache:
            return _metadata_cache[layer_id_str]

        async with self._pool.acquire() as conn:
            # Query layer metadata from customer.layer table
            row = await conn.fetchrow(
                """
                SELECT
                    l.id,
                    l.user_id,
                    l.name,
                    l.feature_layer_geometry_type,
                    ST_XMin(e.e) AS xmin,
                    ST_YMin(e.e) AS ymin,
                    ST_XMax(e.e) AS xmax,
                    ST_YMax(e.e) AS ymax
                FROM customer.layer l
                LEFT JOIN LATERAL ST_Envelope(l.extent) e ON TRUE
                WHERE l.id = $1
                """,
                layer_id,
            )

        if not row:
            return None

        user_id_str = str(row["user_id"]).replace("-", "") if row["user_id"] else None

        # Build LayerInfo for getting columns
        from geoapi.dependencies import LayerInfo

        schema_name = f"user_{user_id_str}" if user_id_str else "public"
        table_name = f"t_{layer_id_str}"

        layer_info = LayerInfo(
            layer_id=layer_id_str,
            schema_name=schema_name,
            table_name=table_name,
        )

        # Get column information from DuckLake schema
        columns = await self._get_layer_columns(layer_info)

        # Detect geometry column from columns (None if no geometry)
        geometry_column = None
        for col in columns:
            if col.get("json_type") == "geometry":
                geometry_column = col["name"]
                break

        bounds = [
            row["xmin"] or -180,
            row["ymin"] or -90,
            row["xmax"] or 180,
            row["ymax"] or 90,
        ]

        metadata = LayerMetadata(
            layer_id=layer_id_str,
            name=row["name"],
            geometry_type=row["feature_layer_geometry_type"],
            bounds=bounds,
            columns=columns,
            user_id=user_id_str,
            geometry_column=geometry_column,
        )

        # Cache the metadata
        _metadata_cache[layer_id_str] = metadata
        logger.debug("Cached metadata for layer %s", layer_id_str)

        return metadata

    async def get_layer_metadata(
        self, layer_info: LayerInfo
    ) -> Optional[LayerMetadata]:
        """Get layer metadata from PostgreSQL.

        Args:
            layer_info: Layer information from URL

        Returns:
            LayerMetadata if found, None otherwise
        """
        if not self._pool:
            raise RuntimeError("LayerService not initialized")

        # Check cache first
        cache_key = layer_info.layer_id
        if cache_key in _metadata_cache:
            return _metadata_cache[cache_key]

        # Format layer_id as UUID for query
        layer_id_uuid = (
            f"{layer_info.layer_id[:8]}-{layer_info.layer_id[8:12]}-"
            f"{layer_info.layer_id[12:16]}-{layer_info.layer_id[16:20]}-"
            f"{layer_info.layer_id[20:]}"
        )

        async with self._pool.acquire() as conn:
            # Query layer metadata from customer.layer table
            row = await conn.fetchrow(
                """
                SELECT
                    l.id,
                    l.user_id,
                    l.name,
                    l.feature_layer_geometry_type,
                    ST_XMin(e.e) AS xmin,
                    ST_YMin(e.e) AS ymin,
                    ST_XMax(e.e) AS xmax,
                    ST_YMax(e.e) AS ymax
                FROM customer.layer l
                LEFT JOIN LATERAL ST_Envelope(l.extent) e ON TRUE
                WHERE l.id = $1
                """,
                UUID(layer_id_uuid),
            )

        if not row:
            return None

        # Get column information from DuckLake schema
        columns = await self._get_layer_columns(layer_info)

        # Detect geometry column from columns (None if no geometry)
        geometry_column = None
        for col in columns:
            if col.get("json_type") == "geometry":
                geometry_column = col["name"]
                break

        bounds = [
            row["xmin"] or -180,
            row["ymin"] or -90,
            row["xmax"] or 180,
            row["ymax"] or 90,
        ]

        metadata = LayerMetadata(
            layer_id=layer_info.layer_id,
            name=row["name"],
            geometry_type=row["feature_layer_geometry_type"],
            bounds=bounds,
            columns=columns,
            user_id=str(row["user_id"]).replace("-", "") if row["user_id"] else None,
            geometry_column=geometry_column,
        )

        # Cache the metadata
        _metadata_cache[cache_key] = metadata
        logger.debug("Cached metadata for layer %s", cache_key)

        return metadata

    async def _get_layer_columns(self, layer_info: LayerInfo) -> list[dict[str, Any]]:
        """Get column information for a layer from DuckLake.

        Since DuckLake uses native column names, we query the schema directly.
        """
        from geoapi.ducklake import ducklake_manager

        columns = []
        try:
            with ducklake_manager.connection() as con:
                # Get column info from DuckDB for the 'lake' attached catalog
                result = con.execute(
                    f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_catalog = 'lake'
                    AND table_schema = '{layer_info.schema_name}'
                    AND table_name = '{layer_info.table_name}'
                    ORDER BY ordinal_position
                    """
                ).fetchall()

                for row in result:
                    col_name, col_type = row
                    # Map DuckDB types to JSON schema types
                    json_type = self._duckdb_to_json_type(col_type)
                    columns.append(
                        {
                            "name": col_name,
                            "type": col_type,
                            "json_type": json_type,
                        }
                    )
        except Exception:
            # If DuckLake query fails, return empty columns
            pass

        return columns

    @staticmethod
    def _duckdb_to_json_type(duckdb_type: str) -> str:
        """Map DuckDB data type to JSON schema type."""
        type_lower = duckdb_type.lower()

        if any(t in type_lower for t in ["int", "bigint", "smallint", "tinyint"]):
            return "integer"
        elif any(
            t in type_lower for t in ["float", "double", "decimal", "numeric", "real"]
        ):
            return "number"
        elif "bool" in type_lower:
            return "boolean"
        elif any(t in type_lower for t in ["geometry", "geography"]):
            return "geometry"
        elif any(t in type_lower for t in ["timestamp", "date", "time"]):
            return "string"  # ISO format
        else:
            return "string"

    async def list_layers(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[LayerMetadata], int]:
        """List available layers.

        Args:
            user_id: Optional user ID filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (layers, total_count)
        """
        if not self._pool:
            raise RuntimeError("LayerService not initialized")

        async with self._pool.acquire() as conn:
            # Build condition
            condition = ""
            params = []
            param_idx = 1

            if user_id:
                # Format user_id as UUID
                user_id_uuid = (
                    f"{user_id[:8]}-{user_id[8:12]}-"
                    f"{user_id[12:16]}-{user_id[16:20]}-"
                    f"{user_id[20:]}"
                )
                condition = f"WHERE l.user_id = ${param_idx}"
                params.append(UUID(user_id_uuid))
                param_idx += 1

            # Get total count
            count_sql = f"""
                SELECT COUNT(*)
                FROM customer.layer l
                {condition}
            """
            total = await conn.fetchval(count_sql, *params)

            # Get layers
            sql = f"""
                SELECT
                    l.id,
                    l.user_id,
                    l.name,
                    l.feature_layer_geometry_type,
                    ST_XMin(e.e) AS xmin,
                    ST_YMin(e.e) AS ymin,
                    ST_XMax(e.e) AS xmax,
                    ST_YMax(e.e) AS ymax
                FROM customer.layer l
                LEFT JOIN LATERAL ST_Envelope(l.extent) e ON TRUE
                {condition}
                ORDER BY l.created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([limit, offset])

            rows = await conn.fetch(sql, *params)

            layers = []
            for row in rows:
                layer_id = str(row["id"]).replace("-", "")
                user_id_str = str(row["user_id"]).replace("-", "")

                bounds = [
                    row["xmin"] or -180,
                    row["ymin"] or -90,
                    row["xmax"] or 180,
                    row["ymax"] or 90,
                ]

                layers.append(
                    LayerMetadata(
                        layer_id=layer_id,
                        user_id=user_id_str,
                        name=row["name"],
                        geometry_type=row["feature_layer_geometry_type"],
                        bounds=bounds,
                        columns=[],  # Skip columns for list view
                    )
                )

            return layers, total


# Singleton instance
layer_service = LayerService()
