from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from goatlib.routing.schemas.ab_routing import (
    ABRoute,
    ABRouteLeg,
    ABRoutingRequest,
    ABRoutingResponse,
)
from goatlib.routing.schemas.base import TransportMode
from pydantic import ValidationError

# =====================================================================
#  FIXTURES: Test Data
# =====================================================================


@pytest.fixture
def valid_location_data() -> Dict[str, float]:
    """Provides valid data for a Location model."""
    return {"lat": 48.8566, "long": 2.3522}


@pytest.fixture
def valid_leg_data(valid_location_data: Dict[str, float]) -> Dict[str, Any]:
    """Provides a valid dictionary for creating an ABRouteLeg."""
    now = datetime.now(timezone.utc)
    return {
        "leg_id": "leg_123",
        "mode": TransportMode.WALK,
        "origin": valid_location_data,
        "destination": {"lat": 48.8606, "long": 2.3376},
        "departure_time": now,
        "arrival_time": now,
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
        "time": datetime.now(timezone.utc),  # Inherited from base Route
        "legs": [valid_leg_data],
        "optimization_score": 0.9,
    }


# =====================================================================
#  SCHEMA TESTS: ABRoutingRequest
# =====================================================================


def test_ab_request_creation_with_defaults(
    valid_location_data: Dict[str, float],
) -> None:
    """Tests that a minimal ABRoutingRequest is created with correct defaults."""
    # ABRoutingRequest inherits from ABRoutingRequestBase which needs modes.
    req = ABRoutingRequest(
        origin=valid_location_data,
        destination={"lat": 40.7128, "long": -74.0060},
        modes=[TransportMode.TRANSIT],
    )

    # Assert that the composed and default fields are set correctly
    assert req.max_results == 3
    assert req.include_geometry is True
    assert req.include_instructions is True


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
        "destination": {"lat": 40.7128, "long": -74.0060},
        "modes": [TransportMode.TRANSIT],
        "max_results": results,
    }
    if should_fail:
        with pytest.raises(ValidationError):
            ABRoutingRequest(**base_data)
    else:
        assert ABRoutingRequest(**base_data).max_results == results


# =====================================================================
#  SCHEMA TESTS: ABRoute
# =====================================================================


def test_ab_route_creation_success(valid_route_data: Dict[str, Any]) -> None:
    """Tests successful creation of an ABRoute from valid data."""
    route = ABRoute(**valid_route_data)

    assert route.route_id == "route_abc"
    assert route.optimization_score == 0.9
    assert len(route.legs) == 1
    assert isinstance(route.legs[0], ABRouteLeg)
    assert route.duration == 25  # Check inherited field


# =====================================================================
#  SCHEMA TESTS: ABRoutingResponse
# =====================================================================


def test_ab_response_creation_success(valid_route_data: Dict[str, Any]) -> None:
    """Tests successful creation of ABRoutingResponse with consistent route counts."""
    route_obj = ABRoute(**valid_route_data)

    response = ABRoutingResponse(
        request_id="req_123",
        routes=[route_obj],
        total_routes=1,
    )

    assert response.total_routes == 1
    assert response.type == "FeatureCollection"  # Check default
    assert isinstance(response.timestamp, datetime)


def test_ab_response_mismatch_route_count_fails(
    valid_route_data: Dict[str, Any],
) -> None:
    """Tests the custom validator fails if total_routes != len(routes)."""
    route_obj = ABRoute(**valid_route_data)

    # Using `match` to check for our specific custom error message
    with pytest.raises(
        ValidationError, match="Internal data inconsistency: route count mismatch"
    ):
        ABRoutingResponse(
            request_id="req_456",
            routes=[route_obj],  # List has 1 route
            total_routes=5,  # but the total is stated as 5
        )


def test_ab_response_zero_routes_success() -> None:
    """Tests that a response with an empty routes list is valid."""
    response = ABRoutingResponse(
        request_id="req_789",
        routes=[],
        total_routes=0,
    )
    assert response.total_routes == 0
    assert len(response.routes) == 0
