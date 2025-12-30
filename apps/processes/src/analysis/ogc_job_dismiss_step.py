"""
OGC Job Dismiss Endpoint.

Dismisses/cancels a job.
DELETE /jobs/{jobId}
"""

import os
import sys
from typing import Any, Dict
from uuid import UUID

sys.path.insert(0, "/app/apps/processes/src")
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path

config = {
    "name": "OGCJobDismiss",
    "type": "api",
    "description": "Dismiss/cancel a job (OGC API Processes)",
    "path": "/jobs/:jobId",
    "method": "DELETE",
    "emits": [],
    "flows": ["analysis-flow"],
}


async def handler(req: Dict[str, Any], context):
    """
    Dismiss/cancel a job.

    Behavior depends on job state:
    - pending: Remove from queue, update status to dismissed
    - running: Cannot cancel (return 409 Conflict)
    - finished/failed: Update status to dismissed
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

    context.logger.info("OGC Job dismiss requested", {"job_id": job_id})

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

            # Check if job can be dismissed
            if job.status == "running":
                await engine.dispose()
                return {
                    "status": 409,
                    "body": {
                        "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/JobNotDismissible",
                        "title": "Job cannot be cancelled",
                        "status": 409,
                        "detail": "Running jobs cannot be cancelled. Wait for completion or timeout.",
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

            # Store previous status for logging
            previous_status = job.status

            # Update job status to killed (dismissed in OGC terms)
            job.status = "killed"
            await session.commit()

            context.logger.info(
                f"Job {job_id} dismissed", {"previous_status": previous_status}
            )

            # Build OGC StatusInfo response
            status_info = {
                "processID": job.type,
                "type": "process",
                "jobID": str(job.id),
                "status": "dismissed",
                "created": job.created_at.isoformat() if job.created_at else None,
                "updated": job.updated_at.isoformat() if job.updated_at else None,
                "message": "Job has been dismissed",
                "links": [
                    {
                        "href": f"{base_url}/jobs/{job_id}",
                        "rel": "self",
                        "type": "application/json",
                    },
                ],
            }

        await engine.dispose()

        return {"status": 200, "body": status_info}

    except Exception as e:
        context.logger.error(f"Failed to dismiss job: {e}")
        return {
            "status": 500,
            "body": {
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/ServerError",
                "title": "Internal server error",
                "status": 500,
                "detail": str(e),
            },
        }
