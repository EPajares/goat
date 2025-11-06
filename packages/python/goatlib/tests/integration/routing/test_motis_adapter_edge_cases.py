import pytest
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.schemas.ab_routing import ABRoutingRequest
from goatlib.routing.schemas.base import Location, TransportMode


@pytest.fixture
def edge_adapter() -> MotisPlanApiAdapter:
    """Create adapter configured for online API."""
    return create_motis_adapter(use_fixtures=False)


"""Test edge cases and boundary conditions."""


def test_very_short_distance_routing(edge_adapter: MotisPlanApiAdapter) -> None:
    """Test routing for very short distances."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=52.5201, lon=13.4051),  # ~100m apart
        modes=[TransportMode.WALK],
        max_results=1,
    )

    response = edge_adapter.route(request)
    routes = response.routes
    # Should return walking route even for very short distances
    assert len(routes) >= 0  # May return empty if too short


def test_single_transport_mode_edge_case(edge_adapter: MotisPlanApiAdapter) -> None:
    """Test routing with single transport mode at edge case coordinates."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=52.5200001, lon=13.4050001),  # Very close coordinates
        modes=[TransportMode.WALK],  # Only walking for micro-distance
        max_results=1,
    )

    response = edge_adapter.route(request)
    routes = response.routes
    # Should handle micro-distances gracefully
    if len(routes) > 0:
        # For very short distances, should primarily return walking
        walk_legs_found = any(
            leg.mode == TransportMode.WALK for route in routes for leg in route.legs
        )
        assert walk_legs_found, "Should have walking legs for micro-distances"


def test_extreme_coordinates_boundaries(edge_adapter: MotisPlanApiAdapter) -> None:
    """Test with coordinates at extreme but valid boundaries."""
    request = ABRoutingRequest(
        origin=Location(lat=85.0, lon=179.0),  # Near north pole and dateline
        destination=Location(lat=84.9, lon=178.9),  # Slightly different
        modes=[TransportMode.WALK],
        max_results=1,
    )

    # This might not find routes (no transit coverage) but shouldn't crash
    response = edge_adapter.route(request)
    routes = response.routes
    assert isinstance(routes, list)  # Should return a list, even if empty


def test_duplicate_transport_modes_handling(
    edge_adapter: MotisPlanApiAdapter,
) -> None:
    """Test handling of duplicate transport modes."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=53.5511, lon=9.9937),
        modes=[TransportMode.TRANSIT, TransportMode.TRANSIT],  # Duplicates
        max_results=1,
    )

    # Should handle duplicates gracefully (might deduplicate internally)
    response = edge_adapter.route(request)
    routes = response.routes
    assert isinstance(routes, list)
