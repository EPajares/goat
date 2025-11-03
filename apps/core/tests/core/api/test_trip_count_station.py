import pytest
from core.core.config import settings
from core.schemas.toolbox_base import PTSupportedDay
from httpx import AsyncClient
from tests.utils import check_job_status


@pytest.mark.parametrize(
    "weekday,from_time,to_time",
    [
        (PTSupportedDay.weekday, 25200, 32400),
        (PTSupportedDay.saturday, 41400, 54000),
        (PTSupportedDay.sunday, 3600, 14400),
        (PTSupportedDay.weekday, 57600, 59400),
    ],
)
async def test_trip_count_station(
    client: AsyncClient,
    fixture_add_polygon_layer_to_project,
    weekday: str,
    from_time: int,
    to_time: int,
):
    # Generate sample layer for conducting the test
    project_id = fixture_add_polygon_layer_to_project["project_id"]
    reference_layer_project_id = fixture_add_polygon_layer_to_project[
        "layer_project_id"
    ]

    # Produce request payload
    params = {
        "reference_area_layer_project_id": reference_layer_project_id,
        "time_window": {
            "weekday": weekday,
            "from_time": from_time,
            "to_time": to_time,
        },
    }

    # Call endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/motorized-mobility/trip-count-station?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"
