"""CLI tool to sync goatlib tools to Windmill.

Usage:
    python -m goatlib.tools.sync_windmill
    python -m goatlib.tools.sync_windmill --url http://localhost:8110 --token xxx
    python -m goatlib.tools.sync_windmill --dry-run
"""

import argparse
import logging
import os
import sys
from typing import Any, Self

import httpx

from goatlib.tools.codegen import generate_windmill_script
from goatlib.tools.registry import TOOL_REGISTRY, ToolDefinition

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WindmillSyncer:
    """Sync goatlib tools to Windmill."""

    def __init__(
        self: Self,
        base_url: str,
        token: str,
        workspace: str = "plan4better",
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

    def sync_tool(
        self: Self, tool_def: ToolDefinition, dry_run: bool = False
    ) -> dict[str, Any]:
        """Sync a single tool to Windmill.

        Args:
            tool_def: Tool definition from registry
            dry_run: If True, don't actually sync

        Returns:
            Result dict with path and status
        """
        params_class = tool_def.get_params_class()
        content = generate_windmill_script(tool_def.module_path, params_class)

        if dry_run:
            logger.info(f"[DRY RUN] Would sync: {tool_def.windmill_path}")
            logger.debug(f"Generated script:\n{content}")
            return {"path": tool_def.windmill_path, "status": "dry-run"}

        try:
            # Delete existing script first
            self._delete_script(tool_def.windmill_path)

            # Create new script
            result = self._create_script(
                path=tool_def.windmill_path,
                content=content,
                summary=tool_def.display_name,
                description=tool_def.description or "",
                tag=tool_def.worker_tag,
            )
            logger.info(f"✓ Synced: {tool_def.windmill_path}")
            return result

        except Exception as e:
            logger.error(f"✗ Failed: {tool_def.windmill_path} - {e}")
            return {
                "path": tool_def.windmill_path,
                "status": "failed",
                "error": str(e),
            }

    def sync_all(self: Self, dry_run: bool = False) -> list[dict[str, Any]]:
        """Sync all tools from registry.

        Args:
            dry_run: If True, don't actually sync

        Returns:
            List of result dicts
        """
        logger.info(f"Syncing {len(TOOL_REGISTRY)} tools to {self.base_url}")
        results = []

        for tool_def in TOOL_REGISTRY:
            result = self.sync_tool(tool_def, dry_run=dry_run)
            results.append(result)

        # Summary
        synced = sum(1 for r in results if r["status"] == "synced")
        failed = sum(1 for r in results if r["status"] == "failed")
        logger.info(f"Done: {synced} synced, {failed} failed")

        return results


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sync goatlib tools to Windmill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  WINDMILL_URL        Windmill base URL (default: http://localhost:8110)
  WINDMILL_TOKEN      Windmill API token (required)
  WINDMILL_WORKSPACE  Windmill workspace (default: plan4better)

Examples:
  # Using environment variables
  export WINDMILL_TOKEN=xxx
  python -m goatlib.tools.sync_windmill

  # Using command line args
  python -m goatlib.tools.sync_windmill --url http://windmill:8000 --token xxx

  # Dry run to see what would be synced
  python -m goatlib.tools.sync_windmill --dry-run

  # Sync specific tool
  python -m goatlib.tools.sync_windmill --tool buffer
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
        "--tool",
        help="Sync only a specific tool by name (e.g., buffer, heatmap)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_tools",
        help="List available tools without syncing",
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
    if args.list_tools:
        print(f"\nAvailable tools ({len(TOOL_REGISTRY)}):\n")
        for tool in TOOL_REGISTRY:
            print(f"  {tool.name:20} {tool.windmill_path}")
        return 0

    # Validate token
    if not args.token:
        logger.error(
            "WINDMILL_TOKEN is required. Set via --token or environment variable."
        )
        return 1

    syncer = WindmillSyncer(
        base_url=args.url,
        token=args.token,
        workspace=args.workspace,
    )

    try:
        if args.tool:
            # Find specific tool
            tool_def = next(
                (t for t in TOOL_REGISTRY if t.name == args.tool),
                None,
            )
            if not tool_def:
                logger.error(f"Tool not found: {args.tool}")
                logger.info(
                    "Available tools: " + ", ".join(t.name for t in TOOL_REGISTRY)
                )
                return 1
            results = [syncer.sync_tool(tool_def, dry_run=args.dry_run)]
        else:
            results = syncer.sync_all(dry_run=args.dry_run)

        # Return non-zero if any failed
        failed = sum(1 for r in results if r["status"] == "failed")
        return 1 if failed else 0

    finally:
        syncer.close()


if __name__ == "__main__":
    sys.exit(main())
