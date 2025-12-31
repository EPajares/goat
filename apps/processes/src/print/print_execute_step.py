"""
PrintReport Execute Step - OGC API Processes

API endpoint to initiate print report generation.
Emits print-requested event for the print_generate_step to process.

OGC Process ID: PrintReport
Endpoint: POST /processes/PrintReport/execution
"""

import sys

sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import lib.paths  # noqa: F401 - sets up remaining paths
from lib.auth import auth_middleware, get_access_token_from_request
from pydantic import BaseModel, Field


class PrintReportInput(BaseModel):
    """Input schema for PrintReport process."""

    project_id: str = Field(..., description="Project UUID")
    layout_id: str = Field(..., description="Report layout UUID")
    format: str = Field(
        default="pdf",
        description="Output format: 'pdf' or 'png'",
    )
    atlas_page_indices: Optional[List[int]] = Field(
        default=None,
        description="Specific atlas page indices to print (0-indexed). If None, prints all pages.",
    )


class PrintReportJobResponse(BaseModel):
    """OGC API Processes async job response."""

    jobID: str
    type: str = "process"
    processID: str = "PrintReport"
    status: str
    created: str
    links: List[Dict[str, str]]


config = {
    "name": "PrintReportExecute",
    "type": "api",
    "description": "Generate a printable report (PDF/PNG) from a project layout",
    "path": "/processes/PrintReport/execution",
    "method": "POST",
    "emits": ["print-requested"],
    "flows": ["print-flow"],
    "middleware": [auth_middleware],
}


def error_response(status: int, title: str, detail: str) -> Dict[str, Any]:
    """Create OGC API error response."""
    return {
        "status": status,
        "body": {
            "type": f"http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/{title.lower().replace(' ', '-')}",
            "title": title,
            "status": status,
            "detail": detail,
        },
    }


def get_base_url(req: Dict[str, Any]) -> str:
    """Extract base URL from request headers."""
    headers = req.get("headers", {})
    # Handle case-insensitive headers
    host = headers.get("host") or headers.get("Host", "localhost")
    proto = headers.get("x-forwarded-proto") or headers.get("X-Forwarded-Proto", "http")
    return f"{proto}://{host}"


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle POST /processes/PrintReport/execution request.

    Creates a new print job and emits print-requested event.

    Returns:
        OGC API Processes async job response with status 201
    """
    # Get user_id from auth middleware (attached to request)
    user_id = req.get("user_id")
    if not user_id:
        return error_response(401, "Unauthorized", "Authentication required")

    # Get access token for downstream API calls
    try:
        access_token = get_access_token_from_request(req)
    except ValueError as e:
        return error_response(401, "Unauthorized", str(e))

    # Get inputs from request body
    body = req.get("body", {})
    inputs = body.get("inputs", body)  # Support both {inputs: {...}} and direct {...}

    # Validate required inputs
    project_id = inputs.get("project_id")
    layout_id = inputs.get("layout_id")

    if not project_id:
        return error_response(400, "Bad Request", "project_id is required")

    if not layout_id:
        return error_response(400, "Bad Request", "layout_id is required")

    # Validate format
    output_format = inputs.get("format", "pdf").lower()
    if output_format not in ("pdf", "png"):
        return error_response(
            400,
            "Bad Request",
            f"Invalid format: {output_format}. Must be 'pdf' or 'png'",
        )

    # Get optional atlas page indices
    atlas_page_indices = inputs.get("atlas_page_indices")
    if atlas_page_indices is not None:
        if not isinstance(atlas_page_indices, list):
            return error_response(
                400, "Bad Request", "atlas_page_indices must be a list of integers"
            )
        if not all(isinstance(i, int) and i >= 0 for i in atlas_page_indices):
            return error_response(
                400,
                "Bad Request",
                "atlas_page_indices must contain non-negative integers",
            )

    # Generate job ID
    job_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    base_url = get_base_url(req)

    context.logger.info(
        "Creating print job",
        {
            "job_id": job_id,
            "user_id": str(user_id),
            "project_id": project_id,
            "layout_id": layout_id,
            "format": output_format,
            "atlas_page_indices": atlas_page_indices,
        },
    )

    # Store job state in Redis
    from lib.job_state import job_state_manager

    await job_state_manager.create_job(
        job_id=job_id,
        process_id="PrintReport",
        user_id=str(user_id),
        inputs={
            "project_id": project_id,
            "layout_id": layout_id,
            "format": output_format,
            "atlas_page_indices": atlas_page_indices,
        },
    )

    # Emit print-requested event for print_generate_step to handle
    await context.emit(
        {
            "topic": "print-requested",
            "data": {
                "job_id": job_id,
                "user_id": str(user_id),
                "access_token": access_token,
                "project_id": project_id,
                "layout_id": layout_id,
                "format": output_format,
                "atlas_page_indices": atlas_page_indices,
                "timestamp": timestamp,
            },
        }
    )

    context.logger.info(
        "Print job created, event emitted",
        {"job_id": job_id, "topic": "print-requested"},
    )

    # Return OGC API Processes async job response
    response_body = PrintReportJobResponse(
        jobID=job_id,
        status="accepted",
        created=timestamp,
        links=[
            {
                "href": f"{base_url}/processes/PrintReport",
                "rel": "process",
                "type": "application/json",
                "title": "Process description",
            },
            {
                "href": f"{base_url}/jobs/{job_id}",
                "rel": "self",
                "type": "application/json",
                "title": "Job status",
            },
            {
                "href": f"{base_url}/jobs/{job_id}/results",
                "rel": "results",
                "type": "application/json",
                "title": "Job results",
            },
        ],
    )

    return {
        "status": 201,
        "headers": {
            "Location": f"{base_url}/jobs/{job_id}",
            "Content-Type": "application/json",
        },
        "body": response_body.model_dump(),
    }
