import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.params import Query
from fastapi_pagination import Page
from fastapi_pagination import Params as PaginationParams
from keycloak.exceptions import KeycloakError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.crud.crud_invitation import invitation as crud_invitation
from core.crud.crud_organization import organization as crud_organization
from core.crud.crud_role import role as crud_role
from core.crud.crud_user import user as crud_user
from core.db.models._link_model import UserRoleLink
from core.db.models.invitation import Invitation, InvitationStatusEnum, InvitationType
from core.db.models.organization import Organization
from core.deps.auth import auth, auth_z, user_token
from core.deps.keycloak import get_keycloak_user, keycloak_admin
from core.endpoints.deps import get_db
from core.schemas.common import OrderEnum
from core.schemas.user import UserProfileUpdate, UserRead, UserUpdate, request_examples
from core.services.s3 import s3_service
from core.utils.other import decode_base64_file, get_image_extension_from_base64

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/organization",
    summary="Get user organization",
    response_model=Organization,
)
async def get_organization(
    *,
    db: AsyncSession = Depends(get_db),
    user_token: dict = Depends(user_token),
    user_id: str | None = None,
) -> Any:
    """
    Get an organization
    """
    user_id = user_id or user_token["sub"]
    user = await crud_user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    organization_id = user.organization_id
    organization = await crud_organization.get(db=db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no organization",
        )
    return organization


@router.patch(
    "/invitations/{invitation_id}",
    summary="Accept invitation",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def accept_invitation(
    *,
    db: AsyncSession = Depends(get_db),
    user_token: dict = Depends(user_token),
    token: str = Depends(auth),
    invitation_id: str,
) -> None:
    invitation = await crud_invitation.get(db=db, id=invitation_id)
    if (
        not invitation
        or invitation.status != InvitationStatusEnum.pending
        # Case-insensitive: legacy invitations may store the email as typed,
        # while Keycloak lowercases the token's email claim.
        or invitation.payload["user_email"].lower()
        != (user_token.get("email") or "").lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.type == InvitationType.organization:
        user_id = user_token["sub"]
        organization_id = invitation.payload["organization_id"]
        role = invitation.payload["role"]
        user = await crud_user.create_if_not_exists(user_id=user_id, db_session=db)
        organization_obj = await crud_organization.get(db=db, id=organization_id)
        user.organization = organization_obj
        # Add Roles to the user as organization owner
        role = await crud_role.get_by_key(db=db, key="name", value=role)
        role = role[0]
        user_role = UserRoleLink(role=role, user=user)
        db.add(user_role)
        await db.commit()

    await crud_invitation.update(
        db=db,
        db_obj=invitation,
        obj_in={
            "status": InvitationStatusEnum.accepted,
        },
    )


@router.delete(
    "/invitations/{invitation_id}",
    summary="Decline invitation",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def decline_invitation(
    *,
    db: AsyncSession = Depends(get_db),
    user_token: dict = Depends(user_token),
    invitation_id: str,
) -> None:
    """
    Decline invitation
    """
    invitation = await crud_invitation.get(db=db, id=invitation_id)
    if (
        not invitation
        or invitation.status != InvitationStatusEnum.pending
        # Case-insensitive: legacy invitations may store the email as typed,
        # while Keycloak lowercases the token's email claim.
        or invitation.payload["user_email"].lower()
        != (user_token.get("email") or "").lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    await crud_invitation.delete(db=db, id=invitation_id)


@router.get(
    "/invitations",
    summary="Get invitations for the user",
    response_model=Page[Invitation],
)
async def get_invitations(
    *,
    db: AsyncSession = Depends(get_db),
    status: InvitationStatusEnum = InvitationStatusEnum.pending,
    type: InvitationType = None,
    invitation_id: str = Query(None, description="Query by invitation by id"),
    user_token: dict = Depends(user_token),
    page_params: PaginationParams = Depends(),
    search: str = None,
    order_by: str = None,
    order: OrderEnum = None,
) -> Any:
    """
    Get invitations
    """

    # Invitations are keyed by email (they can target users without an account
    # yet); the token's email claim is also what accept/decline validate against.
    # Case-insensitive: legacy invitations may store the email as typed.
    email = (user_token.get("email") or "").lower()
    query = select(crud_invitation.model)
    query = query.where(
        func.lower(crud_invitation.model.payload["user_email"].astext) == email,
    )

    if invitation_id:
        query = query.where(crud_invitation.model.id == invitation_id)

    if type:
        query = query.where(crud_invitation.model.type == type)

    if status:
        query = query.where(crud_invitation.model.status == status)

    invitations = await crud_invitation.get_multi(
        db=db,
        page_params=page_params,
        query=query,
        order_by=order_by,
        order=order,
    )
    return invitations


@router.get(
    "/profile",
    summary="Get user profile",
    response_model=UserRead,
    dependencies=[Depends(auth_z)],
)
async def get_profile(
    *,
    db: AsyncSession = Depends(get_db),
    user_token: dict = Depends(user_token),
    user_id: str | None = None,
) -> Any:
    """
    Get user profile
    """
    user_id = user_id or user_token["sub"]
    db_user = await crud_user.get_user_with_roles(db_session=db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    keycloak_user = await get_keycloak_user(user_id)

    roles = []
    for role_link in db_user.role_links:
        roles.append(role_link.role.name)

    user = UserRead(
        **db_user.model_dump(),
        enabled=keycloak_user.get("enabled"),
        topt=keycloak_user.get("totp"),
        roles=roles,
    )
    return user


@router.patch(
    "/profile",
    summary="Update user profile",
    response_model=UserProfileUpdate,
    dependencies=[Depends(auth_z)],
)
async def update_profile(
    *,
    db: AsyncSession = Depends(get_db),
    user: UserProfileUpdate = Body(..., examples=[request_examples["user"]["update"]]),
    user_token: dict = Depends(user_token),
    user_id: str | None = None,
) -> Any:
    """
    Update user profile
    """
    user_id = user_id or user_token["sub"]
    db_user = await crud_user.get(db=db, id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    admin = await keycloak_admin()
    if admin:
        keycloak_payload = {}
        if user.firstname:
            keycloak_payload["firstName"] = user.firstname
        if user.lastname:
            keycloak_payload["lastName"] = user.lastname
        if user.email and user.email != db_user.email:
            keycloak_payload["email"] = user.email
            keycloak_payload["emailVerified"] = False
        # Only touch Keycloak when a Keycloak-managed field actually changed, so
        # avatar-only edits never depend on the service account's write access.
        # A failed write (e.g. the service account lacks manage-users) surfaces
        # as a clean error and stops the request before the DB is updated, so
        # name/email never desync from the identity provider.
        if keycloak_payload:
            try:
                admin.update_user(
                    user_id=user_id,
                    payload=keycloak_payload,
                )
            except KeycloakError:
                logger.warning(
                    "keycloak profile write failed for %s", user_id, exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Name and email can't be updated right now. Other profile changes are unaffected.",
                )
    if user.avatar and user.avatar.startswith("data:image"):
        extension = get_image_extension_from_base64(user.avatar)
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d%H%M%S")
        file_name = f"avatar_{user_id}_T{timestamp_str}.{extension}"
        file = decode_base64_file(user.avatar)
        s3_service.upload_asset(
            file,
            f"img/users/{settings.ENVIRONMENT}/{file_name}",
            f"image/{extension}",
        )
        user.avatar = f"https://assets.plan4better.de/img/users/{settings.ENVIRONMENT}/{file_name}"
    user_update = UserUpdate(
        **user.model_dump(exclude_unset=True, exclude_none=True),
    )
    updated_user = await crud_user.update(db=db, db_obj=db_user, obj_in=user_update)

    return updated_user


@router.delete(
    "",
    summary="Delete user account",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_z)],
)
async def delete_account(
    *,
    db: AsyncSession = Depends(get_db),
    user_token: dict = Depends(user_token),
    user_id: str | None = None,
) -> None:
    user_id = user_id or user_token["sub"]
    admin = await keycloak_admin()
    if admin:
        admin.delete_user(user_id)
