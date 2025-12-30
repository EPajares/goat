"""
OGC API Processes - Landing Page
GET /

Returns links to API endpoints per OGC spec.
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

from lib.ogc_base import PROCESSES_CONFORMANCE, get_base_url, pydantic_response
from lib.ogc_schemas import LandingPage, Link

config = {
    "name": "OGCLandingPage",
    "type": "api",
    "path": "/",
    "method": "GET",
    "description": "OGC API Processes landing page with API links",
    "emits": [],
}


async def handler(req, context):
    """Handle GET / request - landing page."""
    base_url = get_base_url(req)

    context.logger.info("OGC Landing page requested", {"base_url": base_url})

    landing = LandingPage(
        title="GOAT Analysis API",
        description="OGC API Processes for geospatial analysis tools",
        links=[
            Link(
                href=base_url,
                rel="self",
                type="application/json",
                title="This document",
            ),
            Link(
                href=f"{base_url}/openapi.json",
                rel="service-desc",
                type="application/openapi+json;version=3.0",
                title="API definition",
            ),
            Link(
                href=f"{base_url}/swagger",
                rel="service-doc",
                type="text/html",
                title="API documentation (Swagger UI)",
            ),
            Link(
                href=f"{base_url}/conformance",
                rel="http://www.opengis.net/def/rel/ogc/1.0/conformance",
                type="application/json",
                title="Conformance classes",
            ),
            Link(
                href=f"{base_url}/processes",
                rel="http://www.opengis.net/def/rel/ogc/1.0/processes",
                type="application/json",
                title="Processes",
            ),
            Link(
                href=f"{base_url}/jobs",
                rel="http://www.opengis.net/def/rel/ogc/1.0/job-list",
                type="application/json",
                title="Jobs",
            ),
        ],
    )

    return pydantic_response(landing)
