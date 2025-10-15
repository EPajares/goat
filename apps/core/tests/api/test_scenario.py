import pytest
from core.core.config import settings
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_scenario(client: AsyncClient, fixture_create_project_scenario):
    assert fixture_create_project_scenario["scenario_id"] is not None


@pytest.mark.asyncio
async def test_update_scenario(client: AsyncClient, fixture_create_project_scenario):
    # Generate scenario for conducting the test
    project_id = fixture_create_project_scenario["project_id"]
    scenario_id = fixture_create_project_scenario["scenario_id"]

    # Produce request payload
    params = {
        "name": "Updated Test Scenario",
    }

    # Call endpoint
    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}/scenario/{scenario_id}",
        json=params,
    )

    # Check if response is valid
    assert response.status_code == 201
    assert response.json()["name"] == params["name"]


@pytest.mark.asyncio
async def test_delete_scenario(client: AsyncClient, fixture_create_project_scenario):
    # Generate scenario for conducting the test
    project_id = fixture_create_project_scenario["project_id"]
    scenario_id = fixture_create_project_scenario["scenario_id"]

    # Call endpoint
    response = await client.delete(
        f"{settings.API_V2_STR}/project/{project_id}/scenario/{scenario_id}",
    )

    # Check if response is valid
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_scenarios(client: AsyncClient, fixture_create_project_scenario):
    # Generate scenario for conducting the test
    project_id = fixture_create_project_scenario["project_id"]

    # Call endpoint
    response = await client.get(
        f"{settings.API_V2_STR}/project/{project_id}/scenario",
    )

    # Check if response is valid
    assert response.status_code == 200
    assert len(response.json()["items"]) > 0


@pytest.mark.asyncio
async def test_create_scenario_features(
    client: AsyncClient,
    fixture_create_project_scenario_features,
):
    assert len(fixture_create_project_scenario_features["features"]) > 0


@pytest.mark.asyncio
async def test_update_scenario_features(
    client: AsyncClient,
    fixture_create_project_scenario_features,
):
    # Generate scenario features for conducting the test
    project_id = fixture_create_project_scenario_features["project_id"]
    layer_project_id = fixture_create_project_scenario_features["layer_project_id"]
    scenario_id = fixture_create_project_scenario_features["scenario_id"]
    features = fixture_create_project_scenario_features["features"]

    # Produce request payload
    params = [
        {
            "id": features[0]["id"],
            "edit_type": "m",
            "layer_project_id": layer_project_id,
            "geom": "POINT (35.5 47.8)",
        }
    ]

    # Call endpoint
    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_project_id}/scenario/{scenario_id}/features",
        json=params,
    )

    # Check if response is valid
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_delete_scenario_features(
    client: AsyncClient,
    fixture_create_project_scenario_features,
):
    # Generate scenario features for conducting the test
    project_id = fixture_create_project_scenario_features["project_id"]
    layer_project_id = fixture_create_project_scenario_features["layer_project_id"]
    scenario_id = fixture_create_project_scenario_features["scenario_id"]
    features = fixture_create_project_scenario_features["features"]

    # Select a feature to delete
    feature_id = features[0]["id"]

    # Call endpoint
    response = await client.delete(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_project_id}/scenario/{scenario_id}/features/{feature_id}",
    )

    # Check if response is valid
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_scenario_features(
    client: AsyncClient,
    fixture_create_project_scenario_features,
):
    # Generate scenario features for conducting the test
    project_id = fixture_create_project_scenario_features["project_id"]
    scenario_id = fixture_create_project_scenario_features["scenario_id"]

    # Call endpoint
    response = await client.get(
        f"{settings.API_V2_STR}/project/{project_id}/scenario/{scenario_id}/features",
    )

    # Check if response is valid
    assert response.status_code == 200
    assert len(response.json()["features"]) > 0
