from typing import Any, Dict, List, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import UUID4

from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.crud.crud_project import project as crud_project
from core.db.models._link_model import LayerProjectLink
from core.db.models.project import Project
from core.db.session import AsyncSession
from core.deps.auth import auth_z
from core.endpoints.deps import get_db
from core.schemas.project import (
    IFeatureStandardProjectRead,
    IFeatureStreetNetworkProjectRead,
    IFeatureToolProjectRead,
    IRasterProjectRead,
    ITableProjectRead,
)
from core.schemas.project import (
    request_examples as project_request_examples,
)

router = APIRouter()


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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    layer_ids: List[UUID4] = Query(
        ...,
        description="List of layer IDs to add to the project",
        examples=[["3fa85f64-5717-4562-b3fc-2c963f66afa6"]],
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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    layer_project_id: int = Path(
        ...,
        description="Layer project ID to get",
        examples=["1"],
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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    layer_project_id: int = Path(
        ...,
        description="Layer Project ID to update",
        examples=["1"],
    ),
    layer_in: Dict[str, Any] = Body(
        ...,
        examples=[project_request_examples["update_layer"]],
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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    layer_project_id: int = Query(
        ...,
        description="Layer ID to delete",
        examples=["1"],
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

    # layer_order may be None (e.g. copied projects whose source had no order),
    # so treat it as empty and only remove the id if present.
    layer_order = list(project.layer_order or [])
    if layer_project.id in layer_order:
        layer_order.remove(layer_project.id)

    await crud_project.update(
        async_session,
        db_obj=project,
        obj_in={"layer_order": layer_order},
    )

    return None
