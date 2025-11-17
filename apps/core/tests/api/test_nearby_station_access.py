from typing import List

import pytest
from core.core.config import settings
from core.schemas.catchment_area import (
    CatchmentAreaRoutingModeActiveMobility,
    CatchmentAreaRoutingModePT,
)
from core.schemas.toolbox_base import PTSupportedDay
from httpx import AsyncClient
from tests.utils import check_job_status


@pytest.mark.parametrize(
    "starting_points_type,access_mode,speed,max_traveltime,mode,weekday,from_time,to_time",
    [
        (
            "point_single",
            CatchmentAreaRoutingModeActiveMobility.walking,
            5,
            15,
            [
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.rail,
            ],
            PTSupportedDay.weekday,
            25200,
            32400,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeActiveMobility.pedelec,
            23,
            8,
            [
                CatchmentAreaRoutingModePT.funicular,
                CatchmentAreaRoutingModePT.gondola,
                CatchmentAreaRoutingModePT.bus,
            ],
            PTSupportedDay.sunday,
            61200,
            79200,
        ),
        (
            "point_multiple",
            CatchmentAreaRoutingModeActiveMobility.walking,
            7,
            13,
            [
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.rail,
            ],
            PTSupportedDay.saturday,
            25200,
            32400,
        ),
        (
            "point_multiple",
            CatchmentAreaRoutingModeActiveMobility.bicycle,
            15,
            11,
            [
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.ferry,
                CatchmentAreaRoutingModePT.cable_car,
                CatchmentAreaRoutingModePT.rail,
            ],
            PTSupportedDay.weekday,
            68400,
            82800,
        ),
        (
            "point_layer",
            CatchmentAreaRoutingModeActiveMobility.walking,
            13,
            5,
            [
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.rail,
            ],
            PTSupportedDay.saturday,
            46800,
            57600,
        ),
        (
            "point_layer_scenario",
            CatchmentAreaRoutingModeActiveMobility.pedelec,
            20,
            15,
            [
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.rail,
                CatchmentAreaRoutingModePT.ferry,
            ],
            PTSupportedDay.weekday,
            25200,
            61200,
        ),
    ],
)
async def test_nearby_station_access(
    client: AsyncClient,
    fixture_create_project,
    fixture_create_project_scenario_features,
    fixture_add_aggregate_point_layer_to_project,
    starting_points_type: str,
    access_mode: str,
    speed: float,
    max_traveltime: int,
    mode: List[str],
    weekday: str,
    from_time: int,
    to_time: int,
):
    # Generate sample layers for conducting the test
    scenario_id = None
    if starting_points_type == "point_single":
        project_id = fixture_create_project["id"]
        starting_points = {"latitude": [48.138577], "longitude": [11.561173]}
    elif starting_points_type == "point_multiple":
        project_id = fixture_create_project["id"]
        starting_points = {
            "latitude": [48.800548, 48.802696, 48.786122],
            "longitude": [9.180397, 9.181044, 9.201984],
        }
    elif starting_points_type == "point_layer":
        project_id = fixture_add_aggregate_point_layer_to_project["project_id"]
        layer_project_id = fixture_add_aggregate_point_layer_to_project[
            "source_layer_project_id"
        ]
        starting_points = {"layer_project_id": layer_project_id}
    elif starting_points_type == "point_layer_scenario":
        project_id = fixture_create_project_scenario_features["project_id"]
        layer_project_id = fixture_create_project_scenario_features["layer_project_id"]
        starting_points = {"layer_project_id": layer_project_id}
        scenario_id = fixture_create_project_scenario_features["scenario_id"]
    else:
        raise NotImplementedError("Invalid starting_points_type specified.")

    # Produce request payload
    params = {
        "starting_points": starting_points,
        "access_mode": access_mode,
        "speed": speed,
        "max_traveltime": max_traveltime,
        "mode": mode,
        "time_window": {
            "weekday": weekday,
            "from_time": from_time,
            "to_time": to_time,
        },
        "scenario_id": scenario_id,
    }

    # Call endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/motorized-mobility/nearby-station-access?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"
