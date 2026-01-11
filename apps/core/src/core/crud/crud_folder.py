from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.folder import Folder
from core.schemas.error import FolderNotFoundError
from core.schemas.folder import FolderCreate, FolderUpdate

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

        # Remove folder (cascades to layer records)
        await self.remove(async_session, id=db_obj[0].id)


folder = CRUDFolder(Folder)
