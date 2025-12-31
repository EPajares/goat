"""
OGC Job Dismiss Endpoint.

Cancels a running job or deletes a finished job.
DELETE /jobs/{jobId}
"""

import os
import sys

sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
from typing import Any, Dict
from uuid import UUID

import lib.paths  # noqa: F401 - sets up remaining paths
from lib.auth import auth_middleware
from lib.ogc_base import (
    error_response,
    get_base_url,
    not_found_response,
    pydantic_response,
)
from lib.ogc_schemas import Link, StatusCode, StatusInfo

config = {
    "name": "OGCJobDismiss",
    "type": "api",
    "description": "Dismiss/cancel a job (OGC API Processes)",
    "path": "/jobs/:jobId",
    "method": "DELETE",
    "emits": [],
    "flows": ["analysis-flow"],
    "middleware": [auth_middleware],
}


async def handler(req: Dict[str, Any], context):
    """Dismiss/cancel a job in GOAT Core."""
    job_id = req.get("pathParams", {}).get("jobId")
    base_url = get_base_url(req)

    context.logger.info("OGC Job dismiss requested", {"job_id": job_id})

    if not job_id:
        return error_response(400, "Bad request", "jobId is required")

    # Validate UUID format
    try:
        job_uuid = UUID(job_id)
    except (ValueError, TypeError):
        return error_response(400, "Invalid job ID", f"Invalid job ID format: {job_id}")

    try:
        from lib.db import Job, get_async_session
        from sqlalchemy import select

        engine, async_session = await get_async_session()

        try:
            async with async_session() as session:
                result = await session.execute(select(Job).where(Job.id == job_uuid))
                job = result.scalar_one_or_none()

                if not job:
                    return not_found_response("job", job_id)

                # Update job status to dismissed (OGC-compliant)
                job.status = "dismissed"
                await session.commit()

                status_info = StatusInfo(
                    processID=job.type,
                    jobID=str(job.id),
                    status=StatusCode.dismissed,
                    message="Job dismissed by user request",
                    updated=job.updated_at.isoformat() if job.updated_at else None,
                    links=[
                        Link(
                            href=f"{base_url}/jobs/{job_id}",
                            rel="self",
                            type="application/json",
                        )
                    ],
                )

                return pydantic_response(status_info)
        finally:
            await engine.dispose()

    except Exception as e:
        context.logger.error(f"Failed to dismiss job: {e}")
        return error_response(500, "Internal server error", str(e))
