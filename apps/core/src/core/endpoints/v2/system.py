
from fastapi import APIRouter, Body, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.crud_system_setting import system_setting as crud_system_setting
from core.deps.auth import auth_z
from core.endpoints.deps import get_db, get_user_id
from core.schemas.system_setting import (
    SystemSettingsCreate,
    SystemSettingsRead,
    SystemSettingsUpdate,
    default_system_settings,
)
from core.schemas.system_setting import (
    request_examples as system_settings_request_examples,
)

router = APIRouter()


@router.get(
    "/settings",
    summary="Retrieve system settings",
    response_model=SystemSettingsRead,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_system_settings(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
) -> SystemSettingsRead:
    """Retrieve system settings"""

    existing_settings = await crud_system_setting.get_by_multi_keys(
        async_session, keys={"user_id": user_id}
    )

    if not existing_settings or len(existing_settings) == 0:
        default_system_settings_obj_in = SystemSettingsCreate(
            **default_system_settings.model_dump()
        )
        default_system_settings_obj_in.user_id = user_id

        return SystemSettingsRead(
            **(
                await crud_system_setting.create(
                    async_session, obj_in=default_system_settings_obj_in
                )
            ).model_dump()
        )

    return SystemSettingsRead(**existing_settings[0].model_dump())


@router.put(
    "/settings",
    summary="Update system settings",
    response_model=SystemSettingsRead,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_system_settings(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    system_settings_in: SystemSettingsUpdate = Body(
        ..., example=system_settings_request_examples["update"]
    ),
) -> SystemSettingsRead:
    """Update system settings"""

    existing_settings = await crud_system_setting.get_by_multi_keys(
        async_session, keys={"user_id": user_id}
    )

    if not existing_settings or len(existing_settings) == 0:
        new_system_settings = SystemSettingsCreate(**system_settings_in.dict())
        new_system_settings.user_id = user_id

        return SystemSettingsRead(
            **(
                await crud_system_setting.create(
                    async_session, obj_in=new_system_settings
                )
            ).model_dump()
        )

    return SystemSettingsRead(
        **(
            await crud_system_setting.update(
                async_session, db_obj=existing_settings[0], obj_in=system_settings_in
            )
        ).model_dump()
    )
