from typing import AsyncGenerator

import pytest
import pytest_asyncio
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.schemas.ab_routing import ABRoute, ABRoutingRequest
from goatlib.routing.schemas.base import Location, Mode

# --- Constants for Validation ---
MAX_SPEEDS_KMH = {
    Mode.BUS: 120,
    Mode.TRAM: 80,
    Mode.SUBWAY: 120,
    Mode.RAIL: 400,
}
DEFAULT_MAX_SPEED_KMH = 250


# --- Helper Functions ---
def validate_route_data(routes: list[ABRoute]) -> None:
    """Helper function to validate route data structure and content."""
    for route in routes:
        # Route validation
        assert route.duration > 0
        assert route.distance >= 0
        assert route.departure_time is not None
        assert len(route.legs) > 0

        # Leg validation
        for leg in route.legs:
            assert (
                leg.duration > 0
            ), f"Leg {leg.leg_id} has invalid duration: {leg.duration}"
            assert (
                leg.departure_time < leg.arrival_time
            ), f"Leg {leg.leg_id} has invalid timing"
            assert leg.origin is not None
            assert leg.destination is not None


# --- Fixtures ---


# CHANGE 1: Use pytest_asyncio.fixture with function scope for async compatibility.
# The adapter is just reading local files, but needs to match event loop scope.
@pytest_asyncio.fixture
async def fixture_adapter(
    motis_fixtures_dir: str,
) -> AsyncGenerator[MotisPlanApiAdapter, None]:
    """Module-scoped adapter configured for fixture data, with proper cleanup."""
    adapter = create_motis_adapter(use_fixtures=True, fixture_path=motis_fixtures_dir)
    yield adapter
    # Even if the fixture client doesn't need it, this is robust future-proofing.
    if hasattr(adapter.motis_client, "close"):
        await adapter.motis_client.close()


# CHANGE 2: Scope the request to "function" to match async fixture scope.
@pytest.fixture
def test_request() -> ABRoutingRequest:
    """Standard, module-scoped test request for fixture testing."""
    return ABRoutingRequest(
        origin=Location(lat=48.1351, lon=11.5820),  # Munich
        destination=Location(lat=48.7758, lon=9.1829),  # Stuttgart
        modes=[Mode.TRANSIT, Mode.WALK],
        max_results=3,
    )


# --- Test Cases ---

# CHANGE 3: All tests calling `adapter.route` are now `async` and use `await`.


async def test_fixture_routing_basic_success(
    fixture_adapter: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test basic fixture routing functionality returns valid routes."""
    response = await fixture_adapter.route(test_request)
    routes = response.routes

    assert routes, "Should return routes from fixture data"
    validate_route_data(routes)


# This test is synchronous and tests a factory function; it remains unchanged.
def test_fixture_adapter_creation_with_valid_path(motis_fixtures_dir: str) -> None:
    """Test creating fixture adapter with valid path."""
    adapter = create_motis_adapter(use_fixtures=True, fixture_path=motis_fixtures_dir)
    assert isinstance(adapter, MotisPlanApiAdapter)
    assert adapter.motis_client.use_fixtures is True


# CHANGE 4: Combined realism checks into a single, more comprehensive test.
async def test_fixture_route_realism_validation(
    fixture_adapter: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test that fixture data calculations (distance, speed) are reasonable."""
    response = await fixture_adapter.route(test_request)
    routes = response.routes
    assert routes, "Cannot perform validation on an empty route list."

    for route in routes:
        assert (
            500 <= route.distance <= 1_000_000
        ), f"Route distance {route.distance}m is unrealistic"
        assert (
            120 <= route.duration <= 43_200
        ), f"Route duration {route.duration}s is unrealistic"

        for leg in route.legs:
            if leg.mode == Mode.WALK:
                continue

            # Speed checks are only meaningful if duration is positive
            if leg.duration > 0:
                speed_kmh = (leg.distance / 1000) / (leg.duration / 3600)
                max_speed = MAX_SPEEDS_KMH.get(leg.mode, DEFAULT_MAX_SPEED_KMH)
                assert (
                    5 <= speed_kmh <= max_speed
                ), f"Leg {leg.leg_id} ({leg.mode.value}) has unrealistic speed: {speed_kmh:.1f} km/h."
