from typing import Any, Dict, List, Union
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from fastapi.responses import JSONResponse
from fastapi_pagination import Page
from fastapi_pagination import Params as PaginationParams
from pydantic import UUID4
from sqlalchemy import select
from sqlmodel import update

from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.crud.crud_layer_project_group import (
    layer_project_group as crud_layer_project_group,
)
from core.crud.crud_project import project as crud_project
from core.crud.crud_scenario import scenario as crud_scenario
from core.crud.crud_user_project import user_project as crud_user_project
from core.db.models._link_model import (
    LayerProjectGroup,
    LayerProjectLink,
    UserProjectLink,
)
from core.db.models.project import Project
from core.db.models.scenario import Scenario
from core.db.session import AsyncSession
from core.deps.auth import auth_z
from core.endpoints.deps import get_db, get_scenario, get_user_id
from core.schemas.common import OrderEnum
from core.schemas.project import (
    IFeatureStandardProjectRead,
    IFeatureStreetNetworkProjectRead,
    IFeatureToolProjectRead,
    ILayerProjectGroupCreate,
    ILayerProjectGroupRead,
    ILayerProjectGroupUpdate,
    InitialViewState,
    IProjectBaseUpdate,
    IProjectCreate,
    IProjectRead,
    IRasterProjectRead,
    ITableProjectRead,
    LayerTreeUpdate,
    ProjectPublicRead,
)
from core.schemas.project import (
    request_examples as project_request_examples,
)
from core.schemas.scenario import (
    IScenarioCreate,
    IScenarioFeatureCreate,
    IScenarioFeatureUpdate,
    IScenarioUpdate,
)
from core.schemas.scenario import (
    request_examples as scenario_request_examples,
)
from core.utils import to_feature_collection

router = APIRouter()


### Project endpoints
@router.post(
    "",
    summary="Create a new project",
    response_model=IProjectRead,
    response_model_exclude_none=True,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def create_project(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    *,
    project_in: IProjectCreate = Body(
        ..., example=project_request_examples["create"], description="Project to create"
    ),
) -> IProjectRead:
    """This will create an empty project with a default initial view state. The project does not contains layers."""

    # Create project
    return await crud_project.create(
        async_session=async_session,
        project_in=Project(**project_in.model_dump(exclude_none=True), user_id=user_id),
        initial_view_state=project_in.initial_view_state,
    )


@router.get(
    "/{project_id}",
    summary="Retrieve a project by its ID",
    response_model=IProjectRead,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_project(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
) -> IProjectRead:
    """Retrieve a project by its ID."""

    # Get project
    project = await crud_project.get(async_session, id=project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return IProjectRead(**project.model_dump())


@router.get(
    "",
    summary="Retrieve a list of projects",
    response_model=Page[IProjectRead],
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_projects(
    async_session: AsyncSession = Depends(get_db),
    page_params: PaginationParams = Depends(),
    folder_id: UUID4 | None = Query(None, description="Folder ID"),
    user_id: UUID4 = Depends(get_user_id),
    team_id: UUID | None = Query(
        None,
        description="The ID of the team to get the layers from",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    organization_id: UUID | None = Query(
        None,
        description="The ID of the organization to get the layers from",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    search: str = Query(None, description="Searches the name of the project"),
    order_by: str = Query(
        None,
        description="Specify the column name that should be used to order. You can check the Project model to see which column names exist.",
        example="created_at",
    ),
    order: OrderEnum = Query(
        "descendent",
        description="Specify the order to apply. There are the option ascendent or descendent.",
        example="descendent",
    ),
) -> Page[IProjectRead]:
    """Retrieve a list of projects."""

    projects = await crud_project.get_projects(
        async_session=async_session,
        user_id=user_id,
        folder_id=folder_id,
        page_params=page_params,
        search=search,
        order_by=order_by,
        order=order,
        team_id=team_id,
        organization_id=organization_id,
    )

    return projects


@router.put(
    "/{project_id}",
    response_model=IProjectRead,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_project(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    project_in: IProjectBaseUpdate = Body(
        ..., example=project_request_examples["update"], description="Project to update"
    ),
) -> IProjectRead:
    """Update base attributes of a project by its ID."""

    # Update project
    project = await crud_project.update_base(
        async_session=async_session,
        id=project_id,
        project=project_in,
    )
    return project


@router.delete(
    "/{project_id}",
    response_model=None,
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_project(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
) -> None:
    """Delete a project by its ID."""

    # Get project
    project = await crud_project.get(async_session, id=project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Delete project
    await crud_project.delete(db=async_session, id=project_id)
    return


@router.get(
    "/{project_id}/initial-view-state",
    response_model=InitialViewState,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_project_initial_view_state(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
) -> InitialViewState:
    """Retrieve initial view state of a project by its ID."""

    # Get initial view state
    user_project = (
        await crud_user_project.get_by_multi_keys(
            async_session, keys={"user_id": user_id, "project_id": project_id}
        )
    )[0]
    assert type(user_project) is UserProjectLink
    return InitialViewState(**user_project.initial_view_state)


@router.put(
    "/{project_id}/initial-view-state",
    response_model=InitialViewState,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_project_initial_view_state(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    initial_view_state: InitialViewState = Body(
        ...,
        example=project_request_examples["initial_view_state"],
        description="Initial view state to update",
    ),
) -> InitialViewState:
    """Update initial view state of a project by its ID."""

    # Update project
    user_project = await crud_user_project.update_initial_view_state(
        async_session,
        user_id=user_id,
        project_id=project_id,
        initial_view_state=initial_view_state,
    )
    return InitialViewState(**user_project.initial_view_state)


##############################################
### Layer endpoints
##############################################


@router.post(
    "/{project_id}/layer",
    response_model=List[
        IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    ],
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def add_layers_to_project(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    layer_ids: List[UUID4] = Query(
        ...,
        description="List of layer IDs to add to the project",
        example=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
) -> List[
    IFeatureStandardProjectRead
    | IFeatureToolProjectRead
    | ITableProjectRead
    | IRasterProjectRead
]:
    """Add layers to a project by its ID."""

    # Add layers to project
    layers_project = await crud_layer_project.create(
        async_session=async_session,
        project_id=project_id,
        layer_ids=layer_ids,
    )
    assert isinstance(layers_project, List)

    return layers_project


@router.get(
    "/{project_id}/layer",
    response_model=list,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def get_layers_from_project(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
) -> List[
    IFeatureStandardProjectRead
    | IFeatureToolProjectRead
    | IFeatureStreetNetworkProjectRead
    | ITableProjectRead
    | IRasterProjectRead
]:
    """Get layers from a project by its ID."""

    # Get all layers from project
    layers_project = await crud_layer_project.get_layers(
        async_session,
        project_id=project_id,
    )
    assert isinstance(layers_project, List)

    return layers_project


@router.get(
    "/{project_id}/layer/{layer_project_id}",
    response_model=IFeatureStandardProjectRead
    | IFeatureToolProjectRead
    | ITableProjectRead
    | IRasterProjectRead,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def get_layer_from_project(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    layer_project_id: int = Path(
        ...,
        description="Layer project ID to get",
        example="1",
    ),
) -> Union[
    IFeatureStandardProjectRead
    | IFeatureToolProjectRead
    | ITableProjectRead
    | IRasterProjectRead
]:
    layer_project = (
        await crud_layer_project.get_by_ids(async_session, ids=[layer_project_id])
    )[0]
    assert type(layer_project) is (
        IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    )

    return layer_project


@router.put(
    "/{project_id}/layer/{layer_project_id}",
    response_model=IFeatureStandardProjectRead
    | IFeatureToolProjectRead
    | ITableProjectRead
    | IRasterProjectRead,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_layer_in_project(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    layer_project_id: int = Path(
        ...,
        description="Layer Project ID to update",
        example="1",
    ),
    layer_in: Dict[str, Any] = Body(
        ...,
        example=project_request_examples["update_layer"],
        description="Layer to update",
    ),
) -> Union[
    IFeatureStandardProjectRead
    | IFeatureToolProjectRead
    | ITableProjectRead
    | IRasterProjectRead
]:
    """Update layer in a project by its ID."""

    # NOTE: Avoid getting layer_id from layer_in as the authorization is running against the query params.

    # Update layer in project
    layer_project: (
        IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    ) = await crud_layer_project.update(
        async_session=async_session,
        id=layer_project_id,
        layer_in=layer_in,
    )

    # Update the last updated at of the project
    # Get project to update it
    project = await crud_project.get(async_session, id=project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Update project updated_at
    await crud_project.update(
        async_session,
        db_obj=project,
        obj_in={"updated_at": layer_project.updated_at},
    )

    # Get layers in project
    return layer_project


@router.delete(
    "/{project_id}/layer",
    response_model=None,
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_layer_from_project(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    layer_project_id: int = Query(
        ...,
        description="Layer ID to delete",
        example="1",
    ),
) -> None:
    """Delete layer from a project by its ID."""

    # Get layer project
    layer_project = await crud_layer_project.get(async_session, id=layer_project_id)
    if layer_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer project relation not found",
        )
    assert type(layer_project) is LayerProjectLink
    assert isinstance(layer_project.id, int)

    # Delete layer from project
    await crud_layer_project.delete(
        db=async_session,
        id=layer_project.id,
    )

    # Delete layer from project layer order
    project = await crud_project.get(async_session, id=project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    assert type(project) is Project
    assert isinstance(project.layer_order, List)

    layer_order = project.layer_order.copy()
    layer_order.remove(layer_project.id)

    await crud_project.update(
        async_session,
        db_obj=project,
        obj_in={"layer_order": layer_order},
    )

    return None


##############################################
### Scenario endpoints
##############################################


@router.get(
    "/{project_id}/scenario",
    summary="Retrieve a list of scenarios",
    response_model=Page[Scenario],
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_scenarios(
    async_session: AsyncSession = Depends(get_db),
    page_params: PaginationParams = Depends(),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    search: str = Query(None, description="Searches the name of the scenario"),
    order_by: str = Query(
        None,
        description="Specify the column name that should be used to order",
        example="created_at",
    ),
    order: OrderEnum = Query(
        "descendent",
        description="Specify the order to apply. There are the option ascendent or descendent.",
        example="descendent",
    ),
) -> Page[Scenario]:
    """Retrieve a list of scenarios."""
    query = select(Scenario).where(Scenario.project_id == project_id)
    scenarios = await crud_scenario.get_multi(
        db=async_session,
        query=query,
        page_params=page_params,
        search_text={"name": search} if search else {},
        order_by=order_by,
        order=order,
    )
    assert type(scenarios) is Page

    return scenarios


@router.post(
    "/{project_id}/scenario",
    summary="Create scenario",
    status_code=201,
    response_model=Scenario,
    response_model_exclude_none=True,
    dependencies=[Depends(auth_z)],
)
async def create_scenario(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project to create a scenario",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    scenario_in: IScenarioCreate = Body(
        ...,
        example=scenario_request_examples["create"],
        description="Scenario to create",
    ),
) -> Scenario:
    """Create scenario."""

    result = await crud_scenario.create(
        db=async_session,
        obj_in=Scenario(
            **scenario_in.model_dump(exclude_none=True),
            user_id=user_id,
            project_id=project_id,
        ).model_dump(),
    )
    assert type(result) is Scenario

    return result


@router.put(
    "/{project_id}/scenario/{scenario_id}",
    summary="Update scenario",
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def update_scenario(
    async_session: AsyncSession = Depends(get_db),
    scenario: Scenario = Depends(get_scenario),
    scenario_in: IScenarioUpdate = Body(
        ...,
        example=scenario_request_examples["update"],
        description="Scenario to update",
    ),
) -> Scenario:
    """Update scenario."""

    result = await crud_scenario.update(
        db=async_session,
        db_obj=scenario,
        obj_in=scenario_in,
    )
    assert type(result) is Scenario

    return result


@router.delete(
    "/{project_id}/scenario/{scenario_id}",
    summary="Delete scenario",
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_scenario(
    async_session: AsyncSession = Depends(get_db),
    scenario: Scenario = Depends(get_scenario),
) -> None:
    """Delete scenario."""

    await crud_scenario.remove(db=async_session, id=scenario.id)

    return None


@router.get(
    "/{project_id}/scenario/{scenario_id}/features",
    summary="Retrieve a list of scenario features",
    response_class=JSONResponse,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_scenario_features(
    async_session: AsyncSession = Depends(get_db),
    scenario: Scenario = Depends(get_scenario),
) -> Dict[str, Any]:
    """Retrieve a list of scenario features."""

    if not scenario.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Scenario ID is required"
        )

    scenario_features = await crud_scenario.get_features(
        async_session=async_session,
        scenario_id=scenario.id,
    )

    fc = to_feature_collection(scenario_features)

    return dict(fc)


@router.post(
    "/{project_id}/layer/{layer_project_id}/scenario/{scenario_id}/features",
    summary="Create scenario features",
    response_class=JSONResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def create_scenario_features(
    async_session: AsyncSession = Depends(get_db),
    scenario: Scenario = Depends(get_scenario),
    features: List[IScenarioFeatureCreate] = Body(
        ...,
        example=scenario_request_examples["create_scenario_features"],
        description="Scenario features to create",
    ),
) -> Dict[str, Any]:
    """Create scenario features."""

    fc = await crud_scenario.create_features(
        async_session=async_session,
        user_id=scenario.user_id,
        scenario=scenario,
        features=features,
    )

    return dict(fc)


@router.put(
    "/{project_id}/layer/{layer_project_id}/scenario/{scenario_id}/features",
    summary="Update scenario features",
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def update_scenario_feature(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    layer_project_id: int = Path(
        ...,
        description="Layer Project ID",
        example="1",
    ),
    scenario: Scenario = Depends(get_scenario),
    features: List[IScenarioFeatureUpdate] = Body(
        ...,
        description="Scenario features to update",
    ),
) -> None:
    """Update scenario features."""

    layer_project = await crud_layer_project.get(
        async_session, id=layer_project_id, extra_fields=[LayerProjectLink.layer]
    )
    if layer_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer project relation not found",
        )
    assert type(layer_project) is LayerProjectLink

    for feature in features:
        await crud_scenario.update_feature(
            async_session=async_session,
            user_id=user_id,
            layer_project=layer_project,
            scenario=scenario,
            feature=feature,
        )

    return None


@router.delete(
    "/{project_id}/layer/{layer_project_id}/scenario/{scenario_id}/features/{feature_id}",
    summary="Delete scenario feature",
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_scenario_features(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    layer_project_id: int = Path(
        ...,
        description="Layer Project ID",
        example="1",
    ),
    scenario: Scenario = Depends(get_scenario),
    feature_id: UUID = Path(
        ...,
        description="Feature ID to delete",
    ),
    h3_3: int | None = Query(
        None,
        description="H3 3 resolution",
        example=5,
    ),
) -> None:
    layer_project = await crud_layer_project.get(
        async_session, id=layer_project_id, extra_fields=[LayerProjectLink.layer]
    )
    if layer_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer project relation not found",
        )
    assert type(layer_project) is LayerProjectLink

    await crud_scenario.delete_feature(
        async_session=async_session,
        user_id=user_id,
        layer_project=layer_project,
        scenario=scenario,
        feature_id=feature_id,
        h3_3=h3_3,
    )

    return None


##############################################
### Project public endpoints
##############################################


@router.get(
    "/{project_id}/public",
    summary="Get public project",
    response_model=ProjectPublicRead | None,
    response_model_exclude_none=True,
)
async def get_public_project(
    project_id: str,
    async_session: AsyncSession = Depends(get_db),
) -> ProjectPublicRead | None:
    """
    Get shared project
    """
    result = await crud_project.get_public_project(
        async_session=async_session, project_id=project_id
    )

    return result


@router.post(
    "/{project_id}/publish",
    summary="Publish a project",
    dependencies=[Depends(auth_z)],
)
async def publish_project(
    project_id: str,
    user_id: UUID4 = Depends(get_user_id),
    async_session: AsyncSession = Depends(get_db),
) -> ProjectPublicRead:
    """
    Publish a project
    """
    result = ProjectPublicRead(
        **(
            await crud_project.publish_project(
                async_session=async_session, project_id=project_id
            )
        ).model_dump()
    )

    return result


@router.delete(
    "/{project_id}/unpublish",
    summary="Unpublish a project",
    dependencies=[Depends(auth_z)],
)
async def unpublish_project(
    project_id: str,
    async_session: AsyncSession = Depends(get_db),
) -> None:
    """
    Unpublish a project
    """
    await crud_project.unpublish_project(
        async_session=async_session, project_id=project_id
    )


##############################################
### Layer Group Endpoints
##############################################


@router.get(
    "/{project_id}/group",
    summary="Get project layer groups",
    response_model=List[ILayerProjectGroupRead],
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def get_project_layer_groups(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(..., description="The ID of the project"),
) -> List[ILayerProjectGroupRead]:
    """
    Get all layer groups for a project.
    Returns groups in hierarchical order.
    """
    return await crud_layer_project_group.get_groups_by_project(
        async_session=async_session, project_id=project_id
    )


@router.post(
    "/{project_id}/group",
    summary="Create a layer group",
    response_model=ILayerProjectGroupRead,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def create_layer_group(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(...),
    group_in: ILayerProjectGroupCreate = Body(...),
) -> ILayerProjectGroupRead:
    """
    Create a new layer group.
    Supports nesting up to 2 levels.
    """
    return await crud_layer_project_group.create(
        async_session=async_session, project_id=project_id, obj_in=group_in
    )


@router.put(
    "/{project_id}/group/{group_id}",
    summary="Update a layer group",
    response_model=ILayerProjectGroupRead,
    status_code=200,
)
async def update_layer_group(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(...),
    group_id: int = Path(...),
    group_in: ILayerProjectGroupUpdate = Body(...),
) -> LayerProjectGroup:
    group = await crud_layer_project_group.get(async_session, group_id)
    if not group or group.project_id != project_id:
        raise HTTPException(status_code=404, detail="Group not found")

    return await crud_layer_project_group.update(
        async_session=async_session, db_obj=group, obj_in=group_in
    )


@router.delete(
    "/{project_id}/group/{group_id}", summary="Delete a layer group", status_code=204
)
async def delete_layer_group(
    async_session: AsyncSession = Depends(get_db),
    project_id: UUID4 = Path(...),
    group_id: int = Path(...),
) -> None:
    """
    Delete a group.
    Database Cascade will automatically delete:
    1. The Group
    2. Any Sub-groups
    3. Any Layers linked to these groups (via LayerProjectLink)
    """

    group = await crud_layer_project_group.get(async_session, group_id)
    if not group or group.project_id != project_id:
        raise HTTPException(status_code=404, detail="Group not found")

    await crud_layer_project_group.remove(async_session, group_id)

    return None


@router.put(
    "/{project_id}/layer-tree",
    summary="Update layer tree structure (Reorder/Reparent)",
    status_code=204,
)
async def update_project_layer_tree(
    project_id: UUID4 = Path(..., description="The Project ID"),
    tree_in: LayerTreeUpdate = Body(
        ..., description="The flat list of items with updated positions"
    ),
    async_session: AsyncSession = Depends(get_db),
) -> None:
    """
    Batch updates the structure of the sidebar.
    This handles reordering items and reparenting (moving layers into/out of folders).
    Also updates visibility, collapsed states, and expanded states for both groups and layers.
    """

    updates_groups = []
    updates_layers = []

    # 1. Separate updates by type for efficient batch processing
    for item in tree_in.items:
        if item.type == "group":
            update_data = {
                "id": item.id,
                "parent_id": item.parent_id,
                "order": item.order,
            }
            # Handle properties for groups (visibility, expanded, etc.)
            if item.properties:
                # Get current group to preserve existing properties
                current_group = await async_session.get(LayerProjectGroup, item.id)
                if current_group and current_group.project_id == project_id:
                    current_properties = current_group.properties or {}

                    # Update visibility if provided
                    if "visibility" in item.properties:
                        current_properties["visibility"] = item.properties["visibility"]

                    # Update expanded state if provided
                    if "expanded" in item.properties:
                        current_properties["expanded"] = item.properties["expanded"]

                    update_data["properties"] = current_properties
            updates_groups.append(update_data)

        elif item.type == "layer":
            update_data = {
                "id": item.id,
                # Map standard 'parent_id' back to the specific DB column
                "layer_project_group_id": item.parent_id,
                "order": item.order,
            }
            # Handle properties for layers (visibility, legend.collapsed, etc.)
            if item.properties:
                # Get current layer to preserve existing properties
                current_layer = await async_session.get(LayerProjectLink, item.id)
                if current_layer and current_layer.project_id == project_id:
                    current_properties = current_layer.properties or {}

                    # Update visibility if provided
                    if "visibility" in item.properties:
                        current_properties["visibility"] = item.properties["visibility"]

                    # Update legend collapsed state if provided
                    if "legend" in item.properties:
                        if "legend" not in current_properties:
                            current_properties["legend"] = {}

                        # Merge legend properties
                        for key, value in item.properties["legend"].items():
                            current_properties["legend"][key] = value

                    update_data["properties"] = current_properties
            updates_layers.append(update_data)

    try:
        # 2. Update Groups (Iterative update is safer than bulk for complex constraints)
        if updates_groups:
            for g in updates_groups:
                update_values = {"parent_id": g["parent_id"], "order": g["order"]}
                # Include properties if updated
                if "properties" in g:
                    update_values["properties"] = g["properties"]

                await async_session.execute(
                    update(LayerProjectGroup)
                    .where(LayerProjectGroup.id == g["id"])
                    .where(LayerProjectGroup.project_id == project_id)  # Security check
                    .values(**update_values)
                )

        # 3. Update Layers
        if updates_layers:
            for l in updates_layers:
                update_values = {
                    "layer_project_group_id": l["layer_project_group_id"],
                    "order": l["order"],
                }
                # Include properties if provided
                if "properties" in l:
                    update_values["properties"] = l["properties"]

                await async_session.execute(
                    update(LayerProjectLink)
                    .where(LayerProjectLink.id == l["id"])
                    .where(LayerProjectLink.project_id == project_id)  # Security check
                    .values(**update_values)
                )

        await async_session.commit()

    except Exception:
        await async_session.rollback()
        # In production, log the actual error 'e'
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update layer tree structure.",
        )

    return None
