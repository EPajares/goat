"""Task registry for background/maintenance tasks.

This module provides a registry of all background tasks that can be synced
to Windmill. Tasks are internal operations (not user-facing analytics).

Example:
    from goatlib.tasks.registry import TASK_REGISTRY, TaskDefinition

    for task in TASK_REGISTRY:
        print(f"{task.name}: {task.description}")
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from pydantic import BaseModel


@dataclass(frozen=True)
class TaskDefinition:
    """Definition of a background task for registration.

    Attributes:
        name: Short lowercase name used as task ID (e.g., "sync_pmtiles")
        display_name: Human-readable name (e.g., "Sync PMTiles")
        description: Short description for Windmill
        module_path: Python module path (e.g., "goatlib.tasks.sync_pmtiles")
        params_class_name: Name of the Params class in the module
        windmill_path: Windmill script path (e.g., "f/goat/tasks/sync_pmtiles")
        schedule: Optional cron schedule (e.g., "0 */6 * * *" for every 6 hours)
        worker_tag: Windmill worker tag for job routing
    """

    name: str
    display_name: str
    description: str
    module_path: str
    params_class_name: str
    windmill_path: str
    schedule: str | None = None
    worker_tag: str = "tools"

    def get_params_class(self: Self) -> type["BaseModel"]:
        """Dynamically import and return the params class."""
        import importlib

        module = importlib.import_module(self.module_path)
        return getattr(module, self.params_class_name)


# Central registry of all background tasks
TASK_REGISTRY: tuple[TaskDefinition, ...] = (
    TaskDefinition(
        name="sync_pmtiles",
        display_name="Sync PMTiles",
        description="Synchronize PMTiles for all DuckLake geometry layers",
        module_path="goatlib.tasks.sync_pmtiles",
        params_class_name="PMTilesSyncParams",
        windmill_path="f/goat/tasks/sync_pmtiles",
        schedule=None,  # Run manually
        worker_tag="tools",
    ),
)
