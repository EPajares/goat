import pytest
from core.core.config import settings
from core.db.models.layer import ToolType
from core.schemas.job import JobStatusType
from core.schemas.toolbox_base import ColumnStatisticsOperation
from httpx import AsyncClient
from tests.utils import check_job_status, test_aggregate


@pytest.mark.asyncio
async def test_join(client: AsyncClient, fixture_add_join_layers_to_project):
    (
        layer_id_table,
        layer_id_gpkg,
        project_id,
    ) = fixture_add_join_layers_to_project.values()
    # TODO: Check the produced results
    for operation in ColumnStatisticsOperation:
        # Request join endpoint
        params = {
            "target_layer_project_id": layer_id_gpkg,
            "target_field": "zipcode",
            "join_layer_project_id": layer_id_table,
            "join_field": "plz",
            "column_statistics": {
                "operation": operation.value,
                "field": "events",
            },
            "layer_name": f"{operation.value} result layer",
        }

        response = await client.post(
            f"{settings.API_V2_STR}/tool/join?project_id={project_id}", json=params
        )
        assert response.status_code == 201
        job = await check_job_status(client, response.json()["job_id"])
        assert job["status_simple"] == "finished"


@pytest.mark.asyncio
async def test_join_filter(client: AsyncClient, fixture_add_join_layers_to_project):
    (
        layer_id_table,
        layer_id_gpkg,
        project_id,
    ) = fixture_add_join_layers_to_project.values()

    # Update target layer project and add filter plz=80799
    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_id_gpkg}",
        json={
            "query": {"cql": {"op": "=", "args": [{"property": "plz"}, "80799"]}},
        },
    )
    assert response.status_code == 200

    # Update join layer project and add filter to events > 500
    response = await client.put(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_id_table}",
        json={
            "query": {"cql": {"op": ">", "args": [{"property": "events"}, "500"]}},
        },
    )
    assert response.status_code == 200

    # Request join endpoint
    params = {
        "target_layer_project_id": layer_id_gpkg,
        "target_field": "zipcode",
        "join_layer_project_id": layer_id_table,
        "join_field": "plz",
        "column_statistics": {
            "operation": ColumnStatisticsOperation.sum.value,
            "field": "events",
        },
        "layer_name": "join result layer",
    }
    response = await client.post(
        f"{settings.API_V2_STR}/tool/join?project_id={project_id}", json=params
    )
    assert response.status_code == 201
    job = await check_job_status(client, response.json()["job_id"])
    assert job["status_simple"] == "finished"


@pytest.mark.asyncio
async def test_join_wrong_join_field(
    client: AsyncClient, fixture_add_join_layers_to_project
):
    (
        layer_id_table,
        layer_id_gpkg,
        project_id,
    ) = fixture_add_join_layers_to_project.values()
    # Request join endpoint
    params = {
        "target_layer_project_id": layer_id_gpkg,
        "target_field": "zipcode",
        "join_layer_project_id": layer_id_table,
        "join_field": "not_existing_field",
        "column_statistics": {
            "operation": ColumnStatisticsOperation.sum.value,
            "field": "events",
        },
        "layer_name": f"{ColumnStatisticsOperation.sum.value} result layer",
    }

    response = await client.post(
        f"{settings.API_V2_STR}/tool/join?project_id={project_id}", json=params
    )
    assert response.status_code == 201
    await check_job_status(
        client, response.json()["job_id"], JobStatusType.failed.value
    )


@pytest.mark.asyncio
async def test_aggregate_points_polygon(
    client: AsyncClient, fixture_add_aggregate_point_layers_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_point_layers_to_project,
        "feature",
        "points",
        "value",
    )


@pytest.mark.asyncio
async def test_aggregate_points_polygon_group_by(
    client: AsyncClient, fixture_add_aggregate_point_layers_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_point_layers_to_project,
        "feature",
        "points",
        "value",
        ["category"],
    )


@pytest.mark.asyncio
async def test_aggregate_points_polygon_filter(
    client: AsyncClient, fixture_add_aggregate_point_layers_to_project
):
    filters = [
        {
            "layer_project_id": 1,
            "filter": {
                "op": "=",
                "args": [{"property": "category"}, "second_category"],
            },
        },
        {
            "layer_project_id": 2,
            "filter": {"op": "=", "args": [{"property": "zipcode"}, "80802"]},
        },
    ]
    await test_aggregate(
        client,
        fixture_add_aggregate_point_layers_to_project,
        "feature",
        "points",
        "value",
        ["category"],
        filters,
    )


@pytest.mark.asyncio
async def test_aggregate_points_h3_grid(
    client: AsyncClient, fixture_add_aggregate_point_layer_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_point_layer_to_project,
        "h3_grid",
        "points",
        "value",
    )
    return


@pytest.mark.asyncio
async def test_aggregate_points_h3_grid_group_by(
    client: AsyncClient, fixture_add_aggregate_point_layer_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_point_layer_to_project,
        "h3_grid",
        "points",
        "value",
        ["category"],
    )


@pytest.mark.asyncio
async def test_aggregate_polygons_polygon(
    client: AsyncClient, fixture_add_aggregate_polygon_layers_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_polygon_layers_to_project,
        "feature",
        "polygons",
        "value",
        other_properties={"weigthed_by_intersecting_area": True},
    )


@pytest.mark.asyncio
async def test_aggregate_polygons_polygon_statistics_area(
    client: AsyncClient, fixture_add_aggregate_polygon_layers_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_polygon_layers_to_project,
        "feature",
        "polygons",
        "$intersected_area",
        other_properties={"weigthed_by_intersecting_area": True},
    )


@pytest.mark.asyncio
async def test_aggregate_polygons_polygon_group_by(
    client: AsyncClient, fixture_add_aggregate_polygon_layers_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_polygon_layers_to_project,
        "feature",
        "polygons",
        "value",
        ["category"],
        other_properties={"weigthed_by_intersecting_area": True},
    )


@pytest.mark.asyncio
async def test_aggregate_polygons_h3_grid(
    client: AsyncClient, fixture_add_aggregate_polygon_layer_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_polygon_layer_to_project,
        "h3_grid",
        "polygons",
        "value",
        other_properties={"weigthed_by_intersecting_area": True},
    )


@pytest.mark.asyncio
async def test_aggregate_polygons_h3_grid_statistics_area(
    client: AsyncClient, fixture_add_aggregate_polygon_layer_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_polygon_layer_to_project,
        "h3_grid",
        "polygons",
        "$intersected_area",
        other_properties={"weigthed_by_intersecting_area": True},
    )


@pytest.mark.asyncio
async def test_aggregate_polygons_h3_grid_group_by(
    client: AsyncClient, fixture_add_aggregate_polygon_layer_to_project
):
    await test_aggregate(
        client,
        fixture_add_aggregate_polygon_layer_to_project,
        "h3_grid",
        "polygons",
        "$intersected_area",
        ["category"],
        other_properties={"weigthed_by_intersecting_area": True},
    )


@pytest.mark.asyncio
async def test_buffer(client: AsyncClient, fixture_add_basic_layer_to_project):
    project_id = fixture_add_basic_layer_to_project["project_id"]
    layer_project_id = fixture_add_basic_layer_to_project["layer_project_id"]

    # Request buffer endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/tool/buffer?project_id={project_id}",
        json={
            "source_layer_project_id": layer_project_id,
            "max_distance": 1000,
            "distance_step": 5,
        },
    )
    response_json = response.json()
    assert response.status_code == 201

    # Check job status
    job = await check_job_status(client, response_json["job_id"])
    assert job["status_simple"] == "finished"


@pytest.mark.asyncio
async def test_buffer_union(client: AsyncClient, fixture_add_basic_layer_to_project):
    project_id = fixture_add_basic_layer_to_project["project_id"]
    layer_project_id = fixture_add_basic_layer_to_project["layer_project_id"]

    # Request buffer endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/tool/buffer?project_id={project_id}",
        json={
            "source_layer_project_id": layer_project_id,
            "max_distance": 1000,
            "distance_step": 5,
            "polygon_union": True,
        },
    )
    response_json = response.json()
    assert response.status_code == 201

    # Check job status
    job = await check_job_status(client, response_json["job_id"])
    assert job["status_simple"] == "finished"


@pytest.mark.asyncio
async def test_buffer_union_difference(
    client: AsyncClient, fixture_add_basic_layer_to_project
):
    project_id = fixture_add_basic_layer_to_project["project_id"]
    layer_project_id = fixture_add_basic_layer_to_project["layer_project_id"]

    # Request buffer endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/tool/buffer?project_id={project_id}",
        json={
            "source_layer_project_id": layer_project_id,
            "max_distance": 1000,
            "distance_step": 5,
            "polygon_union": True,
            "polygon_difference": True,
        },
    )
    response_json = response.json()
    assert response.status_code == 201

    # Check job status
    job = await check_job_status(client, response_json["job_id"])
    assert job["status_simple"] == "finished"


@pytest.mark.asyncio
async def test_origin_destination_polygon(
    client: AsyncClient, fixture_add_origin_destination_layers_to_project
):
    origin_destination_matrix_layer_project_id = (
        fixture_add_origin_destination_layers_to_project[
            "origin_destination_matrix_layer_project_id"
        ]
    )
    geometry_layer_project_id = fixture_add_origin_destination_layers_to_project[
        "geometry_layer_project_id"
    ]
    project_id = fixture_add_origin_destination_layers_to_project["project_id"]

    # Request origin destination endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/tool/origin-destination?project_id={project_id}",
        json={
            "geometry_layer_project_id": geometry_layer_project_id,
            "origin_destination_matrix_layer_project_id": origin_destination_matrix_layer_project_id,
            "unique_id_column": "zipcode",
            "origin_column": "origin",
            "destination_column": "destination",
            "weight_column": "weight",
        },
    )
    response_json = response.json()
    assert response.status_code == 201

    # Check job status
    job = await check_job_status(client, response_json["job_id"])
    assert job["status_simple"] == "finished"


@pytest.mark.asyncio
async def test_reference_area(
    client: AsyncClient, fixture_add_polygon_layer_to_project
):
    project_id = fixture_add_polygon_layer_to_project["project_id"]
    layer_project_id = fixture_add_polygon_layer_to_project["layer_project_id"]
    # Request reference area endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/tool/check-reference-area?project_id={project_id}",
        json={
            "layer_project_id": layer_project_id,
            "tool_type": ToolType.oev_gueteklasse.value,
        },
    )

    assert response.status_code == 200
    assert response.json()["type"] == "info"


@pytest.mark.asyncio
async def test_to_large_reference_area(
    client: AsyncClient, fixture_add_large_polygon_layer_to_project
):
    project_id = fixture_add_large_polygon_layer_to_project["project_id"]
    layer_project_id = fixture_add_large_polygon_layer_to_project["layer_project_id"]
    # Request reference area endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/tool/check-reference-area?project_id={project_id}",
        json={
            "layer_project_id": layer_project_id,
            "tool_type": ToolType.oev_gueteklasse.value,
        },
    )
    assert response.status_code == 422
