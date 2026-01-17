"""Background tasks for Windmill.

This module contains internal background tasks that run as scheduled
Windmill jobs or triggered maintenance operations. These are NOT
user-facing analytics tools.

Tasks include:
- PMTiles synchronization (sync_pmtiles) - sequential processing
- Queue PMTiles sync (queue_pmtiles_sync) - queues parallel jobs
- Sync single PMTile (sync_single_pmtile) - processes one layer
- Future: Thumbnail generation
- Future: Storage cleanup

Usage:
    # Sync tasks to Windmill
    python -m goatlib.tasks.sync_windmill --dry-run
    python -m goatlib.tasks.sync_windmill --token xxx

    # Run task locally (sequential)
    python -m goatlib.tasks.sync_pmtiles --dry-run

    # Queue parallel jobs (via Windmill)
    # Run queue_pmtiles_sync task, it queues sync_single_pmtile jobs
"""

from goatlib.tasks.registry import TASK_REGISTRY, TaskDefinition

# NOTE: Do NOT import task classes here - they have heavy deps that
# aren't available on all workers. Import directly when needed:
#   from goatlib.tasks.sync_pmtiles import PMTilesSyncParams, PMTilesSyncTask
#   from goatlib.tasks.queue_pmtiles_sync import QueuePMTilesSyncParams
#   from goatlib.tasks.sync_single_pmtile import SinglePMTileParams

__all__ = [
    "TASK_REGISTRY",
    "TaskDefinition",
]
