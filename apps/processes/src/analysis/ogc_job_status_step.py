"""
OGC Job Status Endpoint.

Returns job status from GOAT Core jobs table.
GET /jobs/{jobId}
"""

import sys
from typing import Any, Dict
from uuid import UUID

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/motia/src")


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
    """
    Get job status from GOAT Core.

    Returns OGC StatusInfo format.
    """
    # Get jobId from path params
    job_id = req.get("pathParams", {}).get("jobId")

    # Build base URL from request headers
    proto = req.get("headers", {}).get("x-forwarded-proto", "http")
    host = req.get("headers", {}).get("host", "localhost:3002")
    base_url = f"{proto}://{host}"

    context.logger.info("OGC Job status requested", {"job_id": job_id})

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
        from core.core.config import settings
        from core.db.models.job import Job
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

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

            # Map GOAT Core status to OGC status
            status_map = {
                "pending": "accepted",
                "running": "running",
                "finished": "successful",
                "failed": "failed",
                "timeout": "failed",
                "killed": "dismissed",
            }
            ogc_status = status_map.get(job.status, "failed")

            # Build OGC StatusInfo response
            status_info = {
                "processID": job.type,
                "type": "process",
                "jobID": str(job.id),
                "status": ogc_status,
                "created": job.created_at.isoformat() if job.created_at else None,
                "updated": job.updated_at.isoformat() if job.updated_at else None,
                "links": [
                    {
                        "href": f"{base_url}/jobs/{job_id}",
                        "rel": "self",
                        "type": "application/json",
                    },
                    {
                        "href": f"{base_url}/processes/{job.type}",
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/process",
                        "type": "application/json",
                    },
                ],
            }

            # Add results link if job is successful
            if ogc_status == "successful":
                status_info["links"].append(
                    {
                        "href": f"{base_url}/jobs/{job_id}/results",
                        "rel": "http://www.opengis.net/def/rel/ogc/1.0/results",
                        "type": "application/json",
                    }
                )

            # Add message if there's an error
            if job.payload and job.payload.get("error_message"):
                status_info["message"] = job.payload["error_message"]

        await engine.dispose()

        return {"status": 200, "body": status_info}

    except Exception as e:
        context.logger.error(f"Failed to get job status: {e}")
        return {
            "status": 500,
            "body": {
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/ServerError",
                "title": "Internal server error",
                "status": 500,
                "detail": str(e),
            },
        }
