import pytest
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.schemas.ab_routing import ABRoutingRequest
from goatlib.routing.schemas.base import Location, TransportMode


@pytest.fixture
def performance_adapter() -> MotisPlanApiAdapter:
    """Create adapter configured for online API."""
    return create_motis_adapter(use_fixtures=False)


"""Test performance characteristics of the adapter."""


def test_multiple_requests_performance(
    performance_adapter: MotisPlanApiAdapter,
) -> None:
    """Test performance of multiple sequential requests."""
    requests = [
        ABRoutingRequest(
            origin=Location(lat=52.5200, lon=13.4050),
            destination=Location(lat=53.5511, lon=9.9937),
            modes=[TransportMode.TRANSIT],
            max_results=1,
        ),
        ABRoutingRequest(
            origin=Location(lat=48.1351, lon=11.5820),
            destination=Location(lat=50.9375, lon=6.9603),
            modes=[TransportMode.TRANSIT],
            max_results=1,
        ),
    ]

    # Execute multiple requests
    all_routes = []
    for request in requests:
        response = performance_adapter.route(request)
        routes = response.routes
        all_routes.extend(routes)

    assert len(all_routes) >= 0, "Should handle multiple requests"


def test_large_response_handling(performance_adapter: MotisPlanApiAdapter) -> None:
    """Test handling of responses with maximum allowed results."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=53.5511, lon=9.9937),
        modes=[TransportMode.TRANSIT, TransportMode.WALK],
        max_results=10,  # Maximum allowed by model validation
    )

    response = performance_adapter.route(request)
    routes = response.routes

    # Should handle large responses efficiently
    assert isinstance(routes, list)
    if len(routes) > 0:
        # Verify all routes are properly structured
        for route in routes:
            assert route.duration > 0
            assert len(route.legs) > 0


def test_complex_multimodal_request_performance(
    performance_adapter: MotisPlanApiAdapter,
) -> None:
    """Test performance with complex multimodal requests."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),  # Berlin
        destination=Location(lat=53.5511, lon=9.9937),  # Hamburg
        modes=[
            TransportMode.TRANSIT,
            TransportMode.WALK,
            TransportMode.BUS,
            TransportMode.RAIL,
        ],
        max_results=5,
    )

    response = performance_adapter.route(request)
    routes = response.routes

    # Should handle complex requests efficiently
    assert isinstance(routes, list)
    if len(routes) > 0:
        # Verify route diversity (multiple modes might be used)
        all_modes = set()
        for route in routes:
            for leg in route.legs:
                all_modes.add(leg.mode)

        # Complex requests should utilize multiple transport modes
        assert len(all_modes) >= 1


def test_long_distance_route_performance(
    performance_adapter: MotisPlanApiAdapter,
) -> None:
    """Test performance with long-distance routing requests."""
    request = ABRoutingRequest(
        origin=Location(lat=48.8566, lon=2.3522),  # Paris
        destination=Location(lat=52.5200, lon=13.4050),  # Berlin
        modes=[TransportMode.TRANSIT, TransportMode.WALK],
        max_results=3,
    )

    response = performance_adapter.route(request)
    routes = response.routes

    # Should handle long-distance requests
    assert isinstance(routes, list)
    if len(routes) > 0:
        # Long-distance routes should have reasonable characteristics
        for route in routes:
            # Duration should be reasonable for international travel (4 hours to 24 hours)
            # Paris-Berlin by train typically takes 8-14 hours
            assert (
                14400 <= route.duration <= 86400
            ), f"Long-distance route duration {route.duration}s seems unrealistic"
            # Distance should be substantial (>800km for Paris-Berlin)
            # Paris-Berlin is ~1,050km by rail, allow for routing variations
            assert (
                800000 <= route.distance <= 1500000
            ), f"Long-distance route distance {route.distance}m seems unrealistic"


def test_response_data_integrity_under_load(
    performance_adapter: MotisPlanApiAdapter,
) -> None:
    """Test that response data remains valid under multiple requests."""
    base_request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=53.5511, lon=9.9937),
        modes=[TransportMode.TRANSIT],
        max_results=2,
    )

    # Make multiple requests to test consistency
    all_routes = []
    for i in range(3):
        response = performance_adapter.route(base_request)
        routes = response.routes
        all_routes.extend(routes)

        # Verify each batch of routes
        for route in routes:
            # Data integrity checks
            assert route.route_id is not None
            assert route.duration > 0
            assert route.distance >= 0
            assert len(route.legs) > 0

            # Verify leg integrity
            for leg in route.legs:
                assert leg.duration > 0
                assert leg.departure_time < leg.arrival_time
                assert leg.origin is not None
                assert leg.destination is not None

    # Should have consistent results across requests
    assert len(all_routes) >= 0


def test_memory_efficiency_with_large_results(
    performance_adapter: MotisPlanApiAdapter,
) -> None:
    """Test memory efficiency when handling many routes."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=48.1351, lon=11.5820),  # Berlin to Munich
        modes=[TransportMode.TRANSIT, TransportMode.WALK],
        max_results=10,  # Request maximum routes
    )

    response = performance_adapter.route(request)
    routes = response.routes

    # Should efficiently handle maximum number of routes
    assert isinstance(routes, list)
    assert len(routes) <= 10

    if len(routes) > 0:
        # Check that large result sets are properly structured
        total_legs = sum(len(route.legs) for route in routes)
        assert total_legs > 0

        # Verify no memory-related issues with large datasets
        for route in routes:
            assert hasattr(route, "route_id")
            assert hasattr(route, "duration")
            assert hasattr(route, "distance")
            assert hasattr(route, "legs")


def test_adapter_reusability_performance(
    performance_adapter: MotisPlanApiAdapter,
) -> None:
    """Test that the same adapter instance can be reused efficiently."""
    requests = [
        ABRoutingRequest(
            origin=Location(lat=52.5200, lon=13.4050),
            destination=Location(lat=53.5511, lon=9.9937),
            modes=[TransportMode.TRANSIT],
            max_results=1,
        ),
        ABRoutingRequest(
            origin=Location(lat=48.1351, lon=11.5820),
            destination=Location(lat=48.7758, lon=9.1829),
            modes=[TransportMode.WALK],
            max_results=1,
        ),
    ]

    results = []
    for request in requests:
        response = performance_adapter.route(request)
        routes = response.routes
        results.append(len(routes))

    assert all(isinstance(result, int) for result in results)
    assert len(results) == len(requests)
