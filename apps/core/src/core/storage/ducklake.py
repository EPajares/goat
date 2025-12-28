"""DuckLake storage backend using GeoParquet files.

DuckLake provides:
- ACID transactions via PostgreSQL catalog
- GeoParquet files on object storage (S3/MinIO/local)
- DuckDB for fast analytical queries
- Native spatial support via DuckDB Spatial extension

Table naming convention:
- Schema per user: lake.user_{user_id}
- Table per layer: t_{layer_id}
- Full path: lake.user_{user_id}.t_{layer_id}

Key differences from PostgreSQL user_data approach:
- PostgreSQL: One table per geometry type per user, filtered by layer_id
- DuckLake: One table per layer with native column names (no attribute_mapping)

Usage:
    # Initialize at app startup (in main.py lifespan)
    ducklake_manager.init(settings)

    # Use in endpoints/services
    with ducklake_manager.connection() as con:
        con.execute("SELECT * FROM lake.user_xxx.t_yyy")

    # Close at app shutdown
    ducklake_manager.close()
"""

from __future__ import annotations

import logging
import os
import shutil
import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Generator, TypeVar
from uuid import UUID

import duckdb
from goatlib.storage import BaseDuckLakeManager, is_connection_error

if TYPE_CHECKING:
    from core.core.config import Settings

logger = logging.getLogger(__name__)

# Default timeout for DuckDB operations (30 seconds)
DEFAULT_QUERY_TIMEOUT = 30

T = TypeVar("T")


class DuckLakeManager(BaseDuckLakeManager):
    """DuckDB connection manager with DuckLake extension and write operations.

    Extends BaseDuckLakeManager with write operations for:
    - Creating/deleting user schemas
    - Creating/deleting/replacing layer tables
    - Exporting layers to various formats

    Example:
        # At startup
        ducklake_manager.init(settings)

        # In request handlers
        with ducklake_manager.connection() as con:
            con.execute("SELECT * FROM lake.user_xxx.t_yyy LIMIT 10")

        # With timeout (for long operations):
        with ducklake_manager.connection_with_timeout(30) as con:
            con.execute("SELECT * FROM large_table")

        # At shutdown
        ducklake_manager.close()
    """

    def init(self: "DuckLakeManager", settings: "Settings") -> None:
        """Initialize DuckLake connection at application startup.

        Args:
            settings: Application settings containing DuckLake configuration
        """

        # Core app uses different field names, so create a wrapper
        # that maps to what BaseDuckLakeManager expects
        class DuckLakeSettings:
            def __init__(self: "DuckLakeSettings", base_settings: "Settings") -> None:
                # BaseDuckLakeManager.init() expects these fields:
                self.POSTGRES_DATABASE_URI = base_settings.POSTGRES_DATABASE_URI
                self.DUCKLAKE_CATALOG_SCHEMA = base_settings.DUCKLAKE_CATALOG_SCHEMA
                # Compute DUCKLAKE_DATA_DIR from DATA_DIR
                self.DUCKLAKE_DATA_DIR = os.path.join(
                    base_settings.DATA_DIR, "ducklake"
                )

        ducklake_settings = DuckLakeSettings(settings)
        super().init(ducklake_settings)

    # =========================================================================
    # Timeout support for long-running operations
    # =========================================================================

    @contextmanager
    def connection_with_timeout(
        self: "DuckLakeManager",
        timeout_seconds: int = DEFAULT_QUERY_TIMEOUT,
    ) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get DuckDB connection with automatic timeout.

        Uses DuckDB's interrupt() to cancel queries that exceed timeout.
        This is useful for long-running operations like exports and imports.

        Args:
            timeout_seconds: Timeout in seconds (default 30)

        Yields:
            DuckDB connection

        Raises:
            TimeoutError: If operation exceeds timeout

        Example:
            with ducklake_manager.connection_with_timeout(60) as con:
                con.execute("SELECT * FROM large_table")
        """
        interrupted = threading.Event()
        timer = None

        def interrupt_query() -> None:
            """Called by timer to interrupt the query."""
            logger.warning(
                "Query timeout reached (%ds), interrupting...",
                timeout_seconds,
            )
            interrupted.set()
            if self._connection:
                try:
                    self._connection.interrupt()
                    logger.info("DuckDB interrupt() called successfully")
                except Exception as e:
                    logger.error("Failed to interrupt query: %s", e)

        try:
            # Schedule interrupt
            timer = threading.Timer(timeout_seconds, interrupt_query)
            timer.start()

            # Yield connection
            with self.connection() as con:
                yield con

            # Cancel timer if we finished in time
            timer.cancel()

        except Exception as e:
            # Cancel timer if still running
            if timer:
                timer.cancel()

            # Check if this was due to our interrupt
            if interrupted.is_set() or "interrupt" in str(e).lower():
                raise TimeoutError(
                    f"Operation timed out after {timeout_seconds} seconds. "
                    "The dataset may be too large."
                ) from e
            raise

    def run_with_timeout(
        self: "DuckLakeManager",
        func: Callable[..., T],
        timeout_seconds: int = DEFAULT_QUERY_TIMEOUT,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Run a function with timeout support.

        Wraps any function that uses the DuckDB connection with a timeout.
        If the function exceeds the timeout, DuckDB's interrupt() is called.

        Args:
            func: Function to run (should use self.connection() internally)
            timeout_seconds: Timeout in seconds (default 30)
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            TimeoutError: If operation exceeds timeout

        Example:
            result = ducklake_manager.run_with_timeout(
                self.create_layer_from_parquet,
                timeout_seconds=60,
                user_id=user_id,
                layer_id=layer_id,
                parquet_path=path,
            )
        """
        interrupted = threading.Event()
        timer = None

        def interrupt_query() -> None:
            """Called by timer to interrupt the query."""
            logger.warning(
                "Operation timeout reached (%ds), interrupting...",
                timeout_seconds,
            )
            interrupted.set()
            if self._connection:
                try:
                    self._connection.interrupt()
                    logger.info("DuckDB interrupt() called successfully")
                except Exception as e:
                    logger.error("Failed to interrupt query: %s", e)

        try:
            # Schedule interrupt
            timer = threading.Timer(timeout_seconds, interrupt_query)
            timer.start()

            # Run function
            result = func(*args, **kwargs)

            # Cancel timer if we finished in time
            timer.cancel()

            return result

        except Exception as e:
            # Cancel timer if still running
            if timer:
                timer.cancel()

            # Check if this was due to our interrupt
            if interrupted.is_set() or "interrupt" in str(e).lower():
                raise TimeoutError(
                    f"Operation timed out after {timeout_seconds} seconds. "
                    "The dataset may be too large."
                ) from e
            raise

    def run_with_retry(
        self: "DuckLakeManager",
        func: Callable[..., T],
        max_retries: int = 2,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Run a function with automatic retry on connection errors.

        Retries on SSL EOF, connection lost, and similar transient errors.
        Reconnects DuckDB before each retry.

        Args:
            func: Function to run
            max_retries: Maximum number of retries (default 2)
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func
        """
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if is_connection_error(e) and attempt < max_retries:
                    logger.warning(
                        "DuckDB operation failed (attempt %d/%d), reconnecting: %s",
                        attempt + 1,
                        max_retries + 1,
                        e,
                    )
                    try:
                        self.reconnect()
                    except Exception as reconnect_error:
                        logger.error("Failed to reconnect: %s", reconnect_error)
                    last_error = e
                    continue
                raise
        raise last_error

    # =========================================================================
    # Static helpers
    # =========================================================================

    @staticmethod
    def get_user_schema_name(user_id: UUID) -> str:
        """Get DuckLake schema name for a user."""
        return f"user_{str(user_id).replace('-', '')}"

    @staticmethod
    def get_layer_table_name(user_id: UUID, layer_id: UUID) -> str:
        """Get fully qualified table name for a layer in DuckLake.

        Returns: lake.user_{user_id}.t_{layer_id}
        """
        schema = DuckLakeManager.get_user_schema_name(user_id)
        table = f"t_{str(layer_id).replace('-', '')}"
        return f"lake.{schema}.{table}"

    # =========================================================================
    # Schema operations (for data-schema endpoints)
    # =========================================================================

    def create_user_schema(self: "DuckLakeManager", user_id: UUID) -> None:
        """Create schema for a user in DuckLake.

        Called when setting up a new user's data storage.
        This is the DuckLake equivalent of creating the user_data tables.
        """
        schema_name = self.get_user_schema_name(user_id)
        with self.connection() as con:
            con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{schema_name}")
            logger.info("Created DuckLake user schema: lake.%s", schema_name)

    def delete_user_schema(self: "DuckLakeManager", user_id: UUID) -> None:
        """Delete schema and all tables for a user.

        Called when cleaning up a user's data.
        WARNING: This deletes ALL data for the user!
        """
        schema_name = self.get_user_schema_name(user_id)
        with self.connection() as con:
            # CASCADE drops all tables in the schema
            con.execute(f"DROP SCHEMA IF EXISTS lake.{schema_name} CASCADE")
            logger.info("Deleted DuckLake user schema: lake.%s", schema_name)

        # Manually delete all parquet files for this schema
        schema_data_path = os.path.join(self._storage_path, schema_name)
        if os.path.isdir(schema_data_path):
            shutil.rmtree(schema_data_path)
            logger.info("Deleted schema parquet files: %s", schema_data_path)
        schema_name = self.get_user_schema_name(user_id)
        with self.connection() as con:
            result = con.execute(f"""
                SELECT COUNT(*) FROM information_schema.schemata
                WHERE catalog_name = 'lake' AND schema_name = '{schema_name}'
            """).fetchone()
            return result[0] > 0 if result else False

    # =========================================================================
    # Layer operations (for layer endpoints)
    # =========================================================================

    def create_layer_from_parquet(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        parquet_path: str,
        target_crs: str = "EPSG:4326",
    ) -> dict[str, Any]:
        """Create a DuckLake table from a GeoParquet file.

        This is the main ingestion method. Takes output from goatlib IOConverter
        and creates a DuckLake table. Includes automatic retry on connection errors.

        Args:
            user_id: User UUID (determines schema)
            layer_id: Layer UUID (determines table name)
            parquet_path: Path to parquet file (local or S3)
            target_crs: Target CRS (default EPSG:4326)

        Returns:
            Dict with table info: table_name, columns, feature_count, extent, geometry_type
        """
        return self.run_with_retry(
            self._create_layer_from_parquet_impl,
            2,  # max_retries
            user_id,
            layer_id,
            parquet_path,
            target_crs,
        )

    def _create_layer_from_parquet_impl(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        parquet_path: str,
        target_crs: str = "EPSG:4326",
    ) -> dict[str, Any]:
        """Internal implementation of create_layer_from_parquet."""
        table_name = self.get_layer_table_name(user_id, layer_id)
        schema_name = self.get_user_schema_name(user_id)

        with self.connection() as con:
            # Ensure user schema exists
            con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{schema_name}")

            # Read parquet and create table
            # DuckDB spatial extension handles GeoParquet natively
            con.execute(f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)

            logger.info(
                "Created DuckLake layer table: %s from %s", table_name, parquet_path
            )

            # Get table info
            info = self._get_table_info(con, table_name)
            info["table_name"] = table_name

            return info

    def create_layer_from_parquet_with_timeout(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        parquet_path: str,
        target_crs: str = "EPSG:4326",
        timeout_seconds: int = DEFAULT_QUERY_TIMEOUT,
    ) -> dict[str, Any]:
        """Create a DuckLake table from a GeoParquet file with timeout.

        Same as create_layer_from_parquet but with timeout support.

        Args:
            user_id: User UUID (determines schema)
            layer_id: Layer UUID (determines table name)
            parquet_path: Path to parquet file (local or S3)
            target_crs: Target CRS (default EPSG:4326)
            timeout_seconds: Timeout in seconds (default from DEFAULT_QUERY_TIMEOUT)

        Returns:
            Dict with table info

        Raises:
            TimeoutError: If import exceeds timeout
        """
        logger.info("Starting layer import with %ds timeout", timeout_seconds)
        return self.run_with_timeout(
            self.create_layer_from_parquet,
            timeout_seconds,
            user_id,
            layer_id,
            parquet_path,
            target_crs,
        )

    def _get_table_info(
        self: "DuckLakeManager", con: "duckdb.DuckDBPyConnection", table_name: str
    ) -> dict[str, Any]:
        """Get metadata about a table."""
        # Get row count
        count_result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        feature_count = count_result[0] if count_result else 0

        # Get columns
        columns_result = con.execute(f"DESCRIBE {table_name}").fetchall()
        columns = [{"name": row[0], "type": row[1]} for row in columns_result]

        # Check for geometry column by type first (GEOMETRY, POINT_2D, etc.)
        # then by name as fallback
        geom_col = None
        geometry_types = (
            "GEOMETRY",
            "POINT_2D",
            "LINESTRING_2D",
            "POLYGON_2D",
            "WKB_BLOB",
        )

        # First, look for actual geometry type columns
        for col in columns:
            col_type = col["type"].upper()
            if any(gt in col_type for gt in geometry_types):
                geom_col = col["name"]
                break

        # Fallback: check by common geometry column names
        if not geom_col:
            for col in columns:
                if col["name"].lower() in ("geometry", "geom"):
                    # Only use if it's not VARCHAR (string/WKT) - that would be a table layer
                    if "VARCHAR" not in col["type"].upper():
                        geom_col = col["name"]
                        break

        info: dict[str, Any] = {
            "feature_count": feature_count,
            "columns": columns,
            "geometry_column": geom_col,
            "geometry_type": None,
            "extent": None,
        }

        # Get geometry info if spatial
        if geom_col:
            try:
                # Get geometry type from first non-null geometry
                geom_type_result = con.execute(f"""
                    SELECT ST_GeometryType({geom_col})
                    FROM {table_name}
                    WHERE {geom_col} IS NOT NULL
                    LIMIT 1
                """).fetchone()
                if geom_type_result:
                    info["geometry_type"] = geom_type_result[0]

                # Get extent
                extent_result = con.execute(f"""
                    SELECT
                        ST_XMin(ST_Extent({geom_col})) as xmin,
                        ST_YMin(ST_Extent({geom_col})) as ymin,
                        ST_XMax(ST_Extent({geom_col})) as xmax,
                        ST_YMax(ST_Extent({geom_col})) as ymax
                    FROM {table_name}
                    WHERE {geom_col} IS NOT NULL
                """).fetchone()
                if extent_result and extent_result[0] is not None:
                    xmin, ymin, xmax, ymax = extent_result
                    info["extent"] = {
                        "xmin": xmin,
                        "ymin": ymin,
                        "xmax": xmax,
                        "ymax": ymax,
                    }
            except Exception as e:
                logger.warning("Could not get geometry info: %s", e)

        return info

    def delete_layer_table(
        self: "DuckLakeManager", user_id: UUID, layer_id: UUID
    ) -> bool:
        """Delete a layer table from DuckLake.

        Called when a layer is deleted. Drops the table from DuckLake catalog
        and manually removes the parquet files from disk.

        Note: This uses manual file deletion instead of DuckLake's cleanup functions
        because ducklake_expire_snapshots affects all tables in the catalog.
        A separate periodic maintenance job should handle general cleanup.

        Returns:
            True if table was deleted, False if it didn't exist
        """
        table_name = self.get_layer_table_name(user_id, layer_id)
        schema_name = self.get_user_schema_name(user_id)
        table_only = f"t_{str(layer_id).replace('-', '')}"

        with self.connection() as con:
            # Check if exists first
            if not self._layer_table_exists(con, user_id, layer_id):
                logger.warning("Layer table does not exist: %s", table_name)
                return False

            # Drop table from DuckLake catalog
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.info("Deleted DuckLake layer table: %s", table_name)

        # Manually delete parquet files from disk
        # This is safer than expire_snapshots which affects all tables
        layer_data_path = os.path.join(self._storage_path, schema_name, table_only)
        if os.path.isdir(layer_data_path):
            shutil.rmtree(layer_data_path)
            logger.info("Deleted layer parquet files: %s", layer_data_path)

            # Try to remove parent user schema folder if empty
            user_schema_path = os.path.join(self._storage_path, schema_name)
            try:
                os.rmdir(user_schema_path)  # Only removes if empty
                logger.info("Deleted empty user schema folder: %s", user_schema_path)
            except OSError:
                pass  # Not empty, that's fine

        return True

    def replace_layer_from_parquet(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        parquet_path: str,
        target_crs: str = "EPSG:4326",
    ) -> dict[str, Any]:
        """Atomically replace a DuckLake table from a new GeoParquet file.

        Uses a safe swap approach with automatic retry on connection errors:
        1. Create new table with temp name
        2. If successful: DROP old table, RENAME new table
        3. If failed: DROP temp table, original intact

        Args:
            user_id: User UUID (determines schema)
            layer_id: Layer UUID (determines table name)
            parquet_path: Path to new parquet file
            target_crs: Target CRS (default EPSG:4326)

        Returns:
            Dict with table info: table_name, columns, feature_count, extent, geometry_type
        """
        return self.run_with_retry(
            self._replace_layer_from_parquet_impl,
            2,  # max_retries
            user_id,
            layer_id,
            parquet_path,
            target_crs,
        )

    def _replace_layer_from_parquet_impl(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        parquet_path: str,
        target_crs: str = "EPSG:4326",
    ) -> dict[str, Any]:
        """Internal implementation of replace_layer_from_parquet."""
        schema_name = self.get_user_schema_name(user_id)
        table_only = f"t_{str(layer_id).replace('-', '')}"
        table_name = f"lake.{schema_name}.{table_only}"
        temp_table_only = f"{table_only}_new"
        temp_table_name = f"lake.{schema_name}.{temp_table_only}"

        with self.connection() as con:
            # Ensure user schema exists
            con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{schema_name}")

            # Clean up any leftover temp table from a previous failed run
            con.execute(f"DROP TABLE IF EXISTS {temp_table_name}")

            # Step 1: Create new table with temp name
            try:
                con.execute(f"""
                    CREATE TABLE {temp_table_name} AS
                    SELECT * FROM read_parquet('{parquet_path}')
                """)
                logger.info(
                    "Created temp DuckLake table: %s from %s",
                    temp_table_name,
                    parquet_path,
                )
            except Exception as e:
                logger.error("Failed to create temp table: %s", e)
                # Try to clean up temp table if it was partially created
                try:
                    con.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
                except Exception:
                    pass
                raise

            # Step 2: Drop old table and rename new one
            try:
                # Check if old table exists
                old_exists = self._layer_table_exists(con, user_id, layer_id)
                if old_exists:
                    con.execute(f"DROP TABLE {table_name}")
                    logger.info("Dropped old table: %s", table_name)

                # Rename temp table to final name
                con.execute(f"ALTER TABLE {temp_table_name} RENAME TO {table_only}")
                logger.info("Renamed temp table %s -> %s", temp_table_name, table_only)
            except Exception as e:
                logger.error("Failed to swap tables: %s", e)
                # Try to clean up temp table
                try:
                    con.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
                except Exception:
                    pass
                raise

            # Step 3: Manually clean up old table's files
            # Delete old data folder if it exists (from dropped table)
            old_data_path = os.path.join(self._storage_path, schema_name, table_only)
            new_data_path = os.path.join(
                self._storage_path, schema_name, temp_table_only
            )

            if os.path.isdir(old_data_path):
                shutil.rmtree(old_data_path)
                logger.info("Deleted old table files: %s", old_data_path)

            # Step 4: Rename physical folder on disk for new table
            # DuckLake's ALTER RENAME only updates catalog, not physical files
            if os.path.isdir(new_data_path):
                os.rename(new_data_path, old_data_path)
                logger.info(
                    "Renamed data folder: %s -> %s", new_data_path, old_data_path
                )

            # Get table info for the new table
            info = self._get_table_info(con, table_name)
            info["table_name"] = table_name

            return info

    def replace_layer_from_parquet_with_timeout(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        parquet_path: str,
        target_crs: str = "EPSG:4326",
        timeout_seconds: int = DEFAULT_QUERY_TIMEOUT,
    ) -> dict[str, Any]:
        """Atomically replace a DuckLake table with timeout support.

        Same as replace_layer_from_parquet but with timeout support.

        Args:
            user_id: User UUID (determines schema)
            layer_id: Layer UUID (determines table name)
            parquet_path: Path to new parquet file
            target_crs: Target CRS (default EPSG:4326)
            timeout_seconds: Timeout in seconds (default from DEFAULT_QUERY_TIMEOUT)

        Returns:
            Dict with table info

        Raises:
            TimeoutError: If replace exceeds timeout
        """
        logger.info("Starting layer replace with %ds timeout", timeout_seconds)
        return self.run_with_timeout(
            self.replace_layer_from_parquet,
            timeout_seconds,
            user_id,
            layer_id,
            parquet_path,
            target_crs,
        )

    def _layer_table_exists(
        self: "DuckLakeManager",
        con: "duckdb.DuckDBPyConnection",
        user_id: UUID,
        layer_id: UUID,
    ) -> bool:
        """Internal check if a layer table exists using existing connection.

        Args:
            con: Existing DuckDB connection
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            True if table exists, False otherwise
        """
        schema_name = self.get_user_schema_name(user_id)
        table_only = f"t_{str(layer_id).replace('-', '')}"

        result = con.execute(f"""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_catalog = 'lake'
            AND table_schema = '{schema_name}'
            AND table_name = '{table_only}'
        """).fetchone()
        return result[0] > 0 if result else False

    def layer_table_exists(
        self: "DuckLakeManager", user_id: UUID, layer_id: UUID
    ) -> bool:
        """Check if a layer table exists in DuckLake."""
        with self.connection() as con:
            return self._layer_table_exists(con, user_id, layer_id)

    def get_layer_info(
        self: "DuckLakeManager", user_id: UUID, layer_id: UUID
    ) -> dict[str, Any]:
        """Get metadata about a layer table in DuckLake."""
        table_name = self.get_layer_table_name(user_id, layer_id)

        with self.connection() as con:
            info = self._get_table_info(con, table_name)
            info["table_name"] = table_name
            return info

    def query_layer(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        columns: list[str] | None = None,
        where: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query a layer table and return results as list of dicts.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            columns: Columns to select (None = all)
            where: WHERE clause (without WHERE keyword)
            limit: Max rows to return
            offset: Rows to skip

        Returns:
            List of row dictionaries
        """
        table_name = self.get_layer_table_name(user_id, layer_id)

        # Build query
        col_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_str} FROM {table_name}"

        if where:
            query += f" WHERE {where}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"

        with self.connection() as con:
            result = con.execute(query).fetchall()
            col_names = [desc[0] for desc in con.description]
            return [dict(zip(col_names, row)) for row in result]

    def get_feature_count(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        where: str | None = None,
    ) -> int:
        """Get feature count for a layer, optionally filtered."""
        table_name = self.get_layer_table_name(user_id, layer_id)

        query = f"SELECT COUNT(*) FROM {table_name}"
        if where:
            query += f" WHERE {where}"

        with self.connection() as con:
            result = con.execute(query).fetchone()
            return result[0] if result else 0

    def export_to_format(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        output_path: str,
        output_format: str = "GPKG",
        target_crs: str | None = None,
        where: str | None = None,
    ) -> str:
        """Export a layer to any supported format.

        Supported formats: PARQUET, GPKG, GeoJSON, Shapefile, CSV, etc.
        Uses DuckDB COPY for parquet, GDAL driver for vector formats.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            output_path: Output file path
            output_format: Output format (PARQUET, GPKG, GEOJSON, CSV, etc.)
            target_crs: Optional target CRS for reprojection
            where: Optional WHERE clause for filtering

        Returns:
            Path to the exported file
        """
        return self._export_to_format_impl(
            user_id, layer_id, output_path, output_format, target_crs, where, retry=True
        )

    def export_to_format_with_timeout(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        output_path: str,
        output_format: str = "GPKG",
        target_crs: str | None = None,
        where: str | None = None,
        timeout_seconds: int = DEFAULT_QUERY_TIMEOUT,
    ) -> str:
        """Export a layer with timeout support.

        Uses DuckDB's interrupt() method to cancel queries that exceed timeout.

        Args:
            user_id: User UUID
            layer_id: Layer UUID
            output_path: Output file path
            output_format: Output format (PARQUET, GPKG, GEOJSON, CSV, etc.)
            target_crs: Optional target CRS for reprojection
            where: Optional WHERE clause for filtering
            timeout_seconds: Timeout in seconds (default from DEFAULT_QUERY_TIMEOUT)

        Returns:
            Path to the exported file

        Raises:
            TimeoutError: If export exceeds timeout
        """
        logger.info("Starting export with %ds timeout", timeout_seconds)
        return self.run_with_timeout(
            self._export_to_format_impl,
            timeout_seconds,
            user_id,
            layer_id,
            output_path,
            output_format,
            target_crs,
            where,
            True,  # retry
        )

    def _export_to_format_impl(
        self: "DuckLakeManager",
        user_id: UUID,
        layer_id: UUID,
        output_path: str,
        output_format: str,
        target_crs: str | None,
        where: str | None,
        retry: bool = True,
    ) -> str:
        """Internal export implementation with retry support."""
        import os

        table_name = self.get_layer_table_name(user_id, layer_id)
        format_upper = output_format.upper()

        # Check if table exists
        if not self.layer_table_exists(user_id, layer_id):
            raise ValueError(
                f"Layer table does not exist in DuckLake: {table_name}. "
                f"The layer may not have been imported yet or import failed."
            )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with self.connection() as con:
                # Get layer info
                info = self._get_table_info(con, table_name)
                geom_col = info.get("geometry_column")

                # Detect actual CRS by checking coordinate ranges
                # EPSG:4326: lon in [-180, 180], lat in [-90, 90]
                # EPSG:3857: x in ~[-20M, 20M], y in ~[-20M, 20M]
                source_crs = "EPSG:4326"  # Default assumption

                if geom_col:
                    extent = info.get("extent")
                    if extent:
                        xmin, xmax = extent.get("xmin", 0), extent.get("xmax", 0)
                        ymin, ymax = extent.get("ymin", 0), extent.get("ymax", 0)

                        # If coordinates are outside WGS84 range, assume EPSG:3857
                        if (
                            abs(xmin) > 180
                            or abs(xmax) > 180
                            or abs(ymin) > 90
                            or abs(ymax) > 90
                        ):
                            source_crs = "EPSG:3857"
                            logger.info(
                                "Detected non-WGS84 coordinates (extent: %s), "
                                "assuming source CRS is EPSG:3857",
                                extent,
                            )

                # Build base query with optional CRS transform
                if target_crs and geom_col:
                    # Skip transform if already in target CRS
                    if source_crs == target_crs:
                        logger.info(
                            "Data already in target CRS %s, skipping transform",
                            target_crs,
                        )
                        col_str = "*"
                    else:
                        select_cols = []
                        for col in info["columns"]:
                            if col["name"] == geom_col:
                                # DuckDB ST_Transform requires both source and target CRS
                                # Use always_xy=true for consistent lon/lat axis order
                                select_cols.append(
                                    f"ST_Transform({geom_col}, '{source_crs}', '{target_crs}', always_xy := true) AS {geom_col}"
                                )
                            else:
                                select_cols.append(col["name"])
                        col_str = ", ".join(select_cols)
                else:
                    col_str = "*"

                query = f"SELECT {col_str} FROM {table_name}"
                if where:
                    query += f" WHERE {where}"

                # Export based on format
                if format_upper == "PARQUET":
                    con.execute(f"COPY ({query}) TO '{output_path}' (FORMAT PARQUET)")
                elif format_upper in ("CSV", "XLSX"):
                    # For CSV/XLSX, convert geometry to WKT text (if present)
                    # Table layers (no geometry) export as-is
                    if geom_col:
                        # Replace geometry column with WKT text representation
                        select_cols = []
                        for col in info["columns"]:
                            if col["name"] == geom_col:
                                select_cols.append(
                                    f"ST_AsText({geom_col}) AS {geom_col}"
                                )
                            else:
                                select_cols.append(col["name"])
                        tabular_query = (
                            f"SELECT {', '.join(select_cols)} FROM ({query})"
                        )
                    else:
                        tabular_query = query

                    if format_upper == "CSV":
                        con.execute(
                            f"COPY ({tabular_query}) TO '{output_path}' (FORMAT CSV, HEADER)"
                        )
                    else:  # XLSX
                        # Use DuckDB's excel extension if available, otherwise fall back to pandas
                        try:
                            con.execute("INSTALL excel; LOAD excel;")
                            con.execute(
                                f"COPY ({tabular_query}) TO '{output_path}' WITH (FORMAT xlsx, HEADER true)"
                            )
                        except Exception:
                            # Fallback: export via pandas
                            df = con.execute(tabular_query).fetch_df()
                            df.to_excel(output_path, index=False, engine="openpyxl")
                elif not geom_col:
                    # Table layer (no geometry) - only CSV and XLSX are valid
                    raise ValueError(
                        f"Format '{output_format}' requires geometry. "
                        f"Table layers can only be exported to CSV or XLSX."
                    )
                else:
                    # Vector formats (require geometry)
                    # Map format names to GDAL driver names
                    format_drivers = {
                        "GPKG": "GPKG",
                        "GEOPACKAGE": "GPKG",
                        "GEOJSON": "GeoJSON",
                        "JSON": "GeoJSON",
                        "SHP": "ESRI Shapefile",
                        "SHAPEFILE": "ESRI Shapefile",
                        "KML": "KML",
                        "GML": "GML",
                        "FLATGEOBUF": "FlatGeobuf",
                        "FGB": "FlatGeobuf",
                    }
                    driver = format_drivers.get(format_upper, format_upper)

                    # Set output CRS: use target_crs if specified, else detected source_crs
                    output_crs = target_crs if target_crs else source_crs

                    # GDAL doesn't support complex types (arrays, structs, maps)
                    # Convert them to JSON strings
                    gdal_select_cols = []
                    for col in info["columns"]:
                        col_name = col["name"]
                        col_type = col["type"].upper()
                        # Check for array, struct, map, or list types
                        if any(t in col_type for t in ["[]", "STRUCT", "MAP", "LIST"]):
                            # Convert to JSON string
                            gdal_select_cols.append(
                                f'to_json("{col_name}")::VARCHAR AS "{col_name}"'
                            )
                        else:
                            gdal_select_cols.append(f'"{col_name}"')

                    gdal_query = f"SELECT {', '.join(gdal_select_cols)} FROM ({query}) AS inner_q"

                    # Filter out invalid geometries to avoid GDAL errors with Inf bounds
                    # GDAL fails when extent contains Inf values from invalid geometries
                    # Check for: NULL, empty, invalid, or geometries with Inf/NaN bounds
                    export_query = f"""
                        SELECT * FROM ({gdal_query}) AS subq
                        WHERE {geom_col} IS NOT NULL
                        AND NOT ST_IsEmpty({geom_col})
                        AND ST_XMin({geom_col}) > -1e308
                        AND ST_XMax({geom_col}) < 1e308
                        AND ST_YMin({geom_col}) > -1e308
                        AND ST_YMax({geom_col}) < 1e308
                    """

                    # Check if there are any valid geometries to export
                    valid_count = con.execute(
                        f"SELECT COUNT(*) FROM ({export_query}) AS cnt"
                    ).fetchone()[0]

                    if valid_count == 0:
                        raise ValueError(
                            "No valid geometries to export. "
                            "All geometries are NULL, empty, or have invalid coordinates."
                        )

                    con.execute(f"""
                        COPY ({export_query}) TO '{output_path}'
                        WITH (FORMAT GDAL, DRIVER '{driver}', SRS '{output_crs}')
                    """)

                logger.info("Exported layer to %s: %s", output_format, output_path)

        except Exception as e:
            # Retry on connection-related errors (SSL EOF, connection lost)
            if retry and is_connection_error(e):
                logger.warning("Export failed due to connection error, retrying: %s", e)
                # Force reconnection
                self.reconnect()
                # Retry once
                return self._export_to_format_impl(
                    user_id,
                    layer_id,
                    output_path,
                    output_format,
                    target_crs,
                    where,
                    retry=False,
                )
            raise

        return output_path


# Singleton instance - initialize with ducklake_manager.init(settings) at startup
ducklake_manager = DuckLakeManager()
