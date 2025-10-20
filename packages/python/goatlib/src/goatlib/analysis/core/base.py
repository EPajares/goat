from pathlib import Path
from typing import Any, List, Self, Tuple

import duckdb
from goatlib.models.io import DatasetMetadata


class AnalysisTool:
    def __init__(self: Self) -> None:
        self.con = duckdb.connect(database=":memory:")
        self._setup_duckdb_extensions()

    def _setup_duckdb_extensions(self: Self) -> None:
        """Configure DuckDB with necessary extensions and settings."""
        self.con.execute("INSTALL spatial; LOAD spatial;")
        self.con.execute("INSTALL httpfs; LOAD httpfs;")

    def run(
        self: Self, *args: Any, **kwargs: Any
    ) -> List[Tuple[Path, DatasetMetadata]]:
        raise NotImplementedError("Each tool must implement the run() method.")
