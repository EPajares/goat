"""
Log Job Status Step.

Persists final job status to GOAT Core's jobs table.
Subscribes to job.completed and job.failed events emitted by analysis steps.

NOTE: Uses GOAT Core's Job model for database operations.
Motia only defines Pydantic schemas for API validation.
"""

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

from typing import Any, Dict
from uuid import UUID

config = {
    "name": "LogJobStatus",
    "type": "event",
    "description": "Persists job status to GOAT Core jobs table",
    "subscribes": ["job.completed", "job.failed"],
    "emits": [],
    "flows": ["analysis-flow", "layer-flow"],
    "infrastructure": {
        "handler": {
            "timeout": 30  # Short timeout for DB write
        }
    },
}


async def handler(input_data: Dict[str, Any], context):
    """
    Persist final job status to GOAT Core's jobs table.

    Expected input:
    - job_id: str (UUID format)
    - user_id: str (UUID format)
    - tool_name: str (e.g., "clip", "buffer")
    - status: str ("successful", "failed")
    - project_id: str | None
    - scenario_id: str | None
    - result_layer_id: str | None (on success)
    - feature_count: int | None (on success)
    - error_message: str | None (on failure)
    - input_params: dict | None
    """
    job_id = input_data.get("job_id")
    user_id = input_data.get("user_id")
    tool_name = input_data.get("tool_name")
    status = input_data.get("status")

    context.logger.info(
        "Logging job status to GOAT Core",
        {
            "job_id": job_id,
            "tool_name": tool_name,
            "status": status,
        },
    )

    try:
        from lib.db import Job, get_async_session

        # Parse UUIDs
        try:
            job_uuid = UUID(job_id) if job_id else None
            user_uuid = UUID(user_id) if user_id else None
        except (ValueError, TypeError) as e:
            context.logger.info(f"Invalid UUID format: {e}")
            job_uuid = None
            user_uuid = None

        if not job_uuid or not user_uuid:
            context.logger.error("Missing required job_id or user_id")
            return {"status": "error", "message": "Missing required fields"}

        # Status is now OGC-compliant (accepted, running, successful, failed, dismissed)
        # Use directly without mapping
        db_status = status

        # Build payload
        payload = {
            "project_id": input_data.get("project_id"),
            "scenario_id": input_data.get("scenario_id"),
            "result_layer_id": input_data.get("result_layer_id"),
            "feature_count": input_data.get("feature_count"),
            "error_message": input_data.get("error_message"),
            "input_params": input_data.get("input_params"),
            # Presigned URL fields (when save_results=False)
            "download_url": input_data.get("download_url"),
            "download_expires_at": input_data.get("download_expires_at"),
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        engine, async_session = await get_async_session()

        async with async_session() as session:
            # Create job record
            job = Job(
                id=job_uuid,
                user_id=user_uuid,
                type=tool_name,  # Tool name as job type
                status=db_status,
                payload=payload,
            )

            session.add(job)
            await session.commit()

            context.logger.info(
                f"Job {job_id} logged with status {db_status}",
                {"job_id": job_id, "status": db_status},
            )

        await engine.dispose()

        # Delete job from Redis now that it's persisted to PostgreSQL
        from lib.job_state import job_state_manager

        deleted = await job_state_manager.delete_job(job_id)
        if deleted:
            context.logger.info(f"Job {job_id} removed from Redis")

        return {
            "status": "success",
            "job_id": job_id,
            "logged_status": db_status,
        }

    except Exception as e:
        context.logger.error(
            f"Failed to log job status: {e}",
            {"job_id": job_id, "error": str(e)},
        )
        # Don't fail the entire flow if logging fails
        return {
            "status": "error",
            "job_id": job_id,
            "error": str(e),
        }
