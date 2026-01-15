"""PMTiles generation from GeoParquet/DuckLake tables.

This module provides utilities for generating PMTiles (static vector tiles)
from GeoParquet files or DuckLake tables. PMTiles enable fast tile serving
without dynamic generation overhead.

The generation pipeline:
    1. Export geometry data to FlatGeobuf (intermediate format)
    2. Use tippecanoe to generate PMTiles with optimal settings
    3. Store PMTiles in a separate tiles directory (cache/derived data)

Usage:
    from goatlib.io.pmtiles import PMTilesGenerator

    generator = PMTilesGenerator(tiles_data_dir="/app/data/tiles")
    pmtiles_path = generator.generate_from_table(
        duckdb_con=con,
        table_name="lake.user_xxx.t_yyy",
        user_id="xxx",
        layer_id="yyy",
    )
"""

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

import duckdb

logger = logging.getLogger(__name__)


@dataclass
class PMTilesConfig:
    """Configuration for PMTiles generation.

    Attributes:
        enabled: Whether PMTiles generation is enabled
        min_zoom: Minimum zoom level (default: 0)
        max_zoom: Maximum zoom level (default: 14)
        layer_name: Name for the MVT layer (default: "default")
    """

    enabled: bool = True
    min_zoom: int = 0
    max_zoom: int = 14
    layer_name: str = "default"


class PMTilesGenerator:
    """Generate PMTiles from GeoParquet/DuckLake tables.

    PMTiles are stored separately from source data (cache/derived data):
        /app/data/tiles/
        └── user_{user_id}/
            └── t_{layer_id}.pmtiles

    Source data remains in DuckLake:
        /app/data/ducklake/
        └── user_{user_id}/
            └── t_{layer_id}/
                └── *.parquet
    """

    def __init__(
        self: Self,
        tiles_data_dir: str = "/app/data/tiles",
        config: PMTilesConfig | None = None,
    ) -> None:
        """Initialize PMTiles generator.

        Args:
            tiles_data_dir: Root directory for tiles storage (separate from source data)
            config: PMTiles generation configuration
        """
        self.tiles_data_dir = Path(tiles_data_dir)
        self.config = config or PMTilesConfig()
        self._check_dependencies()

    def _check_dependencies(self: Self) -> bool:
        """Check if required tools are available.

        Returns:
            True if all dependencies are available

        Raises:
            RuntimeError: If tippecanoe is not installed
        """
        if not shutil.which("tippecanoe"):
            raise RuntimeError(
                "tippecanoe is required for PMTiles generation. "
                "Install it with: apt-get install tippecanoe"
            )
        return True

    def get_pmtiles_path(self: Self, user_id: str, layer_id: str) -> Path:
        """Get the path where PMTiles should be stored.

        Args:
            user_id: User UUID (without dashes)
            layer_id: Layer UUID (without dashes)

        Returns:
            Path to the PMTiles file
        """
        user_id_clean = user_id.replace("-", "")
        layer_id_clean = layer_id.replace("-", "")

        tiles_dir = self.tiles_data_dir / f"user_{user_id_clean}"
        return tiles_dir / f"t_{layer_id_clean}.pmtiles"

    def pmtiles_exists(self: Self, user_id: str, layer_id: str) -> bool:
        """Check if PMTiles file exists for a layer.

        Args:
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            True if PMTiles file exists
        """
        return self.get_pmtiles_path(user_id, layer_id).exists()

    def generate_from_table(
        self: Self,
        duckdb_con: duckdb.DuckDBPyConnection,
        table_name: str,
        user_id: str,
        layer_id: str,
        geometry_column: str = "geometry",
        exclude_columns: list[str] | None = None,
    ) -> Path | None:
        """Generate PMTiles from a DuckLake table.

        Exports the table to FlatGeobuf (intermediate), then uses tippecanoe
        to generate PMTiles with optimal settings.

        Args:
            duckdb_con: DuckDB connection with DuckLake attached
            table_name: Full table path (e.g., "lake.user_xxx.t_yyy")
            user_id: User UUID
            layer_id: Layer UUID
            geometry_column: Name of the geometry column
            exclude_columns: Columns to exclude from tiles (e.g., ["bbox"])

        Returns:
            Path to generated PMTiles file, or None if generation failed
        """
        if not self.config.enabled:
            logger.debug("PMTiles generation is disabled")
            return None

        exclude_columns = exclude_columns or ["bbox"]
        pmtiles_path = self.get_pmtiles_path(user_id, layer_id)

        # Ensure tiles directory exists
        pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating PMTiles for {table_name} -> {pmtiles_path}")

        # Detect geometry type for optimized tippecanoe settings
        geometry_type = self._detect_geometry_type(
            duckdb_con, table_name, geometry_column
        )

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".fgb", delete=True, prefix="pmtiles_"
            ) as tmp_fgb:
                # Step 1: Export to FlatGeobuf (faster than GeoJSON)
                self._export_to_flatgeobuf(
                    duckdb_con=duckdb_con,
                    table_name=table_name,
                    output_path=tmp_fgb.name,
                    geometry_column=geometry_column,
                    exclude_columns=exclude_columns,
                )

                # Step 2: Generate PMTiles with tippecanoe
                self._run_tippecanoe(
                    input_path=tmp_fgb.name,
                    output_path=str(pmtiles_path),
                    geometry_type=geometry_type,
                )

            logger.info(
                f"PMTiles generated successfully: {pmtiles_path} "
                f"({pmtiles_path.stat().st_size / 1024 / 1024:.1f} MB)"
            )
            return pmtiles_path

        except Exception as e:
            logger.error(f"PMTiles generation failed: {e}")
            # Clean up partial file if it exists
            if pmtiles_path.exists():
                pmtiles_path.unlink()
            return None

    def _detect_geometry_type(
        self: Self,
        duckdb_con: duckdb.DuckDBPyConnection,
        table_name: str,
        geometry_column: str,
    ) -> str | None:
        """Detect the geometry type of a table.

        Args:
            duckdb_con: DuckDB connection
            table_name: Full table path
            geometry_column: Name of the geometry column

        Returns:
            Geometry type string (e.g., "POINT", "POLYGON") or None
        """
        try:
            # First, find the actual geometry column name
            cols = duckdb_con.execute(f"DESCRIBE {table_name}").fetchall()
            actual_geom_col = None
            for col_name, col_type, *_ in cols:
                if "GEOMETRY" in col_type.upper():
                    actual_geom_col = col_name
                    break

            if not actual_geom_col:
                logger.warning(f"No geometry column found in {table_name}")
                return None

            result = duckdb_con.execute(f"""
                SELECT DISTINCT ST_GeometryType("{actual_geom_col}")
                FROM {table_name}
                WHERE "{actual_geom_col}" IS NOT NULL
                LIMIT 1
            """).fetchone()
            if result:
                geom_type = result[0]
                logger.info(
                    f"Detected geometry type: {geom_type} (column: {actual_geom_col})"
                )
                return geom_type
        except Exception as e:
            logger.warning(f"Could not detect geometry type: {e}")
            logger.warning(f"Could not detect geometry type: {e}")
        return None

    def generate_from_parquet(
        self: Self,
        duckdb_con: duckdb.DuckDBPyConnection,
        parquet_path: str | Path,
        user_id: str,
        layer_id: str,
        geometry_column: str = "geometry",
        exclude_columns: list[str] | None = None,
    ) -> Path | None:
        """Generate PMTiles from a GeoParquet file.

        Args:
            duckdb_con: DuckDB connection (for reading parquet)
            parquet_path: Path to the GeoParquet file
            user_id: User UUID
            layer_id: Layer UUID
            geometry_column: Name of the geometry column
            exclude_columns: Columns to exclude from tiles

        Returns:
            Path to generated PMTiles file, or None if generation failed
        """
        if not self.config.enabled:
            logger.debug("PMTiles generation is disabled")
            return None

        exclude_columns = exclude_columns or ["bbox"]
        pmtiles_path = self.get_pmtiles_path(user_id, layer_id)

        # Ensure tiles directory exists
        pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating PMTiles from {parquet_path} -> {pmtiles_path}")

        # Detect geometry type for optimized tippecanoe settings
        geometry_type = None
        try:
            result = duckdb_con.execute(f"""
                SELECT DISTINCT ST_GeometryType("{geometry_column}")
                FROM read_parquet('{parquet_path}')
                WHERE "{geometry_column}" IS NOT NULL
                LIMIT 1
            """).fetchone()
            if result:
                geometry_type = result[0]
                logger.debug(f"Detected geometry type from parquet: {geometry_type}")
        except Exception as e:
            logger.warning(f"Could not detect geometry type from parquet: {e}")

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".geojson", delete=True, prefix="pmtiles_"
            ) as tmp_geojson:
                # Build exclusion clause
                exclude_clause = ""
                if exclude_columns:
                    exclude_clause = f"EXCLUDE({', '.join(exclude_columns)})"

                # Check if parquet has an 'id' column
                has_id_column = False
                try:
                    cols = duckdb_con.execute(f"""
                        SELECT column_name FROM (DESCRIBE SELECT * FROM read_parquet('{parquet_path}'))
                    """).fetchall()
                    has_id_column = any(col[0].lower() == "id" for col in cols)
                except Exception as e:
                    logger.warning(f"Could not check columns in parquet: {e}")

                # If no 'id' column, generate one using row_number for highlighting
                id_select = ""
                if not has_id_column:
                    id_select = "row_number() OVER () AS id, "
                    logger.debug("Adding synthetic 'id' column for highlighting")

                # Export to GeoJSON via DuckDB (preserves attribute types)
                duckdb_con.execute(f"""
                    COPY (
                        SELECT {id_select}* {exclude_clause}
                        FROM read_parquet('{parquet_path}')
                    ) TO '{tmp_geojson.name}' WITH (FORMAT GDAL, DRIVER 'GeoJSON')
                """)

                # Generate PMTiles
                self._run_tippecanoe(
                    input_path=tmp_geojson.name,
                    output_path=str(pmtiles_path),
                    geometry_type=geometry_type,
                )

            logger.info(
                f"PMTiles generated successfully: {pmtiles_path} "
                f"({pmtiles_path.stat().st_size / 1024 / 1024:.1f} MB)"
            )
            return pmtiles_path

        except Exception as e:
            logger.error(f"PMTiles generation failed: {e}")
            if pmtiles_path.exists():
                pmtiles_path.unlink()
            return None

    def _export_to_flatgeobuf(
        self: Self,
        duckdb_con: duckdb.DuckDBPyConnection,
        table_name: str,
        output_path: str,
        geometry_column: str = "geometry",
        exclude_columns: list[str] | None = None,
    ) -> None:
        """Export a DuckLake table to FlatGeobuf format.

        FlatGeobuf is faster to write and read than GeoJSON.
        Note: tippecanoe may convert integer attributes to strings with FGB.

        Args:
            duckdb_con: DuckDB connection
            table_name: Full table path
            output_path: Output FlatGeobuf file path
            geometry_column: Name of geometry column
            exclude_columns: Columns to exclude (e.g., bbox struct)
        """
        exclude_columns = exclude_columns or []

        # Types that are not supported by FlatGeobuf/tippecanoe
        unsupported_type_prefixes = ("struct", "map", "list", "union")

        # Get actual columns and their types from the table
        columns_to_exclude: set[str] = set(exclude_columns)
        has_id_column = False
        try:
            result = duckdb_con.execute(
                f"SELECT column_name, column_type FROM (DESCRIBE {table_name})"
            ).fetchall()

            for col_name, col_type in result:
                # Check if table has an 'id' column
                if col_name.lower() == "id":
                    has_id_column = True

                col_type_lower = col_type.lower()
                # Exclude complex types that FlatGeobuf/tippecanoe can't handle
                if col_type_lower.startswith(unsupported_type_prefixes):
                    columns_to_exclude.add(col_name)
                    logger.debug(
                        f"Excluding column '{col_name}' with unsupported type: {col_type}"
                    )
                # Also exclude array types (e.g., VARCHAR[], INTEGER[])
                elif col_type_lower.endswith("[]"):
                    columns_to_exclude.add(col_name)
                    logger.debug(f"Excluding array column '{col_name}': {col_type}")

            actual_columns = {row[0] for row in result}
            # Only keep exclusions for columns that actually exist
            columns_to_exclude = columns_to_exclude & actual_columns

        except Exception as e:
            logger.warning(f"Could not get column list for {table_name}: {e}")
            columns_to_exclude = set()

        # Build exclusion clause for columns that exist
        exclude_clause = ""
        if columns_to_exclude:
            exclude_clause = f"EXCLUDE({', '.join(sorted(columns_to_exclude))})"
            logger.debug(
                f"Excluding columns from FlatGeobuf export: {columns_to_exclude}"
            )

        # If no 'id' column exists, generate one from rowid for feature highlighting
        id_select = ""
        if not has_id_column:
            id_select = "rowid AS id, "
            logger.debug("Adding synthetic 'id' column from rowid for highlighting")

        sql = f"""
            COPY (
                SELECT {id_select}* {exclude_clause}
                FROM {table_name}
            ) TO '{output_path}' WITH (FORMAT GDAL, DRIVER 'FlatGeobuf')
        """

        logger.debug(f"Exporting to FlatGeobuf: {sql}")
        duckdb_con.execute(sql)

    def _export_to_geojson(
        self: Self,
        duckdb_con: duckdb.DuckDBPyConnection,
        table_name: str,
        output_path: str,
        geometry_column: str = "geometry",
        exclude_columns: list[str] | None = None,
    ) -> None:
        """Export a DuckLake table to GeoJSON format.

        GeoJSON is used as an intermediate format because:
        - tippecanoe reads it natively
        - GeoJSON preserves attribute types (integers stay integers)
        - DuckDB can write it directly via GDAL driver

        Note: We use GeoJSON instead of FlatGeobuf because tippecanoe
        converts FlatGeobuf attributes to strings, breaking numeric styles.

        Args:
            duckdb_con: DuckDB connection
            table_name: Full table path
            output_path: Output GeoJSON file path
            geometry_column: Name of geometry column
            exclude_columns: Columns to exclude (e.g., bbox struct)
        """
        exclude_columns = exclude_columns or []

        # Types that are not supported by GeoJSON/tippecanoe
        unsupported_type_prefixes = ("struct", "map", "list", "union")

        # Get actual columns and their types from the table
        columns_to_exclude: set[str] = set(exclude_columns)
        has_id_column = False
        try:
            result = duckdb_con.execute(
                f"SELECT column_name, column_type FROM (DESCRIBE {table_name})"
            ).fetchall()

            for col_name, col_type in result:
                # Check if table has an 'id' column
                if col_name.lower() == "id":
                    has_id_column = True

                col_type_lower = col_type.lower()
                # Exclude complex types that GeoJSON/tippecanoe can't handle
                if col_type_lower.startswith(unsupported_type_prefixes):
                    columns_to_exclude.add(col_name)
                    logger.debug(
                        f"Excluding column '{col_name}' with unsupported type: {col_type}"
                    )
                # Also exclude array types (e.g., VARCHAR[], INTEGER[])
                elif col_type_lower.endswith("[]"):
                    columns_to_exclude.add(col_name)
                    logger.debug(f"Excluding array column '{col_name}': {col_type}")

            actual_columns = {row[0] for row in result}
            # Only keep exclusions for columns that actually exist
            columns_to_exclude = columns_to_exclude & actual_columns

        except Exception as e:
            logger.warning(f"Could not get column list for {table_name}: {e}")
            columns_to_exclude = set()

        # Build exclusion clause for columns that exist
        exclude_clause = ""
        if columns_to_exclude:
            exclude_clause = f"EXCLUDE({', '.join(sorted(columns_to_exclude))})"
            logger.debug(f"Excluding columns from GeoJSON export: {columns_to_exclude}")

        # If no 'id' column exists, generate one from rowid for feature highlighting
        id_select = ""
        if not has_id_column:
            id_select = "rowid AS id, "
            logger.debug("Adding synthetic 'id' column from rowid for highlighting")

        sql = f"""
            COPY (
                SELECT {id_select}* {exclude_clause}
                FROM {table_name}
            ) TO '{output_path}' WITH (FORMAT GDAL, DRIVER 'GeoJSON')
        """

        logger.debug(f"Exporting to GeoJSON: {sql}")
        duckdb_con.execute(sql)

    def _run_tippecanoe(
        self: Self,
        input_path: str,
        output_path: str,
        geometry_type: str | None = None,
    ) -> None:
        """Run tippecanoe to generate PMTiles.

        Uses different settings based on geometry type:
        - Points: Use drop-fraction for even distribution at low zooms
        - Polygons/Lines: Use drop-densest to preserve shapes

        Args:
            input_path: Input FlatGeobuf file path
            output_path: Output PMTiles file path
            geometry_type: Geometry type (e.g., "POINT", "POLYGON")

        Raises:
            subprocess.CalledProcessError: If tippecanoe fails
        """
        # Use defaults if config values are None (safety check)
        min_zoom = self.config.min_zoom if self.config.min_zoom is not None else 0
        max_zoom = self.config.max_zoom if self.config.max_zoom is not None else 14

        # Detect geometry type category
        geom_upper = geometry_type.upper() if geometry_type else ""
        is_point_layer = "POINT" in geom_upper
        is_line_layer = "LINE" in geom_upper or "LINESTRING" in geom_upper

        cmd = [
            "tippecanoe",
            "-o",
            output_path,
            input_path,
            "--force",
            "-l",
            self.config.layer_name,
            f"-Z{min_zoom}",
            f"-z{max_zoom}",
            "--full-detail=16",
            # Note: Don't use --use-attribute-for-id as it removes id from properties
            # The frontend filter uses ["in", "id", ...] which needs properties.id
        ]

        if is_point_layer:
            # Point-specific settings:
            # - Higher limits for dense/attribute-heavy POI datasets
            # - Use -r1 to guarantee at least 1 feature per tile at all zooms
            # - Coalesce smallest for even distribution at low zooms
            cmd.extend(
                [
                    "-r1",  # Retain at least 1 feature per tile at every zoom
                    "--coalesce-smallest-as-needed",  # Even distribution instead of densest-first
                    "--extend-zooms-if-still-dropping",
                ]
            )
            logger.info("Using point-optimized tippecanoe settings (-r1, high limits)")
        elif is_line_layer:
            # LineString settings (e.g., roads):
            # - Higher limits for denser output (like Felt)
            # - Allow line simplification at low zooms (default behavior)
            # - Only drop smallest lines when absolutely needed
            cmd.extend(
                [
                    "-M",
                    "2000000",  # 2MB tile size limit (default 500KB)
                    "-O",
                    "300000",  # 300K features per tile (default 200K)
                    "--drop-smallest-as-needed",  # Drop tiny road segments only if needed
                    "--extend-zooms-if-still-dropping",
                ]
            )
            logger.info(
                "Using line-optimized tippecanoe settings (high density, simplify)"
            )
        else:
            # Polygon settings:
            # - Higher limits for dense polygon datasets (buildings, parcels)
            # - Preserve geometry detail
            # - Avoid tiny polygon reduction (keeps small buildings visible)
            # - Drop/coalesce densest areas first
            cmd.extend(
                [
                    "-M",
                    "2000000",  # 2MB tile size limit (default 500KB)
                    "-O",
                    "300000",  # 300K features per tile (default 200K)
                    "--no-tiny-polygon-reduction",
                    "--coalesce-densest-as-needed",
                    "--drop-densest-as-needed",
                    "--extend-zooms-if-still-dropping",
                ]
            )
            logger.debug("Using polygon-optimized tippecanoe settings")

        logger.debug(f"Running tippecanoe: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "No error message"
            logger.error(
                f"tippecanoe failed (exit {result.returncode}): {error_msg}\n"
                f"Command: {' '.join(cmd)}"
            )
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        if result.stderr:
            # tippecanoe outputs progress to stderr, log it as debug
            for line in result.stderr.strip().split("\n"):
                if line.strip():
                    logger.debug(f"tippecanoe: {line}")

    def delete_pmtiles(self: Self, user_id: str, layer_id: str) -> bool:
        """Delete PMTiles file for a layer.

        Args:
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            True if file was deleted, False if it didn't exist
        """
        pmtiles_path = self.get_pmtiles_path(user_id, layer_id)
        if pmtiles_path.exists():
            pmtiles_path.unlink()
            logger.info(f"Deleted PMTiles: {pmtiles_path}")
            return True
        return False


def get_table_geometry_info(
    duckdb_con: duckdb.DuckDBPyConnection, table_name: str
) -> dict[str, Any] | None:
    """Get geometry column info from a DuckLake table.

    Args:
        duckdb_con: DuckDB connection
        table_name: Full table path

    Returns:
        Dict with geometry_column and geometry_type, or None if no geometry
    """
    cols = duckdb_con.execute(f"DESCRIBE {table_name}").fetchall()

    for col_name, col_type, *_ in cols:
        if "GEOMETRY" in col_type.upper():
            # Get geometry type
            type_result = duckdb_con.execute(f"""
                SELECT DISTINCT ST_GeometryType({col_name})
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
                LIMIT 1
            """).fetchone()

            return {
                "geometry_column": col_name,
                "geometry_type": type_result[0] if type_result else None,
            }

    return None
