from datetime import datetime
from typing import Any, List
from uuid import UUID

from fastapi import HTTPException, status
from fastapi_pagination import Page
from fastapi_pagination import Params as PaginationParams
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from core.core.config import settings
from core.crud.base import CRUDBase
from core.db.models.job import Job
from core.schemas.common import OrderEnum
from core.schemas.error import ERROR_MAPPING, UnknownError
from core.schemas.job import JobStatusType, JobType, MsgType, job_mapping
from core.utils import sanitize_error_message


class CRUDJob(CRUDBase[Job, Any, Any]):
    async def check_and_create(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        job_type: JobType,
        project_id: UUID | None = None,
        read: bool | None = None,
    ) -> Job:
        """Create a job."""

        # Count running jobs using count.
        query = select(func.count(self.model.id)).where(
            and_(
                Job.user_id == user_id,
                Job.status_simple == JobStatusType.running.value,
            )
        )
        count = (await async_session.execute(query)).scalar()

        if count is None:
            raise ValueError("Unable to fetch job information")

        # Check if count is greater than or equal to MAX_NUMBER_PARALLEL_JOBS.
        if count >= settings.MAX_NUMBER_PARALLEL_JOBS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can only run {settings.MAX_NUMBER_PARALLEL_JOBS} jobs at a time.",
            )

        # Create job
        # Get job steps if job type is in job_mapping else create empty dict.
        if job_type not in job_mapping:
            job_status = {}
        else:
            job_status = job_mapping[job_type]().dict()

        job = Job(
            user_id=user_id,
            type=job_type,
            status=job_status,
            status_simple=JobStatusType.pending,
        )
        if project_id:
            job.project_id = project_id
        if read:
            job.read = read

        # Create job
        job = await self.create(db=async_session, obj_in=dict(job))
        return job

    async def update_status(
        self,
        async_session: AsyncSession,
        job_id: UUID,
        job_step_name: str,
        status: JobStatusType = JobStatusType.running,
        error: Exception | None = None,
        msg_text: str = "",
    ) -> Job:
        """Update job status."""

        # TODO: Find another way to avoid refetching the job again here.
        # Get job and check if job is killed. This is needed at the moment as the job is not updated in here but in the DB.
        job = await self.get(db=async_session, id=job_id)
        async_session.expire(job)
        job = await self.get(db=async_session, id=job_id)
        assert job is not None

        # Update job step
        job.status[job_step_name]["timestamp_end"] = str(datetime.now())
        job.status[job_step_name]["status"] = status

        # Populate job step msg
        msg_text = sanitize_error_message(msg_text.replace("'", "''"))
        job.status[job_step_name]["msg"] = {
            "type": MsgType.info.value,
            "text": msg_text,
        }
        if status == JobStatusType.finished:
            job.status_simple = JobStatusType.running
        else:
            job.status_simple = status

        # If error is not None population msg_simple
        if status == JobStatusType.failed:
            if error is None:
                error = UnknownError("Unknown error occurred.")
            else:
                # Define msg_simple
                if error.__class__ not in ERROR_MAPPING:
                    error = UnknownError("Unknown error occurred.")
            error_name = error.__class__.__name__
            error_message = str(error)
            job.msg_simple = f"{error_name}: {error_message}"
            flag_modified(job, "msg_simple")

        flag_modified(job, "status")
        flag_modified(job, "status_simple")

        # Update job
        job = await self.update(db=async_session, db_obj=job)
        return job

    async def get_by_date(
        self,
        async_session: AsyncSession,
        user_id: UUID,
        page_params: PaginationParams,
        project_id: UUID | None,
        job_type: List[JobType] | None,
        start_data: datetime | None,
        end_data: datetime | None,
        read: bool | None,
        order_by: str,
        order: OrderEnum,
    ) -> Page[Job]:
        """Get all jobs by date."""

        and_conditions = [Job.user_id == user_id]
        # User start and end date to filter jobs if available else get all jobs by user_id.
        if start_data and end_data:
            # Check if start date is before end date.
            if start_data > end_data:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Start date must be before end date.",
                )
            and_conditions.extend(
                [
                    Job.created_at >= start_data,
                    Job.created_at <= end_data,
                ]
            )
        if job_type:
            and_conditions.append(Job.type.in_(job_type))

        if read is not None:
            and_conditions.append(Job.read == read)

        if project_id is not None:
            and_conditions.append(Job.project_id == project_id)

        query = select(Job).where(and_(*and_conditions))
        jobs = await self.get_multi(
            async_session,
            query=query,
            page_params=page_params,
            order_by=order_by,
            order=order,
        )
        return jobs

    async def mark_as_read(
        self, async_session: AsyncSession, user_id: UUID, job_ids: List[UUID]
    ) -> List[Job]:
        """Mark a job as read."""

        # Get the jobs owned by the user and ids in the list.
        query_get = select(Job).where(
            and_(
                Job.id.in_(job_ids),
                Job.user_id == user_id,
                Job.status_simple.notin_(
                    [JobStatusType.pending.value, JobStatusType.running.value]
                ),
            )
        )
        jobs = [job[0] for job in (await self.get_multi(async_session, query=query_get))]

        # Create dict of len jobs with read=True.
        jobs_update = [{"read": True} for job in jobs]

        return await self.update_multi(async_session, db_objs=jobs, objs_in=jobs_update)


job = CRUDJob(Job)
