"""Background tasks for Windmill.

This module contains internal background tasks that run as scheduled
Windmill jobs or triggered maintenance operations. These are NOT
user-facing analytics tools.

Tasks include:
- PMTiles synchronization (sync_pmtiles)
- Future: Thumbnail generation
- Future: Storage cleanup

Usage:
    # Sync tasks to Windmill
    python -m goatlib.tasks.sync_windmill --dry-run
    python -m goatlib.tasks.sync_windmill --token xxx

    # Run task locally
    python -m goatlib.tasks.sync_pmtiles --dry-run
"""

from goatlib.tasks.registry import TASK_REGISTRY, TaskDefinition

# NOTE: Do NOT import sync_pmtiles here - it has heavy deps (psycopg, etc.)
# that aren't available on all workers. Import directly when needed:
#   from goatlib.tasks.sync_pmtiles import PMTilesSyncParams, PMTilesSyncTask

__all__ = [
    "TASK_REGISTRY",
    "TaskDefinition",
]
