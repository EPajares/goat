import json
import logging
from typing import Any, Dict, List

import pytest
from goatlib.routing.adapters.motis.motis_client import MotisServiceClient
from goatlib.routing.adapters.motis.motis_converters import (
    create_bus_station_buffers,
    extract_bus_stations_for_buffering,
    translate_to_motis_one_to_all_request,
)
from goatlib.routing.schemas.catchment_area_transit import (
    TransitCatchmentAreaRequest,
    TransitCatchmentAreaStartingPoints,
    TransitCatchmentAreaTravelTimeCost,
    TransitMode,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_request() -> TransitCatchmentAreaRequest:
    """Fixture providing a sample transit catchment area request for bus station testing."""
    return TransitCatchmentAreaRequest(
        starting_points=TransitCatchmentAreaStartingPoints(
            latitude=[48.1351],
            longitude=[11.582],  # Munich city center
        ),
        transit_modes=[TransitMode.bus],
        travel_cost=TransitCatchmentAreaTravelTimeCost(
            max_traveltime=20,  # 20 minutes max travel time
            cutoffs=[10, 20],  # 10 and 20 minute cutoffs
        ),
    )


@pytest.fixture
def buffer_configurations() -> List[Dict[str, Any]]:
    """Fixture providing different buffer configurations for testing."""
    return [
        {
            "name": "walking_access",
            "distances": [200, 400, 600],
            "description": "Walking access zones (200m, 400m, 600m)",
        },
        {
            "name": "cycling_access",
            "distances": [500, 1000, 1500],
            "description": "Cycling access zones (500m, 1km, 1.5km)",
        },
        {
            "name": "wheelchair_access",
            "distances": [100, 200, 300],
            "description": "Wheelchair accessible zones (100m, 200m, 300m)",
        },
    ]


@pytest.mark.asyncio
@pytest.mark.slow
async def test_bus_station_extraction(
    sample_request: TransitCatchmentAreaRequest,
) -> None:
    """Test extracting bus stations from MOTIS one-to-all response."""
    client = MotisServiceClient(use_fixtures=False)

    try:
        # Get MOTIS one-to-all response
        motis_request = translate_to_motis_one_to_all_request(sample_request)
        motis_response = await client.one_to_all(motis_request)

        # Extract bus stations for buffering
        bus_stations = extract_bus_stations_for_buffering(motis_response)

        # Assertions
        assert len(motis_response.get("all", [])) > 0, "Should have reachable locations"
        assert len(bus_stations) > 0, "Should extract at least some bus stations"

        # Validate station structure
        for station in bus_stations:
            assert "name" in station, "Station should have a name"
            assert "duration_minutes" in station, "Station should have duration"
            assert "coordinates" in station, "Station should have coordinates"
            assert isinstance(
                station["duration_minutes"], (int, float)
            ), "Duration should be numeric"
            assert station["duration_minutes"] >= 0, "Duration should be non-negative"
            assert (
                station["duration_minutes"] <= sample_request.travel_cost.max_traveltime
            ), "Duration should not exceed max travel time"

        logger.info(
            f"Extracted {len(bus_stations)} bus stations from {len(motis_response.get('all', []))} total locations"
        )

    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_buffer_creation(
    sample_request: TransitCatchmentAreaRequest,
    buffer_configurations: List[Dict[str, Any]],
) -> None:
    """Test creating buffer configurations for bus stations."""
    client = MotisServiceClient(use_fixtures=False)

    try:
        # Get bus stations
        motis_request = translate_to_motis_one_to_all_request(sample_request)
        motis_response = await client.one_to_all(motis_request)
        bus_stations = extract_bus_stations_for_buffering(motis_response)

        assert len(bus_stations) > 0, "Need bus stations to test buffer creation"

        results = []
        for config in buffer_configurations:
            # Create buffer parameters for this configuration
            buffer_result = create_bus_station_buffers(
                bus_stations,
                config["distances"],  # Just pass the distances directly
                dissolve=True,
                output_path=f"/tmp/{config['name']}_buffers.geojson",
            )

            # Assertions
            assert (
                buffer_result is not None
            ), f"Should create buffer result for {config['name']}"
            assert (
                buffer_result.distances == config["distances"]
            ), f"Distances should match for {config['name']}"
            assert len(buffer_result.distances) == len(
                config["distances"]
            ), f"Should have all distance values for {config['name']}"

            results.append(
                {
                    "config": config,
                    "buffer_params": buffer_result,
                    "stations_used": len(bus_stations),
                    "buffer_count": len(config["distances"]),
                }
            )

        # Validate overall results
        total_buffers = sum(r["buffer_count"] for r in results)
        total_stations = len(bus_stations)

        assert total_buffers > 0, "Should create at least some buffer zones"
        assert total_stations > 0, "Should have stations to buffer"
        assert len(results) == len(
            buffer_configurations
        ), "Should have results for all configurations"

        logger.info(
            f"Created {total_buffers} buffer zones for {total_stations} bus stations"
        )

    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_buffer_parameter_validation(
    sample_request: TransitCatchmentAreaRequest,
) -> None:
    """Test that created buffer parameters have valid structure and values."""
    client = MotisServiceClient(use_fixtures=False)

    try:
        # Get bus stations
        motis_request = translate_to_motis_one_to_all_request(sample_request)
        motis_response = await client.one_to_all(motis_request)
        bus_stations = extract_bus_stations_for_buffering(motis_response)

        if len(bus_stations) == 0:
            pytest.skip("No bus stations found for testing")

        # Test with a simple configuration
        test_distances = [200, 500, 1000]

        buffer_result = create_bus_station_buffers(
            bus_stations,
            test_distances,
            dissolve=True,
            output_path="/tmp/test_bus_station_buffers.geojson",
        )

        # Validate buffer parameters structure
        assert buffer_result is not None, "Should create buffer result"

        # Test buffer parameter attributes
        assert hasattr(buffer_result, "distances"), "Should have distances attribute"
        assert hasattr(buffer_result, "dissolve"), "Should have dissolve attribute"
        assert hasattr(buffer_result, "output_crs"), "Should have output_crs attribute"
        assert hasattr(buffer_result, "units"), "Should have units attribute"

        # Test buffer parameter values
        assert buffer_result.distances == test_distances, "Distances should match input"
        assert isinstance(buffer_result.dissolve, bool), "Dissolve should be boolean"
        assert buffer_result.output_crs is not None, "Should have output CRS"
        assert buffer_result.units is not None, "Should have units"

        logger.info(
            f"Buffer parameters validated successfully for {len(bus_stations)} stations"
        )

    finally:
        await client.close()


def test_buffer_configuration_examples() -> None:
    """Test that buffer configuration examples are properly structured."""
    examples = [
        {
            "title": "🚶 Walking Access Analysis",
            "description": "Analyze pedestrian access to transit stations",
            "distances": [200, 400, 600],
            "use_case": "Urban planning for pedestrian infrastructure",
        },
        {
            "title": "🚲 Cycling Access Zones",
            "description": "Define cycling catchment areas around stations",
            "distances": [500, 1000, 1500],
            "use_case": "Bike sharing system placement and planning",
        },
        {
            "title": "♿ Accessibility Analysis",
            "description": "Evaluate accessibility for mobility-impaired users",
            "distances": [100, 200, 300],
            "use_case": "ADA compliance and accessibility improvements",
        },
        {
            "title": "🏘️ Neighborhood Impact",
            "description": "Assess transit impact on surrounding areas",
            "distances": [300, 600, 1200],
            "use_case": "Transit-oriented development planning",
        },
    ]

    # Validate each example
    for example in examples:
        assert "title" in example, "Example should have a title"
        assert "description" in example, "Example should have a description"
        assert "distances" in example, "Example should have distances"
        assert "use_case" in example, "Example should have a use case"

        assert len(example["distances"]) > 0, "Should have at least one distance"
        assert all(
            d > 0 for d in example["distances"]
        ), "All distances should be positive"
        assert len(example["title"]) > 0, "Title should not be empty"
        assert len(example["description"]) > 0, "Description should not be empty"

    logger.info(f"Validated {len(examples)} buffer configuration examples")


async def demo_bus_station_buffers() -> List[Dict[str, Any]]:
    """Demonstrate creating buffers around bus stations from MOTIS one-to-all response.

    This function is kept for backward compatibility and demo purposes.
    Use the individual test functions for actual testing.
    """
    import asyncio
    from datetime import datetime

    logger.info("🚌 Bus Station Buffer Analysis Demo")

    # 1. Create a transit catchment area request
    request = TransitCatchmentAreaRequest(
        starting_points=TransitCatchmentAreaStartingPoints(
            latitude=[48.1351],
            longitude=[11.582],  # Munich city center
        ),
        transit_modes=[TransitMode.bus],
        travel_cost=TransitCatchmentAreaTravelTimeCost(
            max_traveltime=20,  # 20 minutes max travel time
            cutoffs=[10, 20],  # 10 and 20 minute cutoffs
        ),
    )

    client = MotisServiceClient(use_fixtures=False)

    try:
        # 2. Get MOTIS one-to-all response
        motis_request = translate_to_motis_one_to_all_request(request)
        motis_response = await client.one_to_all(motis_request)

        # 3. Extract bus stations for buffering
        bus_stations = extract_bus_stations_for_buffering(motis_response)

        # 4. Create different buffer configurations
        buffer_configs = [
            {
                "name": "walking_access",
                "distances": [200, 400, 600],
                "description": "Walking access zones (200m, 400m, 600m)",
            },
            {
                "name": "cycling_access",
                "distances": [500, 1000, 1500],
                "description": "Cycling access zones (500m, 1km, 1.5km)",
            },
            {
                "name": "wheelchair_access",
                "distances": [100, 200, 300],
                "description": "Wheelchair accessible zones (100m, 200m, 300m)",
            },
        ]

        results = []
        for config in buffer_configs:
            # Create buffer parameters for this configuration
            buffer_result = create_bus_station_buffers(
                bus_stations,
                config["distances"],  # Just pass the distances directly
                dissolve=True,
                output_path=f"/tmp/{config['name']}_buffers.geojson",
            )

            results.append(
                {
                    "config": config,
                    "buffer_params": buffer_result,
                    "stations_used": len(bus_stations),
                    "buffer_count": len(config["distances"]),
                }
            )

        # 5. Save analysis results
        output_file = "/app/packages/python/goatlib/tests/benchmarks/results/bus_station_buffer_analysis.json"
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "request_params": {
                "starting_point": [
                    request.starting_points.latitude[0],
                    request.starting_points.longitude[0],
                ],
                "transit_modes": [mode.value for mode in request.transit_modes],
                "max_travel_time": request.travel_cost.max_traveltime,
            },
            "stations_analysis": {
                "total_stations": len(bus_stations),
                "sample_stations": bus_stations[:3],  # First 3 as sample
                "travel_time_range": [
                    min(s["duration_minutes"] for s in bus_stations),
                    max(s["duration_minutes"] for s in bus_stations),
                ]
                if bus_stations
                else [0, 0],
            },
            "buffer_configurations": [
                {
                    "name": result["config"]["name"],
                    "distances": result["buffer_params"].distances,
                    "dissolve": result["buffer_params"].dissolve,
                    "output_path": result["buffer_params"].output_path,
                    "units": result["buffer_params"].units,
                }
                for result in results
                if result["buffer_params"]
            ],
        }

        with open(output_file, "w") as f:
            json.dump(analysis_results, f, indent=2)

        logger.info(f"Analysis results saved to: {output_file}")
        logger.info("Bus station buffer analysis complete!")

        return results

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return []
    finally:
        await client.close()


def show_buffer_usage_examples() -> None:
    """Show practical examples of how to use the buffer configurations."""
    examples = [
        {
            "title": "🚶 Walking Access Analysis",
            "description": "Analyze pedestrian access to transit stations",
            "distances": [200, 400, 600],
            "use_case": "Urban planning for pedestrian infrastructure",
        },
        {
            "title": "🚲 Cycling Access Zones",
            "description": "Define cycling catchment areas around stations",
            "distances": [500, 1000, 1500],
            "use_case": "Bike sharing system placement and planning",
        },
        {
            "title": "♿ Accessibility Analysis",
            "description": "Evaluate accessibility for mobility-impaired users",
            "distances": [100, 200, 300],
            "use_case": "ADA compliance and accessibility improvements",
        },
        {
            "title": "🏘️ Neighborhood Impact",
            "description": "Assess transit impact on surrounding areas",
            "distances": [300, 600, 1200],
            "use_case": "Transit-oriented development planning",
        },
    ]

    for example in examples:
        logger.info(f"{example['title']}")
        logger.info(f"  📝 {example['description']}")
        logger.info(f"  📏 Distances: {example['distances']} meters")
        logger.info(f"  🎯 Use case: {example['use_case']}")

    logger.info(
        "💡 TIP: Combine multiple buffer configurations to create comprehensive accessibility analyses!"
    )


# Demo function can be run independently for development/debugging
if __name__ == "__main__":
    import asyncio

    logger.info("🚌 Starting Bus Station Buffer Analysis Demo")
    show_buffer_usage_examples()
    asyncio.run(demo_bus_station_buffers())
