import logging
from typing import Self, Tuple

from goatlib.analysis.core.base import AnalysisTool

logger = logging.getLogger(__name__)


def to_short_h3_3_py(h3_index: int) -> int | None:
    if h3_index is None:
        return None
    mask = 0x000FFFF000000000
    return (h3_index & mask) >> 36


class HeatmapToolBase(AnalysisTool):
    """Base class for heatmap analysis tools."""

    def __init__(self: Self) -> None:
        super().__init__()
        self._setup_heatmap_extensions()
        # Additional initialization for heatmap tools can go here

    def _setup_heatmap_extensions(self: Self) -> None:
        # Base already loads 'spatial' and 'httpfs'.
        # Heatmaps need 'h3' additionally.
        self.con.execute("INSTALL h3 FROM community; LOAD h3;")
        # UDF: needed if parquet is partitioned on the short h3_3 key
        self.con.create_function("to_short_h3_3", to_short_h3_3_py)

    def _prepare_od_matrix(
        self: Self, od_matrix_source: str, od_matrix_view_name: str = "od_matrix"
    ) -> Tuple[str, int]:
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
