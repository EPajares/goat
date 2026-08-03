"""
Workflow Endpoints
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import UUID4

from core.crud.crud_workflow import workflow as crud_workflow
from core.db.session import AsyncSession
from core.deps.auth import auth_z
from core.endpoints.deps import get_db, get_user_id
from core.schemas.workflow import (
    WorkflowCreate,
    WorkflowRead,
    WorkflowUpdate,
)
from core.schemas.workflow import (
    request_examples as workflow_request_examples,
)

router = APIRouter()


@router.get(
    "/{project_id}/workflow",
    summary="Get all workflows for a project",
    response_model=List[WorkflowRead],
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def get_workflows(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
) -> List[WorkflowRead]:
    """Get all workflows for a project."""
    workflows = await crud_workflow.get_by_project(async_session, project_id=project_id)
    return [WorkflowRead.model_validate(w) for w in workflows]


@router.get(
    "/{project_id}/workflow/{workflow_id}",
    summary="Get a specific workflow",
    response_model=WorkflowRead,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def get_workflow(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    workflow_id: UUID4 = Path(
        ...,
        description="The ID of the workflow",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
) -> WorkflowRead:
    """Get a specific workflow by ID."""
    wf = await crud_workflow.get_by_project_and_id(
        async_session, project_id=project_id, workflow_id=workflow_id
    )
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return WorkflowRead.model_validate(wf)


@router.post(
    "/{project_id}/workflow",
    summary="Create a new workflow",
    response_model=WorkflowRead,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def create_workflow(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    workflow_in: WorkflowCreate = Body(
        ..., examples=[workflow_request_examples["create"]]
    ),
) -> WorkflowRead:
    """Create a new workflow for a project."""
    wf = await crud_workflow.create_for_project(
        async_session, project_id=project_id, obj_in=workflow_in
    )
    return WorkflowRead.model_validate(wf)


@router.put(
    "/{project_id}/workflow/{workflow_id}",
    summary="Update a workflow",
    response_model=WorkflowRead,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_workflow(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    workflow_id: UUID4 = Path(
        ...,
        description="The ID of the workflow",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    workflow_in: WorkflowUpdate = Body(
        ..., examples=[workflow_request_examples["update"]]
    ),
) -> WorkflowRead:
    """Update an existing workflow."""
    wf = await crud_workflow.update_for_project(
        async_session,
        project_id=project_id,
        workflow_id=workflow_id,
        obj_in=workflow_in,
    )
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return WorkflowRead.model_validate(wf)


@router.delete(
    "/{project_id}/workflow/{workflow_id}",
    summary="Delete a workflow",
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_workflow(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    workflow_id: UUID4 = Path(
        ...,
        description="The ID of the workflow",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
) -> None:
    """Delete a workflow."""
    deleted = await crud_workflow.delete_for_project(
        async_session, project_id=project_id, workflow_id=workflow_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )


@router.post(
    "/{project_id}/workflow/{workflow_id}/duplicate",
    summary="Duplicate a workflow",
    response_model=WorkflowRead,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def duplicate_workflow(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    workflow_id: UUID4 = Path(
        ...,
        description="The ID of the workflow to duplicate",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    new_name: str | None = Query(
        None,
        description="Name for the duplicated workflow",
        max_length=255,
    ),
) -> WorkflowRead:
    """Duplicate a workflow."""
    wf = await crud_workflow.duplicate(
        async_session, project_id=project_id, workflow_id=workflow_id, new_name=new_name
    )
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return WorkflowRead.model_validate(wf)
