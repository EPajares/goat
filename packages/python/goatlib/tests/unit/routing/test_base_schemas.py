from datetime import datetime, timezone

import pytest
from goatlib.routing.schemas.base import (
    Location,
    Mode,
    Route,
)


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
    assert location.lon == 13.4050


def test_transport_mode_enum() -> None:
    """Test that Mode enum has expected values."""
    assert Mode.WALK == "WALK"
    assert Mode.BUS == "BUS"
    assert Mode.CAR == "CAR"
    assert Mode.TRANSIT == "TRANSIT"


# add a test for route schema
def test_route_schema() -> None:
    """Test creating a Route object."""
    route = Route(
        duration=3600,
        distance=10000,
        departure_time=datetime.now(timezone.utc),
    )
    assert route.duration == 3600
    assert route.distance == 10000
    assert route.departure_time is not None
    assert route.route_id is not None
