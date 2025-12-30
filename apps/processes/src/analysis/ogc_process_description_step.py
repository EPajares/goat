"""
OGC API Processes - Process Description
GET /processes/{processId}

Returns full description of a process including inputs/outputs and geometry constraints.
"""

import sys

# Add paths before any lib imports
for path in [
    "/app/apps/processes/src",
    "/app/apps/core/src",
    "/app/packages/python/goatlib/src",
]:
    if path not in sys.path:
        sys.path.insert(0, path)

from lib.ogc_base import get_base_url, not_found_response, pydantic_response
from lib.ogc_process_generator import get_process

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
    process_id = req.get("pathParams", {}).get("processId")

    if not process_id:
        return {
            "status": 400,
            "body": {"error": "processId is required"},
        }

    base_url = get_base_url(req)

    context.logger.info(
        "OGC Process description requested",
        {"process_id": process_id, "base_url": base_url},
    )

    # Get process description
    process = get_process(process_id, base_url)

    if not process:
        return not_found_response("process", process_id)

    return pydantic_response(process)
