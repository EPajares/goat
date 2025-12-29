"""
OGC Job Results Endpoint.

Returns job results from GOAT Core jobs table.
GET /jobs/{jobId}/results
"""

import os
import sys
from typing import Any, Dict
from uuid import UUID

sys.path.insert(0, "/app/apps/processes/src")
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path

config = {
    "name": "OGCJobResults",
    "type": "api",
    "description": "Get job results (OGC API Processes)",
    "path": "/jobs/:jobId/results",
    "method": "GET",
    "emits": [],
    "flows": ["analysis-flow"],
}


async def handler(req: Dict[str, Any], context):
    """
    Get job results from GOAT Core.

    Returns the result layer ID or download URL depending on how the job was run.
    """
    # Get jobId from path params
    job_id = req.get("pathParams", {}).get("jobId")

    # Build base URL from request headers
    default_host = os.environ.get("PROCESSES_HOST", "localhost")
    default_port = os.environ.get("PROCESSES_PORT", "8200")
    default_host_port = f"{default_host}:{default_port}"
    proto = req.get("headers", {}).get("x-forwarded-proto", "http")
    host = req.get("headers", {}).get("host", default_host_port)
    base_url = f"{proto}://{host}"

    context.logger.info("OGC Job results requested", {"job_id": job_id})

    if not job_id:
        return {
            "status": 400,
            "body": {"error": "jobId is required"},
        }

    try:
        # Validate UUID format
        try:
            job_uuid = UUID(job_id)
        except (ValueError, TypeError):
            return {
                "status": 400,
                "body": {
                    "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/InvalidParameterValue",
                    "title": "Invalid job ID",
                    "status": 400,
                    "detail": f"Invalid job ID format: {job_id}",
                },
            }

        # Import GOAT Core components
        import core._dotenv  # noqa
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from core.core.config import settings
        from core.db.models.job import Job

        # Create async engine and session
        engine = create_async_engine(settings.ASYNC_DATABASE_URI, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Query job by ID
            result = await session.execute(select(Job).where(Job.id == job_uuid))
            job = result.scalar_one_or_none()

            if not job:
                await engine.dispose()
                return {
                    "status": 404,
                    "body": {
                        "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/NoSuchJob",
                        "title": "Job not found",
                        "status": 404,
                        "detail": f"Job with ID {job_id} not found",
                    },
                }

            # Check job status - results only available for finished jobs
            if job.status not in ("finished",):
                await engine.dispose()

                status_messages = {
                    "pending": "Job is waiting to be processed",
                    "running": "Job is still running",
                    "failed": "Job failed - no results available",
                    "timeout": "Job timed out - no results available",
                    "killed": "Job was cancelled - no results available",
                }
                message = status_messages.get(job.status, f"Job status: {job.status}")

                return {
                    "status": 404,
                    "body": {
                        "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/ResultNotReady",
                        "title": "Results not ready",
                        "status": 404,
                        "detail": message,
                        "links": [
                            {
                                "href": f"{base_url}/jobs/{job_id}",
                                "rel": "monitor",
                                "type": "application/json",
                                "title": "Check job status",
                            }
                        ],
                    },
                }

            # Build results response from job payload
            payload = job.payload or {}
            results = {}

            # Check if this is a presigned URL result
            if payload.get("download_url"):
                results = {
                    "download_url": payload["download_url"],
                    "expires_at": payload.get("download_expires_at"),
                    "content_type": "application/geoparquet",
                }
            else:
                # Standard result with layer ID
                results = {
                    "result_layer_id": payload.get("result_layer_id"),
                    "feature_count": payload.get("feature_count"),
                    "geometry_type": payload.get("geometry_type"),
                }

            # Add links
            results["links"] = [
                {
                    "href": f"{base_url}/jobs/{job_id}/results",
                    "rel": "self",
                    "type": "application/json",
                },
                {
                    "href": f"{base_url}/jobs/{job_id}",
                    "rel": "up",
                    "type": "application/json",
                    "title": "Job status",
                },
            ]

        await engine.dispose()

        return {"status": 200, "body": results}

    except Exception as e:
        context.logger.error(f"Failed to get job results: {e}")
        return {
            "status": 500,
            "body": {
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/ServerError",
                "title": "Internal server error",
                "status": 500,
                "detail": str(e),
            },
        }
