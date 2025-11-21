from typing import AsyncGenerator

import pytest_asyncio
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.schemas.catchment_area_transit import (
    AccessEgressMode,
    TransitCatchmentAreaRequest,
    TransitCatchmentAreaStartingPoints,
    TransitCatchmentAreaTravelTimeCost,
    TransitMode,
)


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


# Common test data fixtures for one-to-all testing
@pytest_asyncio.fixture
def berlin_request() -> TransitCatchmentAreaRequest:
    """Create a standard Berlin transit catchment area request."""
    return TransitCatchmentAreaRequest(
        starting_points=TransitCatchmentAreaStartingPoints(
            latitude=[52.5200],  # Berlin center
            longitude=[13.4050],
        ),
        transit_modes=[TransitMode.bus, TransitMode.tram, TransitMode.subway],
        access_mode=AccessEgressMode.walk,
        egress_mode=AccessEgressMode.walk,
        travel_cost=TransitCatchmentAreaTravelTimeCost(
            max_traveltime=30,
            cutoffs=[15, 30],  # 15 and 30 minute isochrones
        ),
    )


@pytest_asyncio.fixture
def munich_request() -> TransitCatchmentAreaRequest:
    """Create a Munich transit catchment area request for testing."""
    return TransitCatchmentAreaRequest(
        starting_points=TransitCatchmentAreaStartingPoints(
            latitude=[48.1351],  # Munich center
            longitude=[11.5820],
        ),
        transit_modes=[TransitMode.rail, TransitMode.subway, TransitMode.tram],
        access_mode=AccessEgressMode.walk,
        egress_mode=AccessEgressMode.walk,
        travel_cost=TransitCatchmentAreaTravelTimeCost(
            max_traveltime=45,
            cutoffs=[15, 30, 45],  # Three isochrone bands
        ),
    )


@pytest_asyncio.fixture
def simple_berlin_request() -> TransitCatchmentAreaRequest:
    """Create a simple Berlin request for minimal testing."""
    return TransitCatchmentAreaRequest(
        starting_points=TransitCatchmentAreaStartingPoints(
            latitude=[52.5200],  # Berlin
            longitude=[13.4050],
        ),
        transit_modes=[TransitMode.subway],
        access_mode=AccessEgressMode.walk,
        egress_mode=AccessEgressMode.walk,
        travel_cost=TransitCatchmentAreaTravelTimeCost(max_traveltime=15, cutoffs=[15]),
    )
