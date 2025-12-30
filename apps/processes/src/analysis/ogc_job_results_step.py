"""
OGC Job Results Endpoint.

Returns job results from GOAT Core jobs table.
GET /jobs/{jobId}/results
"""

import sys

sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
from typing import Any, Dict
from uuid import UUID

import lib.paths  # noqa: F401 - sets up remaining paths
from lib.auth import auth_middleware
from lib.ogc_base import error_response, get_base_url, not_found_response
from lib.ogc_schemas import OGC_EXCEPTION_RESULT_NOT_READY

config = {
    "name": "OGCJobResults",
    "type": "api",
    "description": "Get job results (OGC API Processes)",
    "path": "/jobs/:jobId/results",
    "method": "GET",
    "emits": [],
    "flows": ["analysis-flow"],
    "middleware": [auth_middleware],
}


async def handler(req: Dict[str, Any], context):
    """Get job results from GOAT Core."""
    job_id = req.get("pathParams", {}).get("jobId")
    base_url = get_base_url(req)

    context.logger.info("OGC Job results requested", {"job_id": job_id})

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

                # Check if job is finished
                if job.status not in ("finished", "successful"):
                    return error_response(
                        400,
                        "Results not ready",
                        f"Job is not complete. Current status: {job.status}",
                        OGC_EXCEPTION_RESULT_NOT_READY,
                    )

                # Get output layer ID from job payload
                output_layer_id = None
                if job.payload:
                    output_layer_id = job.payload.get("output_layer_id")

                # Build OGC-compliant results response
                results = {
                    "output_layer": {
                        "layerId": output_layer_id,
                        "href": f"{base_url}/collections/{output_layer_id}"
                        if output_layer_id
                        else None,
                        "type": "application/geo+json",
                    }
                }

                return {"status": 200, "body": results}
        finally:
            await engine.dispose()

    except Exception as e:
        context.logger.error(f"Failed to get job results: {e}")
        return error_response(500, "Internal server error", str(e))
