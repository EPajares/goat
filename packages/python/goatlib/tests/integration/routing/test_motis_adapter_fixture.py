import pytest
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.errors import RoutingError
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


async def test_fixture_routing_basic_success(
    motis_adapter_fixture: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test basic fixture routing functionality returns valid routes."""
    response = await motis_adapter_fixture.route(test_request)
    routes = response.routes

    assert routes, "Should return routes from fixture data"
    validate_route_data(routes)


def test_fixture_adapter_creation_with_valid_path(motis_fixtures_dir: str) -> None:
    """Test creating fixture adapter with valid path."""
    adapter = create_motis_adapter(use_fixtures=True, fixture_path=motis_fixtures_dir)
    assert isinstance(adapter, MotisPlanApiAdapter)
    assert adapter.motis_client.use_fixtures is True


# CHANGE 4: Combined realism checks into a single, more comprehensive test.
async def test_fixture_route_realism_validation(
    motis_adapter_fixture: MotisPlanApiAdapter, test_request: ABRoutingRequest
) -> None:
    """Test that fixture data calculations (distance, speed) are reasonable."""
    response = await motis_adapter_fixture.route(test_request)
    routes = response.routes
    assert routes, "Cannot perform validation on an empty route list."

    for route in routes:
        # Route distance might be None if no walking legs have distance data (MOTIS behavior)
        if route.distance is not None:
            assert (
                100 <= route.distance <= 1_000_000
            ), f"Route distance {route.distance}m is unrealistic"
        assert (
            120 <= route.duration <= 43_200
        ), f"Route duration {route.duration}s is unrealistic"

        for leg in route.legs:
            if leg.mode == Mode.WALK:
                continue

            # Speed checks are only meaningful if both duration and distance are available
            if leg.duration > 0 and leg.distance is not None:
                speed_kmh = (leg.distance / 1000) / (leg.duration / 3600)
                max_speed = MAX_SPEEDS_KMH.get(leg.mode, DEFAULT_MAX_SPEED_KMH)
                assert (
                    5 <= speed_kmh <= max_speed
                ), f"Leg {leg.leg_id} ({leg.mode.value}) has unrealistic speed: {speed_kmh:.1f} km/h."
            # For transit legs without distance data (common with MOTIS), we can't validate speed
            # This is expected behavior since MOTIS doesn't always provide route distances for transit


# --- Error Handling Tests ---


async def test_empty_fixture_directory(tmp_path: pytest.TempPathFactory) -> None:
    """Test handling of empty fixture directories."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    adapter = create_motis_adapter(use_fixtures=True, fixture_path=empty_dir)
    request = ABRoutingRequest(
        origin=Location(lat=48.1, lon=11.5),
        destination=Location(lat=48.2, lon=11.6),
        modes=[Mode.WALK],
        max_results=1,
    )

    try:
        with pytest.raises(RoutingError):
            await adapter.route(request)
    finally:
        # For fixture-based adapters, close might not be needed, but let's be safe
        if hasattr(adapter.motis_client, "close"):
            await adapter.motis_client.close()


async def test_corrupted_fixture_file_handling(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """Test handling of corrupted fixture files."""
    # Create a corrupted JSON file
    corrupted_file = tmp_path / "test_motis_routes_corrupted.json"
    corrupted_file.write_text("{ invalid json content")

    adapter = create_motis_adapter(use_fixtures=True, fixture_path=tmp_path)
    request = ABRoutingRequest(
        origin=Location(lat=48.1, lon=11.5),
        destination=Location(lat=48.2, lon=11.6),
        modes=[Mode.WALK],
        max_results=1,
    )

    try:
        with pytest.raises(RoutingError):
            await adapter.route(request)
    finally:
        if hasattr(adapter.motis_client, "close"):
            await adapter.motis_client.close()
