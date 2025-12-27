from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select

from core.core.layer import CRUDLayerBase
from core.db.models._link_model import LayerProjectGroup
from core.db.session import AsyncSession
from core.schemas.project import ILayerProjectGroupCreate, ILayerProjectGroupUpdate


class CRUDLayerProjectGroup(CRUDLayerBase):
    async def get(
        self, async_session: AsyncSession, id: UUID
    ) -> Optional[LayerProjectGroup]:
        return await async_session.get(LayerProjectGroup, id)

    async def get_groups_by_project(
        self, async_session: AsyncSession, project_id: UUID
    ) -> list[LayerProjectGroup]:
        """Get all layer groups for a project"""
        query = select(LayerProjectGroup).where(
            LayerProjectGroup.project_id == project_id
        )
        result = await async_session.execute(query)
        return result.scalars().all()

    async def create(
        self,
        async_session: AsyncSession,
        project_id: UUID,
        obj_in: ILayerProjectGroupCreate,
    ) -> LayerProjectGroup:
        # 1. Depth Validation
        if obj_in.parent_id:
            parent_group = await async_session.get(LayerProjectGroup, obj_in.parent_id)
            if not parent_group:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, detail="Parent group not found"
                )

            # Explain:
            # Level 1: parent_id is None
            # Level 2: parent_id is Level 1.
            # Level 3 (Forbidden): parent_id is Level 2.

            if parent_group.parent_id is not None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Maximum nesting level reached (Max 2 levels)",
                )

            if parent_group.project_id != project_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Parent group belongs to another project",
                )

        # 2. Creation
        db_obj = LayerProjectGroup(**obj_in.model_dump(), project_id=project_id)
        async_session.add(db_obj)
        await async_session.commit()
        await async_session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        async_session: AsyncSession,
        db_obj: LayerProjectGroup,
        obj_in: ILayerProjectGroupUpdate,
    ) -> LayerProjectGroup:
        update_data = obj_in.model_dump(exclude_unset=True)

        # If moving to a new parent, run depth check logic again
        if "parent_id" in update_data and update_data["parent_id"] is not None:
            if update_data["parent_id"] == db_obj.id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, detail="Cannot set parent to self"
                )

            parent_group = await async_session.get(
                LayerProjectGroup, update_data["parent_id"]
            )
            if parent_group.parent_id is not None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, detail="Maximum nesting level reached"
                )

        for key, value in update_data.items():
            setattr(db_obj, key, value)

        async_session.add(db_obj)
        await async_session.commit()
        await async_session.refresh(db_obj)
        return db_obj

    async def remove(self, async_session: AsyncSession, id: UUID) -> None:
        obj = await async_session.get(LayerProjectGroup, id)
        if obj:
            await async_session.delete(obj)
            await async_session.commit()


layer_project_group = CRUDLayerProjectGroup(LayerProjectGroup)
