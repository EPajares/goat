"""
Test plausibility validation with real AB routing data.
"""

import asyncio
import logging
from datetime import datetime, timezone

from goatlib.routing.validation.route_plausibility import (
    validate_single_route,
    validate_route_response,
)
from goatlib.routing.schemas.ab_routing import ABLeg, ABRoute, ABRoutingRequest
from goatlib.routing.schemas.base import Mode, Location

# Set up logging to see validation messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


async def test_plausibility_validation():
    """Test the plausibility validation system."""
    print("=" * 60)
    print("TESTING AB ROUTING PLAUSIBILITY VALIDATION")
    print("=" * 60)

    # Test 1: Good route
    print("\n1. Testing GOOD route:")
    good_route = create_sample_route()
    issues, score = validate_single_route(good_route, verbose=True)

    if not issues:
        print(f"✅ Good route passed validation with score {score:.1f}/100")
    else:
        print(f"⚠️ Good route has {len(issues)} issues (score: {score:.1f}/100)")

    # Test 2: Problematic route
    print("\n2. Testing PROBLEMATIC route:")
    bad_route = create_problematic_route()
    issues, score = validate_single_route(bad_route, verbose=True)

    if issues:
        print(
            f"✅ Problematic route correctly identified {len(issues)} issues (score: {score:.1f}/100)"
        )
    else:
        print("❌ Problematic route was not caught!")

    # Test 3: Bulk validation
    print("\n3. Testing BULK validation:")
    routes = [good_route, bad_route, create_sample_route()]
    report = validate_route_response(routes)
    report.print_summary()

    print("\n" + "=" * 60)
    print("PLAUSIBILITY VALIDATION TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_plausibility_validation())
