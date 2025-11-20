import logging
from pathlib import Path

from sqlalchemy import text

from core.core.config import settings
from core.db.session import session_manager

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
SQL_FOLDER = BASE_DIR / "triggers"


async def init_triggers() -> None:
    """
    Initialize PostgreSQL triggers by executing all SQL files
    in the triggers folder using the async session_manager.
    """

    if settings.ASYNC_SQLALCHEMY_DATABASE_URI is None:
        raise ValueError("PostgreSQL database URI not configured.")

    sql_files = sorted(SQL_FOLDER.glob("*.sql"))
    if not sql_files:
        logger.info("No SQL trigger files found.")
        return

    # Use the async session manager
    async with session_manager.session() as session:
        try:
            for file_path in sql_files:
                logger.info(f"Executing trigger: {file_path.name}")
                sql_text = file_path.read_text()

                await session.execute(text(sql_text))

            await session.commit()
            logger.info("All SQL triggers applied successfully.")

        except Exception as e:
            logger.error("Error applying triggers — transaction rolled back.")
            logger.exception(e)
            await session.rollback()
            raise
