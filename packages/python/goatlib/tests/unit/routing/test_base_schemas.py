import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest
from _pytest.logging import LogCaptureFixture
from goatlib.routing.schemas.base import (
    Location,
    Route,
    RoutingRequestBase,
    RoutingResponse,
    TransportMode,
)

logger = logging.getLogger(__name__)

# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def fixed_time() -> datetime:
    """Provides a consistent, timezone-aware 'now' for the duration of a test."""
    return datetime.now(timezone.utc)


@pytest.fixture
def base_request_data() -> Dict[str, Any]:
    """Provides a minimal valid dictionary to instantiate RoutingRequestBase."""
    return {
        "origin": {"lat": 48.1402, "long": 11.5583},
        "destination": {"lat": 52.5251, "long": 13.3693},
    }


@pytest.fixture
def valid_origin() -> Location:
    """Provides the location for Munich Central Station (Hauptbahnhof)."""
    return Location(lat=48.1402, long=11.5583)


@pytest.fixture
def valid_destination() -> Location:
    """Provides the location for Berlin Central Station (Hauptbahnhof)."""
    return Location(lat=52.5251, long=13.3693)


# =====================================================================
# Basic Validation Tests (Exceptions for Hard Failures)
# =====================================================================


@pytest.mark.parametrize(
    "lat, long, expected_error",
    [
        (91.0, 13.4050, ValueError),
        (-91.0, 13.4050, ValueError),
        (52.5200, 181.0, ValueError),
        (52.5200, -181.0, ValueError),
    ],
    ids=["lat-too-high", "lat-too-low", "long-too-high", "long-too-low"],
)
def test_location_invalid_coordinates(
    lat: float, long: float, expected_error: type
) -> None:
    """Test that invalid coordinates raise a ValueError."""
    with pytest.raises(expected_error):
        Location(lat=lat, long=long)


def test_location_valid() -> None:
    """Test creating a valid location."""
    location = Location(lat=52.5200, long=13.4050)
    assert location.lat == 52.5200
    assert location.long == 13.4050


def test_routing_request_same_origin_destination(valid_origin: Location) -> None:
    """Test that same origin and destination raises a validation error."""
    with pytest.raises(ValueError, match="Origin and destination cannot be the same"):
        RoutingRequestBase(
            modes=[TransportMode.WALK], origin=valid_origin, destination=valid_origin
        )


def test_route_valid() -> None:
    """Test creating a valid route."""
    route = Route(duration=30.5, distance=5000.0)
    assert route.duration == 30.5
    assert route.distance == 5000.0


def test_routing_request_valid() -> None:
    """Test creating a valid AB routing request."""
    origin = Location(lat=52.5200, long=13.4050)
    destination = Location(lat=52.5170, long=13.3888)

    request = RoutingRequestBase(
        modes=[TransportMode.WALK], origin=origin, destination=destination
    )

    assert request.modes == [TransportMode.WALK]
    assert request.origin == origin
    assert request.destination == destination


def test_routing_response_valid() -> None:
    """Test creating a valid routing response."""
    route = Route(duration=30.5, distance=5000.0)

    response = RoutingResponse(routes=[route], processing_time_ms=250)

    assert len(response.routes) == 1
    assert response.routes[0] == route
    assert response.processing_time_ms == 250


def test_routing_response_invalid_processing_time() -> None:
    """Test that negative processing time raises validation error."""
    route = Route(duration=30.5, distance=5000.0)

    with pytest.raises(ValueError):
        RoutingResponse(
            routes=[route],
            processing_time_ms=-10,  # must be >= 0
        )


# =====================================================================
# Advisory Validation Tests (Warnings for Soft Failures)
# =====================================================================


@pytest.mark.parametrize(
    "time_delta, is_naive, expected_warnings",
    [
        (timedelta(hours=1), False, []),
        (timedelta(hours=-1), False, ["is in the past"]),
        (timedelta(minutes=10), True, ["lacks a timezone"]),
        (timedelta(minutes=-10), True, ["lacks a timezone", "is in the past"]),
        (None, False, []),
    ],
    ids=[
        "future-aware-no-warning",
        "past-aware-past-warning",
        "future-naive-naive-warning",
        "past-naive-both-warnings",
        "null-time-no-warning",
    ],
)
def test_departure_time_warnings(
    caplog: LogCaptureFixture,
    base_request_data: Dict[str, Any],
    time_delta: Optional[timedelta],
    is_naive: bool,
    expected_warnings: List[str],
    fixed_time: datetime,
) -> None:
    """Tests all time-related advisory warnings for RoutingRequestBase."""
    test_time: Optional[datetime]
    if time_delta is None:
        test_time = None
    else:
        test_time = fixed_time + time_delta
        if is_naive:
            test_time = test_time.replace(tzinfo=None)

    with caplog.at_level(logging.WARNING):
        RoutingRequestBase(**base_request_data, time=test_time)

    if not expected_warnings:
        assert not caplog.text, "Expected no warnings, but some were logged."
    else:
        assert len(caplog.records) == len(expected_warnings)
        for warning_text in expected_warnings:
            assert (
                warning_text in caplog.text
            ), f"Expected warning '{warning_text}' was not found."


@pytest.mark.parametrize(
    "modes_list",
    [
        pytest.param([TransportMode.CAR], id="car-only"),
        pytest.param(
            [TransportMode.WALK, TransportMode.BUS], id="public-transport-and-walk"
        ),
        pytest.param([TransportMode.WALK], id="walk-only"),
    ],
)
def test_unmixed_modes_do_not_trigger_warning(
    caplog: LogCaptureFixture,
    base_request_data: Dict[str, Any],
    modes_list: List[TransportMode],
) -> None:
    """Tests that valid, non-mixed mode combinations produce no warnings."""
    with caplog.at_level(logging.WARNING):
        if hasattr(RoutingRequestBase, "warn_on_mixed_car_mode"):
            RoutingRequestBase(**base_request_data, modes=modes_list)
    assert not caplog.text, "A warning was logged unexpectedly."
