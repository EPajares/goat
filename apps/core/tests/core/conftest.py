# Standard library imports
import asyncio
import logging
import os

# Third party imports
import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt
from sqlalchemy import text
from tests.utils import (
    check_job_status,
    check_user_data_deleted,
    generate_random_string,
    upload_file,
    upload_invalid_file,
    upload_valid_file,
    upload_valid_files,
)

# Local application imports
from core.core.config import settings
from core.crud.base import CRUDBase
from core.db.models import (
    LayerOrganizationLink,
    LayerTeamLink,
    Organization,
    ProjectTeamLink,
    Role,
    Team,
    User,
)
from core.db.models.layer import LayerType
from core.endpoints.deps import get_db, session_manager
from core.main import app
from core.schemas.catchment_area import (
    request_examples_catchment_area_active_mobility as active_mobility_request_examples,
)
from core.schemas.catchment_area import (
    request_examples_catchment_area_car,
    request_examples_catchment_area_pt,
)
from core.schemas.layer import request_examples as layer_request_examples
from core.schemas.project import (
    request_examples as project_request_examples,
)


def set_test_mode():
    settings.RUN_AS_BACKGROUND_TASK = True
    settings.USER_DATA_SCHEMA = "test_user_data"
    settings.CUSTOMER_SCHEMA = "test_customer1"
    settings.ACCOUNTS_SCHEMA = "test_accounts1"
    settings.MAX_FOLDER_COUNT = 15
    settings.TEST_MODE = True


set_test_mode()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def session_fixture(event_loop):
    session_manager.init(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    session_manager._engine.update_execution_options(
        schema_translate_map={
            "customer": settings.CUSTOMER_SCHEMA,
            "accounts": settings.ACCOUNTS_SCHEMA,
        }
    )
    async with session_manager.connect() as connection:
        for schema in [
            settings.CUSTOMER_SCHEMA,
            settings.USER_DATA_SCHEMA,
            settings.ACCOUNTS_SCHEMA,
        ]:
            await connection.execute(
                text(f"""DROP SCHEMA IF EXISTS {schema} CASCADE""")
            )
            await connection.execute(text(f"""CREATE SCHEMA IF NOT EXISTS {schema}"""))
        await session_manager.drop_all(connection)
        await session_manager.create_all(connection)
        await connection.commit()
    yield
    logging.info("Starting session_fixture finalizer")
    async with session_manager.connect() as connection:
        pass
    await session_manager.close()
    logging.info("Finished session_fixture finalizer")


@pytest_asyncio.fixture(autouse=True)
async def session_override(session_fixture):
    async def get_db_override():
        async with session_manager.session() as session:
            yield session

    app.dependency_overrides[get_db] = get_db_override


@pytest_asyncio.fixture
async def db_session():
    async with session_manager.session() as session:
        yield session


@pytest.fixture
async def fixture_create_user(client: AsyncClient, db_session):
    # Get base user_id
    scheme, _, token = settings.SAMPLE_AUTHORIZATION.partition(" ")
    user_id = jwt.get_unverified_claims(token)["sub"]

    # Create a user
    user = User(
        id=user_id,
        firstname="Green",
        lastname="GOAT",
        avatar="https://assets.plan4better.de/img/goat_app_subscription_professional.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Setup: Create user data schemas
    result = await client.post(f"{settings.API_V2_STR}/user/data-schema")
    assert result.status_code == 201
    yield user.id
    # Teardown: Delete the user after the test
    await CRUDBase(User).delete(db_session, id=user_id)
    await client.delete(f"{settings.API_V2_STR}/user/data-schema")


@pytest.fixture
async def fixture_create_folder(client: AsyncClient, fixture_create_user):
    # Setup: Create the folder
    response = await client.post(f"{settings.API_V2_STR}/folder", json={"name": "test"})
    folder = response.json()
    yield folder
    # Teardown: Delete the folder after the test
    await client.delete(f"{settings.API_V2_STR}/folder/{folder['id']}")


@pytest.fixture
async def fixture_get_home_folder(client: AsyncClient):
    response = await client.get(
        f"{settings.API_V2_STR}/folder?search=home&order=descendent&page=1&size=1",
    )
    assert response.status_code == 200
    return response.json()[0]


@pytest.fixture
async def fixture_create_exceed_folders(client: AsyncClient, fixture_create_user):
    max_folder_cnt = settings.MAX_FOLDER_COUNT
    folder_names = [f"test{i}" for i in range(1, max_folder_cnt + 1)]

    # Setup: Create multiple folders
    cnt = 0
    folder_ids = []
    for name in folder_names:
        cnt += 1
        # Request to create a folder
        response = await client.post(
            f"{settings.API_V2_STR}/folder", json={"name": name}
        )
        if cnt >= max_folder_cnt:
            assert response.status_code == 429  # Too Many Requests
        else:
            assert response.status_code == 201
            folder_ids.append(response.json()["id"])

    yield
    # Delete the folders after the test
    for id in folder_ids:
        await client.delete(f"{settings.API_V2_STR}/folder/{id}")


@pytest.fixture
async def fixture_create_folders(client: AsyncClient, fixture_create_user):
    folder_names = ["test1", "test2", "test3"]
    created_folders = []

    # Setup: Create multiple folders
    for name in folder_names:
        response = await client.post(
            f"{settings.API_V2_STR}/folder", json={"name": name}
        )
        folder = response.json()
        created_folders.append(folder)

    yield created_folders

    # Teardown: Delete the folders after the test
    for folder in created_folders:
        await client.delete(f"{settings.API_V2_STR}/folder/{folder['id']}")


@pytest.fixture
async def fixture_create_project(
    client: AsyncClient, fixture_create_user, fixture_create_folder
):
    # Assuming fixture_create_folder yields a folder object
    folder = fixture_create_folder

    # Setup: Create the project within the folder
    example = project_request_examples["create"]
    example["folder_id"] = folder["id"]
    response = await client.post(f"{settings.API_V2_STR}/project", json=example)
    project = response.json()

    yield project

    # Teardown: Delete the project after the test
    # Note: Folder deletion will be handled by the fixture_create_folder fixture's teardown
    await client.delete(f"{settings.API_V2_STR}/project/{project['id']}")


@pytest.fixture
async def fixture_create_projects(
    client: AsyncClient, fixture_create_user, fixture_create_folder
):
    project_names = ["test1", "test2", "test3"]

    # Assuming fixture_create_folder yields a folder object
    folder = fixture_create_folder

    # Setup: Create the project within the folder
    example = project_request_examples["create"]
    example["folder_id"] = folder["id"]
    created_projects = []
    for i in project_names:
        example["name"] = i
        response = await client.post(f"{settings.API_V2_STR}/project", json=example)
        project = response.json()
        created_projects.append(project)

    yield created_projects

    # Teardown: Delete the project after the test
    # Note: Folder deletion will be handled by the fixture_create_folder fixture's teardown
    for project in created_projects:
        await client.delete(f"{settings.API_V2_STR}/project/{project['id']}")


@pytest.fixture
async def fixture_create_layer_project(
    client: AsyncClient,
    fixture_create_project,
    fixture_create_feature_and_raster_and_table_layer,
):
    project_id = fixture_create_project["id"]
    feature_layer, raster_layer, table_layer = (
        fixture_create_feature_and_raster_and_table_layer
    )
    feature_layer_id = feature_layer["id"]
    raster_layer_id = raster_layer["id"]
    table_layer_id = table_layer["id"]

    # Add layers to project
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={feature_layer_id}&layer_ids={raster_layer_id}&layer_ids={table_layer_id}"
    )
    assert response.status_code == 200
    layer_project = response.json()

    # Get layer project ids
    layer_project_ids = []
    for layer in response.json():
        layer_project_ids.append(layer["id"])

    # Get Project
    response = await client.get(f"{settings.API_V2_STR}/project/{project_id}")
    assert response.status_code == 200

    # Check if layers are in layer order at right position
    layer_order = response.json()["layer_order"]
    assert layer_order[0] == layer_project_ids[0]
    assert layer_order[1] == layer_project_ids[1]

    return {"layer_project": layer_project, "project_id": project_id}


async def create_scenario(
    client: AsyncClient,
    project_id: str,
):
    # Create a scenario
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/scenario",
        json={"name": "Test Scenario"},
    )
    assert response.status_code == 201

    return response.json()


@pytest.fixture
async def fixture_create_project_scenario(
    client: AsyncClient,
    fixture_create_project,
):
    # Create a project
    project_id = fixture_create_project["id"]

    # Create a scenario
    scenario = await create_scenario(client, project_id)

    return {
        "project_id": project_id,
        "scenario_id": scenario["id"],
    }


@pytest.fixture
async def fixture_create_project_scenario_features(
    client: AsyncClient,
    fixture_add_aggregate_point_layer_to_project,
):
    # Create a point layer associated with a project
    project_id = fixture_add_aggregate_point_layer_to_project["project_id"]
    layer_project_id = fixture_add_aggregate_point_layer_to_project[
        "source_layer_project_id"
    ]

    # Create a scenario
    scenario_id = (await create_scenario(client, project_id))["id"]

    # Create scenario features
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer/{layer_project_id}/scenario/{scenario_id}/features",
        json=[
            {
                "layer_project_id": layer_project_id,
                "edit_type": "n",
                "geom": "POINT (11.519519090652468 48.15706825475166)",
            },
            {
                "layer_project_id": layer_project_id,
                "feature_id": "01910d8e-0bdd-7e9e-88d7-45b177eb0e04",
                "edit_type": "m",
                "geom": "POINT (11.596396565437317 48.11837666091377)",
            },
            {
                "layer_project_id": layer_project_id,
                "feature_id": "01910d8e-0bbf-78bd-903b-50c8c060aafb",
                "edit_type": "d",
                "geom": "POINT (11.566457578680202 48.14265042244961)",
            },
        ],
    )
    assert response.status_code == 201

    return {
        "project_id": project_id,
        "layer_project_id": layer_project_id,
        "scenario_id": scenario_id,
        "features": response.json()["features"],
    }


@pytest.fixture(autouse=True)
def set_testing_config():
    settings.TESTING = True
    yield
    settings.TESTING = False


@pytest.fixture()
async def fixture_upload_file_point(client: AsyncClient, fixture_create_user):
    return await upload_valid_file(client, "point")


@pytest.fixture()
async def fixture_upload_file_table(client: AsyncClient, fixture_create_user):
    return await upload_valid_file(client, "table")


file_types = ["point", "line", "polygon", "no_geometry"]


@pytest.fixture(params=file_types)
async def fixture_upload_files(client: AsyncClient, fixture_create_user, request):
    return await upload_valid_files(client, request.param)


files = [
    "invalid_wrong_file_extension.gpkg",
    "invalid_bad_formed.xlsx",
    "invalid_no_header.csv",
    "invalid_missing_file.zip",
]


@pytest.fixture(params=files)
async def fixture_upload_file_invalid(
    client: AsyncClient, fixture_create_user, request
):
    return await upload_invalid_file(client, request.param)


async def create_layer_from_dataset(
    client: AsyncClient,
    dataset_id,
    fixture_get_home_folder,
    layer_type,
    project_id=None,
    layer_dict=None,
):
    # Get feature layer dict and add layer ID
    if layer_dict is None:
        layer_dict = layer_request_examples["create"][layer_type]["value"]
    layer_dict["name"] = generate_random_string(12)
    layer_dict["dataset_id"] = dataset_id
    layer_dict["folder_id"] = fixture_get_home_folder["id"]

    # Identify correct endpoint
    endpoint = None
    if LayerType.feature.value in layer_type:
        endpoint = "feature-standard"
    elif LayerType.table.value in layer_type:
        endpoint = "table"
    else:
        raise ValueError("Layer type not recognized")

    # Hit endpoint to create layer and add optional project_id
    if project_id:
        url = f"{settings.API_V2_STR}/layer/{endpoint}?project_id={project_id}"
    else:
        url = f"{settings.API_V2_STR}/layer/{endpoint}"
    response = await client.post(url, json=layer_dict)
    assert response.status_code == 201

    # Get job id
    job_id = response.json()["job_id"]

    # Check if job is finished
    job = await check_job_status(client, job_id)
    assert job["status_simple"] == "finished"
    response = await client.post(
        f"{settings.API_V2_STR}/layer", json={"search": layer_dict["name"]}
    )
    assert response.status_code == 200
    layer_dict = response.json()["items"][0]
    return {**layer_dict, "job_id": job_id}


async def upload_and_create_layer(client, file_dir, home_folder, layer_type):
    dataset = await upload_file(client, file_dir)
    layer = await create_layer_from_dataset(
        client,
        dataset["dataset_id"],
        home_folder,
        layer_type,
    )
    return layer


layer_types = [
    LayerType.feature,
    LayerType.raster,
    LayerType.table,
]


@pytest.fixture(params=layer_types)
async def fixture_create_layers(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder, request
):
    if request.param == LayerType.feature:
        metadata = await upload_valid_file(client, "point")
        layer = await create_layer_from_dataset(
            client, metadata["dataset_id"], fixture_get_home_folder, request.param
        )
    elif request.param == LayerType.raster:
        layer = await create_raster_layer(client, fixture_get_home_folder)
    elif request.param == LayerType.table:
        metadata = await upload_valid_file(client, "no_geometry")
        layer = await create_layer_from_dataset(
            client, metadata["dataset_id"], fixture_get_home_folder, request.param
        )
    return layer


@pytest.fixture
async def fixture_create_layer_in_project(
    client: AsyncClient, fixture_create_project, fixture_get_home_folder
):
    metadata = await upload_valid_file(client, "point")
    layer = await create_layer_from_dataset(
        client,
        metadata["dataset_id"],
        fixture_get_home_folder,
        LayerType.feature,
        fixture_create_project["id"],
    )
    return layer


@pytest.fixture
async def fixture_create_polygon_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    dir_gpkg = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "zipcode_polygon.gpkg"
    )
    return await upload_and_create_layer(
        client, dir_gpkg, fixture_get_home_folder, LayerType.feature
    )


@pytest.fixture
async def fixture_create_feature_and_raster_and_table_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    metadata = await upload_valid_file(client, "point")
    feature_layer = await create_layer_from_dataset(
        client,
        metadata["dataset_id"],
        fixture_get_home_folder,
        LayerType.feature,
    )

    raster_layer = await create_raster_layer(
        client,
        fixture_get_home_folder,
    )

    metadata = await upload_valid_file(client, "no_geometry")
    table_layer = await create_layer_from_dataset(
        client,
        metadata["dataset_id"],
        fixture_get_home_folder,
        LayerType.table,
    )

    return feature_layer, raster_layer, table_layer


@pytest.fixture
async def fixture_add_polygon_layer_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_polygon_layer
):
    layer_gpkg = fixture_create_polygon_layer
    project_id = fixture_create_project["id"]
    # Add layers to project
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_gpkg['id']}"
    )
    assert response.status_code == 200
    layers_project = response.json()
    layer_project_id = layers_project[0]["id"]

    return {
        "layer_project_id": layer_project_id,
        "project_id": project_id,
    }


@pytest.fixture
async def fixture_create_large_polygon_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    dir_gpkg = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "large_polygon.gpkg"
    )
    return await upload_and_create_layer(
        client, dir_gpkg, fixture_get_home_folder, LayerType.feature
    )


@pytest.fixture
async def fixture_add_large_polygon_layer_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_large_polygon_layer
):
    layer_gpkg = fixture_create_large_polygon_layer
    project_id = fixture_create_project["id"]
    # Add layers to project
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_gpkg['id']}"
    )
    assert response.status_code == 200
    layers_project = response.json()
    layer_project_id = layers_project[0]["id"]

    return {
        "layer_project_id": layer_project_id,
        "project_id": project_id,
    }


@pytest.fixture
async def fixture_create_join_layers(client: AsyncClient, fixture_get_home_folder):
    dir_csv = os.path.join(settings.TEST_DATA_DIR, "layers", "tool", "events.csv")
    dir_gpkg = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "zipcode_polygon.gpkg"
    )
    layer_csv = await upload_and_create_layer(
        client, dir_csv, fixture_get_home_folder, LayerType.table
    )
    layer_gpkg = await upload_and_create_layer(
        client, dir_gpkg, fixture_get_home_folder, LayerType.feature
    )
    return {
        "home_folder": fixture_get_home_folder,
        "layer_csv": layer_csv,
        "layer_gpkg": layer_gpkg,
    }


@pytest.fixture
async def fixture_create_aggregate_point_layers(
    client: AsyncClient, fixture_get_home_folder
):
    dir_points = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "points_with_category.gpkg"
    )
    dir_polygons = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "zipcode_polygon.gpkg"
    )
    layer_points = await upload_and_create_layer(
        client, dir_points, fixture_get_home_folder, LayerType.feature
    )
    layer_polygons = await upload_and_create_layer(
        client, dir_polygons, fixture_get_home_folder, LayerType.feature
    )
    return {
        "home_folder": fixture_get_home_folder,
        "layer_points": layer_points,
        "layer_polygons": layer_polygons,
    }


@pytest.fixture
async def fixture_create_aggregate_point_layer(
    client: AsyncClient, fixture_get_home_folder
):
    dir_points = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "points_with_category.gpkg"
    )
    layer_points = await upload_and_create_layer(
        client, dir_points, fixture_get_home_folder, LayerType.feature
    )
    return {"home_folder": fixture_get_home_folder, "layer_points": layer_points}


@pytest.fixture
async def fixture_add_join_layers_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_join_layers
):
    layer_csv = fixture_create_join_layers["layer_csv"]
    layer_gpkg = fixture_create_join_layers["layer_gpkg"]
    project_id = fixture_create_project["id"]
    # Add layers to project
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_csv['id']}&layer_ids={layer_gpkg['id']}"
    )
    assert response.status_code == 200
    layers_project = response.json()
    for layer in layers_project:
        if layer["type"] == LayerType.table.value:
            layer_id_table = layer["id"]
        elif layer["type"] == LayerType.feature.value:
            layer_id_gpkg = layer["id"]

    return {
        "layer_id_table": layer_id_table,
        "layer_id_gpkg": layer_id_gpkg,
        "project_id": project_id,
    }


@pytest.fixture
async def fixture_add_aggregate_point_layers_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_aggregate_point_layers
):
    layer_points = fixture_create_aggregate_point_layers["layer_points"]
    layer_polygons = fixture_create_aggregate_point_layers["layer_polygons"]
    project_id = fixture_create_project["id"]

    # Add layers to project one by one and return layer_project_id
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_points['id']}"
    )
    assert response.status_code == 200
    layer_project_points = response.json()
    source_layer_project_id = layer_project_points[0]["id"]

    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_polygons['id']}"
    )
    assert response.status_code == 200
    layer_project_polygons = response.json()
    aggregation_layer_project_id = layer_project_polygons[0]["id"]

    return {
        "source_layer_project_id": source_layer_project_id,
        "aggregation_layer_project_id": aggregation_layer_project_id,
        "project_id": project_id,
    }


@pytest.fixture
async def fixture_add_aggregate_point_layer_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_aggregate_point_layer
):
    layer_points = fixture_create_aggregate_point_layer["layer_points"]
    project_id = fixture_create_project["id"]

    # Add layers to project one by one and return layer_project_id
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_points['id']}"
    )
    assert response.status_code == 200
    layer_project_points = response.json()
    source_layer_project_id = layer_project_points[0]["id"]

    return {
        "source_layer_project_id": source_layer_project_id,
        "project_id": project_id,
    }


@pytest.fixture
async def fixture_create_aggregate_polygon_layers(
    client: AsyncClient, fixture_get_home_folder
):
    dir_source_layer = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "green_areas.gpkg"
    )
    dir_aggregation_layer = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "zipcode_polygon.gpkg"
    )
    layer_source = await upload_and_create_layer(
        client, dir_source_layer, fixture_get_home_folder, LayerType.feature
    )
    layer_aggregation = await upload_and_create_layer(
        client, dir_aggregation_layer, fixture_get_home_folder, LayerType.feature
    )
    return {
        "home_folder": fixture_get_home_folder,
        "layer_source": layer_source,
        "layer_aggregation": layer_aggregation,
    }


@pytest.fixture
async def fixture_create_aggregate_polygon_layer(
    client: AsyncClient, fixture_get_home_folder
):
    dir_source_layer = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "green_areas.gpkg"
    )
    layer_source = await upload_and_create_layer(
        client, dir_source_layer, fixture_get_home_folder, LayerType.feature
    )
    return {
        "home_folder": fixture_get_home_folder,
        "layer_source": layer_source,
    }


@pytest.fixture
async def fixture_add_aggregate_polygon_layers_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_aggregate_polygon_layers
):
    layer_source = fixture_create_aggregate_polygon_layers["layer_source"]
    layer_aggregation = fixture_create_aggregate_polygon_layers["layer_aggregation"]
    project_id = fixture_create_project["id"]

    # Add layers to project one by one and return layer_project_id
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_source['id']}"
    )
    assert response.status_code == 200
    layer_project_source = response.json()
    source_layer_project_id = layer_project_source[0]["id"]

    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_aggregation['id']}"
    )
    assert response.status_code == 200
    layer_project_aggregation = response.json()
    aggregation_layer_project_id = layer_project_aggregation[0]["id"]

    return {
        "source_layer_project_id": source_layer_project_id,
        "aggregation_layer_project_id": aggregation_layer_project_id,
        "project_id": project_id,
    }


@pytest.fixture
async def fixture_add_aggregate_polygon_layer_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_aggregate_polygon_layer
):
    layer_source = fixture_create_aggregate_polygon_layer["layer_source"]
    project_id = fixture_create_project["id"]

    # Add layers to project one by one and return layer_project_id
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_source['id']}"
    )
    assert response.status_code == 200
    layer_project_source = response.json()
    source_layer_project_id = layer_project_source[0]["id"]

    return {
        "source_layer_project_id": source_layer_project_id,
        "project_id": project_id,
    }


geometry_types = ["point", "line", "polygon"]


@pytest.fixture(params=geometry_types)
async def fixture_create_basic_layer(
    request, client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    layer_type = request.param
    dir_gpkg = os.path.join(
        settings.TEST_DATA_DIR, "layers", "valid", layer_type, "valid.gpkg"
    )
    layer = await upload_and_create_layer(
        client, dir_gpkg, fixture_get_home_folder, LayerType.feature
    )
    return {
        "home_folder": fixture_get_home_folder,
        "layer": layer,
        "layer_type": layer_type,
    }


@pytest.fixture
async def fixture_add_basic_layer_to_project(
    client: AsyncClient, fixture_create_project, fixture_create_basic_layer
):
    layer = fixture_create_basic_layer["layer"]
    project_id = fixture_create_project["id"]
    # Add layers to project
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer['id']}"
    )
    assert response.status_code == 200
    layers_project = response.json()
    layer_project_id = layers_project[0]["id"]

    return {
        "layer_project_id": layer_project_id,
        "project_id": project_id,
        "layer_type": fixture_create_basic_layer["layer_type"],
    }


geometry_layers = ["zipcode_polygon.gpkg", "zipcode_point.gpkg"]


@pytest.fixture(params=geometry_layers)
async def fixture_add_origin_destination_layers_to_project(
    request,
    client: AsyncClient,
    fixture_create_project,
    fixture_get_home_folder,
):
    # Create layers
    dir_origin_destination_matrix = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", "origin_destination_matrix.csv"
    )
    dir_geometry_layer = os.path.join(
        settings.TEST_DATA_DIR, "layers", "tool", request.param
    )
    layer_origin_destination_matrix = await upload_and_create_layer(
        client, dir_origin_destination_matrix, fixture_get_home_folder, "table"
    )
    layer_geometry_layer = await upload_and_create_layer(
        client, dir_geometry_layer, fixture_get_home_folder, LayerType.feature
    )
    project_id = fixture_create_project["id"]

    # Add layers to project one by one and return layer_project_id
    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_origin_destination_matrix['id']}"
    )
    assert response.status_code == 200
    layer_project_origin_destination_matrix = response.json()
    origin_destination_matrix_layer_project_id = (
        layer_project_origin_destination_matrix[0]["id"]
    )

    response = await client.post(
        f"{settings.API_V2_STR}/project/{project_id}/layer?layer_ids={layer_geometry_layer['id']}"
    )
    assert response.status_code == 200
    layer_project_geometry_layer = response.json()
    geometry_layer_project_id = layer_project_geometry_layer[0]["id"]

    return {
        "origin_destination_matrix_layer_project_id": origin_destination_matrix_layer_project_id,
        "geometry_layer_project_id": geometry_layer_project_id,
        "project_id": project_id,
    }


async def create_raster_layer(client: AsyncClient, home_folder):
    # Get table layer dict and add layer ID
    layer_dict = layer_request_examples["create"][LayerType.raster.value]["value"]
    layer_dict["folder_id"] = home_folder["id"]

    # Give layer a random name
    layer_dict["name"] = generate_random_string(10)
    # Hit endpoint to create raster layer
    response = await client.post(f"{settings.API_V2_STR}/layer/raster", json=layer_dict)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def fixture_create_feature_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    metadata = await upload_valid_file(client, "point")
    return await create_layer_from_dataset(
        client,
        metadata["dataset_id"],
        fixture_get_home_folder,
        LayerType.feature,
    )


@pytest.fixture
async def fixture_create_raster_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    return await create_raster_layer(
        client,
        fixture_get_home_folder,
    )


@pytest.fixture
async def fixture_create_feature_polygon_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    metadata = await upload_valid_file(client, "polygon")
    return await create_layer_from_dataset(
        client,
        metadata["dataset_id"],
        fixture_get_home_folder,
        LayerType.feature,
    )


@pytest.fixture
async def fixture_create_table_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    metadata = await upload_valid_file(client, "no_geometry")
    return await create_layer_from_dataset(
        client, metadata["dataset_id"], fixture_get_home_folder, LayerType.table
    )


@pytest.fixture
async def fixture_delete_layers(client: AsyncClient, fixture_create_layers):
    layer = fixture_create_layers
    layer_id = layer["id"]
    response = await client.delete(f"{settings.API_V2_STR}/layer/{layer_id}")
    assert response.status_code == 204

    # Check if layer is deleted
    response = await client.get(f"{settings.API_V2_STR}/layer/{layer_id}")
    assert response.status_code == 404  # Not Found

    if layer["type"] in (LayerType.feature, LayerType.table):
        await check_user_data_deleted(
            layer=layer,
        )


async def create_multiple_layer(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder, in_catalog: bool
):
    # Define layer metadata for the different layer types
    varying_attributes = [
        {
            "geographical_code": "de",
            "language_code": "de",
            "distributor_name": "Plan4Better GmbH",
            "data_category": "transportation",
            "license": "CC_BY",
            "in_catalog": in_catalog,
        },
        {
            "geographical_code": "be",
            "language_code": "en",
            "distributor_name": "Plan4Better GmbH",
            "data_category": "environment",
            "license": "ODC_ODbL",
            "in_catalog": in_catalog,
        },
        {
            "geographical_code": "de",
            "language_code": "de",
            "distributor_name": "Technical University of Munich",
            "data_category": "transportation",
            "license": "ODC_ODbL",
            "in_catalog": in_catalog,
        },
        {
            "geographical_code": "de",
            "language_code": "en",
            "distributor_name": "Technical University of Munich",
            "data_category": "transportation",
            "license": "CC_BY",
            "in_catalog": in_catalog,
        },
    ]
    layer_geometry_types = ["point", "line", "polygon", "point"]
    layers = []
    cnt = 0
    for type in layer_geometry_types:
        # Get layer type specific metadata
        additional_metadata = varying_attributes[cnt]
        file_dir = os.path.join(
            settings.TEST_DATA_DIR, "layers", "valid", type, "valid.gpkg"
        )
        layer_dict = {
            "description": "Layer description",
            "tags": ["tag1", "tag2"],
            "lineage": "Derived from web research and ground surveys conducted in 2021 by trained professionals.",
            "positional_accuracy": "High accuracy with an error margin of ±2 meters.",
            "attribute_accuracy": "Attribute data verified with 90% confidence level.",
            "completeness": "Data is 98% complete, missing data in remote areas.",
            "upload_reference_system": 4326,
            "upload_file_type": "geojson",
            "distributor_email": "info@plan4better.de",
            "distribution_url": "https://plan4better.de/data/samples/sample_data.geojson",
            "attribution": "Dataset provided by Plan4Better GmbH.",
            "data_reference_year": 2021,
            **additional_metadata,
        }
        dataset = await upload_file(client, file_dir)
        layer = await create_layer_from_dataset(
            client,
            dataset["dataset_id"],
            fixture_get_home_folder,
            LayerType.feature.value,
            project_id=None,
            layer_dict=layer_dict,
        )
        layers.append(layer)
        cnt += 1
    return layers


@pytest.fixture
async def fixture_create_multiple_layers(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    return await create_multiple_layer(
        client, fixture_create_user, fixture_get_home_folder, False
    )


@pytest.fixture
async def fixture_create_catalog_layers(
    client: AsyncClient, fixture_create_user, fixture_get_home_folder
):
    return await create_multiple_layer(
        client, fixture_create_user, fixture_get_home_folder, True
    )


def get_payload_types(request_examples: dict) -> list:
    return request_examples


def create_generic_toolbox_fixture(endpoint: str, request_examples: dict):
    @pytest.fixture(params=get_payload_types(request_examples))
    async def generic_post_fixture(
        client: AsyncClient, fixture_create_project, request
    ):
        payload = request_examples[request.param]["value"]
        project_id = fixture_create_project["id"]
        response = await client.post(
            f"{settings.API_V2_STR}{endpoint}?project_id={project_id}", json=payload
        )
        assert response.status_code == 201
        return response.json()

    return generic_post_fixture


@pytest.fixture
async def fixture_create_shared_team_layers(
    client: AsyncClient, fixture_create_folder, db_session
):

    # Create five layers
    layers = []
    for _i in range(5):
        layer = await create_raster_layer(client, fixture_create_folder)
        layers.append(layer)

    # Create a team
    team1 = Team(name="test_team", avatar="https://www.plan4better.de/logo.png")
    team2 = Team(name="test_team2", avatar="https://www.plan4better.de/logo.png")

    # Create role
    role = Role(name="team-member")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)

    # Create layer team links
    layer_teams1 = []
    layer_teams2 = []
    for layer in layers:
        layer_team1 = LayerTeamLink(
            layer_id=layer["id"], team_id=team1.id, role_id=role.id
        )
        layer_team2 = LayerTeamLink(
            layer_id=layer["id"], team_id=team2.id, role_id=role.id
        )
        layer_teams1.append(layer_team1)
        layer_teams2.append(layer_team2)

    team1.layer_links = layer_teams1
    team2.layer_links = layer_teams2
    db_session.add(team1)
    db_session.add(team2)
    await db_session.commit()

    return {"teams": [team1, team2], "layers": layers}


@pytest.fixture
async def fixture_create_shared_organization_layers(
    client: AsyncClient, fixture_create_folder, db_session
):

    # Create five layers
    layers = []
    for _i in range(5):
        layer = await create_raster_layer(client, fixture_create_folder)
        layers.append(layer)

    # Create organization
    organization1 = Organization(
        name="test_organization", avatar="https://www.plan4better.de/logo.png"
    )
    organization2 = Organization(
        name="test_organization2", avatar="https://www.plan4better.de/logo.png"
    )

    # Create role
    role = Role(name="organization_member")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)

    # Create layer organization links
    layer_organizations1 = []
    layer_organizations2 = []
    for layer in layers:
        layer_organization1 = LayerOrganizationLink(
            layer_id=layer["id"], organization_id=organization1.id, role_id=role.id
        )
        layer_organization2 = LayerOrganizationLink(
            layer_id=layer["id"], organization_id=organization2.id, role_id=role.id
        )
        layer_organizations1.append(layer_organization1)
        layer_organizations2.append(layer_organization2)

    organization1.layer_links = layer_organizations1
    organization2.layer_links = layer_organizations2
    db_session.add(organization1)
    db_session.add(organization2)
    await db_session.commit()

    return {"organizations": [organization1, organization2], "layers": layers}


@pytest.fixture
async def fixture_create_shared_team_projects(
    client: AsyncClient, fixture_create_folder, fixture_create_projects, db_session
):

    # Create projects
    projects = fixture_create_projects

    # Create a team
    team1 = Team(name="test_team", avatar="https://www.plan4better.de/logo.png")
    team2 = Team(name="test_team2", avatar="https://www.plan4better.de/logo.png")

    # Create role
    role = Role(name="team-member")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)

    # Create layer team links
    project_teams1 = []
    project_teams2 = []
    for project in projects:
        project_team1 = ProjectTeamLink(
            project_id=project["id"], team_id=team1.id, role_id=role.id
        )
        project_team2 = ProjectTeamLink(
            project_id=project["id"], team_id=team2.id, role_id=role.id
        )
        project_teams1.append(project_team1)
        project_teams2.append(project_team2)

    team1.project_links = project_teams1
    team2.project_links = project_teams2
    db_session.add(team1)
    db_session.add(team2)
    await db_session.commit()

    return {"teams": [team1, team2], "projects": projects}


fixture_catchment_area_active_mobility = create_generic_toolbox_fixture(
    "/active-mobility/catchment-area",
    active_mobility_request_examples["catchment_area_active_mobility"],
)

fixture_catchment_area_pt = create_generic_toolbox_fixture(
    "/motorized-mobility/pt/catchment-area",
    request_examples_catchment_area_pt,
)

fixture_catchment_area_car = create_generic_toolbox_fixture(
    "/motorized-mobility/car/catchment-area",
    request_examples_catchment_area_car,
)
