import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get(
        "/api/healthz",
    )

    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}
