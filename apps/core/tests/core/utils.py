import asyncio
import os
import random
import string
from typing import List
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.sql import text

from core.core.config import settings
from core.core.layer import get_user_table
from core.db.session import session_manager
from core.schemas.job import JobStatusType
from core.schemas.toolbox_base import ColumnStatisticsOperation


async def check_job_status(
    client: AsyncClient, job_id: str, target_status: str = JobStatusType.finished.value
):
    """Check if job is finished."""

    # Get job status recursively until they return status_simplified = finished
    max_retries = 60
    retry_delay = 1  # delay in seconds
    retries = 0

    while retries < max_retries:
        response = await client.get(f"{settings.API_V2_STR}/job/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["status_simple"] not in [
            JobStatusType.running.value,
            JobStatusType.pending.value,
        ]:
            break
        else:
            await asyncio.sleep(retry_delay)
            retries += 1

    # Make sure that the job finished within the allowed retries
    assert (
        retries < max_retries
    ), f"Job {job_id} did not finish within the allowed retries."
    # Make sure job is finished
    assert job["status_simple"] == target_status
    # Make sure each job_step is finished
    for job_step in job["status"]:
        assert job["status"][job_step]["status"] == target_status

    return job


async def check_if_job_failed(client: AsyncClient, job_id: str):
    """Check if job is failed."""

    # Get job status recursively until they return status_simplified = finished
    max_retries = 10
    retry_delay = 1  # delay in seconds
    retries = 0

    while retries < max_retries:
        response = await client.get(f"{settings.API_V2_STR}/job/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["status_simple"] not in [
            JobStatusType.running.value,
            JobStatusType.pending.value,
        ]:
            break
        else:
            await asyncio.sleep(retry_delay)
            retries += 1

    # Make sure that the job finished within the allowed retries
    assert (
        retries < max_retries
    ), f"Job {job_id} did not finish within the allowed retries."
    # Make sure job is failed
    assert job["status_simple"] == JobStatusType.failed.value
    # Make sure that one job_step is failed
    for job_step in job["status"]:
        if job["status"][job_step]["status"] == JobStatusType.failed.value:
            break

    return job


async def get_files_to_test(file_type: str) -> List[str]:
    """Get list of files based on file_type."""
    data_dir = f"tests/data/layers/valid/{file_type}"
    return os.listdir(data_dir)


async def upload_file(client: AsyncClient, file_dir: str) -> int:
    """Upload a single file and get its job ID."""
    with open(os.path.join(file_dir), "rb") as f:
        response = await client.post(
            f"{settings.API_V2_STR}/layer/file-upload", files={"file": f}
        )
    assert response.status_code == 201
    return response.json()


async def upload_valid_file(client: AsyncClient, file_type: str):
    """Validate valid file."""

    if file_type == "point":
        response = await upload_file(
            client,
            os.path.join(
                settings.TEST_DATA_DIR, "layers", "valid", "point", "valid.geojson"
            ),
        )
    elif file_type == "polygon":
        response = await upload_file(
            client,
            os.path.join(
                settings.TEST_DATA_DIR, "layers", "valid", "polygon", "valid.geojson"
            ),
        )
    elif file_type == "line":
        response = await upload_file(
            client,
            os.path.join(
                settings.TEST_DATA_DIR, "layers", "valid", "line", "valid.geojson"
            ),
        )
    elif file_type == "no_geometry":
        response = await upload_file(
            client,
            os.path.join(
                settings.TEST_DATA_DIR, "layers", "valid", "no_geometry", "valid.csv"
            ),
        )
    else:
        raise ValueError("file_type must be either point or table")
    return response


async def upload_valid_files(client: AsyncClient, file_type: str):
    """Validate valid files."""
    files = await get_files_to_test(file_type)

    dataset_ids = []
    for filename in files:
        file_dir = os.path.join(
            settings.TEST_DATA_DIR, "layers", "valid", file_type, filename
        )
        metadata = await upload_file(client, file_dir)
        dataset_ids.append(metadata["dataset_id"])

    return dataset_ids


async def upload_invalid_file(client: AsyncClient, file_type: str):
    """Validate invalid file."""

    # Get files to test
    data_dir = "tests/data/layers/invalid/" + file_type

    # Upload file by file and validate. Get response.
    response = await client.post(
        f"{settings.API_V2_STR}/layer/file-upload",
        files={"file": open(data_dir, "rb")},
    )
    assert response.status_code == 422

    return response.json()


async def get_with_wrong_id(client: AsyncClient, item: str):
    """Get item with wrong ID."""

    id = uuid4()
    response = await client.get(
        f"{settings.API_V2_STR}/{item}/{str(id)}",
    )
    assert response.status_code == 404


def generate_random_string(length):
    # Define the characters to use in the string
    characters = string.ascii_letters + string.digits
    # Generate the random string
    random_string = "".join(random.choice(characters) for i in range(length))
    return random_string


async def test_aggregate(
    client: AsyncClient,
    fixture,
    area_type,
    aggregate_type,
    statistics_field,
    group_by_field=None,
    filters=None,
    other_properties={},
):
    aggregation_layer_project_id = fixture.get("aggregation_layer_project_id")
    source_layer_project_id = fixture.get("source_layer_project_id")
    project_id = fixture.get("project_id")

    if filters:
        for i in filters:
            layer_project_id = i["layer_project_id"]
            filter = i["filter"]
            response = await client.put(
                f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_project_id}",
                json={
                    "query": {"cql": filter},
                },
            )
            assert response.status_code == 200

    # Request aggregate points endpoint
    for operation in ColumnStatisticsOperation:
        params = {
            "source_layer_project_id": source_layer_project_id,
            "area_type": area_type,
            "column_statistics": {"operation": operation.value},
            **other_properties,
        }
        if aggregation_layer_project_id:
            params["aggregation_layer_project_id"] = aggregation_layer_project_id
        if group_by_field:
            params["source_group_by_field"] = group_by_field
        if area_type == "h3_grid":
            params["h3_resolution"] = 10
        if operation != ColumnStatisticsOperation.count:
            params["column_statistics"]["field"] = statistics_field

        response = await client.post(
            f"{settings.API_V2_STR}/tool/aggregate-{aggregate_type}?project_id={project_id}",
            json=params,
        )
        assert response.status_code == 201
        job = await check_job_status(client, response.json()["job_id"])
        assert job["status_simple"] == "finished"


async def check_user_data_deleted(
    layer: dict,
):
    # Get table name
    table_name = get_user_table(layer)

    # Check if there is data for the layer_id
    async with session_manager.session() as session:
        result = await session.execute(
            text(
                f"""SELECT COUNT(*) FROM {table_name} WHERE layer_id = :layer_id LIMIT 1""",
            ),
            {"layer_id": layer["id"]},
        )
        assert result.scalar() == 0
