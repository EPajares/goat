import os
import zipfile
from uuid import uuid4

import pytest
from core.core.config import settings
from core.db.models.layer import LayerType
from core.schemas.layer import (
    AreaStatisticsOperation,
    ComputeBreakOperation,
    FeatureLayerExportType,
    TableLayerExportType,
)
from core.utils import delete_dir, delete_file
from httpx import AsyncClient
from tests.utils import get_with_wrong_id


@pytest.mark.asyncio
async def test_files_upload(client: AsyncClient, fixture_upload_files):
    assert fixture_upload_files is not None


@pytest.mark.asyncio
async def test_files_upload_invalid(client: AsyncClient, fixture_upload_file_invalid):
    job_id = fixture_upload_file_invalid

    # Check if folder was deleted with the data using os
    assert os.path.exists(f"{settings.DATA_DIR}/{job_id}") is False


@pytest.mark.asyncio
async def test_create_layers(client: AsyncClient, fixture_create_layers):
    assert fixture_create_layers is not None


@pytest.mark.asyncio
async def test_create_feature_layer_in_project(
    client: AsyncClient, fixture_create_layer_in_project
):
    assert fixture_create_layer_in_project is not None


@pytest.mark.asyncio
async def test_export_layers(client: AsyncClient, fixture_create_layers):
    layer = fixture_create_layers
    layer_id = layer["id"]

    # Define export types based on layer type
    if layer["type"] == LayerType.table:
        export_types = TableLayerExportType
    elif layer["type"] == LayerType.feature:
        export_types = FeatureLayerExportType
    else:
        return

    # Loop through all export types
    for export_type in export_types:
        # Define request body
        body = {
            "id": layer_id,
            "file_type": export_type.value,
            "file_name": "test",
        }
        # Add CRS in case of feature layer
        if layer["type"] == "feature":
            body["crs"] = "EPSG:4326"

        # Call export endpoint
        response = await client.post(
            f"{settings.API_V2_STR}/layer/{layer_id}/export",
            json=body,
        )
        assert response.status_code == 200

        # Check response in content and save it to /tmp as zip
        assert response.headers["Content-Type"] == "application/zip"
        assert (
            response.headers["Content-Disposition"] == 'attachment; filename="test.zip"'
        )
        file_name = (
            response.headers["Content-Disposition"].split("=")[1].replace('"', "")
        )
        file_path = f"/tmp/{file_name}"
        unzip_dir = "/tmp/test"

        # Empty /tmp folder
        delete_file(file_path)
        delete_dir(unzip_dir)

        with open(file_path, "wb") as f:
            f.write(response.content)

        # Unzip file into a specific directory and check if it contains the expected files
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall("/tmp")

        assert os.path.exists(f"{unzip_dir}/test.{export_type.value}")
        assert os.path.exists(f"{unzip_dir}/metadata.txt")

        # Additional checks
        # Check if the unzipped directory is not empty
        assert os.listdir(unzip_dir)
        # Check if the size of the unzipped file is not zero
        assert os.path.getsize(f"{unzip_dir}/test.{export_type.value}") > 0
        assert os.path.getsize(f"{unzip_dir}/metadata.txt") > 0


@pytest.mark.asyncio
async def test_export_feature_layer_with_filter(
    client: AsyncClient, fixture_create_polygon_layer
):
    layer = fixture_create_polygon_layer
    layer_id = layer["id"]

    # Define request body
    body = {
        "id": layer_id,
        "file_type": "gpkg",
        "file_name": "test",
        "crs": "EPSG:4326",
        "query": {"cql": {"op": ">", "args": [{"property": "zipcode"}, "80802"]}},
    }

    # Call export endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/layer/{layer_id}/export",
        json=body,
    )
    assert response.status_code == 200

    # Check response in content and save it to /tmp as zip
    assert response.headers["Content-Type"] == "application/zip"
    assert response.headers["Content-Disposition"] == 'attachment; filename="test.zip"'
    file_name = response.headers["Content-Disposition"].split("=")[1].replace('"', "")
    file_path = f"/tmp/{file_name}"
    unzip_dir = "/tmp/test"

    # Empty /tmp folder
    delete_file(file_path)
    delete_dir(unzip_dir)

    with open(file_path, "wb") as f:
        f.write(response.content)

    # Unzip file into a specific directory and check if it contains the expected files
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall("/tmp")

    assert os.path.exists(f"{unzip_dir}/test.gpkg")
    assert os.path.exists(f"{unzip_dir}/metadata.txt")

    # Additional checks
    # Check if the unzipped directory is not empty
    assert os.listdir(unzip_dir)
    # Check if the size of the unzipped file is not zero
    assert os.path.getsize(f"{unzip_dir}/test.gpkg") > 0
    assert os.path.getsize(f"{unzip_dir}/metadata.txt") > 0


# TODO: Add test that fails for export
@pytest.mark.asyncio
async def test_export_feature_layer_wrong_srid(
    client: AsyncClient, fixture_create_polygon_layer
):
    layer = fixture_create_polygon_layer
    layer_id = layer["id"]

    # Define request body
    body = {
        "id": layer_id,
        "file_type": "gpkg",
        "file_name": "test",
        "crs": "EPSG:32660",
    }

    # Call export endpoint
    response = await client.post(
        f"{settings.API_V2_STR}/layer/{layer_id}/export",
        json=body,
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "The data is outside the bounds of the provided CRS."
    )


@pytest.mark.asyncio
async def test_get_feature_layer(client: AsyncClient, fixture_create_feature_layer):
    layer_id = fixture_create_feature_layer["id"]
    response = await client.get(f"{settings.API_V2_STR}/layer/{layer_id}")
    assert response.status_code == 200
    assert response.json()["id"] == layer_id


@pytest.mark.asyncio
async def test_get_layer_wrong_id(client: AsyncClient, fixture_create_feature_layer):
    await get_with_wrong_id(client, "layer")


@pytest.mark.asyncio
async def test_update_feature_layer(client: AsyncClient, fixture_create_feature_layer):
    layer_id = fixture_create_feature_layer["id"]
    layer_dict = fixture_create_feature_layer
    layer_dict["name"] = "Updated name"
    layer_dict["description"] = "Updated description"
    layer_dict["tags"] = ["Update tag 1", "Update tag 2"]
    layer_dict["thumbnail_url"] = "https://updated-example.com"
    response = await client.put(
        f"{settings.API_V2_STR}/layer/{layer_id}", json=layer_dict
    )
    updated_layer = response.json()
    assert response.status_code == 200
    assert updated_layer["name"] == "Updated name"
    assert updated_layer["description"] == "Updated description"
    assert set(updated_layer["tags"]) == {"Update tag 1", "Update tag 2"}
    assert updated_layer["thumbnail_url"] == "https://updated-example.com"


@pytest.mark.asyncio
async def test_delete_layers(client: AsyncClient, fixture_delete_layers):
    return


@pytest.mark.asyncio
async def test_get_feature_cnt(client: AsyncClient, fixture_create_feature_layer):
    layer_id = fixture_create_feature_layer["id"]
    query = '{"op": "=", "args": [{"property": "category"}, "bus_stop"]}'
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/feature-count?query={str(query)}"
    )
    assert response.status_code == 200
    assert response.json()["filtered_count"] == 2
    assert response.json()["total_count"] == 26


@pytest.mark.asyncio
async def test_get_area_statistics(
    client: AsyncClient, fixture_create_feature_polygon_layer
):
    layer_id = fixture_create_feature_polygon_layer["id"]
    expected_result = {
        "sum": 978867237.0440512,
        "min": 239195114.2226817,
        "max": 739672122.8213694,
    }

    query = '{"op": "=", "args": [{"property": "gen"}, "Hamburg"]}'
    # Request each statistical operation
    for operation in AreaStatisticsOperation:
        response = await client.get(
            f"{settings.API_V2_STR}/layer/{layer_id}/area/{operation.value}?query={str(query)}"
        )
        assert response.status_code == 200
        # Check if results are same as expected results
        assert response.json()[operation.value] == expected_result[operation.value]


@pytest.mark.asyncio
async def test_get_area_statistics_no_query(
    client: AsyncClient, fixture_create_feature_polygon_layer
):
    layer_id = fixture_create_feature_polygon_layer["id"]

    response = await client.get(f"{settings.API_V2_STR}/layer/{layer_id}/area/sum")
    assert response.status_code == 200
    return


@pytest.mark.asyncio
async def test_get_wrong_area_statistics_wrong_geom_type(
    client: AsyncClient, fixture_create_feature_layer
):
    layer_id = fixture_create_feature_layer["id"]
    response = await client.get(f"{settings.API_V2_STR}/layer/{layer_id}/area/sum")
    assert response.status_code == 422
    return


@pytest.mark.asyncio
async def test_get_unique_values_layer_pagination(
    client: AsyncClient, fixture_create_feature_layer
):
    layer_id = fixture_create_feature_layer["id"]
    column = "name"

    # Request the first 5 unique values
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/unique-values/{column}?page=1&size=5&order=descendent"
    )
    assert response.status_code == 200
    first_five = response.json()["items"]
    assert len(first_five) == 5

    # Request the next 5 unique values
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/unique-values/{column}?page=2&size=5"
    )
    assert response.status_code == 200
    next_five = response.json()["items"]
    assert len(next_five) == 5

    # Request the first 10 unique values
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/unique-values/{column}?page=1&size=10"
    )
    assert response.status_code == 200
    first_ten = response.json()["items"]
    assert len(first_ten) == 10

    # Check that the first and next five are the same as the 10 unique values
    assert first_five + next_five == first_ten

    return


@pytest.mark.asyncio
async def test_get_unique_values_layer_query(
    client: AsyncClient, fixture_create_feature_layer
):
    layer_id = fixture_create_feature_layer["id"]
    column = "name"
    query = '{"op": "=", "args": [{"property": "category"}, "bus_stop"]}'

    # Request the first 5 unique values
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/unique-values/{column}?query={str(query)}&page=1&size=5"
    )
    assert response.status_code == 200
    values = response.json()
    assert len(values["items"]) == 1
    assert values["items"][0]["count"] == 2
    return


@pytest.mark.asyncio
async def test_get_unique_values_wrong_layer_id(
    client: AsyncClient, fixture_create_feature_layer
):
    layer_id = uuid4()
    column = "name"

    # Request the first 5 unique values
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/unique-values/{column}?page=1&size=5"
    )
    assert response.status_code == 404
    return


@pytest.mark.asyncio
async def test_get_unique_values_wrong_layer_type(
    client: AsyncClient, fixture_create_raster_layer
):
    layer_id = fixture_create_raster_layer["id"]
    column = "name"

    # Request the first 5 unique values
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/unique-values/{column}?page=1&size=5"
    )
    assert response.status_code == 422
    return


@pytest.mark.asyncio
async def test_get_unique_value_wrong_column_name(
    client: AsyncClient, fixture_create_feature_layer
):
    layer_id = fixture_create_feature_layer["id"]
    column = "wrong_column"

    # Request the first 5 unique values
    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/unique-values/{column}?page=1&size=5"
    )
    assert response.status_code == 404
    return


@pytest.mark.asyncio
async def test_get_statistics_column(client: AsyncClient, fixture_create_table_layer):
    layer_id = fixture_create_table_layer["id"]
    column = "einwohnerzahl_ewz"

    base_results = {
        "max": 3677472,
        "min": 34091,
        "mean": 208092.81,
    }
    results = {
        "quantile": {
            **base_results,
            "breaks": [88430, 122724, 155900, 203831, 288097],
        },
        "standard_deviation": {
            **base_results,
            "breaks": [
                85339.48205224,
                330846.13794776,
                576352.7938432801,
                821859.4497388001,
            ],
        },
        "equal_interval": {
            **base_results,
            "breaks": [
                641321.1666666666,
                1248551.3333333333,
                1855781.5,
                2463011.6666666665,
                3070241.833333333,
            ],
        },
        "heads_and_tails": {
            **base_results,
            "breaks": [
                208092.81,
                383477.3106060606,
                720935.3636363636,
                1668162.6666666667,
                2765703.5,
            ],
        },
    }

    # Request each statistical operation
    for operation in ComputeBreakOperation:
        if operation.value == ComputeBreakOperation.standard_deviation.value:
            # There is no breaks parameter for standard deviation
            response = await client.get(
                f"{settings.API_V2_STR}/layer/{layer_id}/class-breaks/{operation.value}/{column}?stripe_zeros=true"
            )
        else:
            response = await client.get(
                f"{settings.API_V2_STR}/layer/{layer_id}/class-breaks/{operation.value}/{column}?breaks=5&stripe_zeros=true"
            )
        assert response.status_code == 200
        # Check that the results are the same as the expected results. Avoid checking the breaks for standard deviation as they can slighly differ.
        if operation.value != ComputeBreakOperation.standard_deviation.value:
            assert response.json() == results[operation.value]
    return


@pytest.mark.asyncio
async def test_get_statistics_column_wrong_layer_id(
    client: AsyncClient, fixture_create_table_layer
):
    layer_id = uuid4()
    column = "einwohnerzahl_ewz"

    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/class-breaks/quantile/{column}?breaks=5&stripe_zeros=true"
    )
    assert response.status_code == 404
    return


# Get not existing column name
@pytest.mark.asyncio
async def test_get_statistics_column_wrong_column_name(
    client: AsyncClient, fixture_create_table_layer
):
    layer_id = fixture_create_table_layer["id"]
    column = "wrong_column"

    response = await client.get(
        f"{settings.API_V2_STR}/layer/{layer_id}/class-breaks/quantile/{column}?breaks=5&stripe_zeros=true"
    )
    assert response.status_code == 404
    return


# Get metadata aggregate for layers based on different filters
async def test_get_layers(client: AsyncClient, fixture_create_multiple_layers):
    response = await client.post(f"{settings.API_V2_STR}/layer")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 4

async def test_get_shared_team_layers(client: AsyncClient, fixture_create_shared_team_layers):
    team_id = fixture_create_shared_team_layers["teams"][0].id
    response = await client.post(f"{settings.API_V2_STR}/layer?team_id={team_id}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 5

async def test_get_shared_organization_layers(client: AsyncClient, fixture_create_shared_organization_layers):
    organization_id = fixture_create_shared_organization_layers["organizations"][0].id
    response = await client.post(f"{settings.API_V2_STR}/layer?organization_id={organization_id}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 5

# Get metadata aggregate for layers based on different filters
async def test_get_layers_with_shared(client: AsyncClient, fixture_create_shared_team_layers, fixture_create_shared_organization_layers):
    response = await client.post(f"{settings.API_V2_STR}/layer")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 10


# Get metadata aggregate for layers based on different filters
async def test_get_layers_metadata_aggregate(
    client: AsyncClient, fixture_create_catalog_layers
):
    response = await client.post(
        f"{settings.API_V2_STR}/layer/metadata/aggregate", json={"in_catalog": True}
    )
    assert response.status_code == 200
    assert len(response.json()["license"]) == 2
    assert len(response.json()["type"]) == 1
    assert len(response.json()["data_category"]) == 2
    assert len(response.json()["geographical_code"]) == 2
    assert len(response.json()["distributor_name"]) == 2


@pytest.mark.asyncio
async def test_get_layers_metadata_aggregate_with_attribute_filter(
    client: AsyncClient, fixture_create_catalog_layers
):
    payload = {
        "in_catalog": True,
        "license": ["CC_BY"],
        "geographical_code": ["de", "be"],
    }
    response = await client.post(
        f"{settings.API_V2_STR}/layer/metadata/aggregate",
        json=payload,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_layers_metadata_aggregate_with_spatial_filter(
    client: AsyncClient, fixture_create_catalog_layers
):
    polygon = "MULTIPOLYGON(((9.772307485052327 53.543531304032136,10.168237437905436 53.73823597146107,10.152582687165927 53.53979279933822,10.325959157503771 53.44963953853681,9.916487327887564 53.414067878974436,9.772307485052327 53.543531304032136)))"
    payload = {
        "in_catalog": True,
        "spatial_search": polygon,
    }
    response = await client.post(
        f"{settings.API_V2_STR}/layer/metadata/aggregate", json=payload
    )
    assert response.status_code == 200
    assert len(response.json()["license"]) == 1
    assert len(response.json()["type"]) == 1
    assert len(response.json()["data_category"]) == 1
    assert len(response.json()["geographical_code"]) == 1
    assert len(response.json()["distributor_name"]) == 1
