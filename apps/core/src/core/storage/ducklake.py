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
from typing import TYPE_CHECKING, Any
from uuid import UUID

import duckdb
from goatlib.storage import BaseDuckLakeManager

if TYPE_CHECKING:
    from core.core.config import Settings

logger = logging.getLogger(__name__)


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
            def __init__(self, base_settings: "Settings"):
                # BaseDuckLakeManager.init() expects these fields:
                self.POSTGRES_DATABASE_URI = base_settings.POSTGRES_DATABASE_URI
                self.DUCKLAKE_CATALOG_SCHEMA = base_settings.DUCKLAKE_CATALOG_SCHEMA
                # Compute DUCKLAKE_DATA_DIR from DATA_DIR
                self.DUCKLAKE_DATA_DIR = os.path.join(
                    base_settings.DATA_DIR, "ducklake"
                )

        ducklake_settings = DuckLakeSettings(settings)
        super().init(ducklake_settings)

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

    def user_schema_exists(self: "DuckLakeManager", user_id: UUID) -> bool:
        """Check if user schema exists in DuckLake."""
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
        and creates a DuckLake table.

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
                    info["extent"] = {
                        "xmin": extent_result[0],
                        "ymin": extent_result[1],
                        "xmax": extent_result[2],
                        "ymax": extent_result[3],
                    }
            except Exception as e:
                logger.warning("Could not get geometry info: %s", e)

        return info

    def delete_layer_table(
        self: "DuckLakeManager", user_id: UUID, layer_id: UUID
    ) -> bool:
        """Delete a layer table from DuckLake.

        Called when a layer is deleted. Removes both the DuckLake table
        (metadata) and the underlying parquet files from disk.

        Returns:
            True if table was deleted, False if it didn't exist
        """
        table_name = self.get_layer_table_name(user_id, layer_id)
        schema_name = self.get_user_schema_name(user_id)
        table_only = f"t_{str(layer_id).replace('-', '')}"

        with self.connection() as con:
            # Check if exists first
            if not self.layer_table_exists(user_id, layer_id):
                logger.warning("Layer table does not exist: %s", table_name)
                return False

            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.info("Deleted DuckLake layer table: %s", table_name)

        # Delete parquet files from disk
        layer_data_path = os.path.join(self._storage_path, schema_name, table_only)
        if os.path.isdir(layer_data_path):
            shutil.rmtree(layer_data_path)
            logger.info("Deleted layer parquet files: %s", layer_data_path)

            # Also try to remove parent user schema folder if empty
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

        Uses a safe swap approach:
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
                old_exists = self.layer_table_exists(user_id, layer_id)
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

            # Step 3: Rename physical folders on disk
            # DuckLake's ALTER RENAME only updates catalog, not physical files
            old_data_path = os.path.join(self._storage_path, schema_name, table_only)
            new_data_path = os.path.join(
                self._storage_path, schema_name, temp_table_only
            )

            # Remove old data folder if it exists (from dropped table)
            if os.path.isdir(old_data_path):
                shutil.rmtree(old_data_path)
                logger.info("Removed old data folder: %s", old_data_path)

            # Rename new data folder to final name
            if os.path.isdir(new_data_path):
                os.rename(new_data_path, old_data_path)
                logger.info(
                    "Renamed data folder: %s -> %s", new_data_path, old_data_path
                )

            # Get table info for the new table
            info = self._get_table_info(con, table_name)
            info["table_name"] = table_name

            return info

    def layer_table_exists(
        self: "DuckLakeManager", user_id: UUID, layer_id: UUID
    ) -> bool:
        """Check if a layer table exists in DuckLake."""
        schema_name = self.get_user_schema_name(user_id)
        table_only = f"t_{str(layer_id).replace('-', '')}"

        with self.connection() as con:
            result = con.execute(f"""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_catalog = 'lake'
                AND table_schema = '{schema_name}'
                AND table_name = '{table_only}'
            """).fetchone()
            return result[0] > 0 if result else False

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
            error_msg = str(e).lower()
            # Retry on connection-related errors (SSL EOF, connection lost)
            if retry and (
                "ssl" in error_msg or "eof" in error_msg or "connection" in error_msg
            ):
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
