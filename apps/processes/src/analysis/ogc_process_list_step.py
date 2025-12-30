"""
OGC API Processes - Process List
GET /processes

Returns list of all available processes with summaries.
"""

import sys

sys.path.insert(0, "/app/apps/processes/src")
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path
from lib.ogc_process_generator import get_process_list
from lib.ogc_schemas import Link, ProcessList

config = {
    "name": "OGCProcessList",
    "type": "api",
    "path": "/processes",
    "method": "GET",
    "description": "OGC API Processes - list all available processes",
    "emits": [],
}


import os

# Default host and port from env (fallback when headers missing)
DEFAULT_HOST = os.environ.get("PROCESSES_HOST", "localhost")
DEFAULT_PORT = os.environ.get("PROCESSES_PORT", "8200")
DEFAULT_HOST_PORT = f"{DEFAULT_HOST}:{DEFAULT_PORT}"


async def handler(req, context):
    """Handle GET /processes request."""
    # Build base URL from request headers
    proto = req.get("headers", {}).get("x-forwarded-proto", "http")
    host = req.get("headers", {}).get("host", DEFAULT_HOST_PORT)
    base_url = f"{proto}://{host}"

    context.logger.info("OGC Process list requested", {"base_url": base_url})

    # Get process summaries from generator
    processes = get_process_list(base_url)

    # Build response
    process_list = ProcessList(
        processes=processes,
        links=[
            Link(
                href=f"{base_url}/processes",
                rel="self",
                type="application/json",
                title="Process list",
            ),
        ],
    )

    return {
        "status": 200,
        "body": process_list.model_dump(by_alias=True, exclude_none=True),
    }
