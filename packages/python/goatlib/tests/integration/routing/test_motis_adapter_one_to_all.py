import pytest
from goatlib.routing.schemas.catchment_area_transit import (
    AccessEgressMode,
    CatchmentAreaRoutingModePT,
    TransitCatchmentAreaRequest,
    TransitCatchmentAreaResponse,
    TransitCatchmentAreaStartingPoints,
    TransitCatchmentAreaTravelTimeCost,
)


def validate_response_structure(
    response: TransitCatchmentAreaResponse, expected_cutoffs: list[int]
) -> None:
    """
    Validate the basic structure and consistency of a transit catchment area response.

    Args:
        response: The response to validate
        expected_cutoffs: List of expected cutoff times
    """
    # Validate response structure
    assert response is not None
    assert hasattr(response, "polygons")
    assert hasattr(response, "metadata")

    # Validate metadata structure
    assert response.metadata is not None
    total_locations = response.metadata.get("total_locations", 0)
    assert total_locations >= 0

    # If no reachable locations, polygons list should be empty
    if total_locations == 0:
        assert len(response.polygons) == 0
        return

    # Should generate polygons for each cutoff when locations are reachable
    assert len(response.polygons) == len(expected_cutoffs)

    # Validate each polygon
    for polygon in response.polygons:
        assert polygon.travel_time in expected_cutoffs
        assert polygon.geometry is not None
        assert polygon.geometry["type"] == "Polygon"
        assert "coordinates" in polygon.geometry

    # Additional metadata validation for successful responses
    assert response.metadata.get("source") == "motis_one_to_all"

    # Check that travel times match cutoffs and are properly ordered
    travel_times = [p.travel_time for p in response.polygons]
    assert sorted(travel_times) == sorted(expected_cutoffs)


def validate_polygon_geometry(response: TransitCatchmentAreaResponse) -> None:
    """Validate that polygon geometries have correct GeoJSON structure."""
    for polygon in response.polygons:
        geometry = polygon.geometry

        # Check GeoJSON Polygon structure
        assert geometry["type"] == "Polygon"
        assert "coordinates" in geometry
        assert isinstance(geometry["coordinates"], list)

        # Check that coordinates form a valid polygon
        if geometry["coordinates"]:
            coord_ring = geometry["coordinates"][0]
            assert len(coord_ring) >= 4  # Minimum for a closed polygon
            assert len(coord_ring[0]) == 2  # [lon, lat] format

            # First and last coordinates should be the same (closed polygon)
            assert coord_ring[0] == coord_ring[-1]


@pytest.mark.slow
@pytest.mark.network
class TestMotisAdapterOneToAll:
    """Test class for MOTIS one-to-all functionality."""

    async def test_basic_one_to_all_success(self, motis_adapter_online, berlin_request):
        """Test basic one-to-all functionality returns valid catchment areas."""
        response = await motis_adapter_online.get_transit_catchment_area(berlin_request)

        validate_response_structure(response, berlin_request.travel_cost.cutoffs)
        validate_polygon_geometry(response)

        # Berlin should have reachable locations
        assert response.metadata["total_locations"] > 0

    async def test_multiple_cutoffs(self, motis_adapter_online, munich_request):
        """Test that multiple travel time cutoffs generate correct polygons."""
        response = await motis_adapter_online.get_transit_catchment_area(munich_request)

        validate_response_structure(response, munich_request.travel_cost.cutoffs)

        # Polygons should be ordered by travel time
        for i, polygon in enumerate(response.polygons):
            assert polygon.travel_time == sorted(munich_request.travel_cost.cutoffs)[i]

    async def test_different_transit_modes(self, motis_adapter_online):
        """Test different combinations of transit modes."""
        rail_only_request = TransitCatchmentAreaRequest(
            starting_points=TransitCatchmentAreaStartingPoints(
                latitude=[52.5200], longitude=[13.4050]
            ),
            transit_modes=[CatchmentAreaRoutingModePT.rail],
            access_mode=AccessEgressMode.walk,
            egress_mode=AccessEgressMode.walk,
            travel_cost=TransitCatchmentAreaTravelTimeCost(
                max_traveltime=20, cutoffs=[20]
            ),
        )

        response = await motis_adapter_online.get_transit_catchment_area(
            rail_only_request
        )

        validate_response_structure(response, [20])

    async def test_single_cutoff(self, motis_adapter_online):
        """Test with a single travel time cutoff."""
        single_cutoff_request = TransitCatchmentAreaRequest(
            starting_points=TransitCatchmentAreaStartingPoints(
                latitude=[48.1351],  # Munich
                longitude=[11.5820],
            ),
            transit_modes=[
                CatchmentAreaRoutingModePT.subway,
                CatchmentAreaRoutingModePT.tram,
            ],
            access_mode=AccessEgressMode.walk,
            egress_mode=AccessEgressMode.walk,
            travel_cost=TransitCatchmentAreaTravelTimeCost(
                max_traveltime=20, cutoffs=[20]
            ),
        )

        response = await motis_adapter_online.get_transit_catchment_area(
            single_cutoff_request
        )

        validate_response_structure(response, [20])

    async def test_geometry_structure(self, motis_adapter_online, berlin_request):
        """Test that returned geometry has correct GeoJSON structure."""
        response = await motis_adapter_online.get_transit_catchment_area(berlin_request)

        validate_polygon_geometry(response)

    @pytest.mark.skip(reason="MOTIS bicycle access causes 500 error on public instance")
    async def test_bike_access_egress(self, motis_adapter_online):
        """Test catchment area with bicycle access and egress modes."""
        bike_request = TransitCatchmentAreaRequest(
            starting_points=TransitCatchmentAreaStartingPoints(
                latitude=[52.5200], longitude=[13.4050]
            ),
            transit_modes=[
                CatchmentAreaRoutingModePT.bus,
                CatchmentAreaRoutingModePT.tram,
            ],
            access_mode=AccessEgressMode.bicycle,
            egress_mode=AccessEgressMode.bicycle,
            travel_cost=TransitCatchmentAreaTravelTimeCost(
                max_traveltime=25, cutoffs=[25]
            ),
        )

        response = await motis_adapter_online.get_transit_catchment_area(bike_request)

        validate_response_structure(response, [25])

    async def test_invalid_coordinates_handling(self, motis_adapter_online):
        """Test handling of coordinates outside valid geographic range."""
        # MOTIS accepts invalid coordinates and returns empty results
        invalid_request = TransitCatchmentAreaRequest(
            starting_points=TransitCatchmentAreaStartingPoints(
                latitude=[91.0],  # Invalid latitude > 90
                longitude=[181.0],  # Invalid longitude > 180
            ),
            transit_modes=[CatchmentAreaRoutingModePT.bus],
            access_mode=AccessEgressMode.walk,
            egress_mode=AccessEgressMode.walk,
            travel_cost=TransitCatchmentAreaTravelTimeCost(
                max_traveltime=15, cutoffs=[15]
            ),
        )

        response = await motis_adapter_online.get_transit_catchment_area(
            invalid_request
        )

        # Should return valid structure but with no locations
        validate_response_structure(response, [15])
        # Specifically check that no locations were found
        assert response.metadata.get("total_locations", 0) == 0


@pytest.mark.slow
@pytest.mark.network
async def test_motis_one_to_all_integration_minimal(
    simple_berlin_request: TransitCatchmentAreaRequest,
) -> None:
    """Minimal integration test that can run independently."""
    from goatlib.routing.adapters.motis import create_motis_adapter

    adapter = create_motis_adapter(use_fixtures=False)

    try:
        response = await adapter.get_transit_catchment_area(simple_berlin_request)
        validate_response_structure(response, simple_berlin_request.travel_cost.cutoffs)

    finally:
        await adapter.motis_client.close()
