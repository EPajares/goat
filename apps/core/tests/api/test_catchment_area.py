import pytest
from core.core.config import settings
from core.schemas.catchment_area import (
    CatchmentAreaRoutingAccessModePT,
    CatchmentAreaRoutingEgressModePT,
    CatchmentAreaRoutingModeActiveMobility,
    CatchmentAreaRoutingModeCar,
    CatchmentAreaRoutingModePT,
    CatchmentAreaTypeActiveMobility,
    CatchmentAreaTypeCar,
    CatchmentAreaTypePT,
)
from core.schemas.toolbox_base import PTSupportedDay
from httpx import AsyncClient
from tests.utils import check_job_status


@pytest.mark.parametrize(
    "starting_points_type,routing_type,travel_cost,catchment_area_type,polygon_difference",
    [
        (
            "point_single",
            CatchmentAreaRoutingModeActiveMobility.walking,
            {"max_traveltime": 15, "speed": 5, "steps": 3},
            CatchmentAreaTypeActiveMobility.polygon,
            False,
        ),
        (
            "point_multiple",
            CatchmentAreaRoutingModeActiveMobility.walking,
            {"max_distance": 500, "steps": 5},
            CatchmentAreaTypeActiveMobility.network,
            None,
        ),
        (
            "point_layer",
            CatchmentAreaRoutingModeActiveMobility.walking,
            {"max_traveltime": 37, "speed": 4, "steps": 22},
            CatchmentAreaTypeActiveMobility.rectangular_grid,
            None,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeActiveMobility.walking,
            {"max_distance": 15000, "steps": 8},
            CatchmentAreaTypeActiveMobility.polygon,
            True,
        ),
        (
            "point_multiple",
            CatchmentAreaRoutingModeActiveMobility.bicycle,
            {"max_traveltime": 5, "speed": 15, "steps": 3},
            CatchmentAreaTypeActiveMobility.polygon,
            False,
        ),
        (
            "point_layer_scenario",
            CatchmentAreaRoutingModeActiveMobility.bicycle,
            {"max_distance": 4300, "steps": 6},
            CatchmentAreaTypeActiveMobility.network,
            None,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeActiveMobility.bicycle,
            {"max_traveltime": 20, "speed": 11, "steps": 19},
            CatchmentAreaTypeActiveMobility.rectangular_grid,
            None,
        ),
        (
            "point_multiple",
            CatchmentAreaRoutingModeActiveMobility.bicycle,
            {"max_distance": 7250, "steps": 9},
            CatchmentAreaTypeActiveMobility.polygon,
            True,
        ),
        (
            "point_layer",
            CatchmentAreaRoutingModeActiveMobility.pedelec,
            {"max_traveltime": 7, "speed": 23, "steps": 3},
            CatchmentAreaTypeActiveMobility.polygon,
            False,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeActiveMobility.pedelec,
            {"max_distance": 900, "steps": 4},
            CatchmentAreaTypeActiveMobility.network,
            None,
        ),
        (
            "point_multiple",
            CatchmentAreaRoutingModeActiveMobility.pedelec,
            {"max_traveltime": 28, "speed": 7, "steps": 28},
            CatchmentAreaTypeActiveMobility.rectangular_grid,
            None,
        ),
        (
            "point_layer_scenario",
            CatchmentAreaRoutingModeActiveMobility.pedelec,
            {"max_distance": 2400, "steps": 3},
            CatchmentAreaTypeActiveMobility.polygon,
            True,
        ),
    ],
)
async def test_catchment_area_active_mobility(
    client: AsyncClient,
    fixture_create_project,
    fixture_create_project_scenario_features,
    fixture_add_aggregate_point_layer_to_project,
    starting_points_type: str,
    routing_type: str,
    travel_cost: dict,
    catchment_area_type: str,
    polygon_difference: bool,
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
        "routing_type": routing_type,
        "travel_cost": travel_cost,
        "catchment_area_type": catchment_area_type,
        "scenario_id": scenario_id,
    }
    if polygon_difference is not None:
        params["polygon_difference"] = polygon_difference

    # Call endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/active-mobility/catchment-area?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"


# TODO: Add test combinations for layer input
@pytest.mark.parametrize(
    "starting_points_type,mode,access_mode,egress_mode,max_traveltime,steps,weekday,from_time,to_time,catchment_area_type,polygon_difference",
    [
        (
            "point_single",
            [
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.rail,
            ],
            CatchmentAreaRoutingAccessModePT.walk,
            CatchmentAreaRoutingEgressModePT.walk,
            30,
            5,
            PTSupportedDay.weekday,
            25200,
            32400,
            CatchmentAreaTypePT.polygon,
            True,
        ),
        (
            "point_single",
            [
                CatchmentAreaRoutingModePT.rail,
                CatchmentAreaRoutingModePT.gondola,
                CatchmentAreaRoutingModePT.ferry,
                CatchmentAreaRoutingModePT.funicular,
            ],
            CatchmentAreaRoutingAccessModePT.bicycle,
            CatchmentAreaRoutingEgressModePT.walk,
            72,
            8,
            PTSupportedDay.saturday,
            41400,
            54000,
            CatchmentAreaTypePT.polygon,
            False,
        ),
        (
            "point_single",
            [
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.ferry,
                CatchmentAreaRoutingModePT.cable_car,
                CatchmentAreaRoutingModePT.rail,
            ],
            CatchmentAreaRoutingAccessModePT.walk,
            CatchmentAreaRoutingEgressModePT.walk,
            21,
            7,
            PTSupportedDay.sunday,
            3600,
            14400,
            CatchmentAreaTypePT.polygon,
            True,
        ),
        (
            "point_single",
            [
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.rail,
            ],
            CatchmentAreaRoutingAccessModePT.bicycle,
            CatchmentAreaRoutingEgressModePT.walk,
            11,
            10,
            PTSupportedDay.weekday,
            57600,
            59400,
            CatchmentAreaTypePT.polygon,
            False,
        ),
        (
            "point_single",
            [
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.rail,
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.ferry,
                CatchmentAreaRoutingModePT.cable_car,
                CatchmentAreaRoutingModePT.gondola,
                CatchmentAreaRoutingModePT.funicular,
            ],
            CatchmentAreaRoutingAccessModePT.walk,
            CatchmentAreaRoutingEgressModePT.walk,
            90,
            9,
            PTSupportedDay.saturday,
            25200,
            32400,
            CatchmentAreaTypePT.polygon,
            True,
        ),
        (
            "point_single",
            [
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
                CatchmentAreaRoutingModePT.rail,
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.ferry,
                CatchmentAreaRoutingModePT.cable_car,
                CatchmentAreaRoutingModePT.gondola,
                CatchmentAreaRoutingModePT.funicular,
            ],
            CatchmentAreaRoutingAccessModePT.bicycle,
            CatchmentAreaRoutingEgressModePT.walk,
            47,
            17,
            PTSupportedDay.sunday,
            21600,
            72000,
            CatchmentAreaTypePT.polygon,
            False,
        ),
    ],
)
async def test_catchment_area_pt(
    client: AsyncClient,
    fixture_create_project,
    fixture_add_aggregate_point_layer_to_project,
    starting_points_type: str,
    mode: list[str],
    access_mode: str,
    egress_mode: str,
    max_traveltime: int,
    steps: int,
    weekday: str,
    from_time: int,
    to_time: int,
    catchment_area_type: str,
    polygon_difference: bool,
):
    # Generate sample layers for conducting the test
    if starting_points_type == "point_single":
        project_id = fixture_create_project["id"]
        starting_points = {"latitude": [48.138577], "longitude": [11.561173]}
    elif starting_points_type == "point_multiple":
        raise NotImplementedError(
            "Multiple starting points are not supported for PT catchment areas."
        )
    else:
        # TODO: Use a layer with only 1 starting point for this test case
        # project_id = fixture_add_aggregate_point_layer_to_project["project_id"]
        # layer_project_id = fixture_add_aggregate_point_layer_to_project["source_layer_project_id"]
        # starting_points = {"layer_project_id": layer_project_id}
        raise NotImplementedError("Test case yet to be implemented.")

    # Produce request payload
    params = {
        "starting_points": starting_points,
        "routing_type": {
            "mode": mode,
            "access_mode": access_mode,
            "egress_mode": egress_mode,
        },
        "travel_cost": {
            "max_traveltime": max_traveltime,
            "steps": steps,
        },
        "time_window": {
            "weekday": weekday,
            "from_time": from_time,
            "to_time": to_time,
        },
        "catchment_area_type": catchment_area_type,
    }
    if polygon_difference is not None:
        params["polygon_difference"] = polygon_difference

    # Call endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/motorized-mobility/pt/catchment-area?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"


# TODO: Add test combinations for single point layer input
@pytest.mark.parametrize(
    "starting_points_type,routing_type,travel_cost,catchment_area_type,polygon_difference",
    [
        (
            "point_single",
            CatchmentAreaRoutingModeCar.car,
            {"max_traveltime": 15, "steps": 5},
            CatchmentAreaTypeCar.polygon,
            False,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeCar.car,
            {"max_distance": 500, "steps": 5},
            CatchmentAreaTypeCar.network,
            None,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeCar.car,
            {"max_traveltime": 45, "steps": 45},
            CatchmentAreaTypeCar.rectangular_grid,
            None,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeCar.car,
            {"max_distance": 6850, "steps": 6},
            CatchmentAreaTypeCar.polygon,
            True,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeCar.car,
            {"max_traveltime": 27, "steps": 15},
            CatchmentAreaTypeCar.network,
            None,
        ),
        (
            "point_single",
            CatchmentAreaRoutingModeCar.car,
            {"max_distance": 3700, "steps": 4},
            CatchmentAreaTypeCar.rectangular_grid,
            None,
        ),
    ],
)
async def test_catchment_area_car(
    client: AsyncClient,
    fixture_create_project,
    fixture_add_aggregate_point_layer_to_project,
    starting_points_type: str,
    routing_type: str,
    travel_cost: dict,
    catchment_area_type: str,
    polygon_difference: bool,
):
    # Generate sample layers for conducting the test
    if starting_points_type == "point_single":
        project_id = fixture_create_project["id"]
        starting_points = {"latitude": [48.138577], "longitude": [11.561173]}
    elif starting_points_type == "point_multiple":
        raise NotImplementedError(
            "Multiple starting points are not supported for car catchment areas."
        )
    else:
        # TODO: Use a layer with only 1 starting point for this test case
        # project_id = fixture_add_aggregate_point_layer_to_project["project_id"]
        # layer_project_id = fixture_add_aggregate_point_layer_to_project["source_layer_project_id"]
        # starting_points = {"layer_project_id": layer_project_id}
        raise NotImplementedError("Test case yet to be implemented.")

    # Produce request payload
    params = {
        "starting_points": starting_points,
        "routing_type": routing_type,
        "travel_cost": travel_cost,
        "catchment_area_type": catchment_area_type,
    }
    if polygon_difference is not None:
        params["polygon_difference"] = polygon_difference

    # Call endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/motorized-mobility/car/catchment-area?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"
