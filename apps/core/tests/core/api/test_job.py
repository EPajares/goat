import pytest
from core.core.config import settings
from httpx import AsyncClient
from tests.utils import get_with_wrong_id, upload_valid_files


@pytest.mark.asyncio
async def test_get_job(client: AsyncClient, fixture_create_feature_layer):
    job_id = fixture_create_feature_layer["job_id"]
    response = await client.get(f"{settings.API_V2_STR}/job/{job_id}")
    assert response.status_code == 200
    assert response.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_job_wrong_id(client: AsyncClient, fixture_create_feature_layer):
    await get_with_wrong_id(client, "job")


@pytest.mark.asyncio
async def test_get_jobs(client: AsyncClient, fixture_create_user):
    await upload_valid_files(client, "point")
    response = await client.get(f"{settings.API_V2_STR}/job")
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_mark_jobs_as_read(client: AsyncClient, fixture_create_feature_layer):
    response = await client.put(
        f"{settings.API_V2_STR}/job/read",
        json=[fixture_create_feature_layer["job_id"]],
    )
    assert response.status_code == 200
    assert response.json()[0]["read"] is True


# @pytest.mark.asyncio
# async def test_kill_job(client: AsyncClient, fixture_create_user):
#     # # Create large geojson file out of valid.geojson by duplicating the features
#     # with open("tests/data/layers/valid/point/valid.geojson", "r") as f:
#     #     data = f.read()
#     # with open("tests/data/layers/valid/point/valid_large.geojson", "w") as ff:
#     #     features_to_add = json.loads(data)["features"]
#     #     features = []
#     #     for i in range(1500):
#     #         features += features_to_add
#     #     new_data = json.loads(data)
#     #     new_data["features"] = features
#     #     ff.write(json.dumps(new_data))

#     # Upload large geojson file
#     validate_job_id = await upload_and_get_job_id(client, "point", "test.gpkg")

#     response = await client.post(
#         f"{settings.API_V2_STR}/layer/file-import",
#         json={"validate_job_id": validate_job_id},
#     )
#     assert response.status_code == 201
#     job_id = response.json()["job_id"]

#     response = await client.put(f"{settings.API_V2_STR}/job/kill/{job_id}")
#     assert response.status_code == 200
#     assert response.json()["status_simple"] == JobStatusType.killed
#     step_status = ""
#     status = response.json()["status"]
#     for job_step in response.json()["status"]:
#         status_step = status[job_step]
#         if status_step["status"] == JobStatusType.killed:
#             step_status = status_step["status"]
#     assert step_status == JobStatusType.killed
