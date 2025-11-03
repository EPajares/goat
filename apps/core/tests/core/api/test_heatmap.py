from typing import List

import pytest
from core.core.config import settings
from core.schemas.heatmap import (
    ActiveRoutingHeatmapType,
    ImpedanceFunctionType,
    MotorizedRoutingHeatmapType,
)
from httpx import AsyncClient
from tests.utils import check_job_status

# TODO: Upload larger heatmap-specific input/opportunity layers to test functionality in a more robust way


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "routing_type,use_scenario,impedance_function,opportunities,use_opportunity_geofence",
    [
        (
            ActiveRoutingHeatmapType.walking,
            False,
            ImpedanceFunctionType.gaussian,
            [{"max_traveltime": 15, "sensitivity": 150000}],
            False,
        ),
        (
            ActiveRoutingHeatmapType.walking,
            True,
            ImpedanceFunctionType.linear,
            [
                {"max_traveltime": 20, "sensitivity": 200000},
                {"max_traveltime": 30, "sensitivity": 300000},
            ],
            True,
        ),
        (
            ActiveRoutingHeatmapType.bicycle,
            False,
            ImpedanceFunctionType.exponential,
            [{"max_traveltime": 15, "sensitivity": 150000}],
            False,
        ),
        (
            ActiveRoutingHeatmapType.bicycle,
            True,
            ImpedanceFunctionType.power,
            [
                {"max_traveltime": 20, "sensitivity": 200000},
                {"max_traveltime": 30, "sensitivity": 300000},
            ],
            True,
        ),
        (
            ActiveRoutingHeatmapType.pedelec,
            False,
            ImpedanceFunctionType.gaussian,
            [{"max_traveltime": 15, "sensitivity": 150000}],
            False,
        ),
        (
            ActiveRoutingHeatmapType.pedelec,
            True,
            ImpedanceFunctionType.linear,
            [
                {"max_traveltime": 20, "sensitivity": 200000},
                {"max_traveltime": 30, "sensitivity": 300000},
            ],
            True,
        ),
        (
            MotorizedRoutingHeatmapType.car,
            False,
            ImpedanceFunctionType.exponential,
            [{"max_traveltime": 15, "sensitivity": 150000}],
            False,
        ),
        (
            MotorizedRoutingHeatmapType.car,
            True,
            ImpedanceFunctionType.power,
            [
                {"max_traveltime": 30, "sensitivity": 300000},
                {"max_traveltime": 60, "sensitivity": 600000},
            ],
            True,
        ),
    ],
)
async def test_heatmap_gravity(
    client: AsyncClient,
    fixture_create_project_scenario_features,
    fixture_add_aggregate_point_layer_to_project,
    fixture_add_aggregate_polygon_layer_to_project,
    routing_type: ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType,
    use_scenario: bool,
    impedance_function: ImpedanceFunctionType,
    opportunities: List[dict],
    use_opportunity_geofence: bool,
):
    # Generate sample layers for conducting the test
    scenario_id = None
    opportunity_geofence_layer_project_id = None
    if not use_scenario:
        project_id = fixture_add_aggregate_point_layer_to_project["project_id"]
        layer_project_id = fixture_add_aggregate_point_layer_to_project[
            "source_layer_project_id"
        ]
    else:
        project_id = fixture_create_project_scenario_features["project_id"]
        layer_project_id = fixture_create_project_scenario_features["layer_project_id"]
        scenario_id = fixture_create_project_scenario_features["scenario_id"]
    if use_opportunity_geofence:
        opportunity_geofence_layer_project_id = (
            fixture_add_aggregate_polygon_layer_to_project["source_layer_project_id"]
        )

    # Produce request payload
    params = {
        "routing_type": routing_type.value,
        "impedance_function": impedance_function.value,
        "opportunities": [
            {
                "opportunity_layer_project_id": layer_project_id,
                "max_traveltime": item["max_traveltime"],
                "sensitivity": item["sensitivity"],
                "destination_potential_column": None,  # TODO: Add dynamic destination potential column
            }
            for item in opportunities
        ],
        "scenario_id": scenario_id,
        "opportunity_geofence_layer_project_id": opportunity_geofence_layer_project_id,
    }

    # Call endpoint
    endpoint_type = (
        "active-mobility"
        if type(routing_type) == ActiveRoutingHeatmapType
        else "motorized-mobility"
    )
    response = await client.post(
        f"{settings.API_V2_STR}/{endpoint_type}/heatmap-gravity?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "routing_type,use_scenario,opportunities,use_opportunity_geofence",
    [
        (
            ActiveRoutingHeatmapType.walking,
            False,
            [
                {"max_traveltime": 15, "number_of_destinations": 3},
            ],
            False,
        ),
        (
            ActiveRoutingHeatmapType.walking,
            True,
            [
                {"max_traveltime": 20, "number_of_destinations": 5},
                {"max_traveltime": 30, "number_of_destinations": 10},
            ],
            True,
        ),
        (
            ActiveRoutingHeatmapType.bicycle,
            False,
            [
                {"max_traveltime": 15, "number_of_destinations": 3},
            ],
            False,
        ),
        (
            ActiveRoutingHeatmapType.bicycle,
            True,
            [
                {"max_traveltime": 20, "number_of_destinations": 5},
                {"max_traveltime": 30, "number_of_destinations": 10},
            ],
            True,
        ),
        (
            ActiveRoutingHeatmapType.pedelec,
            False,
            [
                {"max_traveltime": 15, "number_of_destinations": 3},
            ],
            False,
        ),
        (
            ActiveRoutingHeatmapType.pedelec,
            True,
            [
                {"max_traveltime": 20, "number_of_destinations": 5},
                {"max_traveltime": 30, "number_of_destinations": 10},
            ],
            True,
        ),
        (
            MotorizedRoutingHeatmapType.car,
            False,
            [
                {"max_traveltime": 15, "number_of_destinations": 3},
            ],
            False,
        ),
        (
            MotorizedRoutingHeatmapType.car,
            True,
            [
                {"max_traveltime": 30, "number_of_destinations": 5},
                {"max_traveltime": 60, "number_of_destinations": 10},
            ],
            True,
        ),
    ],
)
async def test_heatmap_closest_average(
    client: AsyncClient,
    fixture_create_project_scenario_features,
    fixture_add_aggregate_point_layer_to_project,
    fixture_add_aggregate_polygon_layer_to_project,
    routing_type: ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType,
    use_scenario: bool,
    opportunities: List[dict],
    use_opportunity_geofence: bool,
):
    # Generate sample layers for conducting the test
    scenario_id = None
    opportunity_geofence_layer_project_id = None
    if not use_scenario:
        project_id = fixture_add_aggregate_point_layer_to_project["project_id"]
        layer_project_id = fixture_add_aggregate_point_layer_to_project[
            "source_layer_project_id"
        ]
    else:
        project_id = fixture_create_project_scenario_features["project_id"]
        layer_project_id = fixture_create_project_scenario_features["layer_project_id"]
        scenario_id = fixture_create_project_scenario_features["scenario_id"]
    if use_opportunity_geofence:
        opportunity_geofence_layer_project_id = (
            fixture_add_aggregate_polygon_layer_to_project["source_layer_project_id"]
        )

    # Produce heatmap request payload
    params = {
        "routing_type": routing_type.value,
        "opportunities": [
            {
                "opportunity_layer_project_id": layer_project_id,
                "max_traveltime": item["max_traveltime"],
                "number_of_destinations": item["number_of_destinations"],
            }
            for item in opportunities
        ],
        "scenario_id": scenario_id,
        "opportunity_geofence_layer_project_id": opportunity_geofence_layer_project_id,
    }

    # Call endpoint
    endpoint_type = (
        "active-mobility"
        if type(routing_type) == ActiveRoutingHeatmapType
        else "motorized-mobility"
    )
    response = await client.post(
        f"{settings.API_V2_STR}/{endpoint_type}/heatmap-closest-average?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "routing_type,max_traveltime",
    [
        (ActiveRoutingHeatmapType.walking, 30),
        (ActiveRoutingHeatmapType.bicycle, 30),
        (ActiveRoutingHeatmapType.pedelec, 30),
        (MotorizedRoutingHeatmapType.car, 60),
    ],
)
async def test_heatmap_connectivity(
    client: AsyncClient,
    fixture_add_aggregate_polygon_layer_to_project,
    routing_type: ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType,
    max_traveltime: int,
):
    # Generate sample layers for conducting the test
    project_id = fixture_add_aggregate_polygon_layer_to_project["project_id"]
    layer_project_id = fixture_add_aggregate_polygon_layer_to_project[
        "source_layer_project_id"
    ]

    # Produce heatmap request payload
    params = {
        "routing_type": routing_type.value,
        "reference_area_layer_project_id": layer_project_id,
        "max_traveltime": max_traveltime,
    }

    # Call endpoint
    endpoint_type = (
        "active-mobility"
        if type(routing_type) == ActiveRoutingHeatmapType
        else "motorized-mobility"
    )
    response = await client.post(
        f"{settings.API_V2_STR}/{endpoint_type}/heatmap-connectivity?project_id={project_id}",
        json=params,
    )
    assert response.status_code == 201

    # Check if job is finished
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"
