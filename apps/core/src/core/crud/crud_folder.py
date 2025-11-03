from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.job import crud_job
from core.crud.crud_layer import CRUDDataDelete
from core.db.models.folder import Folder
from core.schemas.error import FolderNotFoundError
from core.schemas.folder import FolderCreate, FolderUpdate
from core.schemas.job import JobType

from .base import CRUDBase


class CRUDFolder(CRUDBase[Folder, FolderCreate, FolderUpdate]):
    async def delete(
        self,
        async_session: AsyncSession,
        background_tasks: BackgroundTasks,
        *,
        id: UUID,
        user_id: UUID,
    ) -> None:
        db_obj = await self.get_by_multi_keys(
            async_session,
            keys={"id": id, "user_id": user_id},
            extra_fields=[Folder.layers],
        )
        # Check if folder exists
        if len(db_obj) == 0:
            raise FolderNotFoundError("Folder not found")

        # Get all layers with the folder_id
        layers = db_obj[0].layers
        await self.remove(async_session, id=db_obj[0].id)

        # Create job and check if user can create a new job
        job = await crud_job.check_and_create(
            async_session=async_session,
            user_id=user_id,
            job_type=JobType.data_delete_multi,
            read=True,
        )

        # Delete data from all layers
        await CRUDDataDelete(
            async_session=async_session,
            job_id=job.id,
            user_id=user_id,
            background_tasks=background_tasks,
        ).delete_multi_run(async_session=async_session, layers=layers)


folder = CRUDFolder(Folder)
