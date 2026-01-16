"""CLI tool to sync goatlib tasks to Windmill.

Usage:
    python -m goatlib.tasks.sync_windmill
    python -m goatlib.tasks.sync_windmill --url http://localhost:8110 --token xxx
    python -m goatlib.tasks.sync_windmill --dry-run
"""

import argparse
import logging
import os
import sys
from typing import Any, Self

import httpx

from goatlib.tasks.registry import TASK_REGISTRY, TaskDefinition

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_task_script(task_def: TaskDefinition) -> str:
    """Generate a Windmill script for a task.

    Uses the same codegen as tools - expands Pydantic fields into primitive
    function arguments (str, int, bool, etc.) so Windmill can parse them
    without needing pydantic or goatlib installed on the server.
    """
    from goatlib.tools.codegen import generate_windmill_script

    params_class = task_def.get_params_class()
    return generate_windmill_script(
        module_path=task_def.module_path,
        params_class=params_class,
        excluded_fields=set(),  # Tasks don't have hidden fields like tools do
    )


class WindmillTaskSyncer:
    """Sync goatlib tasks to Windmill."""

    def __init__(
        self: Self,
        base_url: str,
        token: str,
        workspace: str = "goat",
    ) -> None:
        """Initialize syncer.

        Args:
            base_url: Windmill base URL (e.g., http://localhost:8110)
            token: Windmill API token
            workspace: Windmill workspace name
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.workspace = workspace
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    def close(self: Self) -> None:
        """Close HTTP client."""
        self.client.close()

    def _delete_script(self: Self, path: str) -> bool:
        """Delete existing script if it exists."""
        try:
            self.client.post(
                f"{self.base_url}/api/w/{self.workspace}/scripts/delete/p/{path}"
            )
            return True
        except Exception:
            return False

    def _create_script(
        self: Self,
        path: str,
        content: str,
        summary: str,
        description: str,
        tag: str | None = None,
    ) -> dict[str, Any]:
        """Create a script in Windmill."""
        script_data: dict[str, Any] = {
            "path": path,
            "content": content,
            "summary": summary,
            "description": description,
            "language": "python3",
        }
        if tag:
            script_data["tag"] = tag

        response = self.client.post(
            f"{self.base_url}/api/w/{self.workspace}/scripts/create",
            json=script_data,
        )
        response.raise_for_status()
        return {"path": path, "status": "synced"}

    def _create_or_update_schedule(
        self: Self, task_def: TaskDefinition
    ) -> dict[str, Any] | None:
        """Create or update schedule for a task if it has one defined."""
        if not task_def.schedule:
            return None

        schedule_path = f"f/goat/schedules/{task_def.name}"

        schedule_data = {
            "path": schedule_path,
            "schedule": task_def.schedule,
            "script_path": task_def.windmill_path,
            "is_flow": False,
            "args": {},  # Default args (empty = use defaults)
            "enabled": True,
            "timezone": "UTC",
        }

        try:
            # Try to update existing
            response = self.client.post(
                f"{self.base_url}/api/w/{self.workspace}/schedules/update/{schedule_path}",
                json=schedule_data,
            )
            if response.status_code == 404:
                # Create new
                response = self.client.post(
                    f"{self.base_url}/api/w/{self.workspace}/schedules/create",
                    json=schedule_data,
                )
            response.raise_for_status()
            return {"path": schedule_path, "schedule": task_def.schedule}
        except Exception as e:
            logger.warning(f"Could not create schedule for {task_def.name}: {e}")
            return None

    def sync_task(
        self: Self, task_def: TaskDefinition, dry_run: bool = False
    ) -> dict[str, Any]:
        """Sync a single task to Windmill.

        Args:
            task_def: Task definition from registry
            dry_run: If True, don't actually sync

        Returns:
            Result dict with path and status
        """
        content = generate_task_script(task_def)

        if dry_run:
            logger.info(f"[DRY RUN] Would sync: {task_def.windmill_path}")
            if task_def.schedule:
                logger.info(f"[DRY RUN] Would create schedule: {task_def.schedule}")
            logger.debug(f"Generated script:\n{content}")
            return {"path": task_def.windmill_path, "status": "dry-run"}

        try:
            # Delete existing script first
            self._delete_script(task_def.windmill_path)

            # Create new script
            result = self._create_script(
                path=task_def.windmill_path,
                content=content,
                summary=task_def.display_name,
                description=task_def.description or "",
                tag=task_def.worker_tag,
            )
            logger.info(f"✓ Synced: {task_def.windmill_path}")

            # Create schedule if defined
            if task_def.schedule:
                schedule_result = self._create_or_update_schedule(task_def)
                if schedule_result:
                    logger.info(
                        f"✓ Schedule: {schedule_result['path']} "
                        f"({schedule_result['schedule']})"
                    )
                    result["schedule"] = schedule_result

            return result

        except Exception as e:
            logger.error(f"✗ Failed: {task_def.windmill_path} - {e}")
            return {
                "path": task_def.windmill_path,
                "status": "failed",
                "error": str(e),
            }

    def sync_all(self: Self, dry_run: bool = False) -> list[dict[str, Any]]:
        """Sync all tasks from registry.

        Args:
            dry_run: If True, don't actually sync

        Returns:
            List of result dicts
        """
        logger.info(f"Syncing {len(TASK_REGISTRY)} tasks to {self.base_url}")
        results = []

        for task_def in TASK_REGISTRY:
            result = self.sync_task(task_def, dry_run=dry_run)
            results.append(result)

        # Summary
        synced = sum(1 for r in results if r["status"] == "synced")
        failed = sum(1 for r in results if r["status"] == "failed")
        logger.info(f"Done: {synced} synced, {failed} failed")

        return results


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sync goatlib tasks to Windmill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  WINDMILL_URL        Windmill base URL (default: http://localhost:8110)
  WINDMILL_TOKEN      Windmill API token (required)
  WINDMILL_WORKSPACE  Windmill workspace (default: plan4better)

Examples:
  # Using environment variables
  export WINDMILL_TOKEN=xxx
  python -m goatlib.tasks.sync_windmill

  # Using command line args
  python -m goatlib.tasks.sync_windmill --url http://windmill:8000 --token xxx

  # Dry run to see what would be synced
  python -m goatlib.tasks.sync_windmill --dry-run

  # Sync specific task
  python -m goatlib.tasks.sync_windmill --task sync_pmtiles
""",
    )

    parser.add_argument(
        "--url",
        default=os.getenv("WINDMILL_URL", "http://localhost:8110"),
        help="Windmill base URL",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("WINDMILL_TOKEN"),
        help="Windmill API token",
    )
    parser.add_argument(
        "--workspace",
        default=os.getenv("WINDMILL_WORKSPACE", "plan4better"),
        help="Windmill workspace",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )
    parser.add_argument(
        "--task",
        help="Sync only a specific task by name (e.g., sync_pmtiles)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_tasks",
        help="List available tasks without syncing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # List mode
    if args.list_tasks:
        print(f"\nAvailable tasks ({len(TASK_REGISTRY)}):\n")
        for task in TASK_REGISTRY:
            schedule_str = f" (schedule: {task.schedule})" if task.schedule else ""
            print(f"  {task.name:20} {task.windmill_path}{schedule_str}")
        return 0

    # Validate token
    if not args.token:
        logger.error(
            "WINDMILL_TOKEN is required. Set via --token or environment variable."
        )
        return 1

    syncer = WindmillTaskSyncer(
        base_url=args.url,
        token=args.token,
        workspace=args.workspace,
    )

    try:
        if args.task:
            # Find specific task
            task_def = next(
                (t for t in TASK_REGISTRY if t.name == args.task),
                None,
            )
            if not task_def:
                logger.error(f"Task not found: {args.task}")
                logger.info(
                    "Available tasks: " + ", ".join(t.name for t in TASK_REGISTRY)
                )
                return 1
            results = [syncer.sync_task(task_def, dry_run=args.dry_run)]
        else:
            results = syncer.sync_all(dry_run=args.dry_run)

        # Return non-zero if any failed
        failed = sum(1 for r in results if r["status"] == "failed")
        return 1 if failed else 0

    finally:
        syncer.close()


if __name__ == "__main__":
    sys.exit(main())
