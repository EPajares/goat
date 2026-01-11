import logging
import re
import unicodedata
from pathlib import Path
from typing import Self

from goatlib.analysis.core.base import AnalysisTool
from goatlib.io.parquet import write_optimized_parquet
from goatlib.analysis.schemas.base import PTTimeWindow

logger = logging.getLogger(__name__)


# =============================================================================
# Transport Mode Mapping (GTFS route_type to mode category)
# =============================================================================

# Based on GTFS extended route types
TRANSPORT_MODE_MAPPING: dict[str, str] = {
    # Bus
    "3": "bus",
    "11": "bus",
    "700": "bus",
    "701": "bus",
    "702": "bus",
    "704": "bus",
    "705": "bus",
    "710": "bus",
    "712": "bus",
    "715": "bus",
    "800": "bus",
    # Tram
    "0": "tram",
    "5": "tram",
    "900": "tram",
    "901": "tram",
    "902": "tram",
    "903": "tram",
    "904": "tram",
    "905": "tram",
    "906": "tram",
    # Metro
    "1": "metro",
    "400": "metro",
    "401": "metro",
    "402": "metro",
    "403": "metro",
    "405": "metro",
    # Rail
    "2": "rail",
    "100": "rail",
    "101": "rail",
    "102": "rail",
    "103": "rail",
    "104": "rail",
    "105": "rail",
    "106": "rail",
    "107": "rail",
    "108": "rail",
    "109": "rail",
    "110": "rail",
    "111": "rail",
    "112": "rail",
    "114": "rail",
    "116": "rail",
    "117": "rail",
    "202": "rail",
    # Other
    "4": "other",
    "6": "other",
    "7": "other",
    "200": "other",
    "201": "other",
    "204": "other",
    "1000": "other",
    "1300": "other",
    "1400": "other",
}


# =============================================================================
# Utility Functions
# =============================================================================


def sanitize_sql_name(name: str, fallback_idx: int = 0) -> str:
    """Sanitize a string to be a valid SQL identifier.

    Normalizes unicode, removes special characters, and ensures valid SQL name.

    Args:
        name: The original name (e.g., layer name with special characters)
        fallback_idx: Index to use if name becomes empty after sanitization

    Returns:
        A valid SQL identifier (lowercase, alphanumeric with underscores)
    """
    # Normalize unicode (converts ö to o, etc.)
    normalized = unicodedata.normalize("NFKD", name)
    safe_name = normalized.encode("ascii", "ignore").decode("ascii")
    # Replace non-alphanumeric with underscore, lowercase
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", safe_name).lower()
    # Remove consecutive/trailing underscores
    safe_name = re.sub(r"_+", "_", safe_name).strip("_")
    # Ensure not empty
    if not safe_name:
        safe_name = f"opp_{fallback_idx}"
    return safe_name


class HeatmapToolBase(AnalysisTool):
    """Base class for heatmap analysis tools."""

    def __init__(self: Self) -> None:
        super().__init__()
        self._setup_heatmap_extensions()
        # Additional initialization for heatmap tools can go here

    def _setup_heatmap_extensions(self: Self) -> None:
        """Install required extensions and register helper functions."""
        self.con.execute("INSTALL h3 FROM community; LOAD h3;")
        logger.debug("H3 extensions and helper UDFs loaded.")

    def _detect_od_columns(
        self: Self,
        od_matrix_path: str,
    ) -> dict[str, str]:
        """Auto-detect column mapping from OD matrix parquet schema.

        Looks for standard column names and common alternatives:
        - orig_id: origin_id, from_id, source_id, orig
        - dest_id: destination_id, to_id, target_id, dest
        - cost: traveltime, travel_time, time, duration, distance

        Returns:
            Column mapping dict with keys: orig_id, dest_id, cost
        """
        # Normalize path for glob pattern (handle directories)
        path = od_matrix_path.rstrip("/")
        if not path.endswith(".parquet") and "*" not in path:
            path = f"{path}/**/*.parquet"

        # Get schema from parquet file(s)
        try:
            schema_result = self.con.execute(f"""
                SELECT DISTINCT name
                FROM parquet_schema('{path}')
            """).fetchall()
            columns = {row[0].lower() for row in schema_result}
            logger.debug(f"Detected parquet columns: {sorted(columns)}")
        except Exception as e:
            logger.warning(f"Could not read parquet schema: {e}, using defaults")
            return {"orig_id": "orig_id", "dest_id": "dest_id", "cost": "traveltime"}

        # Define candidate names for each required column (in priority order)
        candidates = {
            "orig_id": ["orig_id", "origin_id", "from_id", "source_id", "orig", "o_id"],
            "dest_id": [
                "dest_id",
                "destination_id",
                "to_id",
                "target_id",
                "dest",
                "d_id",
            ],
            "cost": [
                "cost",
                "traveltime",
                "travel_time",
                "time",
                "duration",
                "distance",
            ],
        }

        mapping = {}
        for target, options in candidates.items():
            for option in options:
                if option in columns:
                    mapping[target] = option
                    logger.debug(f"Auto-detected {target} -> {option}")
                    break
            if target not in mapping:
                raise ValueError(
                    f"Could not auto-detect '{target}' column. "
                    f"Available columns: {sorted(columns)}. "
                    f"Expected one of: {options}"
                )

        logger.info(f"Auto-detected OD matrix columns: {mapping}")
        return mapping

    def _prepare_od_matrix(
        self: Self,
        od_matrix_path: str,
        od_column_map: dict[str, str] | None = None,
        od_matrix_view_name: str = "od_matrix",
    ) -> tuple[str, int]:
        """
        Register OD matrix source as a DuckDB VIEW and detect H3 resolution.
        Supports custom column mapping: keys = ["orig_id", "dest_id", "cost"]
        Returns (view_name, h3_resolution)
        """
        view_name = od_matrix_view_name

        # Normalize path for glob pattern (handle directories)
        path = od_matrix_path.rstrip("/")
        if not path.endswith(".parquet") and "*" not in path:
            path = f"{path}/**/*.parquet"

        # Default mapping that should trigger auto-detection
        default_mapping = {"orig_id": "orig_id", "dest_id": "dest_id", "cost": "cost"}

        # Auto-detect column mapping if not provided or using defaults
        if od_column_map is None or od_column_map == default_mapping:
            od_column_map = self._detect_od_columns(od_matrix_path)

        mapping = od_column_map

        # Build column selections - only alias if source != target name
        def col_expr(target: str) -> str:
            source = mapping[target]
            if source == target:
                return f'"{source}"'
            return f'"{source}" AS {target}'

        try:
            self.con.execute(f"""
                CREATE OR REPLACE TEMP VIEW {view_name} AS
                SELECT
                    {col_expr('orig_id')},
                    {col_expr('dest_id')},
                    {col_expr('cost')}
                FROM read_parquet('{path}')
            """)
        except Exception as e:
            raise ValueError(
                f"Failed to register OD matrix from '{od_matrix_path}': {e}"
            )

        # Inspect columns
        result = self.con.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{view_name}'
        """).fetchall()
        actual_columns = {row[0] for row in result}
        required_columns = {"orig_id", "dest_id", "cost"}
        if not required_columns.issubset(actual_columns):
            raise ValueError(
                f"OD matrix must contain columns: {required_columns}. Found: {actual_columns}"
            )

        # Detect H3 resolution
        result = self.con.execute(f"""
            SELECT h3_get_resolution(COALESCE(orig_id, dest_id)) AS res
            FROM {view_name}
            WHERE orig_id IS NOT NULL OR dest_id IS NOT NULL
            LIMIT 1
        """).fetchone()

        if result and result[0] is not None:
            h3_resolution = int(result[0])
            logger.info(
                "Registered OD matrix view '%s' at H3 resolution %d",
                view_name,
                h3_resolution,
            )
            return view_name, h3_resolution

        raise ValueError("Could not detect H3 resolution from OD matrix")

    def _filter_od_matrix(
        self: Self,
        od_table: str,
        *,
        origin_ids: list[int] = None,
        destination_ids: list[int] = None,
        max_cost: float = None,
        min_cost: float = None,
    ) -> str:
        """
        Efficiently filter the OD matrix by various criteria.

        Args:
            od_table: Name of the OD matrix table
            origin_ids: List of origin H3 IDs to filter by
            destination_ids: List of destination H3 IDs to filter by
            max_cost: Maximum cost to include
            min_cost: Minimum cost to include

        Returns:
            Name of the filtered table
        """
        filtered_table = "filtered_matrix"

        if (
            not origin_ids
            and not destination_ids
            and max_cost is None
            and min_cost is None
        ):
            raise ValueError("At least one filtering criterion must be provided.")

        conditions = []

        if origin_ids:
            origin_ids_sql = ", ".join(map(str, origin_ids))
            conditions.append(f"orig_id IN ({origin_ids_sql})")

        if destination_ids:
            dest_ids_sql = ", ".join(map(str, destination_ids))
            conditions.append(f"dest_id IN ({dest_ids_sql})")

        if max_cost is not None:
            conditions.append(f"cost <= {max_cost}")

        if min_cost is not None:
            conditions.append(f"cost >= {min_cost}")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            CREATE OR REPLACE TEMP TABLE {filtered_table} AS
            SELECT orig_id, dest_id, cost
            FROM {od_table}
            WHERE {where_clause}
        """

        self.con.execute(query)
        count = self.con.execute(f"SELECT COUNT(*) FROM {filtered_table}").fetchone()[0]

        filter_desc = []
        if origin_ids:
            filter_desc.append(f"{len(origin_ids)} origins")
        if destination_ids:
            filter_desc.append(f"{len(destination_ids)} destinations")
        if max_cost is not None:
            filter_desc.append(f"max_cost={max_cost}")
        if min_cost is not None:
            filter_desc.append(f"min_cost={min_cost}")

        logger.info(
            "Filtered OD matrix created with %d rows (%s)",
            count,
            ", ".join(filter_desc),
        )
        return filtered_table

    def _extract_destination_ids(self: Self, table: str) -> list[int]:
        """Extract unique destination H3 IDs from unified opportunity table."""
        result = self.con.execute(
            f"SELECT DISTINCT dest_id FROM {table} WHERE dest_id IS NOT NULL"
        ).fetchall()
        return [row[0] for row in result] if result else []

    def _export_h3_results(
        self: Self,
        results_table: str,
        output_path: str,
        h3_column: str = "h3_index",
    ) -> Path:
        """Export results with optimized Parquet V2 format and bbox for row group pruning."""
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if output_path_obj.suffix.lower() != ".parquet":
            output_path_obj = output_path_obj.with_suffix(".parquet")

        # Build query that generates H3 polygon geometry
        # Use native GEOMETRY type (not WKB) for proper GeoParquet output
        query = f"""
            SELECT
                {h3_column}::BIGINT AS {h3_column},
                * EXCLUDE ({h3_column}),
                ST_GeomFromText(h3_cell_to_boundary_wkt({h3_column})) AS geometry
            FROM {results_table}
        """

        # Use optimized parquet writer with V2 format, bbox, and Hilbert sort
        write_optimized_parquet(
            self.con,
            query,
            output_path_obj,
            geometry_column="geometry",
        )

        logger.info("Results written to: %s", output_path)
        return output_path_obj


# =============================================================================
# Public Transport Tool Base
# =============================================================================


class PTToolBase(AnalysisTool):
    """Base class for Public Transport analysis tools.

    Provides shared functionality for GTFS data import and station
    service counting used by Trip Count Station and ÖV-Güteklassen tools.

    Subclasses should call these methods in their _run_implementation()
    and then add their specific processing logic.
    """

    def __init__(self: Self) -> None:
        super().__init__()
        self._setup_pt_extensions()

    def _setup_pt_extensions(self: Self) -> None:
        """Install required extensions for PT analysis."""
        self.con.execute("INSTALL h3 FROM community; LOAD h3;")
        logger.debug("H3 extension loaded for PT tool.")

    def _import_gtfs_stops(self: Self, stops_path: str) -> None:
        """Import GTFS stops parquet.

        Creates a view 'gtfs_stops' with standardized columns:
        - stop_id, stop_name, stop_lat, stop_lon, location_type,
          parent_station, h3_3, geom

        Args:
            stops_path: Path to GTFS stops parquet file.
        """
        self.con.execute(f"""
            CREATE OR REPLACE VIEW gtfs_stops AS
            SELECT
                stop_id,
                stop_name,
                stop_lat,
                stop_lon,
                location_type,
                parent_station,
                h3_3,
                ST_Point(stop_lon, stop_lat) AS geom
            FROM read_parquet('{stops_path}')
            WHERE location_type IS NULL OR location_type = '0' OR location_type = ''
        """)

    def _import_gtfs_stop_times(self: Self, stop_times_path: str) -> None:
        """Import GTFS stop_times parquet.

        Creates a view 'gtfs_stop_times' with standardized columns:
        - stop_id, route_type, arrival_time, is_weekday, is_saturday,
          is_sunday, h3_3

        Args:
            stop_times_path: Path to GTFS stop_times parquet file.
        """
        self.con.execute(f"""
            CREATE OR REPLACE VIEW gtfs_stop_times AS
            SELECT
                stop_id,
                route_type,
                arrival_time,
                is_weekday,
                is_saturday,
                is_sunday,
                h3_3
            FROM read_parquet('{stop_times_path}')
        """)

    def _get_stations_in_area(self: Self, ref_geom_col: str) -> None:
        """Find all stops within the reference area.

        Creates a table 'stations_in_area' with stops intersecting
        the reference area.

        Args:
            ref_geom_col: Name of the geometry column in the reference_area view.

        Requires:
            - 'gtfs_stops' view must exist
            - 'reference_area' view must exist
        """
        self.con.execute(f"""
            CREATE OR REPLACE TABLE stations_in_area AS
            SELECT DISTINCT
                s.stop_id,
                s.stop_name,
                s.parent_station,
                s.h3_3,
                s.geom
            FROM gtfs_stops s, reference_area r
            WHERE ST_Intersects(s.geom, r.{ref_geom_col})
        """)

    def _count_pt_services(self: Self, time_window: PTTimeWindow) -> None:
        """Count public transport services per station in the time window.

        Creates a table 'station_trip_counts' with trip counts per
        station and route_type.

        Args:
            time_window: Time window for counting services.

        Requires:
            - 'stations_in_area' table must exist
            - 'gtfs_stop_times' view must exist
        """
        weekday_col = time_window.weekday_column
        from_time = time_window.from_time_str
        to_time = time_window.to_time_str

        self.con.execute(f"""
            CREATE OR REPLACE TABLE station_trip_counts AS
            SELECT
                s.stop_id,
                s.stop_name,
                s.parent_station,
                s.geom,
                t.route_type,
                COUNT(*) AS trip_count
            FROM stations_in_area s
            JOIN gtfs_stop_times t ON s.stop_id = t.stop_id AND s.h3_3 = t.h3_3
            WHERE t.{weekday_col} = true
              AND t.arrival_time >= '{from_time}'
              AND t.arrival_time <= '{to_time}'
            GROUP BY s.stop_id, s.stop_name, s.parent_station, s.geom, t.route_type
        """)

    def _create_mode_mapping_table(self: Self) -> None:
        """Create a table mapping route_type to transport mode category.

        Creates 'route_type_modes' table with columns:
        - route_type: GTFS route type as string
        - mode: Category (bus, tram, metro, rail, other)
        """
        mode_values = ", ".join(
            f"('{k}', '{v}')" for k, v in TRANSPORT_MODE_MAPPING.items()
        )
        self.con.execute(f"""
            CREATE OR REPLACE TABLE route_type_modes AS
            SELECT * FROM (VALUES {mode_values}) AS t(route_type, mode)
        """)

    def _aggregate_trips_by_mode(self: Self, time_window: PTTimeWindow) -> None:
        """Aggregate trip counts by transport mode per station.

        Creates 'station_mode_counts' table with trip counts per station
        and mode category (bus, tram, metro, rail, other).

        Args:
            time_window: Time window (used for frequency calculation).

        Requires:
            - 'station_trip_counts' table must exist
            - 'route_type_modes' table must exist
        """
        time_window_minutes = time_window.time_window_minutes

        self.con.execute(f"""
            CREATE OR REPLACE TABLE station_mode_counts AS
            SELECT
                stop_id,
                ANY_VALUE(stop_name) AS stop_name,
                ANY_VALUE(parent_station) AS parent_station,
                ANY_VALUE(geom) AS geom,
                COALESCE(SUM(CASE WHEN mode = 'bus' THEN trip_count ELSE 0 END), 0) AS bus,
                COALESCE(SUM(CASE WHEN mode = 'tram' THEN trip_count ELSE 0 END), 0) AS tram,
                COALESCE(SUM(CASE WHEN mode = 'metro' THEN trip_count ELSE 0 END), 0) AS metro,
                COALESCE(SUM(CASE WHEN mode = 'rail' THEN trip_count ELSE 0 END), 0) AS rail,
                COALESCE(SUM(CASE WHEN mode = 'other' THEN trip_count ELSE 0 END), 0) AS other,
                SUM(trip_count) AS total,
                CASE
                    WHEN SUM(trip_count) > 0
                    THEN ROUND({time_window_minutes} / SUM(trip_count), 2)
                    ELSE NULL
                END AS frequency
            FROM station_trip_counts stc
            LEFT JOIN route_type_modes rtm
                ON CAST(stc.route_type AS VARCHAR) = rtm.route_type
            GROUP BY stop_id
        """)
