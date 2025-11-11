import pytest
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.schemas.ab_routing import ABRoute, ABRoutingRequest
from goatlib.routing.schemas.base import Location, Mode

MAX_SPEEDS_KMH = {
    Mode.BUS: 120,
    Mode.TRAM: 80,
    Mode.SUBWAY: 120,
    Mode.RAIL: 400,  # Accommodates high-speed rail
}
DEFAULT_MAX_SPEED_KMH = 250


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


@pytest.fixture
def fixture_adapter(motis_fixtures_dir: str) -> MotisPlanApiAdapter:
    """Create adapter configured for fixture data."""
    return create_motis_adapter(use_fixtures=True, fixture_path=motis_fixtures_dir)


@pytest.fixture
def test_request() -> ABRoutingRequest:
    """Standard test request for fixture testing."""
    return ABRoutingRequest(
        origin=Location(lat=48.1351, lon=11.5820),  # Munich
        destination=Location(lat=48.7758, lon=9.1829),  # Stuttgart
        modes=[Mode.TRANSIT, Mode.WALK],
        max_results=3,
    )


##########################################################################
# Test Cases
##########################################################################


def test_fixture_routing_basic_success(
    fixture_adapter: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test basic fixture routing functionality."""
    response = fixture_adapter.route(test_request)
    routes = response.routes

    assert len(routes) > 0, "Should return routes from fixture data"

    # Verify fixture data structure
    validate_route_data(routes)


def test_fixture_deterministic_behavior(
    fixture_adapter: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test that fixture adapter returns consistent results."""
    response1 = fixture_adapter.route(test_request)
    response2 = fixture_adapter.route(test_request)

    # Should be deterministic due to seeded random selection
    assert len(response1.routes) == len(response2.routes)
    assert response1.routes[0].route_id == response2.routes[0].route_id


def test_fixture_different_requests_different_fixtures(
    fixture_adapter: MotisPlanApiAdapter,
) -> None:
    """Test that different requests can return different fixture files."""
    request1 = ABRoutingRequest(
        origin=Location(lat=48.1351, lon=11.5820),
        destination=Location(lat=48.7758, lon=9.1829),
        modes=[Mode.TRANSIT],
        max_results=5,
    )

    request2 = ABRoutingRequest(
        origin=Location(lat=50.0, lon=10.0),
        destination=Location(lat=51.0, lon=11.0),
        modes=[Mode.WALK],
        max_results=2,
    )

    response1 = fixture_adapter.route(request1)
    response2 = fixture_adapter.route(request2)

    assert len(response1.routes) > 0
    assert len(response2.routes) > 0
    # Routes could be different due to random fixture selection


def test_fixture_adapter_creation_with_valid_path(motis_fixtures_dir: str) -> None:
    """Test creating fixture adapter with valid path."""
    adapter = create_motis_adapter(use_fixtures=True, fixture_path=motis_fixtures_dir)

    assert isinstance(adapter, MotisPlanApiAdapter)
    assert adapter.motis_client.use_fixtures is True


def test_fixture_max_results_enforcement(fixture_adapter: MotisPlanApiAdapter) -> None:
    """Test that max_results parameter is respected with fixture data."""
    request = ABRoutingRequest(
        origin=Location(lat=48.1351, lon=11.5820),
        destination=Location(lat=48.7758, lon=9.1829),
        modes=[Mode.TRANSIT],
        max_results=2,
    )

    response = fixture_adapter.route(request)
    assert (
        len(response.routes) <= 2
    ), f"Should return at most 2 routes, got {len(response.routes)}"


def test_fixture_route_data_validation(
    fixture_adapter: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test that fixture data passes all validation checks."""
    response = fixture_adapter.route(test_request)
    routes = response.routes
    validate_route_data(routes)


def test_fixture_distance_calculation_accuracy(
    fixture_adapter: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test that transit distance calculations are reasonable."""

    response = fixture_adapter.route(test_request)
    routes = response.routes

    for route in routes:
        # Total route distance should be reasonable for real-world routes
        # Covers local routes (~500m) to long-distance routes (~1000km)
        assert (
            500 <= route.distance <= 1000000
        ), f"Route distance {route.distance}m seems unrealistic for test route"

        # Route duration should be reasonable (2 minutes to 12 hours)
        assert (
            120 <= route.duration <= 43200
        ), f"Route duration {route.duration}s seems unrealistic"

        for leg in route.legs:
            if leg.mode != Mode.WALK:
                if leg.duration > 0 and leg.distance > 0:
                    # Check leg distance is reasonable (50m to 500km)
                    assert (
                        50 <= leg.distance <= 500000
                    ), f"Leg distance {leg.distance}m seems unrealistic for {leg.mode.value} leg"

                    # Check leg duration is reasonable (30 seconds to 8 hours)
                    assert (
                        30 <= leg.duration <= 28800
                    ), f"Leg duration {leg.duration}s seems unrealistic for {leg.mode.value} leg"

                    # Check speed is reasonable for the transport mode
                    speed_kmh = (leg.distance / 1000) / (leg.duration / 3600)
                    max_speed = MAX_SPEEDS_KMH.get(leg.mode, DEFAULT_MAX_SPEED_KMH)
                    assert 5 <= speed_kmh <= max_speed, (
                        f"Leg with mode '{leg.mode.value}' has unrealistic speed: {speed_kmh:.1f} km/h. "
                        f"Expected 5-{max_speed} km/h."
                    )
