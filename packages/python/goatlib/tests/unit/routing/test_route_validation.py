from datetime import datetime, timezone

from goatlib.routing.schemas.ab_routing import ABLeg, ABRoute
from goatlib.routing.schemas.base import Location, Mode
from goatlib.routing.utils.ab_route_validator import (
    validate_route_response,
    validate_single_route,
)


def create_sample_route() -> ABRoute:
    """Create a sample route for testing."""
    origin = Location(lat=48.1351, lon=11.5820)  # Munich center
    destination = Location(lat=48.1482, lon=11.5680)  # Munich north

    # Walking leg
    walk_leg = ABLeg(
        origin=origin,
        destination=Location(lat=48.1360, lon=11.5810),  # Short walk to transit
        mode=Mode.WALK,
        departure_time=datetime(2025, 12, 15, 9, 0, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2025, 12, 15, 9, 5, 0, tzinfo=timezone.utc),
        duration=300,  # 5 minutes
        distance=400,  # 400m walk
    )

    # Transit leg
    transit_leg = ABLeg(
        origin=Location(lat=48.1360, lon=11.5810),
        destination=Location(lat=48.1480, lon=11.5675),
        mode=Mode.SUBWAY,
        departure_time=datetime(2025, 12, 15, 9, 8, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2025, 12, 15, 9, 15, 0, tzinfo=timezone.utc),
        duration=420,  # 7 minutes
        distance=2500,  # 2.5km by subway
    )

    # Final walking leg
    final_walk = ABLeg(
        origin=Location(lat=48.1480, lon=11.5675),
        destination=destination,
        mode=Mode.WALK,
        departure_time=datetime(2025, 12, 15, 9, 15, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2025, 12, 15, 9, 18, 0, tzinfo=timezone.utc),
        duration=180,  # 3 minutes
        distance=250,  # 250m walk
    )

    route = ABRoute(
        origin=origin,
        destination=destination,
        departure_time=walk_leg.departure_time,
        arrival_time=final_walk.arrival_time,
        duration=1080,  # Total 18 minutes
        distance=3150,  # Total distance
        legs=[walk_leg, transit_leg, final_walk],
    )

    return route


def create_problematic_route() -> ABRoute:
    """Create a route with plausibility issues for testing."""
    origin = Location(lat=48.1351, lon=11.5820)
    destination = Location(lat=48.2000, lon=11.6000)  # Much further

    # Impossibly fast walking
    bad_walk = ABLeg(
        origin=origin,
        destination=destination,
        mode=Mode.WALK,
        departure_time=datetime(2025, 12, 15, 9, 0, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2025, 12, 15, 9, 5, 0, tzinfo=timezone.utc),
        duration=300,  # 5 minutes
        distance=8000,  # 8km in 5 minutes = 96 km/h walking!
    )

    route = ABRoute(
        origin=origin,
        destination=destination,
        departure_time=bad_walk.departure_time,
        arrival_time=bad_walk.arrival_time,
        duration=300,
        distance=8000,
        legs=[bad_walk],
    )

    return route


def test_good_route_validation() -> None:
    """Test validation of a well-formed route."""
    good_route = create_sample_route()
    issues, score = validate_single_route(good_route, verbose=False)

    # A good route should have no major issues and high score
    assert len(issues) == 0, f"Good route should have no issues, got {len(issues)}"
    assert score >= 90, f"Good route should have high score, got {score}"


def test_problematic_route_validation() -> None:
    """Test validation catches problematic routes."""
    bad_route = create_problematic_route()
    issues, score = validate_single_route(bad_route, verbose=False)

    # A bad route should have issues and low score
    assert len(issues) > 0, "Problematic route should have validation issues"
    assert score < 70, f"Problematic route should have low score, got {score}"

    # Check that we catch the specific speed issue
    speed_issues = [issue for issue in issues if "speed" in issue.message.lower()]
    assert len(speed_issues) > 0, "Should catch speed-related issues"


def test_bulk_route_validation() -> None:
    """Test bulk validation of multiple routes."""
    good_route = create_sample_route()
    bad_route = create_problematic_route()
    routes = [good_route, bad_route, create_sample_route()]

    report = validate_route_response(routes)

    assert (
        report.routes_validated == 3
    ), f"Expected 3 routes, got {report.routes_validated}"
    assert report.total_issues > 0, "Should find issues in problematic route"

    avg_score = sum(report.scores) / len(report.scores) if report.scores else 0
    assert avg_score < 100, "Average score should be less than perfect with bad route"


def test_route_leg_consistency() -> None:
    """Test that route validation checks leg consistency."""
    route = create_sample_route()

    # Ensure the route has consistent timing across legs
    assert route.legs[0].arrival_time <= route.legs[1].departure_time
    assert route.legs[1].arrival_time <= route.legs[2].departure_time

    # Validate the route
    issues, score = validate_single_route(route, verbose=False)
    timing_issues = [issue for issue in issues if "time" in issue.message.lower()]

    # Should not have timing issues with our well-formed route
    assert len(timing_issues) == 0, "Well-formed route should not have timing issues"
