# Standard library imports
import asyncio
from typing import AsyncGenerator, Generator

# Third party imports
import pytest_asyncio
from httpx import AsyncClient
from routing.core.config import settings  # noqa: F401

# Local application imports
from routing.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Correct, 4‑space indentation inside the function only
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """pytest‑asyncio event loop fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
