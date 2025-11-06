from datetime import datetime, timezone

import pytest
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.schemas.ab_routing import ABRoutingRequest
from goatlib.routing.schemas.base import Location, TransportMode

from .test_motis_adapter_fixture import validate_route_data

"""Test the MOTIS adapter with real online APIs."""


@pytest.fixture
def online_adapter() -> MotisPlanApiAdapter:
    """Create adapter configured for online API."""
    return create_motis_adapter(use_fixtures=False)


@pytest.fixture
def berlin_hamburg_request() -> ABRoutingRequest:
    """Standard Berlin to Hamburg routing request."""
    return ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),  # Berlin
        destination=Location(lat=53.5511, lon=9.9937),  # Hamburg
        modes=[TransportMode.TRANSIT, TransportMode.WALK],
        max_results=3,
    )


##############################################################################
# Online Routing Tests
##############################################################################


def test_online_routing_basic_success(
    online_adapter: MotisPlanApiAdapter, berlin_hamburg_request: ABRoutingRequest
) -> None:
    """Test basic online routing functionality."""
    response = online_adapter.route(berlin_hamburg_request)
    routes = response.routes
    assert len(routes) > 0, "Should return at least one route"
    # Note: Some APIs may not respect max_results exactly, so we allow flexibility
    assert len(routes) <= 50, "Should return a reasonable number of routes"

    # Verify route structure
    first_route = routes[0]
    assert first_route.route_id.startswith("motis_route_")
    assert first_route.duration > 0
    assert first_route.distance > 0
    assert len(first_route.legs) > 0

    # Verify legs have proper structure
    for leg in first_route.legs:
        assert leg.duration > 0, "All legs should have positive duration"
        assert (
            leg.departure_time < leg.arrival_time
        ), "Arrival should be after departure"
        assert leg.mode in TransportMode, "Mode should be valid TransportMode"


def test_online_routing_different_modes(online_adapter: MotisPlanApiAdapter) -> None:
    """Test routing with different transport modes."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),  # Berlin
        destination=Location(lat=52.5244, lon=13.4105),  # Short distance in Berlin
        modes=[TransportMode.WALK],  # Walking only
        max_results=1,
    )

    response = online_adapter.route(request)
    routes = response.routes
    assert len(routes) > 0

    # Should have walking legs
    walk_legs = [leg for leg in routes[0].legs if leg.mode == TransportMode.WALK]
    assert len(walk_legs) > 0, "Should contain walking legs"


def test_online_routing_with_time_parameter(
    online_adapter: MotisPlanApiAdapter,
) -> None:
    """Test routing with specific departure time."""
    future_time = datetime.now(timezone.utc).replace(
        hour=8, minute=0, second=0, microsecond=0
    )

    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),  # Berlin
        destination=Location(lat=53.5511, lon=9.9937),  # Hamburg
        modes=[TransportMode.TRANSIT, TransportMode.WALK],
        time=future_time,
        max_results=2,
    )

    response = online_adapter.route(request)
    routes = response.routes
    assert len(routes) > 0, "Should return routes even with time parameter"


def test_online_routing_max_results_parameter(
    online_adapter: MotisPlanApiAdapter, berlin_hamburg_request: ABRoutingRequest
) -> None:
    """Test that max_results parameter is properly enforced client-side."""
    # Test with 1 result
    berlin_hamburg_request.max_results = 1
    response = online_adapter.route(berlin_hamburg_request)
    routes = response.routes
    assert len(routes) == 1, f"Should return exactly 1 route, got {len(routes)}"

    # Test with 3 results
    berlin_hamburg_request.max_results = 3
    response = online_adapter.route(berlin_hamburg_request)
    routes = response.routes
    assert len(routes) <= 3, f"Should return at most 3 routes, got {len(routes)}"
    assert len(routes) >= 1, "Should return at least 1 route"

    # Test with 5 results
    berlin_hamburg_request.max_results = 5
    response = online_adapter.route(berlin_hamburg_request)
    routes = response.routes
    assert len(routes) <= 5, f"Should return at most 5 routes, got {len(routes)}"
    assert len(routes) >= 1, "Should return at least 1 route"


def test_online_routing_validates_response_data(
    online_adapter: MotisPlanApiAdapter, berlin_hamburg_request: ABRoutingRequest
) -> None:
    """Test that response validation works correctly."""
    response = online_adapter.route(berlin_hamburg_request)
    validate_route_data(response.routes)


def test_online_routing_multiple_transport_modes(
    online_adapter: MotisPlanApiAdapter,
) -> None:
    """Test routing with multiple transport modes."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),  # Berlin
        destination=Location(lat=53.5511, lon=9.9937),  # Hamburg
        modes=[TransportMode.TRANSIT, TransportMode.WALK, TransportMode.BUS],
        max_results=2,
    )

    response = online_adapter.route(request)
    routes = response.routes
    assert len(routes) > 0

    # Should contain appropriate transport modes
    all_modes = set()
    for route in routes:
        for leg in route.legs:
            all_modes.add(leg.mode)

    # Should contain at least some of the requested modes
    assert len(all_modes) > 0


MAX_SPEEDS_KMH = {
    TransportMode.BUS: 120,
    TransportMode.TRAM: 80,
    TransportMode.SUBWAY: 120,
    TransportMode.RAIL: 400,  # Accommodates high-speed rail
}
DEFAULT_MAX_SPEED_KMH = 250


def test_distance_calculation_accuracy(
    online_adapter: MotisPlanApiAdapter, berlin_hamburg_request: ABRoutingRequest
) -> None:
    """Test that transit distance calculations are reasonable for a real route."""

    # Define realistic speed limits

    response = online_adapter.route(berlin_hamburg_request)
    assert response.routes, "API should have returned routes for Berlin-Hamburg"

    for route in response.routes:
        # Check total distance. Berlin-Hamburg is ~280km straight line.
        # A route distance of 280-450km is plausible.
        assert (
            240000 <= route.distance <= 450000
        ), f"Total route distance {route.distance/1000:.1f}km is unrealistic."

        for leg in route.legs:
            if leg.mode != TransportMode.WALK and leg.duration > 0 and leg.distance > 0:
                speed_kmh = (leg.distance / 1000) / (leg.duration / 3600)
                max_speed = MAX_SPEEDS_KMH.get(leg.mode, DEFAULT_MAX_SPEED_KMH)

                assert (
                    5 <= speed_kmh <= max_speed
                ), f"Leg with mode '{leg.mode.value}' has unrealistic speed: {speed_kmh:.1f} km/h."
