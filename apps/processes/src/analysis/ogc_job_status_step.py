"""
OGC Job Status Endpoint.

Returns job status from:
1. Redis (in-progress jobs: accepted, running)
2. PostgreSQL (completed jobs: successful, failed, dismissed)

GET /jobs/{jobId}
"""

import sys
from typing import Any, Dict
from uuid import UUID

# Add paths before any lib imports
for path in [
    "/app/apps/processes/src",
    "/app/apps/core/src",
    "/app/packages/python/goatlib/src",
]:
    if path not in sys.path:
        sys.path.insert(0, path)

from lib.ogc_base import error_response, get_base_url, not_found_response
from lib.ogc_schemas import Link, StatusCode, StatusInfo

config = {
    "name": "OGCJobStatus",
    "type": "api",
    "description": "Get job status (OGC API Processes)",
    "path": "/jobs/:jobId",
    "method": "GET",
    "emits": [],
    "flows": ["analysis-flow"],
}


async def handler(req: Dict[str, Any], context):
    """Get job status from Redis (in-progress) or PostgreSQL (completed)."""
    job_id = req.get("pathParams", {}).get("jobId")
    base_url = get_base_url(req)

    context.logger.info("OGC Job status requested", {"job_id": job_id})

    if not job_id:
        return error_response(400, "Bad request", "jobId is required")

    try:
        # Step 1: Check Redis for in-progress job
        from lib.job_state import job_state_manager

        redis_job = await job_state_manager.get_job(job_id)

        if redis_job:
            # Job found in Redis (in-progress)
            ogc_status = StatusCode(redis_job.get("status", "accepted"))

            links = [
                Link(
                    href=f"{base_url}/jobs/{job_id}",
                    rel="self",
                    type="application/json",
                ),
                Link(
                    href=f"{base_url}/processes/{redis_job.get('process_id')}",
                    rel="http://www.opengis.net/def/rel/ogc/1.0/process",
                    type="application/json",
                ),
            ]

            status_info = StatusInfo(
                processID=redis_job.get("process_id"),
                jobID=job_id,
                status=ogc_status,
                created=redis_job.get("created"),
                updated=redis_job.get("updated"),
                message=redis_job.get("message"),
                progress=redis_job.get("progress"),
                links=links,
            )

            return {
                "status": 200,
                "body": status_info.model_dump(by_alias=True, exclude_none=True),
            }

        # Step 2: Check PostgreSQL for completed job
        # Validate UUID format for PostgreSQL lookup
        try:
            job_uuid = UUID(job_id)
        except (ValueError, TypeError):
            # Not a valid UUID, and not in Redis - not found
            return not_found_response("job", job_id)

        from lib.db import Job, get_async_session
        from sqlalchemy import select

        engine, async_session = await get_async_session()

        try:
            async with async_session() as session:
                result = await session.execute(select(Job).where(Job.id == job_uuid))
                job = result.scalar_one_or_none()

                if not job:
                    return not_found_response("job", job_id)

                ogc_status = StatusCode(job.status)

                links = [
                    Link(
                        href=f"{base_url}/jobs/{job_id}",
                        rel="self",
                        type="application/json",
                    ),
                    Link(
                        href=f"{base_url}/processes/{job.type}",
                        rel="http://www.opengis.net/def/rel/ogc/1.0/process",
                        type="application/json",
                    ),
                ]

                if ogc_status == StatusCode.successful:
                    links.append(
                        Link(
                            href=f"{base_url}/jobs/{job_id}/results",
                            rel="http://www.opengis.net/def/rel/ogc/1.0/results",
                            type="application/json",
                        )
                    )

                status_info = StatusInfo(
                    processID=job.type,
                    jobID=str(job.id),
                    status=ogc_status,
                    created=job.created_at.isoformat() if job.created_at else None,
                    updated=job.updated_at.isoformat() if job.updated_at else None,
                    message=job.payload.get("error_message") if job.payload else None,
                    links=links,
                )

                return {
                    "status": 200,
                    "body": status_info.model_dump(by_alias=True, exclude_none=True),
                }
        finally:
            await engine.dispose()

    except Exception as e:
        context.logger.error(f"Failed to get job status: {e}")
        return error_response(500, "Internal server error", str(e))
