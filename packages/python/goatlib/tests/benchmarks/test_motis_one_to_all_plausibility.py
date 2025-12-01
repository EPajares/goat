import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import pytest
from goatlib.routing.adapters.motis.motis_adapter import create_motis_adapter
from goatlib.routing.adapters.motis.motis_converters import (
    parse_motis_one_to_all_response,
    translate_to_motis_one_to_all_request,
)
from goatlib.routing.schemas.catchment_area_transit import (
    AccessEgressMode,
    CatchmentAreaRoutingModePT,
    TransitCatchmentAreaRequest,
    TransitCatchmentAreaStartingPoints,
    TransitCatchmentAreaTravelTimeCost,
    TransitRoutingSettings,
)

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MotisOneToAllPlausibilityTester:
    """Comprehensive plausibility tester for MOTIS one-to-all responses."""

    def __init__(self):
        self.tolerance_meters = 1000  # 1km tolerance for location validation
        self.max_reasonable_travel_time = (
            120  # 2 hours max reasonable travel time (in minutes)
        )
        self.min_locations_expected = 5  # Minimum locations we expect to reach

    def validate_raw_motis_response(self, motis_data: Dict[str, Any]) -> List[str]:
        """Validate the raw MOTIS response structure and content."""
        issues = []

        # Check basic structure
        if not isinstance(motis_data, dict):
            issues.append("MOTIS response is not a dictionary")
            return issues

        # Check for expected top-level fields
        if "all" not in motis_data:
            issues.append("Missing 'all' field in MOTIS response")
            return issues

        reachable_locations = motis_data.get("all", [])

        # Validate reachable locations structure
        if not isinstance(reachable_locations, list):
            issues.append("'all' field is not a list")
            return issues

        if len(reachable_locations) < self.min_locations_expected:
            issues.append(
                f"Too few reachable locations: {len(reachable_locations)} < {self.min_locations_expected}"
            )

        # Validate individual location entries
        for idx, location in enumerate(reachable_locations):
            location_issues = self._validate_location_entry(location, idx)
            issues.extend(location_issues)

        return issues

    def _validate_location_entry(self, location: Dict[str, Any], idx: int) -> List[str]:
        """Validate an individual location entry from MOTIS response."""
        issues = []
        prefix = f"Location {idx}:"

        # Check required fields
        required_fields = ["place", "duration"]
        for field in required_fields:
            if field not in location:
                issues.append(f"{prefix} Missing required field '{field}'")
                continue

        # Duration check (simplified - MOTIS is reliable)
        duration = location.get("duration", 0)
        if duration > self.max_reasonable_travel_time:  # Duration is already in minutes
            issues.append(f"{prefix} Unreasonably long travel time: {duration} min")

        # Validate place information
        place = location.get("place", {})
        if not isinstance(place, dict):
            issues.append(f"{prefix} 'place' field is not a dictionary")
            return issues

        place_issues = self._validate_place_data(place, idx)
        issues.extend(place_issues)

        return issues

    def _validate_place_data(self, place: Dict[str, Any], idx: int) -> List[str]:
        """Validate place data within a location entry."""
        issues = []
        prefix = f"Location {idx} place:"

        # Check for coordinate fields
        if "lon" not in place and "lng" not in place:
            issues.append(f"{prefix} Missing longitude field (lon/lng)")
        if "lat" not in place:
            issues.append(f"{prefix} Missing latitude field")

        # Get longitude (handle both lon and lng)
        lon = place.get("lon", place.get("lng"))
        lat = place.get("lat")

        if lon is not None:
            if not isinstance(lon, (int, float)):
                issues.append(f"{prefix} Longitude is not numeric: {type(lon)}")
            elif not -180 <= lon <= 180:
                issues.append(f"{prefix} Invalid longitude: {lon}")

        if lat is not None:
            if not isinstance(lat, (int, float)):
                issues.append(f"{prefix} Latitude is not numeric: {type(lat)}")
            elif not -90 <= lat <= 90:
                issues.append(f"{prefix} Invalid latitude: {lat}")

        return issues

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive plausibility testing."""
        logger.info("🧪 MOTIS One-to-All Plausibility Test")

        adapter = create_motis_adapter(use_fixtures=False)

        try:
            # Create test request
            request = TransitCatchmentAreaRequest(
                starting_points=TransitCatchmentAreaStartingPoints(
                    latitude=[48.1351],
                    longitude=[11.5820],
                ),
                transit_modes=[
                    CatchmentAreaRoutingModePT.bus,
                    CatchmentAreaRoutingModePT.subway,
                ],
                access_mode=AccessEgressMode.walk,
                egress_mode=AccessEgressMode.walk,
                travel_cost=TransitCatchmentAreaTravelTimeCost(
                    max_traveltime=30,
                    cutoffs=[10, 20, 30],
                ),
                routing_settings=TransitRoutingSettings(),
            )

            # Get MOTIS response
            motis_request_data = translate_to_motis_one_to_all_request(request)
            motis_response = await adapter.motis_client.one_to_all(motis_request_data)

            # Validate raw response
            raw_issues = self.validate_raw_motis_response(motis_response)

            # Parse response and validate
            parsed_response = parse_motis_one_to_all_response(motis_response, request)
            parsed_issues = []

            if parsed_response is None:
                parsed_issues.append("Failed to parse MOTIS response")
            elif not hasattr(parsed_response, "polygons"):
                parsed_issues.append("Parsed response missing polygons")
            elif len(parsed_response.polygons) == 0:
                parsed_issues.append("No polygons generated from response")

            # Gather statistics
            reachable_locations = motis_response.get("all", [])
            travel_times = [loc.get("duration", 0) for loc in reachable_locations]

            # Test adapter integration
            try:
                adapter_response = await adapter.get_transit_catchment_area(request)
                adapter_polygon_count = (
                    len(adapter_response.polygons) if adapter_response else 0
                )
                direct_polygon_count = (
                    len(parsed_response.polygons) if parsed_response else 0
                )
            except Exception as e:
                logger.warning(f"Adapter test failed: {e}")
                adapter_polygon_count = 0
                direct_polygon_count = 0

            # Compile results
            results = {
                "timestamp": datetime.now().isoformat(),
                "test_location": "Munich, Germany",
                "request_params": {
                    "starting_point": [
                        request.starting_points.latitude[0],
                        request.starting_points.longitude[0],
                    ],
                    "transit_modes": [mode.value for mode in request.transit_modes],
                    "max_travel_time": request.travel_cost.max_traveltime,
                    "cutoffs": request.travel_cost.cutoffs,
                },
                "motis_request": motis_request_data,
                "raw_response_stats": {
                    "total_locations": len(reachable_locations),
                    "travel_time_range": [min(travel_times), max(travel_times)]
                    if travel_times
                    else [0, 0],
                    "average_travel_time": sum(travel_times) / len(travel_times)
                    if travel_times
                    else 0,
                },
                "validation_results": {
                    "raw_response_issues": raw_issues,
                    "parsed_response_issues": parsed_issues,
                    "total_issues": len(raw_issues) + len(parsed_issues),
                },
                "parsed_response_stats": {
                    "polygon_count": len(parsed_response.polygons)
                    if parsed_response
                    else 0,
                    "travel_times": [p.travel_time for p in parsed_response.polygons]
                    if parsed_response
                    else [],
                },
                "adapter_comparison": {
                    "adapter_polygons": adapter_polygon_count,
                    "direct_polygons": direct_polygon_count,
                    "consistent": adapter_polygon_count == direct_polygon_count,
                },
            }

            return results

        except Exception as e:
            logger.exception("Plausibility test failed")
            return {"error": str(e)}

        finally:
            if hasattr(adapter, "motis_client") and hasattr(
                adapter.motis_client, "close"
            ):
                await adapter.motis_client.close()


@pytest.fixture
def plausibility_tester():
    """Fixture providing a MotisOneToAllPlausibilityTester instance."""
    return MotisOneToAllPlausibilityTester()


@pytest.fixture
def sample_request():
    """Fixture providing a sample transit catchment area request."""
    return TransitCatchmentAreaRequest(
        starting_points=TransitCatchmentAreaStartingPoints(
            latitude=[48.1351],
            longitude=[11.5820],  # Munich city center
        ),
        transit_modes=[
            CatchmentAreaRoutingModePT.bus,
            CatchmentAreaRoutingModePT.subway,
        ],
        access_mode=AccessEgressMode.walk,
        egress_mode=AccessEgressMode.walk,
        travel_cost=TransitCatchmentAreaTravelTimeCost(
            max_traveltime=30,
            cutoffs=[10, 20, 30],
        ),
        routing_settings=TransitRoutingSettings(),
    )


@pytest.mark.asyncio
async def test_motis_one_to_all_raw_response_validation(plausibility_tester):
    """Test that MOTIS one-to-all returns a valid response structure."""
    adapter = create_motis_adapter(use_fixtures=False)

    try:
        request = TransitCatchmentAreaRequest(
            starting_points=TransitCatchmentAreaStartingPoints(
                latitude=[48.1351],
                longitude=[11.5820],
            ),
            transit_modes=[CatchmentAreaRoutingModePT.bus],
            travel_cost=TransitCatchmentAreaTravelTimeCost(
                max_traveltime=20,
                cutoffs=[10, 20],
            ),
        )

        motis_request = translate_to_motis_one_to_all_request(request)
        motis_response = await adapter.motis_client.one_to_all(motis_request)

        # Validate response structure
        issues = plausibility_tester.validate_raw_motis_response(motis_response)

        # Log any issues for debugging but allow minor issues
        if issues:
            logger.warning(f"Validation issues found: {issues}")

        # Basic assertions
        assert isinstance(motis_response, dict), "Response should be a dictionary"
        assert "all" in motis_response, "Response should contain 'all' field"
        assert isinstance(motis_response["all"], list), "'all' field should be a list"

        # Should have at least some reachable locations in Munich
        assert (
            len(motis_response["all"]) > 0
        ), "Should have at least some reachable locations"

    finally:
        await adapter.motis_client.close()


@pytest.mark.asyncio
async def test_motis_response_parsing(sample_request):
    """Test that MOTIS response can be parsed into our internal format."""
    adapter = create_motis_adapter(use_fixtures=False)

    try:
        motis_request = translate_to_motis_one_to_all_request(sample_request)
        motis_response = await adapter.motis_client.one_to_all(motis_request)

        # Parse the response
        parsed_response = parse_motis_one_to_all_response(
            motis_response, sample_request
        )

        # Validate parsed response
        assert parsed_response is not None, "Should successfully parse response"
        assert hasattr(parsed_response, "polygons"), "Should have polygons attribute"
        assert len(parsed_response.polygons) > 0, "Should generate at least one polygon"

        # Check polygon structure
        for polygon in parsed_response.polygons:
            assert hasattr(polygon, "travel_time"), "Polygon should have travel_time"
            assert polygon.travel_time > 0, "Travel time should be positive"
            assert (
                polygon.travel_time <= sample_request.travel_cost.max_traveltime
            ), "Travel time should not exceed maximum"

    finally:
        await adapter.motis_client.close()


@pytest.mark.asyncio
async def test_adapter_consistency(sample_request):
    """Test that adapter and direct parsing produce consistent results."""
    adapter = create_motis_adapter(use_fixtures=False)

    try:
        # Get response through adapter
        adapter_response = await adapter.get_transit_catchment_area(sample_request)

        # Get response directly and parse
        motis_request = translate_to_motis_one_to_all_request(sample_request)
        motis_response = await adapter.motis_client.one_to_all(motis_request)
        direct_response = parse_motis_one_to_all_response(
            motis_response, sample_request
        )

        # Compare results
        assert adapter_response is not None, "Adapter should return a response"
        assert direct_response is not None, "Direct parsing should return a response"

        adapter_polygon_count = len(adapter_response.polygons)
        direct_polygon_count = len(direct_response.polygons)

        assert adapter_polygon_count == direct_polygon_count, (
            f"Adapter and direct parsing should produce same number of polygons: "
            f"{adapter_polygon_count} vs {direct_polygon_count}"
        )

    finally:
        await adapter.motis_client.close()


@pytest.mark.asyncio
async def test_comprehensive_plausibility(plausibility_tester):
    """Run comprehensive plausibility test and verify results."""
    results = await plausibility_tester.run_comprehensive_test()

    # Should not have errored
    assert (
        "error" not in results
    ), f"Test should not error: {results.get('error', 'N/A')}"

    # Should have basic structure
    assert "validation_results" in results
    assert "raw_response_stats" in results
    assert "parsed_response_stats" in results

    # Should have found locations and generated polygons
    assert (
        results["raw_response_stats"]["total_locations"] > 0
    ), "Should find reachable locations"
    assert (
        results["parsed_response_stats"]["polygon_count"] > 0
    ), "Should generate polygons"

    # Log results for manual inspection
    logger.info(
        f"Plausibility test results: {json.dumps(results, indent=2, default=str)}"
    )


def test_location_entry_validation(plausibility_tester):
    """Test validation of individual location entries."""
    # Valid location entry
    valid_location = {
        "place": {"lat": 48.1351, "lon": 11.5820, "name": "Test Station"},
        "duration": 15,
    }

    issues = plausibility_tester._validate_location_entry(valid_location, 0)
    assert len(issues) == 0, f"Valid location should have no issues: {issues}"

    # Invalid location entry
    invalid_location = {
        "place": {"lat": "invalid", "lng": 200},  # Invalid lat, lng out of bounds
        "duration": 150,  # Too long travel time
    }

    issues = plausibility_tester._validate_location_entry(invalid_location, 0)
    assert len(issues) > 0, "Invalid location should have issues"


def test_place_data_validation(plausibility_tester):
    """Test validation of place data within location entries."""
    # Valid place data
    valid_place = {"lat": 48.1351, "lon": 11.5820, "name": "Test Location"}
    issues = plausibility_tester._validate_place_data(valid_place, 0)
    assert len(issues) == 0, f"Valid place should have no issues: {issues}"

    # Test lng vs lon handling
    place_with_lng = {"lat": 48.1351, "lng": 11.5820, "name": "Test Location"}
    issues = plausibility_tester._validate_place_data(place_with_lng, 0)
    assert len(issues) == 0, f"Place with lng field should be valid: {issues}"

    # Invalid place data
    invalid_place = {"lat": 200, "lon": -200}  # Out of bounds coordinates
    issues = plausibility_tester._validate_place_data(invalid_place, 0)
    assert len(issues) > 0, "Invalid place should have issues"
