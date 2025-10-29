import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.core.base import AnalysisTool

logger = logging.getLogger(__name__)


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

    def _prepare_od_matrix(
        self: Self, od_matrix_source: str, od_matrix_view_name: str = "od_matrix"
    ) -> tuple[str, int]:
        """
        Register OD matrix source as a DuckDB VIEW and detect H3 resolution.
        Returns (view_name, h3_resolution)
        """
        view_name = od_matrix_view_name
        try:
            self.con.execute(f"""
                CREATE OR REPLACE TEMP VIEW {view_name} AS
                SELECT * FROM read_parquet('{od_matrix_source}')
            """)
        except Exception as e:
            raise ValueError(
                f"Failed to register OD matrix from '{od_matrix_source}': {e}"
            )

        try:
            result = self.con.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{view_name}'
            """).fetchall()
        except Exception as e:
            raise ValueError(f"Failed to inspect OD matrix schema: {e}")

        actual_columns = {row[0] for row in result}
        required_columns = {"orig_id", "dest_id", "traveltime"}
        if not required_columns.issubset(actual_columns):
            raise ValueError(
                f"OD matrix must contain columns: {required_columns}. "
                f"Found: {actual_columns}"
            )

        # Detect H3 resolution
        try:
            result = self.con.execute(f"""
                SELECT
                    h3_get_resolution(COALESCE(orig_id, dest_id)) AS res
                FROM {view_name}
                WHERE orig_id IS NOT NULL OR dest_id IS NOT NULL
                LIMIT 1
            """).fetchone()
        except Exception as e:
            raise ValueError(f"Failed to detect H3 resolution: {e}")

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
        max_traveltime: float = None,
        min_traveltime: float = None,
    ) -> str:
        """
        Efficiently filter the OD matrix by various criteria.

        Args:
            od_table: Name of the OD matrix table
            origin_ids: List of origin H3 IDs to filter by
            destination_ids: List of destination H3 IDs to filter by
            max_traveltime: Maximum travel time to include
            min_traveltime: Minimum travel time to include

        Returns:
            Name of the filtered table
        """
        filtered_table = "filtered_matrix"

        if (
            not origin_ids
            and not destination_ids
            and max_traveltime is None
            and min_traveltime is None
        ):
            raise ValueError("At least one filtering criterion must be provided.")

        # Build WHERE conditions - put partition filters FIRST for optimal performance
        conditions = []

        # Then specific ID filters
        if origin_ids:
            origin_ids_sql = ", ".join(map(str, origin_ids))
            conditions.append(f"orig_id IN ({origin_ids_sql})")

        if destination_ids:
            dest_ids_sql = ", ".join(map(str, destination_ids))
            conditions.append(f"dest_id IN ({dest_ids_sql})")

        # Travel time filters last (usually less selective)
        if max_traveltime is not None:
            conditions.append(f"traveltime <= {max_traveltime}")

        if min_traveltime is not None:
            conditions.append(f"traveltime >= {min_traveltime}")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            CREATE OR REPLACE TEMP TABLE {filtered_table} AS
            SELECT orig_id, dest_id, traveltime
            FROM {od_table}
            WHERE {where_clause}
        """

        self.con.execute(query)
        count = self.con.execute(f"SELECT COUNT(*) FROM {filtered_table}").fetchone()[0]

        # Build filter description for logging
        filter_desc = []
        if origin_ids:
            filter_desc.append(f"{len(origin_ids)} origins")
        if destination_ids:
            filter_desc.append(f"{len(destination_ids)} destinations")
        if max_traveltime is not None:
            filter_desc.append(f"max_tt={max_traveltime}")
        if min_traveltime is not None:
            filter_desc.append(f"min_tt={min_traveltime}")

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
    ) -> None:
        """Export results"""
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if output_path_obj.suffix.lower() != ".parquet":
            output_path_obj = output_path_obj.with_suffix(".parquet")

        query = f"""
            COPY (
                SELECT
                    *,
                    ST_AsWKB(ST_GeomFromText(h3_cell_to_boundary_wkt({h3_column}))) AS geometry
                FROM {results_table}
                ORDER BY {h3_column}
            ) TO '{output_path_obj}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
        self.con.execute(query)
        logger.info("Results written to: %s", output_path)
        return None
