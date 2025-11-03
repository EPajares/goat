import asyncio
from datetime import datetime, timezone

from core.core.config import settings
from core.core.job import delete_orphan_data
from core.crud.crud_user import user as crud_user
from core.db.session import session_manager
from core.scripts.utils import fetch_last_run_timestamp, update_last_run_timestamp
from sqlalchemy.ext.asyncio import AsyncSession

SYSTEM_TASK_ID = "delete_orphan"


async def bulk_delete_orphan(async_session: AsyncSession, last_run: datetime) -> None:
    """Delete orphaned data from the database."""

    users = await crud_user.get_all(async_session)
    user_ids = [user.id for user in users]

    for user_id in user_ids:
        await delete_orphan_data(async_session, user_id, last_run=last_run)


async def main() -> None:
    session_manager.init(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    async with session_manager.session() as async_session:
        # Get timestamp of last run
        system_task, last_run = await fetch_last_run_timestamp(
            async_session, SYSTEM_TASK_ID
        )
        current_run = datetime.now(timezone.utc)

        # Delete orphaned data
        await bulk_delete_orphan(async_session, last_run=last_run)

        if not system_task:
            raise ValueError(f"System task with ID {SYSTEM_TASK_ID} not found.")

        # Set last run timestamp to current time
        await update_last_run_timestamp(async_session, system_task, current_run)
    await session_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
