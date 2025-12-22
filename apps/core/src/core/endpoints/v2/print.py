"""
Print Report Endpoints
"""

from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Path, Request
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.crud_print_report import start_print_job
from core.deps.auth import auth_z
from core.endpoints.deps import get_db, get_user_id
from core.schemas.print import PrintReportRequest, request_examples

router = APIRouter()


def get_access_token(request: Request) -> str | None:
    """Extract access token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


@router.post(
    "/{project_id}/print",
    summary="Generate a print/PDF from a report layout",
    response_model=Dict[str, Any],
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def create_print_job(
    *,
    request: Request,
    async_session: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks,
    user_id: UUID4 = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    params: PrintReportRequest = Body(..., example=request_examples["print_single"]),
) -> Dict[str, Any]:
    """
    Start a background job to generate a PDF/PNG from a report layout.

    The job will:
    1. Navigate to the print preview page using Playwright
    2. Wait for the page to fully render (including maps)
    3. Capture the page as PDF or PNG
    4. Upload to S3
    5. Return a download URL in the job payload

    Poll the job status using GET /api/v2/job/{job_id} to check progress.
    When status is 'finished', the payload will contain the download_url.
    """
    # Get access token to pass to Playwright for authenticated API calls
    access_token = get_access_token(request)

    return await start_print_job(
        async_session=async_session,
        user_id=user_id,
        background_tasks=background_tasks,
        project_id=project_id,
        params=params,
        access_token=access_token,
    )


@router.get(
    "/{project_id}/print/{job_id}/download",
    summary="Get a fresh download URL for a print job",
    response_model=Dict[str, Any],
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def get_print_download_url(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
    ),
    job_id: UUID4 = Path(
        ...,
        description="The ID of the print job",
    ),
) -> Dict[str, Any]:
    """
    Get a fresh presigned download URL for a completed print job.

    The stored download URL expires after 1 hour. Use this endpoint
    to get a new URL if the original has expired.
    """
    from fastapi import HTTPException

    from core.core.config import settings
    from core.crud.crud_job import job as crud_job
    from core.services.s3 import s3_service

    # Get the job
    job = await crud_job.get(db=async_session, id=job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this job")

    if job.project_id != project_id:
        raise HTTPException(
            status_code=400, detail="Job does not belong to this project"
        )

    if job.status_simple != "finished":
        raise HTTPException(status_code=400, detail="Job is not finished")

    if not job.payload:
        raise HTTPException(status_code=400, detail="Job has no payload")

    # Parse payload if it's a string
    payload = job.payload
    if isinstance(payload, str):
        import json

        payload = json.loads(payload)

    s3_key = payload.get("s3_key")
    if not s3_key:
        raise HTTPException(
            status_code=400, detail="Job payload does not contain s3_key"
        )

    file_name = payload.get("file_name", "report.pdf")

    # Generate a fresh presigned URL with Content-Disposition to force download
    download_url = s3_service.generate_presigned_download_url(
        bucket_name=settings.S3_BUCKET_NAME or "goat",
        s3_key=s3_key,
        expires_in=3600,  # 1 hour
        filename=file_name,  # Forces browser to download instead of display
    )

    return {
        "download_url": download_url,
        "file_name": file_name,
    }
