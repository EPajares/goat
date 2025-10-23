from typing import Self

from goatlib.analysis.core.base import AnalysisTool


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

    pass
