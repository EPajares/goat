import pytest
from core.core.config import settings
from core.schemas.project import initial_view_state_example
from httpx import AsyncClient
from tests.utils import get_with_wrong_id


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, fixture_create_project):
    assert fixture_create_project["id"] is not None


@pytest.mark.asyncio
async def test_get_project(
    client: AsyncClient,
    fixture_create_project,
):
    response = await client.get(
        f"{settings.API_V2_STR}/project/{fixture_create_project['id']}",
    )
    assert response.status_code == 200
    assert response.json()["id"] == fixture_create_project["id"]


@pytest.mark.asyncio
async def test_get_projects(
    client: AsyncClient,
    fixture_create_projects,
):
    response = await client.get(
        f"{settings.API_V2_STR}/project?order_by=created_at&order=descendent&search=test&@page=1&size=50",
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == len(fixture_create_projects)


@pytest.mark.asyncio
async def test_get_shared_projects(
    client: AsyncClient,
    fixture_create_shared_team_projects,
):
    team_id = str(fixture_create_shared_team_projects["teams"][0].id)
    response = await client.get(
        f"{settings.API_V2_STR}/project?team_id={team_id}",
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == len(
        fixture_create_shared_team_projects["projects"]
    )


@pytest.mark.asyncio
async def test_get_project_wrong_id(client: AsyncClient, fixture_create_project):
    await get_with_wrong_id(client, "project")


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, fixture_create_project):
    response = await client.put(
        f"{settings.API_V2_STR}/project/{fixture_create_project['id']}",
        json={"name": "test2"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "test2"


@pytest.mark.asyncio
async def test_update_project_layer_order(
    client: AsyncClient, fixture_create_layer_project
):
    project_id = fixture_create_layer_project["project_id"]

    layer_project_ids = []
    for layer_project in fixture_create_layer_project["layer_project"]:
        layer_project_ids.append(layer_project["id"])

    # Flip layer order
    layer_project_ids.reverse()

    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}",
        json={
            "layer_order": layer_project_ids,
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["layer_order"] == layer_project_ids


@pytest.mark.asyncio
async def test_delete_project(
    client: AsyncClient,
    fixture_create_project,
):
    response = await client.delete(
        f"{settings.API_V2_STR}/project/{fixture_create_project['id']}",
    )
    assert response.status_code == 204

    # Check if project is deleted
    response = await client.get(
        f"{settings.API_V2_STR}/project/{fixture_create_project['id']}",
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_initial_view_state(
    client: AsyncClient,
    fixture_create_project,
):
    response = await client.get(
        f"{settings.API_V2_STR}/project/{fixture_create_project['id']}/initial-view-state",
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_initial_view_state(client: AsyncClient, fixture_create_project):
    initial_view_state = initial_view_state_example
    initial_view_state["latitude"] = initial_view_state_example["latitude"] + 2
    initial_view_state["longitude"] = initial_view_state_example["longitude"] + 2
    initial_view_state["zoom"] = initial_view_state_example["zoom"] + 2

    response = await client.put(
        f"{settings.API_V2_STR}/project/{fixture_create_project['id']}/initial-view-state",
        json=initial_view_state,
    )
    assert response.status_code == 200
    updated_initial_view_state = response.json()
    assert updated_initial_view_state["latitude"] == initial_view_state["latitude"]
    assert updated_initial_view_state["longitude"] == initial_view_state["longitude"]
    assert updated_initial_view_state["zoom"] == initial_view_state["zoom"]


@pytest.mark.asyncio
async def test_create_layer_project(client: AsyncClient, fixture_create_layer_project):
    assert fixture_create_layer_project["project_id"] is not None


@pytest.mark.asyncio
async def test_duplicate_layer_project(
    client: AsyncClient, fixture_create_layer_project
):
    layer_id = fixture_create_layer_project["layer_project"][0]["layer_id"]

    # Duplicate layer
    response = await client.post(
        f"{settings.API_V2_STR}/project/{fixture_create_layer_project['project_id']}/layer?layer_ids={layer_id}",
    )
    assert response.status_code == 200
    res = response.json()

    # Check if layer is duplicated
    for layer in res:
        if layer["id"] == layer_id:
            assert (
                layer["name"]
                == "Copy from "
                + fixture_create_layer_project["layer_project"][0]["name"]
            )


@pytest.mark.asyncio
async def test_get_layer_project(client: AsyncClient, fixture_create_layer_project):
    layer_project_id = fixture_create_layer_project["layer_project"][0]["id"]
    response = await client.get(
        f"{settings.API_V2_STR}/project/{fixture_create_layer_project['project_id']}/layer/{layer_project_id}",
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_layers_project(client: AsyncClient, fixture_create_layer_project):
    response = await client.get(
        f"{settings.API_V2_STR}/project/{fixture_create_layer_project['project_id']}/layer",
    )
    assert response.status_code == 200
    assert (
        response.json()[0]["id"]
        == fixture_create_layer_project["layer_project"][0]["id"]
    )


# TODO: Add test for style
@pytest.mark.asyncio
async def test_update_layer_project(client: AsyncClient, fixture_create_layer_project):
    project_id = fixture_create_layer_project["project_id"]
    layer_project_id = fixture_create_layer_project["layer_project"][0]["id"]
    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_project_id}",
        json={
            "name": "test2",
            "query": {
                "cql": {"op": "=", "args": [{"property": "category"}, "bus_stop"]}
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "test2"
    # Check if feature count is correct
    assert res["total_count"] == 26
    assert res["filtered_count"] == 2


@pytest.mark.asyncio
async def test_update_layer_project_with_spatial_filter(
    client: AsyncClient, fixture_create_layer_project
):
    project_id = fixture_create_layer_project["project_id"]
    layer_project_id = fixture_create_layer_project["layer_project"][0]["id"]
    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_project_id}",
        json={
            "name": "test2",
            "query": {
                "cql": {
                    "op": "s_intersects",
                    "args": [
                        {"property": "geometry"},
                        {
                            "coordinates": [
                                [
                                    [11.072458, 49.467157],
                                    [11.072458, 49.471157],
                                    [11.076458, 49.471157],
                                    [11.076458, 49.467157],
                                    [11.072458, 49.467157],
                                ]
                            ],
                            "type": "Polygon",
                        },
                    ],
                }
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "test2"
    # Check if feature count is correct
    assert res["total_count"] == 26
    assert res["filtered_count"] == 17


@pytest.mark.asyncio
async def test_update_layer_project_bad_format_query(
    client: AsyncClient, fixture_create_layer_project
):
    project_id = fixture_create_layer_project["project_id"]
    layer_project_id = fixture_create_layer_project["layer_project"][0]["id"]
    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_project_id}",
        json={
            "name": "test2",
            "query": {"cql": {"op": "=", "args": "wrong"}},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_layer_project(client: AsyncClient, fixture_create_layer_project):
    project_id = fixture_create_layer_project["project_id"]
    layer_project_id = fixture_create_layer_project["layer_project"][0]["id"]

    # Delete layer
    response = await client.delete(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_project_id={layer_project_id}",
    )
    assert response.status_code == 204

    # Check if layer is deleted
    response = await client.get(
        f"{settings.API_V2_STR}/project/{project_id}/layer",
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert (
        response.json()[0]["id"]
        == fixture_create_layer_project["layer_project"][1]["id"]
    )

    # Check if layer is deleted from layer order
    response = await client.get(
        f"{settings.API_V2_STR}/project/{project_id}",
    )
    assert response.status_code == 200
    assert layer_project_id not in response.json()["layer_order"]
