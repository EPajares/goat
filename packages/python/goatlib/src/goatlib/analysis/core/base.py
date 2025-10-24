import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, List, Self, Tuple, final

import duckdb
from goatlib.io.utils import Metadata, download_if_remote, get_metadata
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class AnalysisTool:
    """
    Base class for analysis tools using DuckDB.
    Connects to a file-backed database by default to allow for disk spilling
    of large intermediate results (like buffers or joins), preventing Out-of-Memory errors.

    The public run() method handles automatic cleanup using a try...finally
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
        self.con.execute("SET memory_limit='2GB';")

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
                logger.info(f"Cleaned up temporary DuckDB files: {self._temp_db_path}")
            except Exception as e:
                # Log a warning if cleanup fails, but don't stop execution
                logger.warning(f"Failed to delete temporary DuckDB files: {e}")

    def import_input(
        self: Self,
        input_path: str,
        table_name: str = "v_input",
    ) -> Tuple[Metadata, str]:
        """
        Imports any supported vector or tabular dataset into DuckDB directly.

        Returns:
        - Metadata about the imported dataset.
        - The name of the table/view created in DuckDB.
        """
        path = Path(download_if_remote(input_path))
        suffix = path.suffix.lower()

        # --- Get unified metadata for both parquet and other spatial formats
        if suffix == ".parquet":
            logger.info("Registering parquet dataset as table: %s", path)
            self.con.execute(
                f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{path}')"
            )
        else:
            logger.info("Reading dataset into DuckDB via ST_Read: %s", path)
            self.con.execute(
                f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM ST_Read('{path}')"
            )

        meta = get_metadata(self.con, str(path))

        return meta, table_name

    def _run_implementation(
        self: Self, *args: Any, **kwargs: Any
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """
        Abstract method. Subclasses MUST override this with their core analysis logic.
        """
        raise NotImplementedError(
            "Each tool must implement the _run_implementation() method."
        )

    @final
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
