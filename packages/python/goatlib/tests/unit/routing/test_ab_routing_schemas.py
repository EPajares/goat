from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from goatlib.routing.schemas.ab_routing import (
    ABLeg,
    ABRoute,
    ABRoutingRequest,
    ABRoutingResponse,
)
from goatlib.routing.schemas.base import Location, Mode
from pydantic import ValidationError

# =====================================================================
#  FIXTURES: Test Data
# =====================================================================


@pytest.fixture
def valid_location_data() -> Dict[str, float]:
    """Provides valid data for a Location model."""
    return {"lat": 48.8566, "lon": 2.3522}


@pytest.fixture
def valid_leg_data(valid_location_data: Dict[str, float]) -> Dict[str, Any]:
    """Provides a valid dictionary for creating an ABLeg."""
    now = datetime.now(timezone.utc)
    return {
        "leg_id": "leg_123",
        "mode": Mode.WALK,
        "origin": valid_location_data,
        "destination": {"lat": 48.8606, "lon": 2.3376},
        "departure_time": now,
        "arrival_time": now.replace(second=now.second + 5),
        "duration": 300,
        "distance": 500,
    }


@pytest.fixture
def valid_route_data(valid_leg_data: Dict[str, Any]) -> Dict[str, Any]:
    """Provides a valid dictionary for creating an ABRoute."""
    return {
        "route_id": "route_abc",
        "duration": 25,  # Inherited from base Route
        "distance": 1500,  # Inherited from base Route
        "departure_time": datetime.now(timezone.utc),  # Required by base Route
        "legs": [valid_leg_data],
    }


# =====================================================================
#  SCHEMA TESTS: ABRoutingRequest
# =====================================================================


def test_ab_request_creation_with_defaults(
    valid_location_data: Dict[str, float],
) -> None:
    """Tests that a minimal ABRoutingRequest is created with correct defaults."""
    req = ABRoutingRequest(
        origin=valid_location_data,
        destination={"lat": 40.7128, "lon": -74.0060},
        modes=[Mode.TRANSIT],
    )

    assert req.max_results == 3


@pytest.mark.parametrize(
    "results, should_fail",
    [
        (0, True),
        (11, True),
        (1, False),
        (10, False),
        (5, False),
    ],
    ids=["too-low", "too-high", "min-success", "max-success", "valid-middle"],
)
def test_ab_request_max_results_constraints(
    valid_location_data: Dict[str, float], results: int, should_fail: bool
) -> None:
    """Tests the ge=1 and le=10 constraints on the max_results field."""
    base_data = {
        "origin": valid_location_data,
        "destination": {"lat": 40.7128, "lon": -74.0060},
        "modes": [Mode.TRANSIT],
        "max_results": results,
    }
    if should_fail:
        with pytest.raises(ValidationError):
            ABRoutingRequest(**base_data)
    else:
        assert ABRoutingRequest(**base_data).max_results == results


def test_same_origin_destination_validation() -> None:
    """Test routing validation with identical origin and destination."""
    location = Location(lat=52.5200, lon=13.4050)

    # This should raise a validation error since origin == destination
    with pytest.raises(ValidationError) as exc_info:
        ABRoutingRequest(
            origin=location,
            destination=location,
            modes=[Mode.WALK],
            max_results=1,
        )

    # Verify the validation error message
    assert "Origin and destination cannot be the same" in str(exc_info.value)


def test_extreme_max_results_validation() -> None:
    """Test validation with extreme max_results values."""
    # This should raise a validation error since max_results > 10
    with pytest.raises(ValidationError) as exc_info:
        ABRoutingRequest(
            origin=Location(lat=52.5200, lon=13.4050),
            destination=Location(lat=53.5511, lon=9.9937),
            modes=[Mode.TRANSIT],
            max_results=100,  # Too high - model limits to max 10
        )

    # Verify the validation error message
    assert "Input should be less than or equal to 10" in str(exc_info.value)


# =====================================================================
#  SCHEMA TESTS: ABRoute
# =====================================================================


def test_ab_route_creation_success(valid_route_data: Dict[str, Any]) -> None:
    """Tests successful creation of an ABRoute from valid data."""
    route = ABRoute(**valid_route_data)

    assert route.route_id == "route_abc"
    assert len(route.legs) == 1
    assert isinstance(route.legs[0], ABLeg)
    assert route.duration == 25


@pytest.mark.parametrize(
    "duration, distance",
    [
        (0, 5000.0),  # Zero duration
        (-10, 5000.0),  # Negative duration
        (30.5, 0),  # Zero distance
        (30.5, -100),  # Negative distance
    ],
    ids=["zero-duration", "neg-duration", "zero-distance", "neg-distance"],
)
def test_ab_route_creation_invalid(duration: float, distance: float) -> None:
    """Tests that a Route with invalid duration or distance raises a ValueError."""
    with pytest.raises(ValueError):
        ABRoute(
            duration=duration,
            distance=distance,
            departure_time=datetime.now(timezone.utc),
            legs=[],
        )


# =====================================================================
#  SCHEMA TESTS: ABRoutingResponse
# =====================================================================


def test_ab_response_creation_success(valid_route_data: Dict[str, Any]) -> None:
    """Tests successful creation of ABRoutingResponse with consistent route counts."""
    route_obj = ABRoute(**valid_route_data)

    response = ABRoutingResponse(
        routes=[route_obj],
    )

    assert response.type == "FeatureCollection"
