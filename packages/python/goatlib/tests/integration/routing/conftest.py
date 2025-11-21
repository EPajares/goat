from typing import AsyncGenerator

import pytest_asyncio
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter


@pytest_asyncio.fixture
async def motis_adapter_online() -> AsyncGenerator[MotisPlanApiAdapter, None]:
    """
    MOTIS adapter for online integration testing.

    This adapter:
    - Makes real HTTP requests to api.transitous.org
    - Should be used for tests that need real API validation
    """
    adapter = create_motis_adapter(use_fixtures=False)
    yield adapter
    await adapter.motis_client.close()


@pytest_asyncio.fixture
async def motis_adapter_fixture(
    motis_fixtures_dir: str,
) -> AsyncGenerator[MotisPlanApiAdapter, None]:
    """
    MOTIS adapter for fixture-based testing using local test data.

    This adapter:
    - Uses local fixture files (no network requests)
    - Very fast execution
    - Deterministic results
    """
    adapter = create_motis_adapter(use_fixtures=True, fixture_path=motis_fixtures_dir)
    yield adapter
    if hasattr(adapter.motis_client, "close"):
        await adapter.motis_client.close()
