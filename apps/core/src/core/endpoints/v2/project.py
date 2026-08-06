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
from fastapi_pagination import Page
from fastapi_pagination import Params as PaginationParams
from pydantic import UUID4
from sqlalchemy import select, text

from core.core.config import settings
from core.crud.crud_project import project as crud_project
from core.crud.crud_project_copy import copy_project as copy_project_fn
from core.crud.crud_user_project import user_project as crud_user_project
from core.db.models._link_model import (
    UserProjectLink,
    UserTeamLink,
)
from core.db.models.project import Project
from core.db.models.user import User
from core.db.session import AsyncSession
from core.deps.auth import auth_z
from core.endpoints.deps import get_db, get_user_id
from core.schemas.common import OrderEnum
from core.schemas.project import (
    InitialViewState,
    IProjectBaseUpdate,
    IProjectCopy,
    IProjectCreate,
    IProjectRead,
)
from core.schemas.project import (
    request_examples as project_request_examples,
)

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
        ...,
        examples=[project_request_examples["create"]],
        description="Project to create",
    ),
) -> IProjectRead:
    """This will create an empty project with a default initial view state. The project does not contains layers."""

    # Create project
    project = await crud_project.create(
        async_session=async_session,
        project_in=Project(**project_in.model_dump(exclude_none=True), user_id=user_id),
        initial_view_state=project_in.initial_view_state,
    )

    # Grant the creator project-owner access in project_user so auth_z can resolve it
    await async_session.execute(
        text(
            f"INSERT INTO {settings.SCHEMA}.project_user (project_id, user_id, role_id) "
            f"SELECT :project_id, :user_id, r.id FROM {settings.SCHEMA}.role r "
            f"WHERE r.name = 'project-owner' ON CONFLICT DO NOTHING"
        ),
        {"project_id": str(project.id), "user_id": str(user_id)},
    )
    await async_session.commit()

    return project


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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
) -> IProjectRead:
    """Retrieve a project by its ID."""

    # Get project
    project = await crud_project.get(async_session, id=project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Populate owned_by from the project owner
    owner = await async_session.get(User, project.user_id)
    owned_by = (
        {
            "id": str(owner.id),
            "firstname": owner.firstname,
            "lastname": owner.lastname,
            "avatar": owner.avatar,
        }
        if owner
        else None
    )

    # Get current user's role, checking all grant paths (user, team, org, folder).
    # The query returns the most permissive role across all paths.
    role_result = await async_session.execute(
        text(
            f"""
            SELECT role_name FROM (
                -- 1. Project owner (user_id matches project owner)
                SELECT 'project-owner' AS role_name, 1 AS priority
                FROM customer.project p
                WHERE p.id = :pid AND p.user_id = :uid

                UNION ALL

                -- 2. Direct user grant
                SELECT r.name, 2
                FROM {settings.SCHEMA}.project_user pu
                JOIN {settings.SCHEMA}.role r ON r.id = pu.role_id
                WHERE pu.project_id = :pid AND pu.user_id = :uid

                UNION ALL

                -- 3. Team grant
                SELECT r.name, 3
                FROM {settings.SCHEMA}.project_team pt
                JOIN {settings.SCHEMA}.user_team ut ON ut.team_id = pt.team_id
                JOIN {settings.SCHEMA}.role r ON r.id = pt.role_id
                WHERE pt.project_id = :pid AND ut.user_id = :uid

                UNION ALL

                -- 4. Organisation grant
                SELECT r.name, 4
                FROM {settings.SCHEMA}.project_organization po
                JOIN {settings.SCHEMA}.role r ON r.id = po.role_id
                JOIN {settings.SCHEMA}.user u ON u.organization_id = po.organization_id
                WHERE po.project_id = :pid AND u.id = :uid

                UNION ALL

                -- 5. Folder grant (team or org)
                SELECT
                    CASE rg.role_name
                        WHEN 'folder-editor' THEN 'project-editor'
                        WHEN 'folder-viewer' THEN 'project-viewer'
                        ELSE NULL
                    END,
                    5
                FROM customer.project p
                JOIN (
                    SELECT rg2.resource_id, r2.name AS role_name
                    FROM {settings.SCHEMA}.resource_grant rg2
                    JOIN {settings.SCHEMA}.role r2 ON r2.id = rg2.role_id
                    WHERE rg2.resource_type = 'folder'
                      AND (
                          (rg2.grantee_type = 'team' AND EXISTS (
                              SELECT 1 FROM {settings.SCHEMA}.user_team ut2
                              WHERE ut2.team_id = rg2.grantee_id AND ut2.user_id = :uid
                          ))
                          OR (rg2.grantee_type = 'organization' AND EXISTS (
                              SELECT 1 FROM {settings.SCHEMA}.user u2
                              WHERE u2.id = :uid AND u2.organization_id = rg2.grantee_id
                          ))
                      )
                ) rg ON rg.resource_id = p.folder_id
                WHERE p.id = :pid AND p.folder_id IS NOT NULL
            ) sub
            WHERE role_name IS NOT NULL
            ORDER BY priority ASC
            LIMIT 1
            """
        ),
        {"pid": str(project_id), "uid": str(user_id)},
    )
    my_role = role_result.scalars().first()

    return IProjectRead(**project.model_dump(), owned_by=owned_by, my_role=my_role)


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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    organization_id: UUID | None = Query(
        None,
        description="The ID of the organization to get the layers from",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    search: str = Query(None, description="Searches the name of the project"),
    order_by: str = Query(
        None,
        description="Specify the column name that should be used to order. You can check the Project model to see which column names exist.",
        examples=["created_at"],
    ),
    order: OrderEnum = Query(
        "descendent",
        description="Specify the order to apply. There are the option ascendent or descendent.",
        examples=["descendent"],
    ),
) -> Page[IProjectRead]:
    """Retrieve a list of projects."""

    # Resolve the user's team memberships and organization for folder-grant checks
    team_ids_result = await async_session.execute(
        select(UserTeamLink.team_id).where(UserTeamLink.user_id == user_id)
    )
    team_ids = [row[0] for row in team_ids_result.all()]
    user_obj = await async_session.get(User, user_id)
    user_organization_id = user_obj.organization_id if user_obj else None

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
        team_ids=team_ids,
        user_organization_id=user_organization_id,
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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    project_in: IProjectBaseUpdate = Body(
        ...,
        examples=[project_request_examples["update"]],
        description="Project to update",
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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
) -> InitialViewState:
    """Retrieve initial view state of a project by its ID."""

    user_projects = await crud_user_project.get_by_multi_keys(
        async_session, keys={"user_id": user_id, "project_id": project_id}
    )
    if user_projects:
        user_project = user_projects[0]
        assert type(user_project) is UserProjectLink
        return InitialViewState(**user_project.initial_view_state)

    # Shared-folder user: no personal row yet — fall back to the owner's view state.
    project = await crud_project.get(async_session, id=project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    owner_projects = await crud_user_project.get_by_multi_keys(
        async_session, keys={"user_id": project.user_id, "project_id": project_id}
    )
    if owner_projects:
        return InitialViewState(**owner_projects[0].initial_view_state)

    raise HTTPException(
        status_code=404,
        detail="Project not found or user has no access to this project",
    )


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
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    initial_view_state: InitialViewState = Body(
        ...,
        examples=[project_request_examples["initial_view_state"]],
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


@router.post(
    "/{project_id}/copy",
    response_model=IProjectRead,
    response_model_exclude_none=True,
    status_code=201,
    summary="Copy project",
    dependencies=[Depends(auth_z)],
)
async def copy_project(
    project_id: UUID4 = Path(..., description="Source project ID"),
    body: IProjectCopy = Body(default=None),
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
) -> IProjectRead:
    """Create a shallow copy of a project."""
    try:
        new_project = await copy_project_fn(
            async_session,
            project_id=project_id,
            user_id=user_id,
            target_folder_id=body.folder_id if body else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return IProjectRead.model_validate(new_project)
