"""
OGC Job List Endpoint.

Returns list of jobs from both:
1. Redis (in-progress jobs: accepted, running)
2. PostgreSQL (completed jobs: successful, failed, dismissed)

GET /jobs
"""

import sys

sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
from typing import Any, Dict

import lib.paths  # noqa: F401 - sets up remaining paths
from lib.auth import auth_middleware
from lib.ogc_base import error_response, get_base_url, pydantic_response, self_link
from lib.ogc_schemas import JobList, Link, StatusCode, StatusInfo

config = {
    "name": "OGCJobList",
    "type": "api",
    "description": "List all jobs (OGC API Processes)",
    "path": "/jobs",
    "method": "GET",
    "emits": [],
    "flows": ["analysis-flow"],
    "middleware": [auth_middleware],
}


# Map legacy status values to OGC-compliant StatusCode
LEGACY_STATUS_MAP = {
    "killed": "dismissed",
    "pending": "accepted",
    "finished": "successful",
    "timeout": "failed",
}


def normalize_status(status: str) -> StatusCode:
    """Convert legacy status to OGC-compliant StatusCode."""
    normalized = LEGACY_STATUS_MAP.get(status, status)
    try:
        return StatusCode(normalized)
    except ValueError:
        # If still invalid, default to failed
        return StatusCode.failed


async def handler(req: Dict[str, Any], context):
    """List all jobs from Redis (in-progress) and PostgreSQL (completed)."""
    base_url = get_base_url(req)

    # Get query parameters for filtering
    query_params = req.get("queryParams", {})
    limit = int(query_params.get("limit", 100))
    offset = int(query_params.get("offset", 0))
    status_filter = query_params.get("status")
    process_filter = query_params.get("processID")

    context.logger.info(
        "OGC Job list requested",
        {
            "limit": limit,
            "offset": offset,
            "status": status_filter,
            "processID": process_filter,
        },
    )

    try:
        jobs = []
        redis_job_ids = set()  # Track Redis job IDs to avoid duplicates

        # Step 1: Get in-progress jobs from Redis
        # (only if not filtering for completed statuses)
        if status_filter not in ["successful", "failed", "dismissed"]:
            from lib.job_state import job_state_manager

            redis_jobs = await job_state_manager.list_jobs(
                status=status_filter,
                process_id=process_filter,
            )

            for redis_job in redis_jobs:
                job_id = redis_job.get("job_id")
                redis_job_ids.add(job_id)

                ogc_status = normalize_status(redis_job.get("status", "accepted"))

                links = [
                    Link(
                        href=f"{base_url}/jobs/{job_id}",
                        rel="self",
                        type="application/json",
                    )
                ]

                jobs.append(
                    StatusInfo(
                        processID=redis_job.get("process_id"),
                        jobID=job_id,
                        status=ogc_status,
                        created=redis_job.get("created"),
                        updated=redis_job.get("updated"),
                        message=redis_job.get("message"),
                        progress=redis_job.get("progress"),
                        links=links,
                    )
                )

        # Step 2: Get completed jobs from PostgreSQL
        # (only if not filtering for in-progress statuses)
        if status_filter not in ["accepted", "running"]:
            from lib.db import Job, get_async_session
            from sqlalchemy import select

            engine, async_session = await get_async_session()

            try:
                async with async_session() as session:
                    query = select(Job).order_by(Job.created_at.desc())

                    # Apply filters
                    if status_filter:
                        query = query.where(Job.status == status_filter)

                    if process_filter:
                        query = query.where(Job.type == process_filter)

                    result = await session.execute(query)
                    jobs_db = result.scalars().all()

                    for job in jobs_db:
                        # Skip if already in Redis results (shouldn't happen, but safety check)
                        if str(job.id) in redis_job_ids:
                            continue

                        ogc_status = normalize_status(job.status)

                        links = [
                            Link(
                                href=f"{base_url}/jobs/{job.id}",
                                rel="self",
                                type="application/json",
                            )
                        ]

                        if ogc_status == StatusCode.successful:
                            links.append(
                                Link(
                                    href=f"{base_url}/jobs/{job.id}/results",
                                    rel="http://www.opengis.net/def/rel/ogc/1.0/results",
                                    type="application/json",
                                )
                            )

                        jobs.append(
                            StatusInfo(
                                processID=job.type,
                                jobID=str(job.id),
                                status=ogc_status,
                                created=job.created_at.isoformat()
                                if job.created_at
                                else None,
                                updated=job.updated_at.isoformat()
                                if job.updated_at
                                else None,
                                links=links,
                            )
                        )
            finally:
                await engine.dispose()

        # Sort all jobs by created time (newest first)
        jobs.sort(key=lambda x: x.created or "", reverse=True)

        # Apply pagination
        paginated_jobs = jobs[offset : offset + limit]

        job_list = JobList(
            jobs=paginated_jobs,
            links=[self_link(base_url, "/jobs", "Job list")],
        )

        return pydantic_response(job_list)

    except Exception as e:
        context.logger.error(f"Failed to list jobs: {e}")
        return error_response(500, "Internal server error", str(e))
