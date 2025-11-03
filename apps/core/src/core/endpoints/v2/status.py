from http import HTTPStatus

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.crud_status import status as crud_status
from core.db.models import Status
from core.deps.auth import is_superuser
from core.endpoints.deps import get_db

router = APIRouter()


@router.get(
    "",
    summary="Get the status of the service",
    response_model=Status,
    status_code=201,
)
async def get_status(
    *,
    async_session: AsyncSession = Depends(get_db),
) -> Status:
    """
    Get the status of the service.
    """

    # Get the status
    result: Status = (await crud_status.get_all(async_session))[0]

    return result


@router.put(
    "",
    summary="Update the status of the service",
    response_model=Status,
    status_code=201,
    dependencies=[Depends(is_superuser)],
)
async def update_status(
    *,
    async_session: AsyncSession = Depends(get_db),
    obj_in: Status = Body(...),
) -> Status:
    """
    Update the status of the service.
    """

    # Get the status
    status: Status = (await crud_status.get_all(async_session))[0]

    # Update the status
    result = await crud_status.update(db=async_session, db_obj=status, obj_in=obj_in)

    if type(result) is not Status:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Failed to update the status",
        )

    return result
