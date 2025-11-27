import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

import geopandas as gpd
import pytest
from goatlib.analysis.schemas.vector import BufferParams
from goatlib.analysis.vector.buffer import BufferTool
from goatlib.routing.adapters.motis.motis_client import MotisServiceClient
from goatlib.routing.adapters.motis.motis_converters import (
    extract_bus_stations_for_buffering,
    translate_to_motis_one_to_all_request,
)
from goatlib.routing.schemas.catchment_area_transit import (
    TransitCatchmentAreaRequest,
    TransitCatchmentAreaStartingPoints,
    TransitCatchmentAreaTravelTimeCost,
    TransitMode,
)
from shapely.geometry import Point

logger = logging.getLogger(__name__)

# ==========================================
#  Data Preparation Helper
# ==========================================


def create_pt_buffer_params(
    reachable_locations: List[Dict[str, Any]],
    config: Dict[str, Any],
    work_dir: Path,
) -> BufferParams:
    """
    Converts dictionary list to Parquet, then returns BufferParams.
    """
    # 1. Prepare Output Paths
    input_path = work_dir / "motis_stations_input.parquet"
    output_path = work_dir / "motis_stations_buffered.parquet"

    # 2. Convert MOTIS list to GeoDataFrame
    gdf_data = []
    for station in reachable_locations:
        coords = station["coordinates"]  # [lon, lat]
        gdf_data.append(
            {
                "name": station.get("name", "Unknown"),
                "duration_minutes": station.get("duration_minutes", 0),
                "stop_id": station.get("stop_id", ""),
                "geometry": Point(coords[0], coords[1]),
            }
        )

    gdf = gpd.GeoDataFrame(gdf_data, crs="EPSG:4326")

    # 3. Save Input Parquet (Required by BufferTool)
    gdf.to_parquet(input_path)

    # 4. Configure Tool
    return BufferParams(
        input_path=str(input_path),
        output_path=str(output_path),
        distances=config["distances"],  # e.g. [200, 400, 600]
        units="meters",
        dissolve=True,  # Merge overlapping circles into one shape
        num_triangles=8,
        cap_style="CAP_ROUND",
        join_style="JOIN_ROUND",
        output_crs="EPSG:4326",
        output_name="pt_access_buffers",
    )


# ==========================================
#  Configuration & Test
# ==========================================


@pytest.fixture
def sample_request() -> TransitCatchmentAreaRequest:
    """Munich City Center Request."""
    return TransitCatchmentAreaRequest(
        starting_points=TransitCatchmentAreaStartingPoints(
            latitude=[48.1351],
            longitude=[11.582],  # Munich center
        ),
        transit_modes=[
            TransitMode.bus,
            TransitMode.subway,
            TransitMode.tram,
            TransitMode.rail,
        ],
        travel_cost=TransitCatchmentAreaTravelTimeCost(max_traveltime=60, cutoffs=[60]),
    )


@pytest.fixture
def pt_buffer_config() -> Dict[str, Any]:
    """Single configuration for Public Transport Station Access."""
    return {
        "name": "pt_station_walk",
        "title": "🚌 Public Transport Access",
        "distances": [200, 400, 600],  # Walking distance from stations
        "description": "Buffer zones around reachable stations",
        "use_case": "Transit Coverage Analysis",
    }


@pytest.mark.asyncio
async def test_public_transport_buffer_pipeline(
    sample_request: TransitCatchmentAreaRequest,
    pt_buffer_config: Dict[str, Any],
    buffered_stations_dir: Path,
) -> None:
    """
    1. Fetch MOTIS reachable stations.
    2. Buffer them (200/400/600m).
    3. Save Parquet.
    """

    buffered_stations_dir.mkdir(exist_ok=True)

    # Fetch MOTIS Data
    client = MotisServiceClient(use_fixtures=False)
    try:
        motis_req = translate_to_motis_one_to_all_request(sample_request)
        logger.info("🚀 Requesting MOTIS One-to-All...")
        motis_response = await client.one_to_all(motis_req)
    finally:
        await client.close()

    bus_stations = extract_bus_stations_for_buffering(motis_response)
    assert len(bus_stations) > 0, "No stations found. Cannot perform buffering."
    logger.info(f"Found {len(bus_stations)} reachable stations.")

    # Prepare & Buffer
    params = create_pt_buffer_params(
        reachable_locations=bus_stations,
        config=pt_buffer_config,
        work_dir=buffered_stations_dir,
    )

    logger.info("⚙️ Running BufferTool...")
    tool = BufferTool()
    results = tool.run(params)

    # D. Assertions & Visualization
    assert len(results) > 0
    output_file, _ = results[0]

    assert output_file.exists()
    assert output_file.suffix == ".parquet"


# ==========================================


@pytest.mark.asyncio
async def test_pipeline_performance(
    sample_request: TransitCatchmentAreaRequest,
    buffered_stations_dir: Path,
    pt_buffer_config: Dict[str, Any],
) -> None:
    """Simplified timing test for MOTIS -> Buffer pipeline."""

    buffered_stations_dir.mkdir(exist_ok=True)

    # Setup timing stats
    stats = {}
    t_start = time.perf_counter()

    # Phase 1: API Request
    logger.info("⏱️ Phase 1: MOTIS API Request")
    t_api = time.perf_counter()

    client = MotisServiceClient(use_fixtures=False)
    try:
        motis_req = translate_to_motis_one_to_all_request(sample_request)
        motis_response = await client.one_to_all(motis_req)
    finally:
        await client.close()

    stats["api_latency_sec"] = round(time.perf_counter() - t_api, 4)

    # Phase 2: Data Processing
    logger.info("⏱️ Phase 2: Data Processing")
    t_process = time.perf_counter()

    bus_stations = extract_bus_stations_for_buffering(motis_response)
    assert len(bus_stations) > 0, "No stations found for timing test"

    stats["processing_sec"] = round(time.perf_counter() - t_process, 4)

    # Phase 3: Buffer Creation
    logger.info("⏱️ Phase 3: Buffer Creation")
    t_buffer_setup = time.perf_counter()

    params = create_pt_buffer_params(
        reachable_locations=bus_stations,
        config=pt_buffer_config,
        work_dir=buffered_stations_dir,
    )

    stats["buffer_setup_sec"] = round(time.perf_counter() - t_buffer_setup, 4)

    # BufferTool execution timing
    t_buffer_run = time.perf_counter()
    tool = BufferTool()
    results = tool.run(params)
    stats["buffer_tool_run_sec"] = round(time.perf_counter() - t_buffer_run, 4)

    stats["buffering_total_sec"] = (
        stats["buffer_setup_sec"] + stats["buffer_tool_run_sec"]
    )
    stats["total_time_sec"] = round(time.perf_counter() - t_start, 4)
    stats["stations_processed"] = len(bus_stations)

    # Log results
    logger.info("🚀 Pipeline Performance Results:")
    logger.info(f"   API Request: {stats['api_latency_sec']}s")
    logger.info(f"   Processing: {stats['processing_sec']}s")
    logger.info(f"   Buffer Setup: {stats['buffer_setup_sec']}s")
    logger.info(f"   Buffer Tool Run: {stats['buffer_tool_run_sec']}s")
    logger.info(f"   Buffering Total: {stats['buffering_total_sec']}s")
    logger.info(f"   Total: {stats['total_time_sec']}s")
    logger.info(f"   Stations: {stats['stations_processed']}")

    # Save results to file
    output_dir = buffered_stations_dir / "benchmarks"
    output_dir.mkdir(exist_ok=True)

    # Save as JSON
    json_path = output_dir / "pipeline_performance.json"
    with open(json_path, "w") as f:
        json.dump(stats, f, indent=2)

    # Save as readable text log
    log_path = output_dir / "pipeline_performance.log"
    with open(log_path, "w") as f:
        f.write("Pipeline Performance Results:\n")
        f.write(f"API Request: {stats['api_latency_sec']}s\n")
        f.write(f"Processing: {stats['processing_sec']}s\n")
        f.write(f"Buffer Setup: {stats['buffer_setup_sec']}s\n")
        f.write(f"Buffer Tool Run: {stats['buffer_tool_run_sec']}s\n")
        f.write(f"Buffering Total: {stats['buffering_total_sec']}s\n")
        f.write(f"Total: {stats['total_time_sec']}s\n")
        f.write(f"Stations: {stats['stations_processed']}\n")

    logger.info("📁 Performance results saved to:")
    logger.info(f"   JSON: {json_path.absolute()}")
    logger.info(f"   Log: {log_path.absolute()}")

    # Assertions
    assert len(results) > 0
    assert results[0][0].exists()  # Output file exists
    assert stats["total_time_sec"] > 0
    assert stats["stations_processed"] > 0
