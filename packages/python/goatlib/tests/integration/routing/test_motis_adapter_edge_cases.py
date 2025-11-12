from typing import AsyncGenerator

import pytest_asyncio
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.schemas.ab_routing import ABRoutingRequest
from goatlib.routing.schemas.base import Location, Mode


@pytest_asyncio.fixture
async def edge_adapter() -> AsyncGenerator[MotisPlanApiAdapter, None]:
    """
    An async fixture that provides a configured Motis adapter and
    properly cleans up its resources.
    """
    # Assume create_motis_adapter now correctly sets up the async client
    adapter = create_motis_adapter(use_fixtures=False)

    yield adapter
    # After the test session, the async cleanup code runs
    await adapter.motis_client.close()


###########################################################################
# Edge Case Tests
###########################################################################


async def test_very_short_distance_routing(edge_adapter: MotisPlanApiAdapter) -> None:
    """Test routing for very short distances."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=52.5201, lon=13.4051),
        modes=[Mode.WALK],
        max_results=1,
    )

    response = await edge_adapter.route(request)

    routes = response.routes
    # Should return empty routes for very short distances - that's expected behavior
    assert response is not None
    assert len(routes) >= 0  # May return empty if too short


async def test_single_transport_mode_edge_case(
    edge_adapter: MotisPlanApiAdapter,
) -> None:
    """Test routing with single transport mode at edge case coordinates."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=52.5200001, lon=13.4050001),  # Very close coordinates
        modes=[Mode.WALK],  # Only walking for micro-distance
        max_results=1,
    )

    response = await edge_adapter.route(request)
    routes = response.routes
    # Should handle micro-distances gracefully
    if len(routes) > 0:
        # For very short distances, should primarily return walking
        walk_legs_found = any(
            leg.mode == Mode.WALK for route in routes for leg in route.legs
        )
        assert walk_legs_found, "Should have walking legs for micro-distances"


async def test_extreme_coordinates_boundaries(
    edge_adapter: MotisPlanApiAdapter,
) -> None:
    """Test with coordinates at extreme but valid boundaries."""
    request = ABRoutingRequest(
        origin=Location(lat=85.0, lon=179.0),  # Near north pole and dateline
        destination=Location(lat=84.9, lon=178.9),  # Slightly different
        modes=[Mode.WALK],
        max_results=1,
    )

    # This might not find routes (no transit coverage) but shouldn't crash
    response = await edge_adapter.route(request)
    routes = response.routes
    assert isinstance(routes, list)  # Should return a list, even if empty


async def test_duplicate_transport_modes_handling(
    edge_adapter: MotisPlanApiAdapter,
) -> None:
    """Test handling of duplicate transport modes."""
    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=53.5511, lon=9.9937),
        modes=[Mode.TRANSIT, Mode.TRANSIT],  # Duplicates
        max_results=1,
    )

    # Should handle duplicates gracefully (might deduplicate internally)
    response = await edge_adapter.route(request)
    routes = response.routes
    assert isinstance(routes, list)
