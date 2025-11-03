from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from core.crud.crud_folder import folder as crud_folder
from core.crud.crud_user import user as crud_user
from core.db.models.user import User
from core.db.session import AsyncSession
from core.deps.auth import auth_z
from core.endpoints.deps import get_db, get_user_id
from core.schemas.folder import FolderCreate

router = APIRouter()


@router.post(
    "/data-schema",
    response_model=None,
    summary="Create data base schemas for the user.",
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def create_user_base_data(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
) -> None:
    """Create a user. This will read the user ID from the JWT token or use the pre-defined user_id if running without authentication."""

    # Create user tables
    await crud_user.create_user_data_tables(async_session, user_id=user_id)
    try:
        # Create home folder
        folder = FolderCreate(name="home", user_id=user_id)
        await crud_folder.create(
            async_session,
            obj_in=folder,
        )
    except Exception as e:
        await crud_user.delete_user_data_tables(async_session, user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    return


@router.delete(
    "/data-schema",
    response_model=None,
    summary="Delete all user related related contents.",
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_user(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
) -> None:
    """Delete a user and all of the related contents. This will read the user ID from the JWT token or use the pre-defined user_id if running without authentication."""
    user = await crud_user.get(async_session, id=user_id)
    assert isinstance(user, User)

    if user:
        await crud_user.delete_user_data_tables(async_session, user_id=user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return
