"""Job service for managing jobs in the database.

This service handles job CRUD operations, storing job metadata in the
customer.job table while using Windmill for actual job execution.
"""

import logging
from typing import Any
from uuid import UUID

import asyncpg

from geoapi.config import settings

logger = logging.getLogger(__name__)


# OGC-compliant job status values
class JobStatus:
    """OGC API Processes job status values."""

    ACCEPTED = "accepted"  # Job has been accepted but not started
    RUNNING = "running"  # Job is currently running
    SUCCESSFUL = "successful"  # Job completed successfully
    FAILED = "failed"  # Job failed
    DISMISSED = "dismissed"  # Job was cancelled/dismissed


class JobService:
    """Service for managing jobs in the database."""

    def __init__(self) -> None:
        """Initialize job service."""
        self._pool: asyncpg.Pool | None = None

    async def init(self) -> None:
        """Initialize connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=2,
                max_size=10,
            )
            logger.info("Job service connection pool initialized")

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _get_pool(self) -> asyncpg.Pool:
        """Get connection pool, initializing if needed."""
        if self._pool is None:
            await self.init()
        return self._pool  # type: ignore

    async def create_job(
        self,
        job_id: UUID,
        user_id: UUID,
        job_type: str,
        status: str = JobStatus.ACCEPTED,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new job record.

        Args:
            job_id: Job UUID (from Windmill)
            user_id: User UUID who owns this job
            job_type: Type/process ID (e.g., "clip", "buffer")
            status: Initial status (default: accepted)
            payload: Optional job payload/inputs

        Returns:
            Created job record as dict
        """
        pool = await self._get_pool()

        import json

        payload_json = json.dumps(payload) if payload else None

        query = f"""
            INSERT INTO {settings.CUSTOMER_SCHEMA}.job (id, user_id, type, status, payload, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, NOW(), NOW())
            RETURNING id, user_id, type, status, payload, created_at, updated_at
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                query, job_id, user_id, job_type, status, payload_json
            )

        return dict(row) if row else {}

    async def get_job(
        self, job_id: UUID, user_id: UUID | None = None
    ) -> dict[str, Any] | None:
        """Get a job by ID.

        Args:
            job_id: Job UUID
            user_id: If provided, only return job if owned by this user

        Returns:
            Job record as dict or None if not found
        """
        pool = await self._get_pool()

        if user_id:
            query = f"""
                SELECT id, user_id, type, status, payload, created_at, updated_at
                FROM {settings.CUSTOMER_SCHEMA}.job
                WHERE id = $1 AND user_id = $2
            """
            params = [job_id, user_id]
        else:
            query = f"""
                SELECT id, user_id, type, status, payload, created_at, updated_at
                FROM {settings.CUSTOMER_SCHEMA}.job
                WHERE id = $1
            """
            params = [job_id]

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        return dict(row) if row else None

    async def update_job_status(
        self,
        job_id: UUID,
        status: str,
        user_id: UUID | None = None,
    ) -> dict[str, Any] | None:
        """Update job status.

        Args:
            job_id: Job UUID
            status: New status value
            user_id: If provided, only update if owned by this user

        Returns:
            Updated job record or None if not found
        """
        pool = await self._get_pool()

        if user_id:
            query = f"""
                UPDATE {settings.CUSTOMER_SCHEMA}.job
                SET status = $1, updated_at = NOW()
                WHERE id = $2 AND user_id = $3
                RETURNING id, user_id, type, status, payload, created_at, updated_at
            """
            params = [status, job_id, user_id]
        else:
            query = f"""
                UPDATE {settings.CUSTOMER_SCHEMA}.job
                SET status = $1, updated_at = NOW()
                WHERE id = $2
                RETURNING id, user_id, type, status, payload, created_at, updated_at
            """
            params = [status, job_id]

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        return dict(row) if row else None

    async def list_jobs(
        self,
        user_id: UUID,
        process_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List jobs for a user.

        Args:
            user_id: User UUID to filter by
            process_id: Optional process type to filter by
            status: Optional status to filter by
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of job records
        """
        pool = await self._get_pool()

        conditions = ["user_id = $1"]
        params: list[Any] = [user_id]
        param_idx = 2

        if process_id:
            conditions.append(f"type = ${param_idx}")
            params.append(process_id)
            param_idx += 1

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        params.extend([limit, offset])

        query = f"""
            SELECT id, user_id, type, status, payload, created_at, updated_at
            FROM {settings.CUSTOMER_SCHEMA}.job
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def delete_job(self, job_id: UUID, user_id: UUID) -> bool:
        """Delete a job.

        Args:
            job_id: Job UUID
            user_id: User UUID (must own the job)

        Returns:
            True if deleted, False if not found
        """
        pool = await self._get_pool()

        query = f"""
            DELETE FROM {settings.CUSTOMER_SCHEMA}.job
            WHERE id = $1 AND user_id = $2
            RETURNING id
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, job_id, user_id)

        return row is not None


# Global singleton instance
job_service = JobService()
