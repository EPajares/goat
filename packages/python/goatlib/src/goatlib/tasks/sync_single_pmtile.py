"""Single PMTile generation task for Windmill.

This task generates PMTiles for a single DuckLake layer.
It's designed to be called by queue_pmtiles_sync for parallel processing.

Usage as Windmill script:
    # Called by Windmill with SinglePMTileParams
    # Typically queued by queue_pmtiles_sync task

Usage as library:
    from goatlib.tasks.sync_single_pmtile import SinglePMTileTask, SinglePMTileParams

    task = SinglePMTileTask()
    task.init_from_env()
    result = task.run(SinglePMTileParams(user_id="...", layer_id="..."))
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    import duckdb

from goatlib.io.pmtiles import PMTilesConfig, PMTilesGenerator
from goatlib.storage import BaseDuckLakeManager
from goatlib.tools.base import ToolSettings

logger = logging.getLogger(__name__)


class SinglePMTileParams(BaseModel):
    """Parameters for single PMTile generation task."""

    user_id: str = Field(
        description="User ID (UUID with dashes)",
    )
    layer_id: str = Field(
        description="Layer ID (UUID with dashes)",
    )
    force: bool = Field(
        default=False,
        description="Regenerate even if PMTiles exist and are in sync",
    )
    show_progress: bool = Field(
        default=True,
        description="Show tippecanoe progress during tile generation",
    )


__all__ = ["SinglePMTileParams", "SinglePMTileTask", "main"]


@dataclass
class SinglePMTileResult:
    """Result of processing a single layer."""

    user_id: str
    layer_id: str
    status: str  # "generated", "in_sync", "skipped", "error"
    message: str = ""
    size_bytes: int = 0

    def to_dict(self: Self) -> dict:
        """Convert to dictionary for Windmill output."""
        return {
            "user_id": self.user_id,
            "layer_id": self.layer_id,
            "status": self.status,
            "message": self.message,
            "size_bytes": self.size_bytes,
        }


class SinglePMTileTask:
    """Generate PMTiles for a single DuckLake layer.

    This task is designed to be called in parallel by multiple workers.
    Each invocation processes exactly one layer.

    Example (Windmill):
        def main(params: SinglePMTileParams) -> dict:
            task = SinglePMTileTask()
            task.init_from_env()
            return task.run(params)
    """

    def __init__(self: Self) -> None:
        """Initialize the single PMTile task."""
        self.settings: ToolSettings | None = None
        self._manager: BaseDuckLakeManager | None = None
        self._generator: PMTilesGenerator | None = None

    @staticmethod
    def _configure_logging_for_windmill() -> None:
        """Configure Python logging to output to stdout for Windmill."""
        import sys

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(handler)

    def init_from_env(self: Self) -> None:
        """Initialize settings from environment variables and Windmill secrets."""
        self._configure_logging_for_windmill()
        self.settings = ToolSettings.from_env()

    def _get_manager(self: Self) -> BaseDuckLakeManager:
        """Get or create DuckLake manager."""
        if self._manager is None:
            if not self.settings:
                raise RuntimeError("Call init_from_env() before running task")
            self._manager = BaseDuckLakeManager(read_only=True)
            self._manager.init_from_params(
                postgres_uri=self.settings.ducklake_postgres_uri,
                storage_path=self.settings.ducklake_data_dir,
                catalog_schema=self.settings.ducklake_catalog_schema,
            )
        return self._manager

    def _get_generator(self: Self) -> PMTilesGenerator:
        """Get or create PMTiles generator."""
        if self._generator is None:
            if not self.settings:
                raise RuntimeError("Call init_from_env() before running task")
            config = PMTilesConfig(enabled=True)
            self._generator = PMTilesGenerator(self.settings.tiles_data_dir, config)
        return self._generator

    def close(self: Self) -> None:
        """Close connections and cleanup resources."""
        if self._manager is not None:
            self._manager.close()
            self._manager = None

    def _attach_postgres(self: Self, con: "duckdb.DuckDBPyConnection") -> None:
        """Attach PostgreSQL as 'pg' for querying catalog tables."""
        if not self.settings:
            raise RuntimeError("Call init_from_env() before running task")

        from urllib.parse import unquote, urlparse

        parsed = urlparse(self.settings.ducklake_postgres_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        user = unquote(parsed.username or "")
        password = unquote(parsed.password or "")
        dbname = parsed.path.lstrip("/") if parsed.path else ""

        libpq_str = (
            f"host={host} port={port} dbname={dbname} user={user} password={password}"
        )
        con.execute(f"ATTACH '{libpq_str}' AS pg (TYPE postgres, READ_ONLY)")

    def _get_layer_info(
        self: Self, user_id: str, layer_id: str
    ) -> tuple[str, str, int] | None:
        """Get layer geometry column and snapshot from PostgreSQL.

        Returns:
            Tuple of (geometry_column, full_table_name, snapshot_id) or None if not found
        """
        # Convert UUIDs to schema/table names
        user_id_nodash = user_id.replace("-", "")
        layer_id_nodash = layer_id.replace("-", "")
        schema_name = f"user_{user_id_nodash}"
        table_name = f"t_{layer_id_nodash}"

        if not self.settings:
            raise RuntimeError("Call init_from_env() before running task")

        catalog_schema = self.settings.ducklake_catalog_schema

        query = f"""
            SELECT
                c.column_name as geometry_column,
                COALESCE(
                    (SELECT MAX(df.begin_snapshot)
                     FROM pg.{catalog_schema}.ducklake_data_file df
                     WHERE df.table_id = t.id AND df.end_snapshot IS NULL),
                    0
                ) as data_snapshot
            FROM pg.{catalog_schema}.ducklake_table t
            JOIN pg.{catalog_schema}.ducklake_schema s ON t.schema_id = s.id
            JOIN pg.{catalog_schema}.ducklake_column c ON c.table_id = t.id
            WHERE s.schema_name = '{schema_name}'
              AND t.table_name = '{table_name}'
              AND c.data_type IN ('GEOMETRY', 'BLOB')
            LIMIT 1
        """

        manager = self._get_manager()
        with manager.connection() as con:
            self._attach_postgres(con)
            rows = con.execute(query).fetchall()

        if not rows:
            return None

        geometry_column, snapshot_id = rows[0]
        full_table_name = f"lake.{schema_name}.{table_name}"
        return geometry_column, full_table_name, snapshot_id

    def run(self: Self, params: SinglePMTileParams) -> dict:
        """Run the single PMTile generation task.

        Args:
            params: Task parameters with user_id and layer_id

        Returns:
            Dict with generation result for Windmill output
        """
        try:
            logger.info(f"Processing layer {params.layer_id} for user {params.user_id}")

            # Get layer info from PostgreSQL
            layer_info = self._get_layer_info(params.user_id, params.layer_id)
            if not layer_info:
                return SinglePMTileResult(
                    user_id=params.user_id,
                    layer_id=params.layer_id,
                    status="error",
                    message="Layer not found in DuckLake catalog",
                ).to_dict()

            geometry_column, full_table_name, snapshot_id = layer_info
            generator = self._get_generator()
            pmtiles_path = generator.get_pmtiles_path(params.user_id, params.layer_id)

            # Clean up any leftover temp files
            temp_paths = [
                pmtiles_path.parent / f".tmp_{pmtiles_path.name}",
                pmtiles_path.with_suffix(".pmtiles.tmp"),
            ]
            for temp_path in temp_paths:
                if temp_path.exists():
                    logger.debug(f"Cleaning up temp file: {temp_path}")
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass

            # Check if already in sync (unless force)
            if pmtiles_path.exists() and not params.force:
                if not generator.is_pmtiles_valid(pmtiles_path):
                    logger.warning(f"Corrupted PMTiles file, deleting: {pmtiles_path}")
                    pmtiles_path.unlink()
                elif generator.is_pmtiles_in_sync(pmtiles_path, snapshot_id):
                    return SinglePMTileResult(
                        user_id=params.user_id,
                        layer_id=params.layer_id,
                        status="in_sync",
                        message=f"Already in sync (snapshot={snapshot_id})",
                        size_bytes=pmtiles_path.stat().st_size,
                    ).to_dict()

            # Generate PMTiles
            logger.info(f"Generating PMTiles: {full_table_name} -> {pmtiles_path}")
            manager = self._get_manager()
            with manager.connection() as con:
                output = generator.generate_from_table(
                    duckdb_con=con,
                    table_name=full_table_name,
                    user_id=params.user_id,
                    layer_id=params.layer_id,
                    geometry_column=geometry_column,
                    snapshot_id=snapshot_id,
                    show_progress=params.show_progress,
                )

            if output and output.exists():
                size_bytes = output.stat().st_size
                size_mb = size_bytes / 1024 / 1024
                logger.info(f"Generated {size_mb:.1f} MB: {output}")
                return SinglePMTileResult(
                    user_id=params.user_id,
                    layer_id=params.layer_id,
                    status="generated",
                    message=f"Generated {size_mb:.1f} MB",
                    size_bytes=size_bytes,
                ).to_dict()
            else:
                return SinglePMTileResult(
                    user_id=params.user_id,
                    layer_id=params.layer_id,
                    status="error",
                    message="Generation returned None or file not found",
                ).to_dict()

        except Exception as e:
            logger.exception(f"Error generating PMTiles: {e}")
            return SinglePMTileResult(
                user_id=params.user_id,
                layer_id=params.layer_id,
                status="error",
                message=str(e),
            ).to_dict()

        finally:
            self.close()


def main(params: SinglePMTileParams) -> dict:
    """Windmill entry point for single PMTile generation task.

    Args:
        params: Parameters matching SinglePMTileParams schema

    Returns:
        Dict with generation result
    """
    task = SinglePMTileTask()
    task.init_from_env()

    try:
        return task.run(params)
    finally:
        task.close()


# CLI entry point for local testing
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Generate PMTiles for a single layer")
    parser.add_argument("--user-id", type=str, required=True, help="User UUID")
    parser.add_argument("--layer-id", type=str, required=True, help="Layer UUID")
    parser.add_argument(
        "--force", action="store_true", help="Regenerate even if in sync"
    )

    args = parser.parse_args()

    params = SinglePMTileParams(
        user_id=args.user_id,
        layer_id=args.layer_id,
        force=args.force,
    )

    result = main(params)
    print(f"\nResult: {result}")
