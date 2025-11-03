import asyncio
from datetime import datetime, timezone

from core.core.config import settings
from core.db.session import session_manager
from core.scripts.utils import fetch_last_run_timestamp, update_last_run_timestamp
from core.utils import print_info, print_warning
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

SYSTEM_TASK_ID = "delete_temp_tables"
COMMENT_TEXT = "EXISTED BEFORE: "
MAX_RETENTION_MINUTES = 60  # minutes


async def delete_old_temp_tables_query(
    async_session: AsyncSession, current_run: datetime
) -> None:
    print_info("Deleting old temporary tables")
    # Get all tables in schema temporal that are older than max_retention_minutes in comments skip table with not matching comment
    result = await async_session.execute(
        text(
            f"""
                WITH to_delete AS
                (
                    SELECT pg_class.relname AS table_name,
                    pg_description.description AS COMMENT,
                    CASE
                        WHEN regexp_match(pg_description.description, '{COMMENT_TEXT}') IS NOT NULL
                        THEN regexp_replace(pg_description.description, '{COMMENT_TEXT}', '', 'g')::timestamp
                        ELSE NULL
                    END AS existed_at
                    FROM pg_description
                    JOIN pg_class ON pg_description.objoid = pg_class.oid
                    JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
                    WHERE pg_namespace.nspname = 'temporal'
                )
                SELECT table_name
                FROM to_delete
                WHERE '{str(current_run)}' - existed_at > interval '{MAX_RETENTION_MINUTES} minutes'
            """
        )
    )
    tables = result.all()
    tables = list(tables)

    # Drop all tables in schema temporal that are older than max_retention_minutes
    if len(tables) > 0:
        for table in tables:
            await async_session.execute(
                text(
                    f"""
                        DROP TABLE temporal."{table[0]}";
                    """
                )
            )
            await async_session.commit()
            print_info(f"Table {table[0]} has been deleted.")
    else:
        print_info("No tables to delete.")


async def label_tables_for_deletion(
    async_session: AsyncSession, current_run: datetime
) -> None:
    print_info("Labeling tables without comments for deletion on next run")

    # Add comment to all tables in schema 'temporal' that do not have a comment
    await async_session.execute(
        text(
            f"""
            DO $$
            DECLARE
                tbl TEXT;
                schema_name TEXT := 'temporal';
                comment_text TEXT := '{COMMENT_TEXT}' || '{str(current_run)}';
            BEGIN
                FOR tbl IN
                    SELECT t.table_name
                    FROM information_schema.tables t
                    LEFT JOIN pg_catalog.pg_description d ON d.objoid = (SELECT oid FROM pg_catalog.pg_class WHERE relname = t.table_name AND relnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = schema_name))
                    WHERE t.table_schema = schema_name AND d.description IS NULL
                LOOP
                    EXECUTE format('COMMENT ON TABLE %I.%I IS %L;', schema_name, tbl, comment_text);
                END LOOP;
            END $$;
            """
        )
    )
    await async_session.commit()

    # Print tables with comments not matching the expected format
    result = await async_session.execute(
        text(
            f"""
            SELECT t.table_schema, t.table_name, d.description
            FROM information_schema.tables t
            JOIN pg_catalog.pg_description d ON d.objoid = (SELECT oid FROM pg_catalog.pg_class WHERE relname = t.table_name AND relnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = t.table_schema))
            WHERE t.table_schema = 'temporal'
            AND d.description NOT LIKE '{COMMENT_TEXT}%'
            """
        )
    )
    tables = result.fetchall()
    if tables:
        print_info("Find tables with comments not matching the expected format")
        for table in tables:
            print_warning(f"Schema: {table[0]}, Table: {table[1]}, Comment: {table[2]}")
    else:
        print_info("No tables with comments not matching the expected format.")


async def main() -> None:
    session_manager.init(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    async with session_manager.session() as async_session:
        # Get timestamp of last run
        system_task, last_run = await fetch_last_run_timestamp(
            async_session, SYSTEM_TASK_ID
        )
        current_run = datetime.now(timezone.utc)

        # Delete all table that have COMMENT_TEXT in their comment
        await delete_old_temp_tables_query(async_session, current_run=current_run)
        # Label all tables in schema temporal for deletion to prepare for next run
        await label_tables_for_deletion(async_session, current_run=current_run)
        # Set last run timestamp to current time
        await update_last_run_timestamp(async_session, system_task, current_run)
    await session_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
