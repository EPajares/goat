from typing import List, Optional
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
from pydantic import UUID4
from sqlalchemy import and_, func, or_, select
from sqlalchemy import delete as sql_delete

from core.core.config import settings
from core.core.content import create_query_accessible_folders
from core.crud.crud_folder import folder as crud_folder
from core.db.models._link_model import ResourceGrant, UserTeamLink
from core.db.models.folder import Folder
from core.db.models.organization import Organization
from core.db.models.role import Role
from core.db.models.team import Team
from core.db.models.user import User
from core.db.session import AsyncSession
from core.deps.auth import auth, auth_z
from core.endpoints.deps import ensure_home_folder, get_db, get_user_id
from core.schemas.common import OrderEnum
from core.schemas.folder import (
    FolderCreate,
    FolderGrantResponse,
    FolderGrantsResponse,
    FolderRead,
    FolderShareCreate,
    FolderUpdate,
)
from core.schemas.folder import (
    request_examples as folder_request_examples,
)

router = APIRouter()


### Folder endpoints
@router.post(
    "",
    summary="Create a new folder",
    response_model=FolderRead,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def create_folder(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    folder_in: FolderCreate = Body(..., examples=[folder_request_examples["create"]]),
) -> FolderRead:
    """Create a new folder."""
    # Count already existing folders for the user
    folder_cnt = (
        await async_session.execute(
            select(func.count(Folder.id)).filter(Folder.user_id == user_id)
        )
    ).scalar()

    if folder_cnt is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch folder count",
        )

    # Check if the user has already reached the maximum number of folders
    if folder_cnt >= settings.MAX_FOLDER_COUNT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"The maximum number of folders ({settings.MAX_FOLDER_COUNT}) has been reached.",
        )

    folder_in.user_id = user_id
    folder = FolderRead(
        **(await crud_folder.create(async_session, obj_in=folder_in)).model_dump()
    )
    return folder


@router.get(
    "/{folder_id}",
    summary="Retrieve a folder by its ID",
    response_model=FolderRead,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_folder(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    folder_id: UUID4 = Path(
        ...,
        description="The ID of the folder to get",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
) -> FolderRead:
    """Retrieve a folder by its ID."""
    folder = await crud_folder.get_by_multi_keys(
        async_session, keys={"id": folder_id, "user_id": user_id}
    )

    if len(folder) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    return FolderRead(**folder[0].model_dump())


@router.get(
    "",
    summary="Retrieve a list of folders",
    response_model=List[FolderRead],
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z), Depends(ensure_home_folder)],
)
async def read_folders(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    search: str = Query(None, description="Searches the name of the folder"),
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
) -> List[FolderRead]:
    """Retrieve a list of owned and shared folders."""
    # Fetch user's team memberships
    team_ids_result = await async_session.execute(
        select(UserTeamLink.team_id).where(UserTeamLink.user_id == user_id)
    )
    team_ids = [row[0] for row in team_ids_result.all()]

    # Fetch user's organization_id
    user_obj = await async_session.get(User, user_id)
    organization_id: Optional[UUID] = user_obj.organization_id if user_obj else None

    # Build the UNION query of accessible folder IDs
    accessible_cte = create_query_accessible_folders(
        user_id=user_id,
        team_ids=team_ids,
        organization_id=organization_id,
    ).cte("accessible_folders")

    # Load full Folder objects for accessible IDs
    folders_query = select(Folder).join(
        accessible_cte, Folder.id == accessible_cte.c.id
    )

    if search:
        folders_query = folders_query.where(Folder.name.ilike(f"%{search}%"))

    result = await async_session.execute(folders_query)
    folders = result.scalars().all()

    owned_ids = [f.id for f in folders if f.user_id == user_id]
    shared_ids = [f.id for f in folders if f.user_id != user_id]

    # Batch: owned-folder grantee_ids (one query for all owned folders)
    owned_grants: dict[UUID, list[UUID]] = {}
    if owned_ids:
        rows = (
            await async_session.execute(
                select(ResourceGrant.resource_id, ResourceGrant.grantee_id).where(
                    ResourceGrant.resource_type == "folder",
                    ResourceGrant.resource_id.in_(owned_ids),
                )
            )
        ).all()
        for resource_id, grantee_id in rows:
            owned_grants.setdefault(resource_id, []).append(grantee_id)

    # Batch: shared-folder grants + roles (one query for all shared folders)
    shared_grant_map: dict[UUID, tuple[ResourceGrant, Role]] = {}
    if shared_ids:
        conditions = []
        if team_ids:
            conditions.append(
                and_(
                    ResourceGrant.grantee_type == "team",
                    ResourceGrant.grantee_id.in_(team_ids),
                )
            )
        if organization_id:
            conditions.append(
                and_(
                    ResourceGrant.grantee_type == "organization",
                    ResourceGrant.grantee_id == organization_id,
                )
            )
        if conditions:
            grant_rows = (
                await async_session.execute(
                    select(ResourceGrant, Role)
                    .join(Role, Role.id == ResourceGrant.role_id)
                    .where(
                        ResourceGrant.resource_type == "folder",
                        ResourceGrant.resource_id.in_(shared_ids),
                        or_(*conditions),
                    )
                )
            ).all()
            for grant, role in grant_rows:
                if grant.resource_id not in shared_grant_map:
                    shared_grant_map[grant.resource_id] = (grant, role)

    # Batch: team / org display names (one query each, only if needed)
    team_ids_needed = {
        g.grantee_id for g, _ in shared_grant_map.values() if g.grantee_type == "team"
    }
    org_ids_needed = {
        g.grantee_id
        for g, _ in shared_grant_map.values()
        if g.grantee_type == "organization"
    }

    teams_by_id: dict[UUID, str] = {}
    if team_ids_needed:
        team_rows = (
            (
                await async_session.execute(
                    select(Team).where(Team.id.in_(team_ids_needed))
                )
            )
            .scalars()
            .all()
        )
        teams_by_id = {t.id: t.name for t in team_rows}

    orgs_by_id: dict[UUID, str] = {}
    if org_ids_needed:
        org_rows = (
            (
                await async_session.execute(
                    select(Organization).where(Organization.id.in_(org_ids_needed))
                )
            )
            .scalars()
            .all()
        )
        orgs_by_id = {o.id: o.name for o in org_rows}

    # Assemble response
    folder_reads: List[FolderRead] = []
    for f in folders:
        if f.user_id == user_id:
            shared_with_ids = owned_grants.get(f.id) or None
            folder_reads.append(
                FolderRead(
                    **f.model_dump(),
                    is_owned=True,
                    role="folder-owner",
                    shared_from_name=None,
                    shared_with_ids=shared_with_ids,
                )
            )
        else:
            entry = shared_grant_map.get(f.id)
            if entry:
                grant, role = entry
                name = (
                    teams_by_id.get(grant.grantee_id)
                    or orgs_by_id.get(grant.grantee_id)
                    or str(grant.grantee_id)
                )
            else:
                role, name = None, None  # type: ignore[assignment]
            folder_reads.append(
                FolderRead(
                    **f.model_dump(),
                    is_owned=False,
                    role=role.name if role else None,
                    shared_from_name=name,
                )
            )

    return folder_reads


@router.put(
    "/{folder_id}",
    summary="Update a folder with new data",
    response_model=FolderUpdate,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_folder(
    *,
    async_session: AsyncSession = Depends(get_db),
    folder_id: UUID4 = Path(
        ...,
        description="The ID of the folder to update",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    user_id: UUID4 = Depends(get_user_id),
    folder_in: FolderUpdate = Body(..., examples=[folder_request_examples["update"]]),
) -> FolderUpdate:
    """Update a folder with new data."""
    db_obj = await crud_folder.get_by_multi_keys(
        async_session, keys={"id": folder_id, "user_id": user_id}
    )

    if len(db_obj) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )

    folder = await crud_folder.update(async_session, db_obj=db_obj[0], obj_in=folder_in)
    return FolderUpdate(name=folder.name)


@router.delete(
    "/{folder_id}",
    summary="Delete a folder and all its contents",
    response_model=None,
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_folder(
    *,
    async_session: AsyncSession = Depends(get_db),
    folder_id: UUID4 = Path(
        ...,
        description="The ID of the folder to delete",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
    user_id: UUID4 = Depends(get_user_id),
    access_token: str = Depends(auth),
) -> None:
    """Delete a folder and all its contents"""

    await crud_folder.delete(
        async_session,
        id=folder_id,
        user_id=user_id,
        access_token=access_token,
    )
    return


### Folder sharing endpoints


@router.post(
    "/{folder_id}/share",
    summary="Share a folder with a team or organization",
    response_model=FolderGrantsResponse,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def share_folder(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    folder_id: UUID4 = Path(..., description="The folder to share"),
    payload: FolderShareCreate = Body(...),
) -> FolderGrantsResponse:
    """Share a folder with a team or organization. Only the folder owner can call this."""
    folder = await async_session.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    if folder.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the folder owner can share it",
        )

    role_result = await async_session.execute(
        select(Role).where(Role.name == payload.role)
    )
    role = role_result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role: {payload.role}",
        )

    # Check for conflicting grant (different grantee)
    conflict_result = await async_session.execute(
        select(ResourceGrant.id)
        .where(
            ResourceGrant.resource_type == "folder",
            ResourceGrant.resource_id == folder_id,
            or_(
                ResourceGrant.grantee_type != payload.grantee_type,
                ResourceGrant.grantee_id != payload.grantee_id,
            ),
        )
        .limit(1)
    )
    if conflict_result.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This folder is already shared with another team or organization. Remove the existing grant first.",
        )

    # Upsert: delete existing grant for this grantee, then insert fresh
    await async_session.execute(
        sql_delete(ResourceGrant).where(
            and_(
                ResourceGrant.resource_type == "folder",
                ResourceGrant.resource_id == folder_id,
                ResourceGrant.grantee_type == payload.grantee_type,
                ResourceGrant.grantee_id == payload.grantee_id,
            )
        )
    )
    grant = ResourceGrant(
        resource_type="folder",
        resource_id=folder_id,
        grantee_type=payload.grantee_type,
        grantee_id=payload.grantee_id,
        role_id=role.id,
        granted_by=user_id,
    )
    async_session.add(grant)
    await async_session.commit()

    return await _get_folder_grants_response(async_session, folder_id)


@router.get(
    "/{folder_id}/share",
    summary="List current grants for a folder",
    response_model=FolderGrantsResponse,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def get_folder_grants(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    folder_id: UUID4 = Path(..., description="The folder whose grants to list"),
) -> FolderGrantsResponse:
    """List current grants for a folder. Only the folder owner can call this."""
    folder = await async_session.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    if folder.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the folder owner can view grants",
        )

    return await _get_folder_grants_response(async_session, folder_id)


@router.delete(
    "/{folder_id}/share/{grantee_type}/{grantee_id}",
    summary="Remove a grant from a folder",
    response_model=None,
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_folder_grant(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    folder_id: UUID4 = Path(..., description="The folder"),
    grantee_type: str = Path(..., description="team or organization"),
    grantee_id: UUID4 = Path(..., description="The team or organization ID"),
) -> None:
    """Remove a specific grant from a folder. Only the folder owner can call this."""
    folder = await async_session.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    if folder.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the folder owner can remove grants",
        )

    result = await async_session.execute(
        sql_delete(ResourceGrant).where(
            and_(
                ResourceGrant.resource_type == "folder",
                ResourceGrant.resource_id == folder_id,
                ResourceGrant.grantee_type == grantee_type,
                ResourceGrant.grantee_id == grantee_id,
            )
        )
    )
    await async_session.commit()
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found"
        )


### Helpers


async def _get_folder_grants_response(
    async_session: AsyncSession,
    folder_id: UUID,
) -> FolderGrantsResponse:
    """Fetch all grants for a folder, enriched with grantee display names."""
    grants_result = await async_session.execute(
        select(ResourceGrant, Role)
        .join(Role, Role.id == ResourceGrant.role_id)
        .where(
            ResourceGrant.resource_type == "folder",
            ResourceGrant.resource_id == folder_id,
        )
    )
    rows = grants_result.all()

    enriched: list[FolderGrantResponse] = []
    for grant, role in rows:
        name = str(grant.grantee_id)  # fallback
        if grant.grantee_type == "team":
            team = await async_session.get(Team, grant.grantee_id)
            if team:
                name = team.name
        elif grant.grantee_type == "organization":
            org = await async_session.get(Organization, grant.grantee_id)
            if org:
                name = org.name
        enriched.append(
            FolderGrantResponse(
                grantee_type=grant.grantee_type,
                grantee_id=grant.grantee_id,
                grantee_name=name,
                role=role.name,
            )
        )
    return FolderGrantsResponse(grants=enriched)


async def _resolve_folder_role(
    async_session: AsyncSession,
    folder_id: UUID,
    team_ids: list[UUID],
    organization_id: Optional[UUID],
) -> tuple[Optional[str], Optional[str]]:
    """Resolve the effective role and grantee name for a shared folder."""
    conditions = []
    if team_ids:
        conditions.append(
            and_(
                ResourceGrant.grantee_type == "team",
                ResourceGrant.grantee_id.in_(team_ids),
            )
        )
    if organization_id:
        conditions.append(
            and_(
                ResourceGrant.grantee_type == "organization",
                ResourceGrant.grantee_id == organization_id,
            )
        )
    if not conditions:
        return None, None

    result = await async_session.execute(
        select(ResourceGrant, Role)
        .join(Role, Role.id == ResourceGrant.role_id)
        .where(
            ResourceGrant.resource_type == "folder",
            ResourceGrant.resource_id == folder_id,
            or_(*conditions),
        )
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None, None

    grant, role = row
    name = str(grant.grantee_id)
    if grant.grantee_type == "team":
        team = await async_session.get(Team, grant.grantee_id)
        if team:
            name = team.name
    elif grant.grantee_type == "organization":
        org = await async_session.get(Organization, grant.grantee_id)
        if org:
            name = org.name

    return role.name, name
