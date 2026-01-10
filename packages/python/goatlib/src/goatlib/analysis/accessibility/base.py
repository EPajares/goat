import logging
import re
import unicodedata
from pathlib import Path
from typing import Self

from goatlib.analysis.core.base import AnalysisTool

logger = logging.getLogger(__name__)


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
        """Export results"""
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if output_path_obj.suffix.lower() != ".parquet":
            output_path_obj = output_path_obj.with_suffix(".parquet")

        query = f"""
            COPY (
                SELECT
                    {h3_column}::BIGINT AS {h3_column},
                    * EXCLUDE ({h3_column}),
                    ST_AsWKB(ST_GeomFromText(h3_cell_to_boundary_wkt({h3_column}))) AS geometry
                FROM {results_table}
                ORDER BY {h3_column}
            ) TO '{output_path_obj}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
        self.con.execute(query)
        logger.info("Results written to: %s", output_path)
        return output_path_obj
