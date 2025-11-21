import pytest
import pytest_asyncio
from goatlib.routing.adapters.motis import MotisPlanApiAdapter
from goatlib.routing.schemas.ab_routing import ABRoute, ABRoutingRequest
from goatlib.routing.schemas.base import (
    DEFAULT_MAX_SPEED_KMH,
    MAX_SPEEDS_KMH,
    Location,
    Mode,
)


# --- Helper Functions ---
def validate_route_data(routes: list[ABRoute]) -> None:
    """Helper function to validate route data structure and content."""
    assert routes, "Response should contain at least one route for validation."
    for route in routes:
        assert route.duration > 0
        assert route.distance >= 0
        assert route.departure_time is not None
        assert len(route.legs) > 0

        for leg in route.legs:
            assert (
                leg.duration > 0
            ), f"Leg {leg.leg_id} has invalid duration: {leg.duration}"
            assert (
                leg.departure_time < leg.arrival_time
            ), f"Leg {leg.leg_id} has invalid timing"
            assert leg.origin is not None
            assert leg.destination is not None


@pytest_asyncio.fixture
def test_request() -> ABRoutingRequest:
    """Standard, module-scoped test request for fixture testing."""
    return ABRoutingRequest(
        origin=Location(lat=48.1351, lon=11.5820),  # Munich
        destination=Location(lat=48.7758, lon=9.1829),  # Stuttgart
        modes=[Mode.TRANSIT, Mode.WALK],
        max_results=3,
    )


# --- Test Cases ---


@pytest.mark.slow
@pytest.mark.network
async def test_fixture_routing_basic_success(
    motis_adapter_online: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test basic fixture routing functionality returns valid routes."""
    response = await motis_adapter_online.route(test_request)
    routes = response.routes

    assert len(routes) > 0, "Should return routes from fixture data"
    validate_route_data(routes)


@pytest.mark.slow
@pytest.mark.network
async def test_fixture_different_requests_return_data(
    motis_adapter_online: MotisPlanApiAdapter,
) -> None:
    """Test that different requests can successfully load different fixture files."""
    request1 = ABRoutingRequest(
        origin=Location(lat=48.1351, lon=11.5820),  # Munich
        destination=Location(lat=48.7758, lon=9.1829),  # Stuttgart
        modes=[Mode.TRANSIT, Mode.WALK],
        max_results=3,
    )
    request2 = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),  # Berlin
        destination=Location(lat=53.5511, lon=9.9937),  # Hamburg
        modes=[Mode.TRANSIT, Mode.WALK],
        max_results=3,
    )

    response1 = await motis_adapter_online.route(request1)
    response2 = await motis_adapter_online.route(request2)

    assert response1.routes, "First request should yield routes"
    assert response2.routes, "Second request should yield routes"


@pytest.mark.slow
@pytest.mark.network
async def test_fixture_max_results_enforcement(
    motis_adapter_online: MotisPlanApiAdapter,
) -> None:
    """Test that max_results parameter is respected by the client-side logic."""
    request = ABRoutingRequest(
        origin=Location(lat=48.1351, lon=11.5820),
        destination=Location(lat=48.7758, lon=9.1829),
        modes=[Mode.TRANSIT],
        max_results=5,  # Request fewer than the default
    )

    response = await motis_adapter_online.route(request)
    assert (
        len(response.routes) <= 5
    ), f"Should return at most 5 routes, got {len(response.routes)}"


@pytest.mark.slow
@pytest.mark.network
async def test_fixture_distance_calculation_and_speed_realism(
    motis_adapter_online: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test that fixture data calculations (distance, speed) are reasonable."""
    response = await motis_adapter_online.route(test_request)
    routes = response.routes

    assert routes, "Cannot perform validation on an empty route list."

    for route in routes:
        # Combined these two tests into one for clarity
        assert (
            500 <= route.distance <= 1_000_000
        ), f"Route distance {route.distance}m is unrealistic"
        assert (
            120 <= route.duration <= 43_200
        ), f"Route duration {route.duration}s is unrealistic"

        for leg in route.legs:
            if leg.mode == Mode.WALK:
                continue  # Speed checks aren't as relevant for walking

            assert (
                50 <= leg.distance <= 500_000
            ), f"Leg distance {leg.distance}m is unrealistic"
            assert (
                30 <= leg.duration <= 28_800
            ), f"Leg duration {leg.duration}s is unrealistic"

            # Avoid division by zero if duration is somehow 0
            if leg.duration > 0:
                speed_kmh = (leg.distance / 1000) / (leg.duration / 3600)
                max_speed = MAX_SPEEDS_KMH.get(leg.mode, DEFAULT_MAX_SPEED_KMH)
                assert 5 <= speed_kmh <= max_speed, (
                    f"Leg {leg.leg_id} ({leg.mode.value}) has unrealistic speed: {speed_kmh:.1f} km/h. "
                    f"Expected 5-{max_speed} km/h."
                )
