from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from core.crud.crud_folder import folder as crud_folder
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

    try:
        # Create home folder
        folder = FolderCreate(name="home", user_id=user_id)
        await crud_folder.create(
            async_session,
            obj_in=folder,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    return
