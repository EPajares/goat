import logging
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from goatlib.routing.schemas.base import (
    Location,
    Route,
    RoutingRequestBase,
    RoutingResponse,
    TransportMode,
)

logger = logging.getLogger(__name__)

# =====================================================================
# FIXTURES: Test Data
# =====================================================================


@pytest.fixture
def fixed_time() -> datetime:
    """Provides a consistent, timezone-aware 'now' for the duration of a test."""
    return datetime.now(timezone.utc)


@pytest.fixture
def base_request_data() -> Dict[str, Any]:
    """Provides a minimal valid dictionary to instantiate RoutingRequestBase."""
    return {
        "origin": {"lat": 48.1402, "lon": 11.5583},
        "destination": {"lat": 52.5251, "lon": 13.3693},
    }


@pytest.fixture
def valid_origin() -> Location:
    """Provides the location for Munich Central Station (Hauptbahnhof)."""
    return Location(lat=48.1402, lon=11.5583)


@pytest.fixture
def valid_destination() -> Location:
    """Provides the location for Berlin Central Station (Hauptbahnhof)."""
    return Location(lat=52.5251, lon=13.3693)


# =====================================================================
# Basic Validation Tests (Exceptions for Hard Failures)
# =====================================================================


@pytest.mark.parametrize(
    "lat, lon, expected_error",
    [
        (91.0, 13.4050, ValueError),
        (-91.0, 13.4050, ValueError),
        (52.5200, 181.0, ValueError),
        (52.5200, -181.0, ValueError),
    ],
    ids=["lat-too-high", "lat-too-low", "lon-too-high", "lon-too-low"],
)
def test_location_invalid_coordinates(
    lat: float, lon: float, expected_error: type
) -> None:
    """Test that invalid coordinates raise a ValueError."""
    with pytest.raises(expected_error):
        Location(lat=lat, lon=lon)


def test_location_valid() -> None:
    """Test creating a valid location."""
    location = Location(lat=52.5200, lon=13.4050)
    assert location.lat == 52.5200
    assert location.lon == 13.4050  # Access via the actual field name


def test_routing_request_same_origin_destination(valid_origin: Location) -> None:
    """Test that same origin and destination raises a validation error."""
    with pytest.raises(ValueError, match="Origin and destination cannot be the same"):
        RoutingRequestBase(
            modes=[TransportMode.WALK], origin=valid_origin, destination=valid_origin
        )


def test_route_valid() -> None:
    """Test creating a valid route."""
    departure_time = datetime.now(timezone.utc)
    route = Route(duration=30.5, distance=5000.0, departure_time=departure_time)
    assert route.duration == 30.5
    assert route.distance == 5000.0
    assert route.departure_time == departure_time


def test_routing_request_valid() -> None:
    """Test creating a valid AB routing request."""
    origin = Location(lat=52.5200, lon=13.4050)
    destination = Location(lat=52.5170, lon=13.3888)

    request = RoutingRequestBase(
        modes=[TransportMode.WALK], origin=origin, destination=destination
    )

    assert request.modes == [TransportMode.WALK]
    assert request.origin == origin
    assert request.destination == destination


def test_routing_response_valid() -> None:
    """Test creating a valid routing response."""
    departure_time = datetime.now(timezone.utc)
    route = Route(duration=30.5, distance=5000.0, departure_time=departure_time)

    response = RoutingResponse(routes=[route], processing_time_ms=250)

    assert len(response.routes) == 1
    assert response.routes[0] == route
    assert response.processing_time_ms == 250


def test_routing_response_invalid_processing_time() -> None:
    """Test that negative processing time raises validation error."""
    departure_time = datetime.now(timezone.utc)
    route = Route(duration=30.5, distance=5000.0, departure_time=departure_time)

    with pytest.raises(ValueError):
        RoutingResponse(
            routes=[route],
            processing_time_ms=-10,  # must be >= 0
        )


# =====================================================================
# Additional Tests
# =====================================================================


def test_transport_mode_enum() -> None:
    """Test that TransportMode enum has expected values."""
    assert TransportMode.WALK == "WALK"
    assert TransportMode.BUS == "BUS"
    assert TransportMode.CAR == "CAR"
    assert TransportMode.TRANSIT == "TRANSIT"


def test_routing_request_defaults() -> None:
    """Test routing request with default values."""
    origin = Location(lat=52.5200, lon=13.4050)
    destination = Location(lat=52.5170, lon=13.3888)

    request = RoutingRequestBase(origin=origin, destination=destination)

    assert request.modes == [TransportMode.WALK]  # default value
    assert request.time is None  # default value
    assert request.provider.value == "motis"  # default provider
