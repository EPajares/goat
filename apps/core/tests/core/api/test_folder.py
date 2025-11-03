import pytest
from core.core.config import settings
from httpx import AsyncClient
from tests.utils import get_with_wrong_id


@pytest.mark.asyncio
async def test_create_folder(client: AsyncClient, fixture_create_folder):
    assert fixture_create_folder["id"] is not None


@pytest.mark.asyncio
async def test_created_exceed_folders(
    client: AsyncClient, fixture_create_exceed_folders
):
    return


@pytest.mark.asyncio
async def test_get_folder(
    client: AsyncClient,
    fixture_create_folder,
):
    response = await client.get(
        f"{settings.API_V2_STR}/folder/{fixture_create_folder['id']}",
    )
    assert response.status_code == 200
    assert response.json()["id"] == fixture_create_folder["id"]


@pytest.mark.asyncio
async def test_get_folder_wrong_id(client: AsyncClient, fixture_create_folder):
    await get_with_wrong_id(client, "folder")


@pytest.mark.asyncio
async def test_get_folders(
    client: AsyncClient,
    fixture_create_folders,
):
    response = await client.get(
        f"{settings.API_V2_STR}/folder?order_by=created_at&order=descendent&search=test",
    )
    assert response.status_code == 200
    assert len(response.json()) == len(fixture_create_folders)


@pytest.mark.asyncio
async def test_update_folder(client: AsyncClient, fixture_create_folder):
    response = await client.put(
        f"{settings.API_V2_STR}/folder/{fixture_create_folder['id']}",
        json={"name": "test2"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "test2"


@pytest.mark.asyncio
async def test_delete_folder(
    client: AsyncClient,
    fixture_create_folder,
):
    response = await client.delete(
        f"{settings.API_V2_STR}/folder/{fixture_create_folder['id']}",
    )
    assert response.status_code == 204

    # Check if folder is deleted
    response = await client.get(
        f"{settings.API_V2_STR}/folder/{fixture_create_folder['id']}",
    )
    assert response.status_code == 404
