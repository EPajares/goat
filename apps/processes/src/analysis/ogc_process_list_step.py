"""
OGC API Processes - Process List
GET /processes

Returns list of all available processes with summaries.
"""

import os
import sys

sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths
from lib.auth import auth_middleware
from lib.ogc_base import get_base_url, pydantic_response, self_link
from lib.ogc_process_generator import get_process_list
from lib.ogc_schemas import ProcessList

config = {
    "name": "OGCProcessList",
    "type": "api",
    "path": "/processes",
    "method": "GET",
    "description": "OGC API Processes - list all available processes",
    "emits": [],
    "middleware": [auth_middleware],
}


async def handler(req, context):
    """Handle GET /processes request."""
    base_url = get_base_url(req)

    context.logger.info("OGC Process list requested", {"base_url": base_url})

    # Get process summaries from generator
    processes = get_process_list(base_url)

    # Build response
    process_list = ProcessList(
        processes=processes,
        links=[self_link(base_url, "/processes", "Process list")],
    )

    return pydantic_response(process_list)
