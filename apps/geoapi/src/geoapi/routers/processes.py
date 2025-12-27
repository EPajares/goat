"""Processes router for OGC API Processes endpoints.

Implements OGC API - Processes - Part 1: Core (OGC 18-062r2)
https://docs.ogc.org/is/18-062r2/18-062r2.html
"""

import logging

from fastapi import APIRouter, HTTPException, Path, Request
from fastapi.responses import JSONResponse

from geoapi.models import (
    ExecuteRequest,
    Link,
    ProcessDescription,
    ProcessList,
)
from geoapi.services.process_service import process_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Processes"])


# === OGC API Processes Conformance Classes ===
PROCESSES_CONFORMANCE = [
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
]


@router.get(
    "/processes",
    summary="Get process list",
    response_model=ProcessList,
    responses={
        200: {
            "description": "List of available processes",
            "content": {
                "application/json": {
                    "example": {
                        "processes": [
                            {
                                "id": "feature-count",
                                "title": "Feature Count",
                                "description": "Count features in a collection",
                                "version": "1.0.0",
                            }
                        ],
                        "links": [],
                    }
                }
            },
        }
    },
)
async def get_processes(request: Request) -> ProcessList:
    """Get list of available processes.

    Returns a list of all processes offered by this API.
    Each process includes a summary with links to the full description.
    """
    base_url = str(request.base_url).rstrip("/")

    processes = process_service.get_process_list(base_url)

    links = [
        Link(
            href=f"{base_url}/processes",
            rel="self",
            type="application/json",
            title="Process list",
        ),
    ]

    return ProcessList(processes=processes, links=links)


@router.get(
    "/processes/{processId}",
    summary="Get process description",
    response_model=ProcessDescription,
    responses={
        200: {"description": "Process description"},
        404: {"description": "Process not found"},
    },
)
async def get_process(
    request: Request,
    processId: str = Path(description="Process identifier"),
) -> ProcessDescription:
    """Get detailed description of a process.

    Returns the full description of the process including:
    - Input parameters with JSON Schema definitions
    - Output format specifications
    - Supported execution modes
    """
    base_url = str(request.base_url).rstrip("/")

    process = process_service.get_process(processId, base_url)
    if not process:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process",
                "title": "Process not found",
                "status": 404,
                "detail": f"Process '{processId}' does not exist",
            },
        )

    return process


@router.post(
    "/processes/{processId}/execution",
    summary="Execute process",
    responses={
        200: {"description": "Process execution result"},
        400: {"description": "Invalid request"},
        404: {"description": "Process not found"},
        500: {"description": "Process execution failed"},
    },
)
async def execute_process(
    request: Request,
    processId: str = Path(description="Process identifier"),
    body: ExecuteRequest = ...,
) -> JSONResponse:
    """Execute a process synchronously.

    Executes the specified process with the provided inputs.
    Returns the process results directly (synchronous execution).

    The request body must contain:
    - inputs: Object with input parameter values
    - outputs: Optional output format specifications
    - response: "raw" (default) or "document"
    """
    base_url = str(request.base_url).rstrip("/")

    # Check if process exists
    process = process_service.get_process(processId, base_url)
    if not process:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process",
                "title": "Process not found",
                "status": 404,
                "detail": f"Process '{processId}' does not exist",
            },
        )

    # Execute the process
    try:
        result = await process_service.execute_process(
            process_id=processId,
            inputs=body.inputs,
            base_url=base_url,
        )
    except ValueError as e:
        # Input validation error
        raise HTTPException(
            status_code=400,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/invalid-parameter-value",
                "title": "Invalid parameter value",
                "status": 400,
                "detail": str(e),
            },
        )
    except RuntimeError as e:
        # Execution error
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/execution-failed",
                "title": "Execution failed",
                "status": 500,
                "detail": str(e),
            },
        )
    except Exception as e:
        logger.exception("Unexpected error executing process %s", processId)
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/execution-failed",
                "title": "Execution failed",
                "status": 500,
                "detail": f"An unexpected error occurred: {str(e)}",
            },
        )

    # Return result based on response type
    if body.response.value == "raw":
        # Return the result directly
        return JSONResponse(content=result, status_code=200)
    else:
        # Return as a document with output keys
        # For now, we return a simple wrapper
        output_key = list(process.outputs.keys())[0] if process.outputs else "result"
        return JSONResponse(content={output_key: result}, status_code=200)
