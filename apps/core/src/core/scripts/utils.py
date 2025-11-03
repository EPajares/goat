from datetime import datetime, timedelta, timezone

from core.crud.base import CRUDBase
from core.db.models.system_task import SystemTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel


async def fetch_last_run_timestamp(
    async_session: AsyncSession, system_task_id: str
) -> tuple[SQLModel | None, datetime]:
    """Fetch the last run timestamp of the thumbnail update task."""

    result = await CRUDBase(SystemTask).get(async_session, system_task_id)
    return result, (
        result.last_run
        if result is not None
        and isinstance(result, SystemTask)
        and hasattr(result, "last_run")
        else datetime.now(timezone.utc) - timedelta(minutes=5)
    )


async def update_last_run_timestamp(
    async_session: AsyncSession,
    system_task: SQLModel,
    new_timestamp: datetime,
) -> None:
    """Update the last run timestamp of the thumbnail update task."""

    await CRUDBase(SystemTask).update(
        db=async_session,
        db_obj=system_task,
        obj_in={"last_run": new_timestamp},
    )
