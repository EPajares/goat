"""OGC API Processes router.

Implements OGC API - Processes - Part 1: Core (OGC 18-062r2)
https://docs.ogc.org/is/18-062r2/18-062r2.html

Endpoints:
- GET /processes - List available processes
- GET /processes/{processId} - Get process description
- POST /processes/{processId}/execution - Execute a process
- GET /jobs - List jobs
- GET /jobs/{jobId} - Get job status
- GET /jobs/{jobId}/results - Get job results
- DELETE /jobs/{jobId} - Cancel/dismiss a job
"""

import logging
from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from geoapi.deps.auth import get_user_id
from geoapi.models.processes import (
    OGC_EXCEPTION_NO_SUCH_JOB,
    OGC_EXCEPTION_NO_SUCH_PROCESS,
    OGC_EXCEPTION_RESULT_NOT_READY,
    ConformanceDeclaration,
    ExecuteRequest,
    JobList,
    LandingPage,
    Link,
    OGCException,
    ProcessDescription,
    ProcessList,
    StatusCode,
    StatusInfo,
)
from geoapi.services.analytics_registry import analytics_registry
from geoapi.services.analytics_service import analytics_service
from geoapi.services.job_service import JobStatus, job_service
from geoapi.services.tool_registry import tool_registry
from geoapi.services.windmill_client import (
    WindmillError,
    WindmillJobNotFound,
    windmill_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Processes"])


def _execute_analytics_sync(process_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute an analytics process synchronously.

    Args:
        process_id: Analytics process ID
        inputs: Process inputs

    Returns:
        Process result as dict

    Raises:
        HTTPException: If execution fails
    """
    try:
        if process_id == "feature-count":
            return analytics_service.feature_count(
                collection=inputs.get("collection", ""),
                filter_expr=inputs.get("filter"),
            )
        elif process_id == "unique-values":
            return analytics_service.unique_values(
                collection=inputs.get("collection", ""),
                attribute=inputs.get("attribute", ""),
                order=inputs.get("order", "descendent"),
                filter_expr=inputs.get("filter"),
                limit=inputs.get("limit", 100),
                offset=inputs.get("offset", 0),
            )
        elif process_id == "class-breaks":
            return analytics_service.class_breaks(
                collection=inputs.get("collection", ""),
                attribute=inputs.get("attribute", ""),
                method=inputs.get("method", "quantile"),
                breaks=inputs.get("breaks", 5),
                filter_expr=inputs.get("filter"),
                strip_zeros=inputs.get("strip_zeros", False),
            )
        elif process_id == "area-statistics":
            return analytics_service.area_statistics(
                collection=inputs.get("collection", ""),
                operation=inputs.get("operation", "sum"),
                filter_expr=inputs.get("filter"),
            )
        else:
            raise HTTPException(
                status_code=404, detail=f"Unknown analytics process: {process_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics execution failed for {process_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/job-execution-failed",
                "title": "Execution failed",
                "status": 500,
                "detail": str(e),
            },
        )


def get_base_url(request: Request) -> str:
    """Build base URL from request."""
    # Check for forwarded headers (reverse proxy)
    proto = request.headers.get("x-forwarded-proto", "http")
    host = request.headers.get("x-forwarded-host") or request.headers.get(
        "host", "localhost"
    )
    return f"{proto}://{host}"


# === Landing Page and Conformance ===


@router.get(
    "/",
    summary="Landing page",
    response_model=LandingPage,
)
async def landing_page(request: Request) -> LandingPage:
    """Get the OGC API landing page with links to available resources."""
    base_url = get_base_url(request)

    return LandingPage(
        title="GOAT Processes API",
        description="OGC API - Processes implementation for GOAT geospatial analysis tools",
        links=[
            Link(
                href=f"{base_url}/",
                rel="self",
                type="application/json",
                title="This document",
            ),
            Link(
                href=f"{base_url}/api/docs",
                rel="service-doc",
                type="text/html",
                title="API documentation",
            ),
            Link(
                href=f"{base_url}/api/openapi.json",
                rel="service-desc",
                type="application/vnd.oai.openapi+json;version=3.0",
                title="OpenAPI definition",
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
                title="Process list",
            ),
            Link(
                href=f"{base_url}/jobs",
                rel="http://www.opengis.net/def/rel/ogc/1.0/job-list",
                type="application/json",
                title="Job list",
            ),
        ],
    )


@router.get(
    "/conformance",
    summary="Conformance classes",
    response_model=ConformanceDeclaration,
)
async def conformance() -> ConformanceDeclaration:
    """Get list of conformance classes implemented by this API."""
    return ConformanceDeclaration(
        conformsTo=[
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/job-list",
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/dismiss",
        ]
    )


# === Process List and Description ===


@router.get(
    "/processes",
    summary="List available processes",
    response_model=ProcessList,
)
async def list_processes(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> ProcessList:
    """Get list of all available processes (analytics + async tools)."""
    base_url = get_base_url(request)

    # Get analytics processes (sync) - auto-generated from goatlib schemas
    analytics_summaries = analytics_registry.get_all_summaries(base_url)

    # Get async tool processes from registry
    tool_list = tool_registry.get_process_list(base_url, limit=limit)

    # Combine both
    all_processes = analytics_summaries + tool_list.processes

    # Apply limit
    all_processes = all_processes[:limit]

    return ProcessList(
        processes=all_processes,
        links=[
            Link(
                href=f"{base_url}/processes",
                rel="self",
                type="application/json",
                title="Process list",
            ),
        ],
    )


@router.get(
    "/processes/{process_id}",
    summary="Get process description",
    response_model=ProcessDescription,
    responses={
        404: {"model": OGCException, "description": "Process not found"},
    },
)
async def get_process(request: Request, process_id: str) -> ProcessDescription:
    """Get detailed description of a specific process."""
    base_url = get_base_url(request)

    # Check analytics processes first (auto-generated from goatlib schemas)
    if analytics_registry.is_analytics_process(process_id):
        return analytics_registry.get_process_description(process_id, base_url)

    # Check async tool processes
    process_desc = tool_registry.get_process_description(process_id, base_url)

    if not process_desc:
        raise HTTPException(
            status_code=404,
            detail={
                "type": OGC_EXCEPTION_NO_SUCH_PROCESS,
                "title": "Process not found",
                "status": 404,
                "detail": f"Process '{process_id}' not found",
            },
        )

    return process_desc


# === Process Execution ===


@router.post(
    "/processes/{process_id}/execution",
    summary="Execute a process",
    status_code=status.HTTP_201_CREATED,
    response_model=StatusInfo,
    responses={
        201: {"description": "Job created (async execution)"},
        200: {"description": "Results (sync execution)"},
        404: {"model": OGCException, "description": "Process not found"},
        500: {"model": OGCException, "description": "Execution error"},
    },
)
async def execute_process(
    request: Request,
    process_id: str,
    execute_request: ExecuteRequest,
    user_id: UUID = Depends(get_user_id),
) -> JSONResponse:
    """Execute a process.

    For analytics processes (feature-count, class-breaks, unique-values, area-statistics):
      Returns results immediately (HTTP 200).

    For async tool processes (buffer, clip, etc.):
      Creates a job and returns status info with job ID (HTTP 201).
      Results can be retrieved via /jobs/{jobId}/results.
    """
    base_url = get_base_url(request)

    # Check if this is an analytics process (sync execution)
    if analytics_registry.is_analytics_process(process_id):
        result = _execute_analytics_sync(process_id, execute_request.inputs)
        return JSONResponse(status_code=200, content=result)

    # For async processes, verify tool exists
    tool_info = tool_registry.get_tool(process_id)
    if not tool_info:
        raise HTTPException(
            status_code=404,
            detail={
                "type": OGC_EXCEPTION_NO_SUCH_PROCESS,
                "title": "Process not found",
                "status": 404,
                "detail": f"Process '{process_id}' not found",
            },
        )

    # Prepare script path for Windmill
    script_path = f"f/goat/{process_id}"

    # Add user_id to inputs for job tracking
    job_inputs = {**execute_request.inputs, "user_id": str(user_id)}

    # Submit job to Windmill
    try:
        job_id = await windmill_client.run_script_async(
            script_path=script_path,
            args=job_inputs,
        )

        logger.info(f"Job {job_id} created for process {process_id} by user {user_id}")

        # Store job in database for user-scoped access
        await job_service.create_job(
            job_id=UUID(job_id),
            user_id=user_id,
            job_type=process_id,
            status=JobStatus.ACCEPTED,
            payload=execute_request.inputs,
        )

        # Build status info response
        status_info = StatusInfo(
            processID=process_id,
            type="process",
            jobID=job_id,
            status=StatusCode.accepted,
            message="Job submitted to execution queue",
            created=datetime.now(timezone.utc),
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

        return JSONResponse(
            status_code=201,
            content=status_info.model_dump(mode="json", exclude_none=True),
            headers={"Location": f"{base_url}/jobs/{job_id}"},
        )

    except WindmillError as e:
        logger.error(f"Windmill error executing {process_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/job-execution-failed",
                "title": "Execution failed",
                "status": 500,
                "detail": str(e),
            },
        )


# === Job Management ===


def _db_status_to_ogc(status: str) -> StatusCode:
    """Convert database status to OGC status code.

    Handles legacy status values like 'killed', 'pending', 'finished'.
    """
    # Direct OGC status values
    if status in ("accepted", "running", "successful", "failed", "dismissed"):
        return StatusCode(status)

    # Legacy status mappings
    legacy_map = {
        "pending": StatusCode.accepted,
        "finished": StatusCode.successful,
        "killed": StatusCode.dismissed,
        "timeout": StatusCode.failed,
    }
    return legacy_map.get(status, StatusCode.failed)


def _windmill_status_to_ogc(job: dict[str, Any]) -> StatusCode:
    """Convert Windmill job status to OGC status code."""
    if job.get("running"):
        return StatusCode.running
    elif job.get("success") is True:
        return StatusCode.successful
    elif job.get("success") is False:
        return StatusCode.failed
    elif job.get("canceled"):
        return StatusCode.dismissed
    else:
        return StatusCode.accepted


def _windmill_job_to_status_info(job: dict[str, Any], base_url: str) -> StatusInfo:
    """Convert Windmill job to OGC StatusInfo."""
    job_id = job.get("id", "")
    process_id = job.get("script_path", "").replace("f/goat/", "")

    # Parse timestamps
    created = None
    started = None
    finished = None

    if job.get("created_at"):
        try:
            created = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00"))
        except Exception:
            pass

    if job.get("started_at"):
        try:
            started = datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))
        except Exception:
            pass

    if not job.get("running") and job.get("duration_ms"):
        if started:
            from datetime import timedelta

            finished = started + timedelta(milliseconds=job["duration_ms"])

    status = _windmill_status_to_ogc(job)

    # Build links
    links = [
        Link(
            href=f"{base_url}/jobs/{job_id}",
            rel="self",
            type="application/json",
            title="Job status",
        ),
    ]

    if status == StatusCode.successful:
        links.append(
            Link(
                href=f"{base_url}/jobs/{job_id}/results",
                rel="http://www.opengis.net/def/rel/ogc/1.0/results",
                type="application/json",
                title="Job results",
            )
        )

    return StatusInfo(
        processID=process_id if process_id else None,
        type="process",
        jobID=job_id,
        status=status,
        message=job.get("logs", "")[:500] if job.get("logs") else None,
        created=created,
        started=started,
        finished=finished,
        links=links,
    )


@router.get(
    "/jobs",
    summary="List jobs",
    response_model=JobList,
)
async def list_jobs(
    request: Request,
    user_id: UUID = Depends(get_user_id),
    process_id: Annotated[str | None, Query(alias="processID")] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> JobList:
    """List all jobs for the authenticated user, optionally filtered by process ID or status."""
    base_url = get_base_url(request)

    try:
        # Get jobs from database (user-scoped)
        db_jobs = await job_service.list_jobs(
            user_id=user_id,
            process_id=process_id,
            status=status,
            limit=limit,
        )

        # For each job, get current status from Windmill and build StatusInfo
        jobs = []
        for db_job in db_jobs:
            job_id = str(db_job["id"])
            try:
                # Get live status from Windmill
                windmill_job = await windmill_client.get_job_status(job_id)
                windmill_status = _windmill_status_to_ogc(windmill_job)

                # Update status in DB if changed
                db_status = db_job["status"]
                if windmill_status.value != db_status:
                    await job_service.update_job_status(
                        job_id=db_job["id"],
                        status=windmill_status.value,
                    )

                # Build StatusInfo with correct process ID from DB
                status_info = _windmill_job_to_status_info(windmill_job, base_url)
                status_info.processID = db_job[
                    "type"
                ]  # Use DB process ID, not Windmill path
                jobs.append(status_info)

            except WindmillJobNotFound:
                # Job exists in DB but not in Windmill - build from DB
                jobs.append(
                    StatusInfo(
                        processID=db_job["type"],
                        type="process",
                        jobID=job_id,
                        status=_db_status_to_ogc(db_job["status"]),
                        created=db_job.get("created_at"),
                        links=[
                            Link(
                                href=f"{base_url}/jobs/{job_id}",
                                rel="self",
                                type="application/json",
                                title="Job status",
                            ),
                        ],
                    )
                )
            except WindmillError as e:
                logger.warning(f"Failed to get Windmill status for job {job_id}: {e}")
                # Include job with DB status only
                jobs.append(
                    StatusInfo(
                        processID=db_job["type"],
                        type="process",
                        jobID=job_id,
                        status=_db_status_to_ogc(db_job["status"]),
                        created=db_job.get("created_at"),
                        links=[
                            Link(
                                href=f"{base_url}/jobs/{job_id}",
                                rel="self",
                                type="application/json",
                                title="Job status",
                            ),
                        ],
                    )
                )

        return JobList(
            jobs=jobs,
            links=[
                Link(
                    href=f"{base_url}/jobs",
                    rel="self",
                    type="application/json",
                    title="Job list",
                ),
            ],
        )

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/internal-error",
                "title": "Internal error",
                "status": 500,
                "detail": str(e),
            },
        )


@router.get(
    "/jobs/{job_id}",
    summary="Get job status",
    response_model=StatusInfo,
    responses={
        404: {"model": OGCException, "description": "Job not found"},
    },
)
async def get_job_status(
    request: Request,
    job_id: str,
    user_id: UUID = Depends(get_user_id),
) -> StatusInfo:
    """Get status information for a specific job."""
    base_url = get_base_url(request)

    try:
        # First check if user owns this job
        db_job = await job_service.get_job(UUID(job_id), user_id)
        if not db_job:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": OGC_EXCEPTION_NO_SUCH_JOB,
                    "title": "Job not found",
                    "status": 404,
                    "detail": f"Job '{job_id}' not found",
                },
            )

        # Get live status from Windmill
        windmill_job = await windmill_client.get_job_status(job_id)
        status_info = _windmill_job_to_status_info(windmill_job, base_url)

        # Use process ID from DB (not Windmill path)
        status_info.processID = db_job["type"]

        # Update status in DB if changed
        windmill_status = _windmill_status_to_ogc(windmill_job)
        if windmill_status.value != db_job["status"]:
            await job_service.update_job_status(
                job_id=UUID(job_id),
                status=windmill_status.value,
            )

        return status_info

    except HTTPException:
        raise
    except WindmillJobNotFound:
        # Job in DB but not in Windmill - return DB info
        db_job = await job_service.get_job(UUID(job_id), user_id)
        if db_job:
            return StatusInfo(
                processID=db_job["type"],
                type="process",
                jobID=job_id,
                status=_db_status_to_ogc(db_job["status"]),
                created=db_job.get("created_at"),
                links=[
                    Link(
                        href=f"{base_url}/jobs/{job_id}",
                        rel="self",
                        type="application/json",
                        title="Job status",
                    ),
                ],
            )
        raise HTTPException(
            status_code=404,
            detail={
                "type": OGC_EXCEPTION_NO_SUCH_JOB,
                "title": "Job not found",
                "status": 404,
                "detail": f"Job '{job_id}' not found",
            },
        )
    except WindmillError as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/internal-error",
                "title": "Internal error",
                "status": 500,
                "detail": str(e),
            },
        )


@router.get(
    "/jobs/{job_id}/results",
    summary="Get job results",
    responses={
        200: {"description": "Job results"},
        404: {
            "model": OGCException,
            "description": "Job not found or results not ready",
        },
    },
)
async def get_job_results(
    request: Request,
    job_id: str,
    user_id: UUID = Depends(get_user_id),
) -> Any:
    """Get results of a completed job."""
    try:
        # First check if user owns this job
        db_job = await job_service.get_job(UUID(job_id), user_id)
        if not db_job:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": OGC_EXCEPTION_NO_SUCH_JOB,
                    "title": "Job not found",
                    "status": 404,
                    "detail": f"Job '{job_id}' not found",
                },
            )

        # Check job status from Windmill
        job = await windmill_client.get_job_status(job_id)
        status = _windmill_status_to_ogc(job)

        if status == StatusCode.running or status == StatusCode.accepted:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": OGC_EXCEPTION_RESULT_NOT_READY,
                    "title": "Results not ready",
                    "status": 404,
                    "detail": f"Job '{job_id}' is still {status.value}",
                },
            )

        if status == StatusCode.failed:
            error_msg = job.get("result", {})
            raise HTTPException(
                status_code=500,
                detail={
                    "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/job-failed",
                    "title": "Job failed",
                    "status": 500,
                    "detail": str(error_msg),
                },
            )

        # Get results
        result = await windmill_client.get_job_result(job_id)

        # Return as document format
        return {"result": result}

    except HTTPException:
        raise
    except WindmillJobNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "type": OGC_EXCEPTION_NO_SUCH_JOB,
                "title": "Job not found",
                "status": 404,
                "detail": f"Job '{job_id}' not found",
            },
        )
    except WindmillError as e:
        logger.error(f"Error getting job results: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/internal-error",
                "title": "Internal error",
                "status": 500,
                "detail": str(e),
            },
        )


@router.delete(
    "/jobs/{job_id}",
    summary="Dismiss/cancel a job",
    response_model=StatusInfo,
    responses={
        200: {"description": "Job dismissed"},
        404: {"model": OGCException, "description": "Job not found"},
    },
)
async def dismiss_job(
    request: Request,
    job_id: str,
    user_id: UUID = Depends(get_user_id),
) -> StatusInfo:
    """Cancel a running job or remove a completed job."""
    base_url = get_base_url(request)

    try:
        # First check if user owns this job
        db_job = await job_service.get_job(UUID(job_id), user_id)
        if not db_job:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": OGC_EXCEPTION_NO_SUCH_JOB,
                    "title": "Job not found",
                    "status": 404,
                    "detail": f"Job '{job_id}' not found",
                },
            )

        # Cancel the job in Windmill
        try:
            await windmill_client.cancel_job(job_id, "User requested dismissal")
        except WindmillJobNotFound:
            pass  # Job might already be finished

        # Update status in DB
        await job_service.update_job_status(
            job_id=UUID(job_id),
            status=JobStatus.DISMISSED,
            user_id=user_id,
        )

        # Build response
        return StatusInfo(
            processID=db_job["type"],
            type="process",
            jobID=job_id,
            status=StatusCode.dismissed,
            message="Job dismissed",
            created=db_job.get("created_at"),
            links=[
                Link(
                    href=f"{base_url}/jobs/{job_id}",
                    rel="self",
                    type="application/json",
                    title="Job status",
                ),
            ],
        )

    except HTTPException:
        raise
    except WindmillError as e:
        logger.error(f"Error dismissing job: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/internal-error",
                "title": "Internal error",
                "status": 500,
                "detail": str(e),
            },
        )


# Create the router instance for export
processes_router = router
