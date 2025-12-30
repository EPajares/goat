"""Redis-based job state manager for tracking running jobs.

This module provides a simple Redis-based state manager for tracking
jobs that are in-progress (accepted, running) before they're persisted
to PostgreSQL upon completion.

Jobs flow:
1. ogc_execute_step creates job in Redis with status=accepted
2. process_analysis_step updates job to status=running
3. log_job_status_step persists to PostgreSQL and deletes from Redis
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from lib.config import get_settings

# Redis key prefix for job state
JOB_KEY_PREFIX = "ogc:job:"
JOB_INDEX_KEY = "ogc:jobs"  # Set of all job IDs


class JobStateManager:
    """Manages job state in Redis for in-progress jobs."""

    _instance: Optional["JobStateManager"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls) -> "JobStateManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            settings = get_settings()
            self._client = redis.Redis(
                host=settings.MOTIA_REDIS_HOST,
                port=settings.MOTIA_REDIS_PORT,
                decode_responses=True,
            )
        return self._client

    async def create_job(
        self,
        job_id: str,
        user_id: str,
        process_id: str,
        status: str = "accepted",
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new job in Redis.

        Args:
            job_id: Unique job identifier
            user_id: User who submitted the job
            process_id: Process/tool being executed
            status: Initial status (default: accepted)
            inputs: Input parameters for the job

        Returns:
            Job data dict
        """
        client = await self._get_client()
        now = datetime.now(timezone.utc).isoformat()

        job_data = {
            "job_id": job_id,
            "user_id": user_id,
            "process_id": process_id,
            "status": status,
            "created": now,
            "updated": now,
            "inputs": inputs or {},
        }

        key = f"{JOB_KEY_PREFIX}{job_id}"
        await client.set(key, json.dumps(job_data))
        await client.sadd(JOB_INDEX_KEY, job_id)

        # Set TTL of 1 hour for jobs (in case they never complete)
        await client.expire(key, 3600)

        return job_data

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        message: Optional[str] = None,
        progress: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update job status in Redis.

        Args:
            job_id: Job identifier
            status: New status
            message: Optional status message
            progress: Optional progress percentage (0-100)

        Returns:
            Updated job data or None if job not found
        """
        client = await self._get_client()
        key = f"{JOB_KEY_PREFIX}{job_id}"

        data = await client.get(key)
        if not data:
            return None

        job_data = json.loads(data)
        job_data["status"] = status
        job_data["updated"] = datetime.now(timezone.utc).isoformat()

        if message:
            job_data["message"] = message
        if progress is not None:
            job_data["progress"] = progress

        await client.set(key, json.dumps(job_data))
        return job_data

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data from Redis.

        Args:
            job_id: Job identifier

        Returns:
            Job data dict or None if not found
        """
        client = await self._get_client()
        key = f"{JOB_KEY_PREFIX}{job_id}"

        data = await client.get(key)
        if not data:
            return None

        return json.loads(data)

    async def delete_job(self, job_id: str) -> bool:
        """Delete job from Redis.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        client = await self._get_client()
        key = f"{JOB_KEY_PREFIX}{job_id}"

        deleted = await client.delete(key)
        await client.srem(JOB_INDEX_KEY, job_id)

        return deleted > 0

    async def list_jobs(
        self,
        status: Optional[str] = None,
        process_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List jobs from Redis with optional filtering.

        Args:
            status: Filter by status
            process_id: Filter by process ID
            user_id: Filter by user ID
            limit: Maximum number of jobs to return
            offset: Offset for pagination

        Returns:
            List of job data dicts
        """
        client = await self._get_client()

        # Get all job IDs
        job_ids = await client.smembers(JOB_INDEX_KEY)

        jobs = []
        for job_id in job_ids:
            job_data = await self.get_job(job_id)
            if not job_data:
                # Clean up orphaned index entry
                await client.srem(JOB_INDEX_KEY, job_id)
                continue

            # Apply filters
            if status and job_data.get("status") != status:
                continue
            if process_id and job_data.get("process_id") != process_id:
                continue
            if user_id and job_data.get("user_id") != user_id:
                continue

            jobs.append(job_data)

        # Sort by created time (newest first)
        jobs.sort(key=lambda x: x.get("created", ""), reverse=True)

        # Apply pagination
        return jobs[offset : offset + limit]

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Singleton instance
job_state_manager = JobStateManager()
