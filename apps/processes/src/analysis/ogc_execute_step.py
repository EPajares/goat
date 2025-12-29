"""
OGC API Processes - Execute Process
POST /processes/{processId}/execution

Executes a process asynchronously and returns job status.
"""

import sys
from datetime import datetime, timezone
from uuid import uuid4

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/motia/src")

from lib.ogc_schemas import (
    OGC_EXCEPTION_INVALID_PARAMETER,
    OGC_EXCEPTION_NO_SUCH_PROCESS,
    Link,
    OGCException,
    StatusCode,
    StatusInfo,
)
from lib.tool_registry import get_tool

config = {
    "name": "OGCExecuteProcess",
    "type": "api",
    "path": "/processes/:processId/execution",
    "method": "POST",
    "description": "OGC API Processes - execute a process asynchronously",
    "emits": ["analysis-requested"],
    "flows": ["analysis-flow"],
}


async def handler(req, context):
    """Handle POST /processes/{processId}/execution request."""
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

    # Get inputs from request body
    body = req.get("body", {})
    inputs = body.get("inputs", body)  # Support both {inputs: {...}} and direct {...}

    context.logger.info("OGC Execute process requested", {
        "process_id": process_id,
        "base_url": base_url,
    })

    # Validate process exists
    tool_info = get_tool(process_id)
    if not tool_info:
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

    # Validate required inputs
    user_id = inputs.get("user_id")
    if not user_id:
        error = OGCException(
            type=OGC_EXCEPTION_INVALID_PARAMETER,
            title="Missing required input",
            status=400,
            detail="'user_id' is required in inputs",
        )
        return {
            "status": 400,
            "body": error.model_dump(),
        }

    # Generate job ID and output layer ID
    job_id = f"{process_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    output_layer_id = inputs.get("output_layer_id") or str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    context.logger.info("Executing process", {
        "process_id": process_id,
        "job_id": job_id,
        "user_id": user_id,
    })

    # Build event data for Motia
    event_data = {
        "jobId": job_id,
        "timestamp": timestamp,
        "tool_name": process_id,
        "output_layer_id": output_layer_id,
        **inputs,  # Include all inputs
    }

    # Emit event for background processing
    await context.emit({
        "topic": "analysis-requested",
        "data": event_data,
    })

    # Return 201 Created with job status
    status_info = StatusInfo(
        processID=process_id,
        jobID=job_id,
        status=StatusCode.accepted,
        message="Job submitted for processing",
        created=timestamp,
        links=[
            Link(
                href=f"{base_url}/jobs/{job_id}",
                rel="self",
                type="application/json",
                title="Job status",
            ),
            Link(
                href=f"{base_url}/jobs/{job_id}/results",
                rel="http://www.opengis.net/def/rel/ogc/1.0/results",
                type="application/json",
                title="Job results",
            ),
        ],
    )

    return {
        "status": 201,
        "body": status_info.model_dump(by_alias=True, exclude_none=True),
    }
