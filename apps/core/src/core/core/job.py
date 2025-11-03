import asyncio
import datetime
import inspect
import logging
import uuid
from functools import wraps
from typing import Any, Awaitable, Callable, Dict
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import Settings, settings
from core.crud.crud_job import job as crud_job
from core.db.models.job import Job
from core.db.models.layer import LayerType
from core.schemas.error import ERROR_MAPPING, JobKilledError, TimeoutError, UnknownError
from core.schemas.job import JobStatusType
from core.schemas.layer import UserDataTable
from core.utils import table_exists

# Create a logger object for background tasks
background_logger = logging.getLogger("Background task")
background_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "\033[92m%(levelname)s\033[0m: %(asctime)s %(name)s %(message)s"
)
handler.setFormatter(formatter)
background_logger.addHandler(handler)


async def delete_orphan_data(
    async_session: AsyncSession, user_id: UUID, last_run: datetime.datetime
) -> None:
    """Delete orphan data from user tables"""

    for table in (
        UserDataTable.polygon,
        UserDataTable.line,
        UserDataTable.point,
        UserDataTable.no_geometry,
    ):
        table_name = f"{table.value}_{str(user_id).replace('-', '')}"

        # Check if table exists
        if not await table_exists(async_session, settings.USER_DATA_SCHEMA, table_name):
            print(f"Table {table_name} for {user_id} does not exist.")
            continue

        # Build condition for layer filtering
        if table == UserDataTable.no_geometry:
            condition = f"type = '{LayerType.table.value}'"
        else:
            condition = f"feature_layer_geometry_type = '{table.value}'"

        # Create temp table with layers owned by user
        await async_session.execute(text("DROP TABLE IF EXISTS temp_layer;"))
        temp_table_name = str(uuid.uuid4()).replace("-", "")
        sql_temp_layer_table = f"""
            CREATE TABLE temporal."{temp_table_name}" AS
            SELECT id
            FROM customer.layer
            WHERE {condition}
            AND user_id = '{str(user_id)}';
        """
        await async_session.execute(text(sql_temp_layer_table))
        await async_session.execute(
            text(f"""ALTER TABLE temporal."{temp_table_name}" ADD PRIMARY KEY(id);""")
        )
        await async_session.commit()

        # Get layer_ids to delete from user data table
        sql_layer_ids_to_delete = f"""
            SELECT DISTINCT d.layer_id
            FROM {settings.USER_DATA_SCHEMA}."{table_name}" d
            LEFT JOIN temporal."{temp_table_name}" l
            ON l.id = d.layer_id
            WHERE l.id IS NULL
            AND d.updated_at > '{last_run.isoformat()}';
        """
        layer_ids_to_delete = [
            row[0]
            for row in (
                await async_session.execute(text(sql_layer_ids_to_delete))
            ).fetchall()
        ]

        # Drop temp table
        await async_session.execute(
            text(f"""DROP TABLE IF EXISTS temporal."{temp_table_name}";""")
        )
        await async_session.commit()

        # Delete orphan data
        if len(layer_ids_to_delete) > 0:
            print(
                f"Orphan data for {table_name} with the following layer-ids: {layer_ids_to_delete}"
            )
            for layer_id in layer_ids_to_delete:
                # Delete orphan data
                sql_delete_orphan_data = f"""
                DELETE FROM {settings.USER_DATA_SCHEMA}."{table_name}"
                WHERE layer_id = '{str(layer_id)}';
                """
                await async_session.execute(text(sql_delete_orphan_data))
                await async_session.commit()
        else:
            print(f"No orphan data for {table_name}.")
    return


async def run_failure_func(
    instance: "CRUDFailedJob",
    func: Callable[[Any], Awaitable[Dict[str, Any]]],
    *args: Any,
    **kwargs: Any,
) -> None:
    # Get failure function
    failure_func_name = f"{func.__name__}_fail"  # Construct the failure function name
    failure_func = getattr(
        instance, failure_func_name, None
    )  # Get the failure function
    # Run failure function if exists
    if failure_func:
        # Merge args and kwargs
        args_dict = vars(args[0]) if args else {}
        args_check = {**args_dict, **kwargs}
        # Check for valid args
        valid_args = inspect.signature(failure_func).parameters.keys()
        func_args = {k: v for k, v in args_check.items() if k in valid_args}
        try:
            await failure_func(**func_args)
        except Exception as e:
            print(f"Failure function {failure_func_name} failed with error: {e}")
    else:
        # Get the delete orphan, delete temp tables function from class
        delete_temp_tables_func = getattr(instance, "delete_temp_tables", None)
        if not callable(delete_temp_tables_func):
            raise ValueError("Unable to fetch delete_temp_tables function from class.")
        delete_created_layers = getattr(instance, "delete_created_layers", None)
        if not callable(delete_created_layers):
            raise ValueError(
                "Unable to fetch delete_created_layers function from class."
            )
        # Delete all orphan data that is older then 20 minutes
        min_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            minutes=20
        )
        await delete_orphan_data(
            async_session=instance.async_session,
            user_id=instance.user_id,
            last_run=min_time,
        )
        # Run delete temp tables function
        await delete_temp_tables_func()
        # Delete all layers created by the job
        await delete_created_layers()


def job_init() -> Callable[[Any], Any]:
    def decorator(
        func: Callable[[Any], Awaitable[Dict[str, Any]]], timeout: int = 1
    ) -> Callable[[Any], Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any] | None:
            self = args[0]
            # Check if job_id and async_session are provided in kwards else search them in the class
            if kwargs.get("async_session"):
                async_session = kwargs["async_session"]
            else:
                async_session = self.async_session

            if kwargs.get("job_id"):
                job_id = kwargs["job_id"]
            else:
                job_id = self.job_id
            background_logger.info(f"Job {str(job_id)} started.")
            # Get job id
            job: Job | None = await crud_job.get(db=async_session, id=job_id)
            if job is None:
                raise ValueError(f"Job with id {job_id} not found.")
            job = await crud_job.update(
                db=async_session,
                db_obj=job,
                obj_in={"status_simple": JobStatusType.running.value},
            )

            # Execute function
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                # Roll back the transaction
                await async_session.rollback()
                # Run failure functions for cleanup
                await run_failure_func(self, func, *args, **kwargs)
                # Define msg_simple
                if e.__class__ in ERROR_MAPPING:
                    error = e
                else:
                    error = UnknownError("Unknown error occurred.")
                msg_simple = f"{error.__class__.__name__}: {str(error)}"
                # Update job status simple to failed
                job = await crud_job.update(
                    db=async_session,
                    db_obj=job,
                    obj_in={
                        "status_simple": JobStatusType.failed.value,
                        "msg_simple": msg_simple,
                    },
                )
                return None

            # Update job status to finished in case it is not killed, timeout or failed
            if result["status"] not in [
                JobStatusType.killed.value,
                JobStatusType.timeout.value,
                JobStatusType.failed.value,
            ]:
                if kwargs.get("params"):
                    payload = {
                        "status_simple": JobStatusType.finished.value,
                        "payload": kwargs["params"].json(exclude_none=True),
                    }
                else:
                    payload = {"status_simple": JobStatusType.finished.value}

                job = await crud_job.update(
                    db=async_session,
                    db_obj=job,
                    obj_in=payload,
                )
                try:
                    # Get the delete temp tables function from class
                    delete_temp_tables_func = getattr(self, "delete_temp_tables", None)
                    if not callable(delete_temp_tables_func):
                        raise ValueError(
                            "Unable to fetch delete_temp_tables function from class."
                        )

                    # Run delete temp tables function
                    await delete_temp_tables_func()
                except Exception:
                    # Don't cause the job to fail if the temp tables can't be deleted
                    background_logger.warn(
                        f"Job {str(job_id)} failed to cleanup temp tables."
                    )

            background_logger.info(f"Job {job_id} finished.")
            return result

        return wrapper

    return decorator


def job_log(
    job_step_name: str, timeout: int = settings.JOB_TIMEOUT_DEFAULT
) -> Callable[
    [Callable[..., Awaitable[Dict[str, Any]]]], Callable[..., Awaitable[Dict[str, Any]]]
]:
    def decorator(
        func: Callable[..., Awaitable[Dict[str, Any]]],
    ) -> Callable[..., Awaitable[Dict[str, Any]]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            # Get async_session
            self = args[0] if args else None
            if not self:
                raise ValueError("Job started from unsupported class.")
            # Check if job_id and async_session are provided in kwards else search them in the class
            job_id: UUID
            if kwargs.get("job_id"):
                job_id = kwargs["job_id"]
            else:
                if not self or not hasattr(self, "job_id"):
                    raise ValueError("Job ID is required.")
                job_id = self.job_id
            # Get async_session
            async_session: Any
            if kwargs.get("async_session"):
                async_session = kwargs["async_session"]
            else:
                if not self or not hasattr(self, "async_session"):
                    raise ValueError("Async session is required.")
                async_session = self.async_session
            # Update job status to indicate running
            job = await crud_job.update_status(
                async_session=async_session,
                job_id=job_id,
                status=JobStatusType.running,
                msg_text="Job is running.",
                job_step_name=job_step_name,
            )
            # Exit if job is killed before starting
            if job.status_simple == JobStatusType.killed.value:
                await run_failure_func(self, func, **kwargs)
                msg_text = "Job was killed."
                background_logger.error(msg_text)
                return {"status": JobStatusType.killed.value, "msg": msg_text}
            # Execute function
            try:
                result: Dict[str, Any] = await asyncio.wait_for(
                    func(*args, **kwargs), timeout
                )
            except asyncio.TimeoutError:
                # Roll back the transaction
                await async_session.rollback()
                # Handle the timeout here. For example, you can raise a custom exception or log it.
                await run_failure_func(self, func, *args, **kwargs)
                # Update job status to indicate timeout
                msg_text = f"Job timed out after {timeout} seconds."
                job = await crud_job.update_status(
                    async_session=async_session,
                    job_id=job_id,
                    status=JobStatusType.timeout,
                    msg_text=msg_text,
                    job_step_name=job_step_name,
                )
                background_logger.error(msg_text)
                raise TimeoutError(msg_text)
            except Exception as e:
                # Roll back the transaction
                await async_session.rollback()
                # Run failure function if exists
                await run_failure_func(self, func, *args, **kwargs)
                # Update job status simple to failed
                job = await crud_job.update_status(
                    async_session=async_session,
                    job_id=job_id,
                    status=JobStatusType.failed,
                    msg_text=str(e),
                    error=e,
                    job_step_name=job_step_name,
                )
                background_logger.error(f"Job failed with error: {e}")
                raise e
            # Check if job was killed. The job needs to be expired as it was fetching old data from cache.
            async_session.expire(job)
            job_obj = await crud_job.get(db=async_session, id=job_id)
            if job_obj is None:
                raise ValueError(f"Job with id {job_id} not found.")
            job = job_obj
            if job.status_simple == JobStatusType.killed.value:
                status = JobStatusType.killed
                msg_text = "Job was killed."
            # Else use the status provided by the function
            else:
                if result["status"] == JobStatusType.failed.value:
                    status = JobStatusType.failed
                    msg_text = result["msg"]
                elif result["status"] == JobStatusType.finished.value:
                    status = JobStatusType.finished
                    msg_text = "Job finished successfully."
                else:
                    raise ValueError(
                        f"Invalid status {result['status']} returned by function {func.__name__}."
                    )
            # Update job status if successful
            job = await crud_job.update_status(
                async_session=async_session,
                job_id=job_id,
                status=status,
                job_step_name=job_step_name,
                msg_text=msg_text,
            )
            # Check if job is killed and run failure function if exists
            if job.status_simple in [
                JobStatusType.killed.value,
                JobStatusType.failed.value,
            ]:
                # Roll back the transaction
                await async_session.rollback()
                # Run failure function if exists
                await run_failure_func(self, func, *args, **kwargs)
                msg_txt = "Job was killed"
                print(msg_txt)
                raise JobKilledError(msg_txt)
            background_logger.info(f"Job step {job_step_name} finished successfully.")
            return result

        return wrapper

    return decorator


def run_background_or_immediately(settings: Settings) -> Callable[[Any], Any]:
    def decorator(
        func: Callable[[Any], Awaitable[Dict[str, Any]]],
    ) -> Callable[[Any], Dict[str, Any] | Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any] | Any:
            # Get background tasks either from class or from function kwargs

            if kwargs.get("background_tasks"):
                background_tasks = kwargs["background_tasks"]
            else:
                background_tasks = args[0].background_tasks

            if settings.RUN_AS_BACKGROUND_TASK is False:
                return await func(*args, **kwargs)
            else:
                return background_tasks.add_task(func, *args, **kwargs)

        return wrapper

    return decorator


class CRUDFailedJob:
    """CRUD class that bundles functions for failed jobs"""

    def __init__(
        self,
        job_id: UUID | None,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
    ) -> None:
        self.job_id = job_id
        self.background_tasks = background_tasks
        self.async_session = async_session
        self.user_id = user_id

    async def delete_orphan_data(self) -> None:
        """Delete orphan data from user tables"""

        await delete_orphan_data(
            async_session=self.async_session,
            user_id=self.user_id,
            last_run=datetime.datetime.now(datetime.timezone.utc),
        )

    async def delete_temp_tables(self) -> None:
        # Get all tables that end with the job id
        sql = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'temporal'
            AND table_name LIKE '%{str(self.job_id).replace('-', '')}'
        """
        res = await self.async_session.execute(text(sql))
        tables = res.fetchall()
        # Delete all tables
        for table in tables:
            await self.async_session.execute(
                text(f"DROP TABLE IF EXISTS temporal.{table[0]} CASCADE;")
            )
        await self.async_session.commit()

    async def delete_created_layers(self) -> None:
        # Delete all layers with the self.job_id
        sql = f"""
            DELETE FROM {settings.CUSTOMER_SCHEMA}.layer
            WHERE job_id = '{str(self.job_id)}'
        """
        await self.async_session.execute(text(sql))
        await self.async_session.commit()
