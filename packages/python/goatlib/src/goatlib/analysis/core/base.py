import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, List, Self, Tuple

import duckdb
from goatlib.models.io import DatasetMetadata


class AnalysisTool:
    """
    Base class for analysis tools using DuckDB.
    Connects to a file-backed database by default to allow for disk spilling
    of large intermediate results (like buffers or joins), preventing Out-of-Memory errors.

    The public run() method now handles automatic cleanup using a try...finally
    block internally, fulfilling the requirement of simple usage: tool.run(params).

    Example Usage:
    tool = BufferTool()
    tool.run(params)
    """

    def __init__(self: Self, db_path: Path | None = None) -> None:
        self._temp_db_path: Path | None = None
        self._db_path: Path

        if db_path is None:
            # Create a unique, file-backed path in the system's temp directory
            unique_name = f"duckdb_temp_{uuid.uuid4()}.db"
            self._temp_db_path = Path(tempfile.gettempdir()) / unique_name
            self._db_path = self._temp_db_path
        else:
            self._db_path = db_path

        # Connect to the file-backed database path
        self.con = duckdb.connect(database=str(self._db_path))

        self._setup_duckdb_extensions()

    def _setup_duckdb_extensions(self: Self) -> None:
        """Configure DuckDB with necessary extensions and settings."""
        self.con.execute("INSTALL spatial; LOAD spatial;")
        self.con.execute("INSTALL httpfs; LOAD httpfs;")

    def cleanup(self: Self) -> None:
        """
        Closes the DuckDB connection and cleans up the temporary database file.
        This is called automatically by the public run() method.
        """
        # 1. Close the connection
        if self.con:
            self.con.close()

        # 2. Clean up the temporary file if one was automatically created
        if self._temp_db_path and self._temp_db_path.exists():
            try:
                os.remove(self._temp_db_path)
                # DuckDB often creates a journal file (.wal), so clean that up too
                wal_path = Path(str(self._temp_db_path) + ".wal")
                if wal_path.exists():
                    os.remove(wal_path)
                print(f"Cleaned up temporary DuckDB files: {self._temp_db_path}")
            except Exception as e:
                # Log a warning if cleanup fails, but don't stop execution
                print(f"Warning: Failed to delete temporary DuckDB files: {e}")

    def _run_implementation(
        self: Self, *args: Any, **kwargs: Any
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """
        Abstract method. Subclasses MUST override this with their core analysis logic.
        """
        raise NotImplementedError(
            "Each tool must implement the _run_implementation() method."
        )

    def run(
        self: Self, *args: Any, **kwargs: Any
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """
        Public execution method. Executes _run_implementation() and guarantees
        connection and resource cleanup via cleanup(), even if an error occurs.
        """
        try:
            # Delegate execution to the subclass's logic
            return self._run_implementation(*args, **kwargs)
        finally:
            # GUARANTEED cleanup runs here
            self.cleanup()
