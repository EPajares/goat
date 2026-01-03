"""Windmill client for job execution.

This module provides an async wrapper around the official Windmill Python SDK
to execute scripts and manage jobs from FastAPI async handlers.

Windmill Python SDK: https://www.windmill.dev/docs/advanced/clients/python_client
"""

import asyncio
import logging
from functools import partial
from typing import Any, Literal

from wmill import Windmill

from geoapi.config import settings

logger = logging.getLogger(__name__)

# Job status type from Windmill SDK
JobStatus = Literal["RUNNING", "WAITING", "COMPLETED"]


class WindmillError(Exception):
    """Base exception for Windmill client errors."""

    pass


class WindmillJobNotFound(WindmillError):
    """Job not found in Windmill."""

    pass


class WindmillClient:
    """Async wrapper around the official Windmill Python SDK.

    The official wmill SDK is synchronous, so we wrap calls in asyncio.to_thread()
    for compatibility with FastAPI's async handlers.
    """

    def __init__(self):
        """Initialize Windmill client."""
        self._client: Windmill | None = None

    def _get_client(self) -> Windmill:
        """Get or create the Windmill client (lazy initialization)."""
        if self._client is None:
            self._client = Windmill(
                base_url=settings.WINDMILL_URL,
                token=settings.WINDMILL_TOKEN,
                workspace=settings.WINDMILL_WORKSPACE,
            )
        return self._client

    async def _run_sync(self, func, *args, **kwargs) -> Any:
        """Run a synchronous function in a thread pool."""
        return await asyncio.to_thread(partial(func, *args, **kwargs))

    async def run_script_async(
        self,
        script_path: str,
        args: dict[str, Any],
        scheduled_in_secs: int | None = None,
    ) -> str:
        """Run a script asynchronously and return job ID.

        Args:
            script_path: Path to the script (e.g., "f/goat/clip")
            args: Script arguments/inputs
            scheduled_in_secs: Optional delay before execution

        Returns:
            Job ID (UUID string)

        Raises:
            WindmillError: If script execution fails

        Note:
            Worker tags are configured on the script itself during sync,
            not per-job. See create_or_update_script().
        """
        client = self._get_client()

        logger.info(f"Submitting job for script {script_path}")

        try:
            # Build params for the Windmill API
            params: dict[str, Any] = {}
            if scheduled_in_secs:
                params["scheduled_in_secs"] = scheduled_in_secs

            # Use low-level post for consistency
            endpoint = f"/w/{client.workspace}/jobs/run/p/{script_path}"
            response = client.post(
                endpoint, json=args, params=params if params else None
            )
            job_id = response.text

            logger.info(f"Job submitted successfully: {job_id} (script: {script_path})")
            return job_id

        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            raise WindmillError(f"Failed to submit job: {e}") from e

    async def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get job details from Windmill.

        Args:
            job_id: Windmill job ID

        Returns:
            Job details dict from Windmill API

        Raises:
            WindmillJobNotFound: If job doesn't exist
            WindmillError: If API call fails
        """
        client = self._get_client()

        try:
            job = await self._run_sync(client.get_job, job_id)
            return job

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                raise WindmillJobNotFound(f"Job not found: {job_id}") from e
            logger.error(f"Error getting job status: {e}")
            raise WindmillError(f"Failed to get job status: {e}") from e

    async def get_job_status_simple(self, job_id: str) -> JobStatus:
        """Get simple job status (RUNNING, WAITING, or COMPLETED).

        Args:
            job_id: Windmill job ID

        Returns:
            Job status literal

        Raises:
            WindmillJobNotFound: If job doesn't exist
            WindmillError: If API call fails
        """
        client = self._get_client()

        try:
            status = await self._run_sync(client.get_job_status, job_id)
            return status

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                raise WindmillJobNotFound(f"Job not found: {job_id}") from e
            logger.error(f"Error getting job status: {e}")
            raise WindmillError(f"Failed to get job status: {e}") from e

    async def get_job_result(self, job_id: str) -> Any:
        """Get job result from Windmill.

        Args:
            job_id: Windmill job ID

        Returns:
            Job result (dict, list, or primitive)

        Raises:
            WindmillJobNotFound: If job doesn't exist
            WindmillError: If job hasn't completed or API call fails
        """
        client = self._get_client()

        try:
            result = await self._run_sync(
                client.get_result,
                job_id,
                assert_result_is_not_none=False,
            )
            return result

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                raise WindmillJobNotFound(f"Job not found: {job_id}") from e
            logger.error(f"Error getting job result: {e}")
            raise WindmillError(f"Failed to get job result: {e}") from e

    async def wait_for_job(
        self,
        job_id: str,
        timeout: float | None = None,
        verbose: bool = False,
    ) -> Any:
        """Wait for a job to complete and return its result.

        Args:
            job_id: Windmill job ID
            timeout: Optional timeout in seconds
            verbose: Whether to print progress

        Returns:
            Job result

        Raises:
            WindmillJobNotFound: If job doesn't exist
            WindmillError: If API call fails or timeout
        """
        client = self._get_client()

        try:
            result = await self._run_sync(
                client.wait_job,
                job_id,
                timeout=timeout,
                verbose=verbose,
                assert_result_is_not_none=False,
            )
            return result

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                raise WindmillJobNotFound(f"Job not found: {job_id}") from e
            logger.error(f"Error waiting for job: {e}")
            raise WindmillError(f"Failed to wait for job: {e}") from e

    async def cancel_job(
        self, job_id: str, reason: str = "User requested cancellation"
    ) -> str:
        """Cancel a running job.

        Args:
            job_id: Windmill job ID
            reason: Cancellation reason

        Returns:
            Response message from Windmill

        Raises:
            WindmillJobNotFound: If job doesn't exist
            WindmillError: If API call fails
        """
        client = self._get_client()

        try:
            response = await self._run_sync(client.cancel_job, job_id, reason)
            logger.info(f"Job {job_id} cancelled: {reason}")
            return response

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                raise WindmillJobNotFound(f"Job not found: {job_id}") from e
            logger.error(f"Error cancelling job: {e}")
            raise WindmillError(f"Failed to cancel job: {e}") from e

    async def run_script_sync(
        self,
        script_path: str,
        args: dict[str, Any],
        timeout: float | None = None,
    ) -> Any:
        """Run a script synchronously and wait for the result.

        Args:
            script_path: Path to the script (e.g., "f/goat/clip")
            args: Script arguments/inputs
            timeout: Optional timeout in seconds

        Returns:
            Script execution result

        Raises:
            WindmillError: If script execution fails
        """
        client = self._get_client()

        logger.info(f"Running script synchronously: {script_path}")

        try:
            result = await self._run_sync(
                client.run_script_by_path,
                path=script_path,
                args=args,
                timeout=timeout,
                assert_result_is_not_none=False,
            )
            logger.info(f"Script completed: {script_path}")
            return result

        except Exception as e:
            logger.error(f"Error running script: {e}")
            raise WindmillError(f"Failed to run script: {e}") from e

    async def whoami(self) -> dict[str, Any]:
        """Get current user info.

        Returns:
            User info dict

        Raises:
            WindmillError: If API call fails
        """
        client = self._get_client()

        try:
            return await self._run_sync(client.whoami)
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise WindmillError(f"Failed to get user info: {e}") from e

    async def list_jobs(
        self,
        running: bool | None = None,
        script_path: str | None = None,
        success: bool | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List jobs from Windmill.

        Note: The official SDK doesn't expose list_jobs directly, so we use
        the underlying HTTP client.

        Args:
            running: Filter by running state
            script_path: Filter by script path (exact match)
            success: Filter by success state
            limit: Maximum results

        Returns:
            List of job dicts

        Raises:
            WindmillError: If API call fails
        """
        client = self._get_client()

        # Build query params
        params: dict[str, Any] = {"per_page": limit}
        if running is not None:
            params["running"] = str(running).lower()
        if script_path is not None:
            params["script_path_exact"] = script_path
        if success is not None:
            params["success"] = str(success).lower()

        try:
            # Use workspace-scoped endpoint: /w/{workspace}/jobs/list
            response = await self._run_sync(
                client.get,
                f"/w/{settings.WINDMILL_WORKSPACE}/jobs/list",
                params=params,
            )
            return response.json()

        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            raise WindmillError(f"Failed to list jobs: {e}") from e

    async def close(self) -> None:
        """Close the client.

        The underlying httpx.Client handles cleanup automatically,
        but we provide this method for compatibility.
        """
        if self._client is not None:
            # The SDK's client property is an httpx.Client, close it
            try:
                self._client.client.close()
            except Exception:
                pass  # Ignore cleanup errors
            self._client = None

    async def create_or_update_script(
        self,
        path: str,
        content: str,
        summary: str = "",
        description: str = "",
        language: str = "python3",
        tag: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a script in Windmill.

        Args:
            path: Script path (e.g., "f/goat/buffer")
            content: Python script content
            summary: Short summary
            description: Full description
            language: Script language (default: python3)
            tag: Worker tag for job routing (e.g., "tools", "print")

        Returns:
            Script info dict

        Raises:
            WindmillError: If API call fails
        """
        client = self._get_client()
        workspace = settings.WINDMILL_WORKSPACE

        # Delete existing script first (POST not DELETE per Windmill API)
        try:
            await self._run_sync(
                client.client.post,
                f"{settings.WINDMILL_URL}/api/w/{workspace}/scripts/delete/p/{path}",
                headers={"Authorization": f"Bearer {settings.WINDMILL_TOKEN}"},
            )
            logger.info(f"Deleted existing script: {path}")
        except Exception:
            pass  # Script might not exist

        script_data = {
            "path": path,
            "content": content,
            "summary": summary,
            "description": description,
            "language": language,
        }
        if tag:
            script_data["tag"] = tag

        try:
            response = await self._run_sync(
                client.client.post,
                f"{settings.WINDMILL_URL}/api/w/{workspace}/scripts/create",
                json=script_data,
                headers={"Authorization": f"Bearer {settings.WINDMILL_TOKEN}"},
            )

            response.raise_for_status()
            logger.info(f"Script synced: {path}")
            return {"path": path, "status": "synced"}

        except Exception as e:
            logger.error(f"Error syncing script {path}: {e}")
            raise WindmillError(f"Failed to sync script: {e}") from e

    async def set_workspace_env_var(self, name: str, value: str) -> None:
        """Set a workspace-level environment variable in Windmill.

        These variables are available to all scripts in the workspace.

        Args:
            name: Environment variable name
            value: Environment variable value

        Raises:
            WindmillError: If API call fails
        """
        client = self._get_client()
        workspace = settings.WINDMILL_WORKSPACE

        try:
            response = await self._run_sync(
                client.client.post,
                f"{settings.WINDMILL_URL}/api/w/{workspace}/workspaces/set_environment_variable",
                json={"name": name, "value": value},
                headers={"Authorization": f"Bearer {settings.WINDMILL_TOKEN}"},
            )
            response.raise_for_status()
            logger.debug(f"Set workspace env var: {name}")
        except Exception as e:
            logger.warning(f"Failed to set env var {name}: {e}")
            # Don't raise - env vars may already exist or be set differently

    async def create_or_update_secret(
        self, name: str, value: str, description: str = ""
    ) -> None:
        """Create or update a secret in Windmill.

        Secrets are encrypted and can have access permissions.
        Scripts access them via wmill.get_variable() or $var: syntax.

        Args:
            name: Secret name (will be stored at f/goat/{name})
            value: Secret value
            description: Optional description

        Raises:
            WindmillError: If API call fails
        """
        client = self._get_client()
        workspace = settings.WINDMILL_WORKSPACE
        path = f"f/goat/{name}"

        # Try to update first, then create if not exists
        try:
            # Check if exists
            response = await self._run_sync(
                client.client.get,
                f"{settings.WINDMILL_URL}/api/w/{workspace}/variables/exists/{path}",
                headers={"Authorization": f"Bearer {settings.WINDMILL_TOKEN}"},
            )
            exists = response.json()

            if exists:
                # Update existing
                response = await self._run_sync(
                    client.client.post,
                    f"{settings.WINDMILL_URL}/api/w/{workspace}/variables/update/{path}",
                    json={"value": value},
                    headers={"Authorization": f"Bearer {settings.WINDMILL_TOKEN}"},
                )
            else:
                # Create new
                response = await self._run_sync(
                    client.client.post,
                    f"{settings.WINDMILL_URL}/api/w/{workspace}/variables/create",
                    json={
                        "path": path,
                        "value": value,
                        "is_secret": True,
                        "description": description or f"GOAT tool secret: {name}",
                    },
                    headers={"Authorization": f"Bearer {settings.WINDMILL_TOKEN}"},
                )

            response.raise_for_status()
            logger.debug(f"Set secret: {path}")
        except Exception as e:
            logger.warning(f"Failed to set secret {name}: {e}")

    async def _configure_workspace_env_vars(self) -> None:
        """Configure required environment variables and secrets for goatlib tools.

        - Non-sensitive config → workspace environment variables
        - Passwords and keys → Windmill secrets (encrypted)
        """
        # Non-sensitive config as environment variables
        env_vars = {
            "POSTGRES_SERVER": settings.POSTGRES_SERVER,
            "POSTGRES_PORT": str(settings.POSTGRES_PORT),
            "POSTGRES_USER": settings.POSTGRES_USER,
            "POSTGRES_DB": settings.POSTGRES_DB,
            "DUCKLAKE_CATALOG_SCHEMA": settings.DUCKLAKE_CATALOG_SCHEMA,
            "DUCKLAKE_DATA_DIR": settings.DUCKLAKE_DATA_DIR,
            "CUSTOMER_SCHEMA": settings.CUSTOMER_SCHEMA,
            # Print worker settings
            "PRINT_BASE_URL": settings.PRINT_BASE_URL,
            "PLAYWRIGHT_BROWSERS_PATH": "/ms-playwright",  # Match Dockerfile location
        }

        # Optional non-sensitive S3 settings
        if settings.S3_PROVIDER:
            env_vars["S3_PROVIDER"] = settings.S3_PROVIDER
        if settings.S3_ENDPOINT_URL:
            env_vars["S3_ENDPOINT_URL"] = settings.S3_ENDPOINT_URL
        if settings.S3_REGION_NAME:
            env_vars["S3_REGION_NAME"] = settings.S3_REGION_NAME
        if settings.S3_BUCKET_NAME:
            env_vars["S3_BUCKET_NAME"] = settings.S3_BUCKET_NAME

        logger.info(f"Configuring {len(env_vars)} workspace environment variables")
        for name, value in env_vars.items():
            await self.set_workspace_env_var(name, value)

        # Sensitive values as secrets
        secrets = {
            "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD,
            "POSTGRES_DATABASE_URI": settings.POSTGRES_DATABASE_URI,
        }

        # Optional sensitive S3 settings
        if settings.S3_ACCESS_KEY_ID:
            secrets["S3_ACCESS_KEY_ID"] = settings.S3_ACCESS_KEY_ID
        if settings.S3_SECRET_ACCESS_KEY:
            secrets["S3_SECRET_ACCESS_KEY"] = settings.S3_SECRET_ACCESS_KEY

        logger.info(f"Configuring {len(secrets)} workspace secrets")
        for name, value in secrets.items():
            await self.create_or_update_secret(name, value)

        logger.info("Workspace configuration complete")

    async def sync_goatlib_tools(self) -> list[dict[str, Any]]:
        """Sync all goatlib tools to Windmill.

        Auto-generates scripts from goatlib tool modules.
        Extracts Pydantic fields to create typed function signatures that Windmill can parse.
        Also configures required environment variables in the workspace.

        Returns:
            List of synced script info dicts
        """
        from goatlib.tools import generate_windmill_script
        from goatlib.tools.registry import TOOL_REGISTRY

        # First, configure required environment variables
        await self._configure_workspace_env_vars()

        results = []
        for tool_def in TOOL_REGISTRY:
            params_class = tool_def.get_params_class()
            content = generate_windmill_script(tool_def.module_path, params_class)
            try:
                result = await self.create_or_update_script(
                    path=tool_def.windmill_path,
                    content=content,
                    summary=tool_def.display_name,
                    description=tool_def.description,
                    tag=tool_def.worker_tag,
                )
                results.append(result)
            except WindmillError as e:
                logger.warning(f"Failed to sync {tool_def.windmill_path}: {e}")
                results.append(
                    {
                        "path": tool_def.windmill_path,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results

    async def list_jobs_filtered(
        self,
        user_id: str,
        script_path_start: str = "f/goat/",
        created_after_days: int = 3,
        process_id: str | None = None,
        success: bool | None = None,
        running: bool | None = None,
        limit: int = 100,
        include_results: bool = True,
    ) -> list[dict[str, Any]]:
        """List jobs from Windmill with efficient filtering.

        Uses indexed filters (script_path_start, created_after) before
        applying args filter for user_id.

        Args:
            user_id: User ID to filter by (in args)
            script_path_start: Script path prefix filter (default: f/goat/)
            created_after_days: Only return jobs from last N days (default: 3)
            process_id: Optional specific process ID to filter
            success: Filter by success state (True/False/None)
            running: Filter by running state (True/False/None)
            limit: Maximum results (max 100)
            include_results: Fetch results for successful jobs (default: True)

        Returns:
            List of job dicts from Windmill

        Raises:
            WindmillError: If API call fails
        """
        import asyncio

        client = self._get_client()
        workspace = settings.WINDMILL_WORKSPACE

        # Calculate created_after timestamp
        from datetime import datetime, timedelta, timezone

        created_after = datetime.now(timezone.utc) - timedelta(days=created_after_days)
        created_after_iso = created_after.isoformat()

        # Build query params - use indexed filters first
        params: dict[str, Any] = {
            "per_page": min(limit, 100),  # Windmill max is 100
            "script_path_start": script_path_start
            if not process_id
            else f"f/goat/{process_id}",
            "created_after": created_after_iso,
            "has_null_parent": "true",  # Only root jobs, not flow steps
            "job_kinds": "script",  # Only script jobs
            "args": f'{{"user_id": "{user_id}"}}',  # JSON subset filter
        }

        # Add optional filters
        if success is not None:
            params["success"] = str(success).lower()
        if running is not None:
            params["running"] = str(running).lower()

        try:
            response = await self._run_sync(
                client.client.get,
                f"{settings.WINDMILL_URL}/api/w/{workspace}/jobs/list",
                params=params,
                headers={"Authorization": f"Bearer {settings.WINDMILL_TOKEN}"},
            )
            response.raise_for_status()
            jobs = response.json()

            # Windmill's /jobs/list returns limited fields
            # Fetch full details for jobs that need args/results
            if include_results:
                # Jobs that need full details (args for filtering, results for download)
                jobs_needing_details = [
                    j
                    for j in jobs
                    if j.get("script_path", "").endswith(
                        ("layer_export", "print_report")
                    )
                ]
                if jobs_needing_details:

                    async def fetch_job_details(job: dict[str, Any]) -> None:
                        try:
                            full_job = await self.get_job_status(job["id"])
                            # Merge full job details into the list item
                            job["args"] = full_job.get("args")
                            if full_job.get("success") is True:
                                job["result"] = full_job.get("result")
                        except Exception as e:
                            logger.warning(
                                f"Failed to fetch details for job {job['id']}: {e}"
                            )

                    await asyncio.gather(
                        *[fetch_job_details(job) for job in jobs_needing_details],
                        return_exceptions=True,
                    )

            return jobs

        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            raise WindmillError(f"Failed to list jobs: {e}") from e

    async def get_job_with_result(self, job_id: str) -> dict[str, Any]:
        """Get job details including result if completed.

        Args:
            job_id: Windmill job ID

        Returns:
            Job dict with 'result' field populated if job completed

        Raises:
            WindmillJobNotFound: If job doesn't exist
            WindmillError: If API call fails
        """
        # Get job status first
        job = await self.get_job_status(job_id)

        # If job completed successfully, fetch the result
        if job.get("success") is True:
            try:
                job["result"] = await self.get_job_result(job_id)
            except Exception as e:
                logger.warning(f"Failed to fetch result for job {job_id}: {e}")

        return job


# Global client instance
windmill_client = WindmillClient()
