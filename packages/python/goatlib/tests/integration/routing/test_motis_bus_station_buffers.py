import json
import logging
import os
from pathlib import Path
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
async def test_buffer_creation(
    sample_request: TransitCatchmentAreaRequest,
    buffer_configurations: List[Dict[str, Any]],
    motis_response_json: Path,
    extracted_stations_json: Path,
    buffered_stations_dir: Path,
) -> None:
    """Test creating buffer configurations for bus stations."""
    client = MotisServiceClient(use_fixtures=False)

    try:
        # Get bus stations
        motis_request = translate_to_motis_one_to_all_request(sample_request)
        motis_response = await client.one_to_all(motis_request)

        # Save the raw MOTIS response to test data directory
        with open(motis_response_json, "w") as f:
            json.dump(motis_response, f, indent=2)

        bus_stations = extract_bus_stations_for_buffering(motis_response)

        # Save the extracted bus stations to test data directory
        with open(extracted_stations_json, "w") as f:
            json.dump(bus_stations, f, indent=2)

        assert len(bus_stations) > 0, "Need bus stations to test buffer creation"

        num_stations = len(bus_stations)
        origin_name = "munich_center"

        meaningful_input_path = (
            buffered_stations_dir
            / f"bus_stations_{origin_name}_{num_stations}stops.parquet"
        )
        meaningful_response_path = (
            buffered_stations_dir
            / f"motis_response_{origin_name}_{num_stations}stops.json"
        )
        meaningful_extracted_path = (
            buffered_stations_dir
            / f"extracted_stations_{origin_name}_{num_stations}stops.json"
        )

        with open(meaningful_response_path, "w") as f:
            json.dump(motis_response, f, indent=2)

        with open(meaningful_extracted_path, "w") as f:
            json.dump(bus_stations, f, indent=2)

        results = []
        for config in buffer_configurations:
            distances_str = "_".join(map(str, config["distances"]))
            meaningful_output_path = (
                buffered_stations_dir
                / f"bus_buffers_{origin_name}_{num_stations}stops_{config['name']}_{distances_str}m.geojson"
            )

            # Create buffer parameters for this configuration
            buffer_result = create_bus_station_buffers(
                bus_stations,
                config["distances"],
                dissolve=True,
                output_path=str(meaningful_output_path),
                input_path=str(meaningful_input_path),
                origin_name=f"Munich_Center_Test_{num_stations}stops",
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

            # Verify files exist
            assert os.path.exists(
                meaningful_response_path
            ), "MOTIS response should be saved with meaningful name"
            assert os.path.exists(
                meaningful_extracted_path
            ), "Extracted stations should be saved with meaningful name"
            assert os.path.exists(
                meaningful_input_path
            ), "Input parquet should exist with meaningful name"
            assert not os.path.exists(
                meaningful_output_path
            ), "Output buffer geometries should NOT exist (requires separate buffer processor)"

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
            f"✅ Created {total_buffers} buffer configuration objects for {total_stations} bus stations"
        )
        logger.info("📁 Input Files Created in Test Data Directory:")
        logger.info(f"   ✅ MOTIS response: {meaningful_response_path.name}")
        logger.info(f"   ✅ Extracted stations: {meaningful_extracted_path.name}")
        logger.info(f"   ✅ Bus stations parquet: {meaningful_input_path.name}")
        logger.info("📁 Configuration Objects Created:")
        logger.info(f"   ✅ BufferParams with {total_buffers} distance configurations")
        logger.info(f"📂 All files saved to: {buffered_stations_dir}")
        logger.info(
            "📝 Note: Buffer geometries require separate processing using the BufferParams configuration"
        )

    finally:
        await client.close()


@pytest.mark.asyncio
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
