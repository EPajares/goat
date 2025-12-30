"""
OGC API Processes - Conformance
GET /conformance

Returns list of conformance classes the API implements.
"""

import sys

# Add paths before any lib imports
for path in ["/app/apps/processes/src", "/app/apps/core/src", "/app/packages/python/goatlib/src"]:
    if path not in sys.path:
        sys.path.insert(0, path)

from lib.ogc_base import PROCESSES_CONFORMANCE, pydantic_response
from lib.ogc_schemas import Conformance

config = {
    "name": "OGCConformance",
    "type": "api",
    "path": "/conformance",
    "method": "GET",
    "description": "OGC API Processes conformance classes",
    "emits": [],
}


async def handler(req, context):
    """Handle GET /conformance request."""
    context.logger.info("OGC Conformance requested")

    conformance = Conformance(conformsTo=PROCESSES_CONFORMANCE)

    return pydantic_response(conformance)
