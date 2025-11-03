import pytest
from core.core.config import settings
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_data_schema(client: AsyncClient, fixture_create_user):
    assert fixture_create_user is not None


@pytest.mark.asyncio
async def test_delete_user_data_schema(
    client: AsyncClient,
    fixture_create_user,
):
    response = await client.delete(
        f"{settings.API_V2_STR}/user/data-schema",
    )
    assert response.status_code == 204
