"""
OGC API Processes - Process Description
GET /processes/{processId}

Returns full description of a process including inputs/outputs and geometry constraints.
"""

import sys

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/motia/src")

from lib.ogc_process_generator import get_process
from lib.ogc_schemas import OGC_EXCEPTION_NO_SUCH_PROCESS, OGCException

config = {
    "name": "OGCProcessDescription",
    "type": "api",
    "path": "/processes/:processId",
    "method": "GET",
    "description": "OGC API Processes - get full process description",
    "emits": [],
}


async def handler(req, context):
    """Handle GET /processes/{processId} request."""
    # Get process ID from path params
    process_id = req.get("pathParams", {}).get("processId")

    if not process_id:
        return {
            "status": 400,
            "body": {"error": "processId is required"},
        }

    # Build base URL from request headers
    proto = req.get("headers", {}).get("x-forwarded-proto", "http")
    host = req.get("headers", {}).get("host", "localhost")
    base_url = f"{proto}://{host}"

    context.logger.info(
        "OGC Process description requested",
        {
            "process_id": process_id,
            "base_url": base_url,
        },
    )

    # Get process description
    process = get_process(process_id, base_url)

    if not process:
        error = OGCException(
            type=OGC_EXCEPTION_NO_SUCH_PROCESS,
            title="Process not found",
            status=404,
            detail=f"Process '{process_id}' does not exist",
        )
        return {
            "status": 404,
            "body": error.model_dump(),
        }

    return {
        "status": 200,
        "body": process.model_dump(by_alias=True, exclude_none=True),
    }
