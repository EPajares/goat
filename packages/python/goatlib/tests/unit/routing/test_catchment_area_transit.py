import pytest
from goatlib.routing.schemas.catchment_area_transit import (
    AccessEgressMode,
    TransitIsochroneRequest,
    TransitIsochroneStartingPoints,
    TransitIsochroneTravelTimeCost,
)


def test_valid_single_point() -> None:
    """Test creating valid single starting point."""
    starting_points = TransitIsochroneStartingPoints(
        latitude=[52.5200], longitude=[13.4050]
    )
    assert starting_points.latitude == [52.5200]
    assert starting_points.longitude == [13.4050]


def test_reject_multiple_points() -> None:
    """Test that multiple starting points are rejected."""
    with pytest.raises(ValueError, match="single starting point"):
        TransitIsochroneStartingPoints(
            latitude=[52.5200, 52.5300], longitude=[13.4050, 13.4150]
        )


def test_valid_travel_cost() -> None:
    """Test creating valid travel cost configuration."""
    travel_cost = TransitIsochroneTravelTimeCost(
        max_traveltime=60, steps=4, cutoffs=[15, 30, 45, 60]
    )
    assert travel_cost.max_traveltime == 60
    assert travel_cost.steps == 4
    assert travel_cost.cutoffs == [15, 30, 45, 60]


def test_cutoffs_exceed_max_time() -> None:
    """Test that cutoffs exceeding max travel time are rejected."""
    with pytest.raises(ValueError, match="exceeds maximum travel time"):
        TransitIsochroneTravelTimeCost(max_traveltime=30, steps=3, cutoffs=[15, 45, 60])


def test_negative_cutoffs() -> None:
    """Test that negative cutoffs are rejected."""
    with pytest.raises(ValueError, match="must be positive"):
        TransitIsochroneTravelTimeCost(
            max_traveltime=60, steps=4, cutoffs=[-15, 30, 45]
        )


def test_unsorted_cutoffs() -> None:
    """Test that unsorted cutoffs are rejected."""
    with pytest.raises(ValueError, match="ascending order"):
        TransitIsochroneTravelTimeCost(
            max_traveltime=60, steps=4, cutoffs=[30, 15, 45, 60]
        )


def test_valid_request() -> None:
    """Test creating a valid transit isochrone request."""
    request_data = {
        "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
        "transit_modes": ["bus", "tram"],
        "access_mode": "walk",
        "egress_mode": "walk",
        "travel_cost": {
            "max_traveltime": 60,
            "steps": 4,
            "cutoffs": [15, 30, 45, 60],
        },
    }

    request = TransitIsochroneRequest(**request_data)
    assert len(request.starting_points.latitude) == 1
    assert len(request.transit_modes) == 2
    assert request.travel_cost.max_traveltime == 60


def test_bike_access_request() -> None:
    """Test transit request with bicycle access mode."""
    request_data = {
        "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
        "transit_modes": ["rail", "subway"],
        "access_mode": "bicycle",
        "egress_mode": "walk",
        "travel_cost": {"max_traveltime": 45, "steps": 3, "cutoffs": [15, 30, 45]},
        "max_bike_time": 25,
    }

    request = TransitIsochroneRequest(**request_data)
    assert request.access_mode == AccessEgressMode.bicycle
    assert request.max_bike_time == 25
