from uuid import uuid4

from core.core.config import settings
from httpx import AsyncClient


async def get_with_wrong_id(client: AsyncClient, item: str):
    """Get item with wrong ID."""

    id = uuid4()
    response = await client.get(
        f"{settings.API_V2_STR}/{item}/{str(id)}",
    )
    assert response.status_code == 404
