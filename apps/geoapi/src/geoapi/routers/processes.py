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

from geoapi.config import settings
from geoapi.deps.auth import get_user_id, oauth2_scheme
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


def get_language_from_request(request: Request) -> str:
    """Extract language from Accept-Language header.

    Returns the first supported language or 'en' as default.
    """
    accept_language = request.headers.get("accept-language", "en")
    # Parse first language preference (e.g., "de-DE,de;q=0.9,en;q=0.8" -> "de")
    if accept_language:
        first_lang = accept_language.split(",")[0].split(";")[0].strip()
        # Extract base language (e.g., "de-DE" -> "de")
        lang_code = first_lang.split("-")[0].lower()
        if lang_code in ("en", "de"):  # Supported languages
            return lang_code
    return "en"


@router.get(
    "/processes",
    summary="List available processes",
    response_model=ProcessList,
)
async def list_processes(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> ProcessList:
    """Get list of all available processes (analytics + async tools).

    Supports i18n via Accept-Language header (en, de).
    """
    base_url = get_base_url(request)
    language = get_language_from_request(request)

    # Get analytics processes (sync) - auto-generated from goatlib schemas
    analytics_summaries = analytics_registry.get_all_summaries(base_url, language)

    # Get async tool processes from registry (with translations)
    tool_list = tool_registry.get_process_list(base_url, limit=limit, language=language)

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
    """Get detailed description of a specific process.

    Supports i18n via Accept-Language header (en, de).
    Returns x-ui-sections and x-ui field metadata for dynamic UI rendering.
    """
    base_url = get_base_url(request)
    language = get_language_from_request(request)

    # Check analytics processes first (auto-generated from goatlib schemas)
    if analytics_registry.is_analytics_process(process_id):
        return analytics_registry.get_process_description(
            process_id, base_url, language
        )

    # Check async tool processes (with translations)
    process_desc = tool_registry.get_process_description(
        process_id, base_url, language=language
    )

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
    access_token: str | None = Depends(oauth2_scheme),
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

    # Use the windmill_path from the registry (ensures correct casing)
    script_path = tool_info.windmill_path

    # Add user_id to inputs for job tracking
    job_inputs = {**execute_request.inputs, "user_id": str(user_id)}

    # Pass access_token to print_report for Playwright authentication
    if process_id == "print_report" and access_token:
        job_inputs["access_token"] = access_token

    # Auto-populate od_matrix_path for heatmap tools based on routing_mode
    # This allows the field to be hidden in the UI while still being required by the analysis
    if (
        "od_matrix_path" not in job_inputs or job_inputs.get("od_matrix_path") is None
    ) and "routing_mode" in job_inputs:
        routing_mode = job_inputs["routing_mode"]
        job_inputs["od_matrix_path"] = (
            f"{settings.TRAVELTIME_MATRICES_DIR}/{routing_mode}/"
        )

    # Submit job to Windmill
    # Note: Worker tag is configured on the script during sync, not per-job
    try:
        job_id = await windmill_client.run_script_async(
            script_path=script_path,
            args=job_inputs,
        )

        logger.info(f"Job {job_id} created for process {process_id} by user {user_id}")

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
        inputs=job.get("args"),
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
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> JobList:
    """List all jobs for the authenticated user from the last 3 days.

    Jobs are queried directly from Windmill using efficient indexed filters.
    """
    base_url = get_base_url(request)

    try:
        # Map OGC status to Windmill filters
        success_filter: bool | None = None
        running_filter: bool | None = None
        if status == "successful":
            success_filter = True
        elif status == "failed":
            success_filter = False
        elif status == "running":
            running_filter = True

        # Query Windmill directly with efficient filters
        windmill_jobs = await windmill_client.list_jobs_filtered(
            user_id=str(user_id),
            script_path_start="f/goat/",
            created_after_days=3,
            process_id=process_id,
            success=success_filter,
            running=running_filter,
            limit=limit,
        )

        # Convert Windmill jobs to OGC StatusInfo
        jobs = []
        for wm_job in windmill_jobs:
            status_info = _windmill_job_to_status_info(wm_job, base_url)
            # Include result for successful jobs
            if wm_job.get("success") is True and wm_job.get("result"):
                status_info.result = wm_job.get("result")
            jobs.append(status_info)

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

    except WindmillError as e:
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


def _verify_job_ownership(job: dict[str, Any], user_id: UUID) -> bool:
    """Verify that a job belongs to the specified user.

    Checks the user_id in the job's args against the authenticated user.

    Args:
        job: Windmill job dict
        user_id: Authenticated user's UUID

    Returns:
        True if job belongs to user, False otherwise
    """
    job_args = job.get("args", {})
    job_user_id = job_args.get("user_id")
    return job_user_id == str(user_id)


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
        # Get job directly from Windmill
        windmill_job = await windmill_client.get_job_with_result(job_id)

        # Verify user owns this job (check user_id in args)
        if not _verify_job_ownership(windmill_job, user_id):
            raise HTTPException(
                status_code=404,
                detail={
                    "type": OGC_EXCEPTION_NO_SUCH_JOB,
                    "title": "Job not found",
                    "status": 404,
                    "detail": f"Job '{job_id}' not found",
                },
            )

        # Convert to StatusInfo
        status_info = _windmill_job_to_status_info(windmill_job, base_url)

        # Include result for successful jobs
        if windmill_job.get("success") is True and windmill_job.get("result"):
            status_info.result = windmill_job.get("result")

        return status_info

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
        # Get job directly from Windmill
        job = await windmill_client.get_job_status(job_id)

        # Verify user owns this job
        if not _verify_job_ownership(job, user_id):
            raise HTTPException(
                status_code=404,
                detail={
                    "type": OGC_EXCEPTION_NO_SUCH_JOB,
                    "title": "Job not found",
                    "status": 404,
                    "detail": f"Job '{job_id}' not found",
                },
            )

        # Check job status
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
        # Get job directly from Windmill
        job = await windmill_client.get_job_status(job_id)

        # Verify user owns this job
        if not _verify_job_ownership(job, user_id):
            raise HTTPException(
                status_code=404,
                detail={
                    "type": OGC_EXCEPTION_NO_SUCH_JOB,
                    "title": "Job not found",
                    "status": 404,
                    "detail": f"Job '{job_id}' not found",
                },
            )

        # Cancel if still running
        status = _windmill_status_to_ogc(job)
        if status in (StatusCode.accepted, StatusCode.running):
            try:
                await windmill_client.cancel_job(job_id, "User requested dismissal")
            except WindmillError:
                pass  # Job might have just finished

        # Parse timestamps for response
        created = None
        if job.get("created_at"):
            try:
                created = datetime.fromisoformat(
                    job["created_at"].replace("Z", "+00:00")
                )
            except Exception:
                pass

        process_id = job.get("script_path", "").replace("f/goat/", "")

        # Build response
        return StatusInfo(
            processID=process_id if process_id else None,
            type="process",
            jobID=job_id,
            status=StatusCode.dismissed,
            message="Job dismissed",
            created=created,
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
