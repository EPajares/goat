"""Queue PMTiles sync jobs for parallel processing.

This task scans DuckLake for layers needing PMTiles generation and queues
individual jobs for each layer. Jobs are picked up by available workers.

Architecture:
    1. This task (queue_pmtiles_sync) runs on any worker
    2. It queries PostgreSQL for layers needing sync
    3. For each layer, it queues a sync_single_pmtile job
    4. Workers pick up jobs from the queue and process in parallel

Usage as Windmill script:
    # Called by Windmill with QueuePMTilesSyncParams

Usage as library:
    from goatlib.tasks.queue_pmtiles_sync import QueuePMTilesSyncTask

    task = QueuePMTilesSyncTask()
    task.init_from_env()
    result = task.run(QueuePMTilesSyncParams(limit=100))
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


class QueuePMTilesSyncParams(BaseModel):
    """Parameters for queue PMTiles sync task."""

    user_id: str | None = Field(
        default=None,
        description="Process only layers for this user (UUID with dashes)",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of jobs to queue",
    )
    force: bool = Field(
        default=False,
        description="Queue jobs even for layers that are in sync",
    )
    missing_only: bool = Field(
        default=False,
        description="Only queue jobs for missing PMTiles, skip stale ones",
    )
    small_first: bool = Field(
        default=True,
        description="Process smaller layers first (default: True)",
    )
    dry_run: bool = Field(
        default=False,
        description="Show what would be queued without actually queuing",
    )


__all__ = ["QueuePMTilesSyncParams", "QueuePMTilesSyncTask", "main"]


@dataclass
class LayerInfo:
    """Information about a DuckLake layer with geometry."""

    schema_name: str
    table_name: str
    user_id: str
    layer_id: str
    geometry_column: str
    snapshot_id: int
    size_bytes: int = 0


@dataclass
class QueueResult:
    """Result of the queue operation."""

    total_layers: int = 0
    in_sync: int = 0
    missing: int = 0
    stale: int = 0
    queued: int = 0
    skipped: int = 0
    job_ids: list[str] | None = None

    def to_dict(self: Self) -> dict:
        """Convert to dictionary for Windmill output."""
        result = {
            "total_layers": self.total_layers,
            "in_sync": self.in_sync,
            "missing": self.missing,
            "stale": self.stale,
            "queued": self.queued,
            "skipped": self.skipped,
        }
        if self.job_ids:
            result["job_ids"] = self.job_ids
        return result


class QueuePMTilesSyncTask:
    """Queue PMTiles sync jobs for parallel processing.

    This task scans DuckLake for layers needing PMTiles generation and
    queues individual jobs for each layer to be processed by workers.

    Example (Windmill):
        def main(params: QueuePMTilesSyncParams) -> dict:
            task = QueuePMTilesSyncTask()
            task.init_from_env()
            return task.run(params)
    """

    def __init__(self: Self) -> None:
        """Initialize the queue task."""
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

    def get_geometry_layers(
        self: Self,
        user_id: str | None = None,
        limit: int | None = None,
        order_by_size: bool = False,
    ) -> list[LayerInfo]:
        """Get all DuckLake tables with geometry columns."""
        if not self.settings:
            raise RuntimeError("Call init_from_env() before running task")

        catalog_schema = self.settings.ducklake_catalog_schema

        user_filter = ""
        if user_id:
            user_schema = f"user_{user_id.replace('-', '')}"
            user_filter = f"AND s.schema_name = '{user_schema}'"

        limit_clause = f"LIMIT {limit}" if limit else ""
        order_clause = (
            "ORDER BY stats.total_size ASC NULLS LAST"
            if order_by_size
            else "ORDER BY s.schema_name, t.table_name"
        )

        query = f"""
            WITH table_stats AS (
                SELECT
                    t.id as table_id,
                    COALESCE(SUM(df.file_size_in_bytes), 0) as total_size,
                    MAX(df.begin_snapshot) as last_data_snapshot
                FROM pg.{catalog_schema}.ducklake_table t
                LEFT JOIN pg.{catalog_schema}.ducklake_data_file df
                    ON df.table_id = t.id AND df.end_snapshot IS NULL
                GROUP BY t.id
            )
            SELECT
                s.schema_name,
                t.table_name,
                c.column_name as geometry_column,
                COALESCE(stats.last_data_snapshot, 0) as data_snapshot,
                stats.total_size
            FROM pg.{catalog_schema}.ducklake_table t
            JOIN pg.{catalog_schema}.ducklake_schema s ON t.schema_id = s.id
            JOIN pg.{catalog_schema}.ducklake_column c ON c.table_id = t.id
            LEFT JOIN table_stats stats ON stats.table_id = t.id
            WHERE c.data_type IN ('GEOMETRY', 'BLOB')
            {user_filter}
            {order_clause}
            {limit_clause}
        """

        manager = self._get_manager()
        with manager.connection() as con:
            self._attach_postgres(con)
            rows = con.execute(query).fetchall()

        if not rows:
            return []

        layers = []
        for (
            schema_name,
            table_name,
            geometry_column,
            data_snapshot,
            total_size,
        ) in rows:
            user_id_nodash = schema_name.replace("user_", "")
            layer_id_nodash = table_name.replace("t_", "")

            # Convert to UUID format (8-4-4-4-12)
            user_id_uuid = (
                f"{user_id_nodash[:8]}-{user_id_nodash[8:12]}-"
                f"{user_id_nodash[12:16]}-{user_id_nodash[16:20]}-{user_id_nodash[20:]}"
            )
            layer_id_uuid = (
                f"{layer_id_nodash[:8]}-{layer_id_nodash[8:12]}-"
                f"{layer_id_nodash[12:16]}-{layer_id_nodash[16:20]}-{layer_id_nodash[20:]}"
            )

            layers.append(
                LayerInfo(
                    schema_name=schema_name,
                    table_name=table_name,
                    user_id=user_id_uuid,
                    layer_id=layer_id_uuid,
                    geometry_column=geometry_column,
                    snapshot_id=data_snapshot,
                    size_bytes=total_size,
                )
            )

        return layers

    def run(self: Self, params: QueuePMTilesSyncParams) -> dict:
        """Run the queue task - scan layers and queue jobs.

        Args:
            params: Task parameters

        Returns:
            Dict with queue statistics for Windmill output
        """
        result = QueueResult()

        try:
            logger.info("Querying geometry layers from PostgreSQL...")
            layers = self.get_geometry_layers(
                user_id=params.user_id,
                limit=None,  # Get all, we'll limit after categorization
                order_by_size=params.small_first,
            )

            result.total_layers = len(layers)
            logger.info(f"Found {len(layers)} geometry layers")

            if not layers:
                logger.info("No layers to process")
                return result.to_dict()

            # Categorize layers
            generator = self._get_generator()
            missing = []
            stale = []
            in_sync = []

            for layer in layers:
                pmtiles_path = generator.get_pmtiles_path(layer.user_id, layer.layer_id)

                if not pmtiles_path.exists():
                    missing.append(layer)
                elif not generator.is_pmtiles_valid(pmtiles_path):
                    # Corrupted - treat as missing
                    logger.warning(f"Corrupted PMTiles: {pmtiles_path}")
                    missing.append(layer)
                elif not generator.is_pmtiles_in_sync(pmtiles_path, layer.snapshot_id):
                    stale.append(layer)
                else:
                    in_sync.append(layer)

            result.in_sync = len(in_sync)
            result.missing = len(missing)
            result.stale = len(stale)

            logger.info(
                f"Status: {result.in_sync} in sync, {result.missing} missing, "
                f"{result.stale} stale"
            )

            # Determine what to queue
            if params.force:
                to_queue = layers
            elif params.missing_only:
                to_queue = missing
                if stale:
                    logger.info(f"Skipping {len(stale)} stale layers (--missing-only)")
                    result.skipped = len(stale)
            else:
                to_queue = missing + stale

            # Apply limit after categorization
            if params.limit and len(to_queue) > params.limit:
                logger.info(f"Limiting to {params.limit} jobs (from {len(to_queue)})")
                result.skipped += len(to_queue) - params.limit
                to_queue = to_queue[: params.limit]

            if not to_queue:
                logger.info("No jobs to queue - all PMTiles are up to date!")
                return result.to_dict()

            if params.dry_run:
                logger.info(f"[DRY RUN] Would queue {len(to_queue)} jobs:")
                for layer in to_queue[:10]:
                    logger.info(f"  - {layer.user_id}/{layer.layer_id}")
                if len(to_queue) > 10:
                    logger.info(f"  ... and {len(to_queue) - 10} more")
                result.queued = len(to_queue)
                return result.to_dict()

            # Queue jobs via Windmill
            import wmill

            job_ids = []
            logger.info(f"Queuing {len(to_queue)} jobs...")

            for i, layer in enumerate(to_queue):
                try:
                    job_id = wmill.run_script_async(
                        path="f/goat/tasks/sync_single_pmtile",
                        args={
                            "user_id": layer.user_id,
                            "layer_id": layer.layer_id,
                            "force": params.force,
                        },
                    )
                    job_ids.append(job_id)

                    if (i + 1) % 100 == 0:
                        logger.info(f"Queued {i + 1}/{len(to_queue)} jobs...")

                except Exception as e:
                    logger.error(f"Failed to queue job for {layer.layer_id}: {e}")

            result.queued = len(job_ids)
            result.job_ids = job_ids[:100]  # Only return first 100 IDs

            logger.info(f"Successfully queued {len(job_ids)} jobs")
            return result.to_dict()

        finally:
            self.close()


def main(params: QueuePMTilesSyncParams) -> dict:
    """Windmill entry point for queue PMTiles sync task.

    Args:
        params: Parameters matching QueuePMTilesSyncParams schema

    Returns:
        Dict with queue statistics
    """
    task = QueuePMTilesSyncTask()
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

    parser = argparse.ArgumentParser(
        description="Queue PMTiles sync jobs for parallel processing"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be queued"
    )
    parser.add_argument("--limit", type=int, help="Maximum jobs to queue")
    parser.add_argument("--user-id", type=str, help="Process only for a specific user")
    parser.add_argument(
        "--force", action="store_true", help="Queue jobs even for in-sync layers"
    )
    parser.add_argument(
        "--missing-only", action="store_true", help="Only queue missing, skip stale"
    )
    parser.add_argument(
        "--small-first", action="store_true", help="Process smaller layers first"
    )

    args = parser.parse_args()

    params = QueuePMTilesSyncParams(
        user_id=args.user_id,
        limit=args.limit,
        force=args.force,
        missing_only=args.missing_only,
        dry_run=args.dry_run,
        small_first=args.small_first,
    )

    result = main(params)
    print(f"\nResult: {result}")
