"""DuckLake manager initialization for Processes API.

Provides DuckLake connection management using goatlib's BaseDuckLakeManager.
"""

import logging
import os
import threading
from contextlib import contextmanager
from typing import Any, Generator
from uuid import UUID

import duckdb
from goatlib.storage import BaseDuckLakeManager

from lib.config import get_settings

logger = logging.getLogger(__name__)


class ProcessesDuckLakeManager(BaseDuckLakeManager):
    """DuckLake manager for Processes API.

    Extends BaseDuckLakeManager with Processes-specific initialization
    and layer operations.
    """

    def init_from_settings(self) -> None:
        """Initialize DuckLake from Processes settings."""
        settings = get_settings()

        # Determine storage path
        s3_bucket = settings.DUCKLAKE_S3_BUCKET
        if s3_bucket:
            storage_path = s3_bucket
        else:
            storage_path = settings.DUCKLAKE_DATA_DIR
            os.makedirs(storage_path, exist_ok=True)

        self.init_from_params(
            postgres_uri=settings.POSTGRES_DATABASE_URI,
            storage_path=storage_path,
            catalog_schema=settings.DUCKLAKE_CATALOG_SCHEMA,
            s3_endpoint=settings.DUCKLAKE_S3_ENDPOINT,
            s3_access_key=settings.DUCKLAKE_S3_ACCESS_KEY,
            s3_secret_key=settings.DUCKLAKE_S3_SECRET_KEY,
        )
        logger.info(
            "DuckLake initialized: catalog=%s storage=%s",
            settings.DUCKLAKE_CATALOG_SCHEMA,
            storage_path,
        )

    # =========================================================================
    # Helper methods
    # =========================================================================

    @staticmethod
    def get_user_schema_name(user_id: UUID) -> str:
        """Get user schema name from user_id."""
        return f"user_{str(user_id).replace('-', '')}"

    @staticmethod
    def get_layer_table_name(user_id: UUID, layer_id: UUID) -> str:
        """Get fully qualified layer table name."""
        schema = ProcessesDuckLakeManager.get_user_schema_name(user_id)
        table = f"t_{str(layer_id).replace('-', '')}"
        return f"lake.{schema}.{table}"

    # =========================================================================
    # Layer operations
    # =========================================================================

    def create_layer_from_parquet(
        self,
        user_id: UUID,
        layer_id: UUID,
        parquet_path: str,
        target_crs: str = "EPSG:4326",
    ) -> dict[str, Any]:
        """Create a DuckLake table from a GeoParquet file.

        Args:
            user_id: User UUID (determines schema)
            layer_id: Layer UUID (determines table name)
            parquet_path: Path to parquet file (local or S3)
            target_crs: Target CRS (default EPSG:4326)

        Returns:
            Dict with table info: table_name, columns, feature_count, extent, geometry_type
        """
        table_name = self.get_layer_table_name(user_id, layer_id)
        schema_name = self.get_user_schema_name(user_id)

        with self.connection() as con:
            # Ensure user schema exists
            con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{schema_name}")

            # Read parquet and create table
            con.execute(f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)

            logger.info("Created DuckLake layer table: %s", table_name)

            # Get table info
            info = self._get_table_info(con, table_name)
            info["table_name"] = table_name

            return info

    def _get_table_info(
        self, con: duckdb.DuckDBPyConnection, table_name: str
    ) -> dict[str, Any]:
        """Get table metadata (columns, count, geometry type, extent)."""
        # Get column info
        columns_result = con.execute(f"DESCRIBE {table_name}").fetchall()
        columns = [{"name": row[0], "type": row[1]} for row in columns_result]

        # Get feature count
        count_result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        feature_count = count_result[0] if count_result else 0

        # Find geometry column
        geometry_column = next(
            (col["name"] for col in columns if "GEOMETRY" in col["type"].upper()), None
        )

        # Get geometry type and extent if geometry exists
        geometry_type = None
        extent = None
        if geometry_column:
            # Get geometry type
            geom_type_result = con.execute(f"""
                SELECT DISTINCT ST_GeometryType({geometry_column})
                FROM {table_name}
                WHERE {geometry_column} IS NOT NULL
                LIMIT 1
            """).fetchone()
            geometry_type = geom_type_result[0] if geom_type_result else None

            # Get extent
            extent_result = con.execute(f"""
                SELECT
                    ST_XMin(ST_Extent({geometry_column})) as xmin,
                    ST_YMin(ST_Extent({geometry_column})) as ymin,
                    ST_XMax(ST_Extent({geometry_column})) as xmax,
                    ST_YMax(ST_Extent({geometry_column})) as ymax
                FROM {table_name}
                WHERE {geometry_column} IS NOT NULL
            """).fetchone()
            if extent_result and all(v is not None for v in extent_result):
                extent = {
                    "xmin": extent_result[0],
                    "ymin": extent_result[1],
                    "xmax": extent_result[2],
                    "ymax": extent_result[3],
                }

        return {
            "columns": columns,
            "feature_count": feature_count,
            "geometry_column": geometry_column,
            "geometry_type": geometry_type,
            "extent": extent,
        }

    def delete_layer_table(self, user_id: UUID, layer_id: UUID) -> bool:
        """Delete a layer table from DuckLake.

        Args:
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            True if deleted, False if table didn't exist
        """
        table_name = self.get_layer_table_name(user_id, layer_id)

        with self.connection() as con:
            # Check if table exists
            result = con.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_catalog = 'lake'
                    AND table_schema = '{self.get_user_schema_name(user_id)}'
                    AND table_name = 't_{str(layer_id).replace('-', '')}'
            """).fetchone()

            if not result or result[0] == 0:
                logger.info("Layer table does not exist: %s", table_name)
                return False

            # Drop table
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.info("Deleted layer table: %s", table_name)
            return True

    def export_to_format_with_timeout(
        self,
        user_id: UUID,
        layer_id: UUID,
        output_path: str,
        output_format: str = "GPKG",
        target_crs: str | None = None,
        where: str | None = None,
        timeout_seconds: int = 300,
    ) -> None:
        """Export a layer table to a file format.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            output_path: Output file path
            output_format: Output format (GPKG, GEOJSON, CSV, etc.)
            target_crs: Optional target CRS for reprojection
            where: Optional WHERE clause for filtering
            timeout_seconds: Timeout in seconds (not enforced yet)
        """
        table_name = self.get_layer_table_name(user_id, layer_id)

        # Build query
        where_clause = f"WHERE {where}" if where else ""

        with self.connection() as con:
            # Export using COPY TO
            con.execute(f"""
                COPY (
                    SELECT * FROM {table_name}
                    {where_clause}
                ) TO '{output_path}' WITH (FORMAT {output_format})
            """)
            logger.info("Exported %s to %s", table_name, output_path)

    def create_user_schema(self, user_id: UUID) -> None:
        """Create user schema in DuckLake.

        Args:
            user_id: User UUID
        """
        schema_name = self.get_user_schema_name(user_id)
        with self.connection() as con:
            con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{schema_name}")
            logger.info("Created user schema: %s", schema_name)

    def delete_user_schema(self, user_id: UUID) -> None:
        """Delete user schema from DuckLake.

        Args:
            user_id: User UUID
        """
        schema_name = self.get_user_schema_name(user_id)
        with self.connection() as con:
            con.execute(f"DROP SCHEMA IF EXISTS lake.{schema_name} CASCADE")
            logger.info("Deleted user schema: %s", schema_name)


# Singleton instance
_ducklake_manager: ProcessesDuckLakeManager | None = None
_init_lock = threading.Lock()


def get_ducklake_manager() -> ProcessesDuckLakeManager:
    """Get or create DuckLake manager singleton.

    Thread-safe initialization.
    """
    global _ducklake_manager
    if _ducklake_manager is None:
        with _init_lock:
            if _ducklake_manager is None:
                _ducklake_manager = ProcessesDuckLakeManager()
                _ducklake_manager.init_from_settings()
    return _ducklake_manager


@contextmanager
def ducklake_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager for DuckLake connection.

    Example:
        with ducklake_connection() as con:
            con.execute("SELECT * FROM lake.user_xxx.t_yyy LIMIT 10")
    """
    manager = get_ducklake_manager()
    with manager.connection() as con:
        yield con
