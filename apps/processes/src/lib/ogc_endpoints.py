"""
OGC API Processes endpoints for Motia.

Implements OGC API - Processes - Part 1: Core (OGC 18-062r2)
https://docs.ogc.org/is/18-062r2/18-062r2.html

Endpoints:
- GET / - Landing page
- GET /conformance - Conformance classes
- GET /processes - List all processes
- GET /processes/{processId} - Process description
- POST /processes/{processId}/execution - Execute process (triggers Motia flow)
- GET /jobs/{jobId} - Job status
- GET /jobs/{jobId}/results - Job results
- DELETE /jobs/{jobId} - Dismiss job
"""

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

# Import path configuration first
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path
from lib.ogc_process_generator import get_process, get_process_list
from lib.ogc_schemas import (
    OGC_EXCEPTION_INVALID_PARAMETER,
    OGC_EXCEPTION_NO_SUCH_JOB,
    OGC_EXCEPTION_NO_SUCH_PROCESS,
    OGC_EXCEPTION_RESULT_NOT_READY,
    PROCESSES_CONFORMANCE,
    Conformance,
    LandingPage,
    Link,
    OGCException,
    ProcessList,
    StatusCode,
    StatusInfo,
)
from lib.tool_registry import get_tool

# === Landing Page ===


async def get_landing_page(base_url: str) -> Dict[str, Any]:
    """GET / - Landing page with API links.

    Args:
        base_url: Base URL of the API

    Returns:
        Landing page response dict
    """
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
    return landing.model_dump(by_alias=True, exclude_none=True)


# === Conformance ===


async def get_conformance() -> Dict[str, Any]:
    """GET /conformance - Conformance classes.

    Returns:
        Conformance response dict
    """
    conformance = Conformance(conformsTo=PROCESSES_CONFORMANCE)
    return conformance.model_dump()


# === Processes ===


async def list_processes(base_url: str) -> Dict[str, Any]:
    """GET /processes - List all available processes.

    Args:
        base_url: Base URL for generating links

    Returns:
        ProcessList response dict
    """
    processes = get_process_list(base_url)
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
    return process_list.model_dump(by_alias=True, exclude_none=True)


async def get_process_description(
    process_id: str,
    base_url: str,
) -> tuple[int, Dict[str, Any]]:
    """GET /processes/{processId} - Full process description.

    Args:
        process_id: Process identifier
        base_url: Base URL for generating links

    Returns:
        Tuple of (status_code, response_dict)
    """
    process = get_process(process_id, base_url)
    if not process:
        error = OGCException(
            type=OGC_EXCEPTION_NO_SUCH_PROCESS,
            title="Process not found",
            status=404,
            detail=f"Process '{process_id}' does not exist",
        )
        return 404, error.model_dump()

    return 200, process.model_dump(by_alias=True, exclude_none=True)


# === Execute ===


async def execute_process(
    process_id: str,
    inputs: Dict[str, Any],
    base_url: str,
    emit_func,  # Motia emit function
    logger,
) -> tuple[int, Dict[str, Any]]:
    """POST /processes/{processId}/execution - Execute a process.

    This triggers an async Motia job and returns job status.

    Args:
        process_id: Process identifier
        inputs: Process inputs from request body
        base_url: Base URL for generating links
        emit_func: Motia context.emit function
        logger: Logger instance

    Returns:
        Tuple of (status_code, response_dict)
    """
    # Validate process exists
    tool_info = get_tool(process_id)
    if not tool_info:
        error = OGCException(
            type=OGC_EXCEPTION_NO_SUCH_PROCESS,
            title="Process not found",
            status=404,
            detail=f"Process '{process_id}' does not exist",
        )
        return 404, error.model_dump()

    # Validate required inputs
    user_id = inputs.get("user_id")
    if not user_id:
        error = OGCException(
            type=OGC_EXCEPTION_INVALID_PARAMETER,
            title="Missing required input",
            status=400,
            detail="'user_id' is required",
        )
        return 400, error.model_dump()

    # Generate job ID and output layer ID
    job_id = f"{process_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    output_layer_id = inputs.get("output_layer_id") or str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(
        "Executing process",
        {
            "process_id": process_id,
            "job_id": job_id,
            "user_id": user_id,
        },
    )

    # Build event data for Motia
    event_data = {
        "jobId": job_id,
        "timestamp": timestamp,
        "tool_name": process_id,
        "output_layer_id": output_layer_id,
        **inputs,  # Include all inputs
    }

    # Emit event for background processing
    await emit_func(
        {
            "topic": "analysis-requested",
            "data": event_data,
        }
    )

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

    return 201, status_info.model_dump(by_alias=True, exclude_none=True)


# === Jobs ===


async def get_job_status(
    job_id: str,
    base_url: str,
    db_session=None,  # Optional: for reading from GOAT Core jobs table
) -> tuple[int, Dict[str, Any]]:
    """GET /jobs/{jobId} - Get job status.

    Args:
        job_id: Job identifier
        base_url: Base URL for generating links
        db_session: Optional database session for GOAT Core

    Returns:
        Tuple of (status_code, response_dict)
    """
    # TODO: Query GOAT Core jobs table
    # For now, return a placeholder
    if db_session:
        # Import here to avoid circular imports
        try:
            from core.db.models.job import Job
            from sqlalchemy import select

            result = await db_session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()

            if job:
                # Job status is already OGC StatusCode (no mapping needed)
                ogc_status = (
                    StatusCode(job.status)
                    if isinstance(job.status, str)
                    else job.status
                )

                payload = job.payload or {}
                status_info = StatusInfo(
                    processID=job.type,
                    jobID=str(job.id),
                    status=ogc_status,
                    message=payload.get("error_message"),
                    created=job.created_at.isoformat() if job.created_at else None,
                    updated=job.updated_at.isoformat() if job.updated_at else None,
                    links=[
                        Link(
                            href=f"{base_url}/jobs/{job_id}",
                            rel="self",
                            type="application/json",
                        ),
                    ],
                )
                return 200, status_info.model_dump(by_alias=True, exclude_none=True)
        except Exception:
            pass

    # Job not found
    error = OGCException(
        type=OGC_EXCEPTION_NO_SUCH_JOB,
        title="Job not found",
        status=404,
        detail=f"Job '{job_id}' does not exist",
    )
    return 404, error.model_dump()


async def get_job_results(
    job_id: str,
    base_url: str,
    db_session=None,
) -> tuple[int, Dict[str, Any]]:
    """GET /jobs/{jobId}/results - Get job results.

    Args:
        job_id: Job identifier
        base_url: Base URL for generating links
        db_session: Optional database session for GOAT Core

    Returns:
        Tuple of (status_code, response_dict)
    """
    if db_session:
        try:
            from core.db.models.job import Job
            from sqlalchemy import select

            result = await db_session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()

            if job:
                if job.status == "finished":
                    payload = job.payload or {}
                    return 200, {
                        "result": payload.get("result_layer_id"),
                        "feature_count": payload.get("feature_count"),
                    }
                elif job.status in ("pending", "running"):
                    error = OGCException(
                        type=OGC_EXCEPTION_RESULT_NOT_READY,
                        title="Result not ready",
                        status=404,
                        detail=f"Job '{job_id}' is still {job.status}",
                    )
                    return 404, error.model_dump()
                else:
                    # Failed job
                    payload = job.payload or {}
                    return 200, {
                        "error": payload.get("error_message", "Job failed"),
                    }
        except Exception:
            pass

    error = OGCException(
        type=OGC_EXCEPTION_NO_SUCH_JOB,
        title="Job not found",
        status=404,
        detail=f"Job '{job_id}' does not exist",
    )
    return 404, error.model_dump()


async def dismiss_job(
    job_id: str,
    base_url: str,
    db_session=None,
) -> tuple[int, Dict[str, Any]]:
    """DELETE /jobs/{jobId} - Dismiss/cancel a job.

    Note: Running jobs cannot be cancelled - only waiting jobs can be removed.

    Args:
        job_id: Job identifier
        base_url: Base URL for generating links
        db_session: Optional database session for GOAT Core

    Returns:
        Tuple of (status_code, response_dict)
    """
    # TODO: Implement BullMQ job removal for waiting jobs
    # TODO: Update GOAT Core jobs table status to 'killed'

    status_info = StatusInfo(
        jobID=job_id,
        status=StatusCode.dismissed,
        message="Job dismissed",
        links=[],
    )
    return 200, status_info.model_dump(by_alias=True, exclude_none=True)
