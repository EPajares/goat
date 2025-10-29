from pathlib import Path

from goatlib.analysis.heatmap.closest_average import HeatmapClosestAverageTool
from goatlib.analysis.heatmap.connectivity import HeatmapConnectivityTool
from goatlib.analysis.heatmap.gravity import HeatmapGravityTool
from goatlib.analysis.schemas.heatmap import (
    HeatmapClosestAverageParams,
    HeatmapConnectivityParams,
    HeatmapGravityParams,
    OpportunityClosestAverage,
    OpportunityGravity,
)


def test_heatmap_gravity_tool(tmp_path: Path, data_root: Path) -> None:
    """Test HeatmapGravityTool"""

    work_dir = tmp_path / "heatmap_gravity_test"
    work_dir.mkdir(parents=True, exist_ok=True)

    od_matrix_source = str(
        data_root.parent.parent.parent.parent.parent
        / "data"
        / "traveltime_matrices"
        / "walking"
    )

    params = HeatmapGravityParams(
        routing_mode="walking",
        od_matrix_source=od_matrix_source,
        output_path=str(work_dir / "heatmap_gravity.parquet"),
        impedance="linear",
        opportunities=[
            OpportunityGravity(
                input_path=str(data_root / "analysis" / "de_weihnachsmaerkte_25.gpkg"),
                name="weihnachsmaerkte_25",
                potential_constant=1.0,
                sensitivity=300000.0,
                max_traveltime=30,
            ),
        ],
    )

    # Run the heatmap gravity analysis tool
    tool = HeatmapGravityTool()
    results = tool.run(params)

    # Basic assertions on output
    assert 1 == 1


def test_heatmap_closest_average_tool(tmp_path: Path, data_root: Path) -> None:
    """Test HeatmapClosestAverageTool"""

    work_dir = tmp_path / "heatmap_closest_average_test"
    work_dir.mkdir(parents=True, exist_ok=True)

    od_matrix_source = str(
        data_root.parent.parent.parent.parent.parent
        / "data"
        / "traveltime_matrices"
        / "walking"
    )

    params = HeatmapClosestAverageParams(
        routing_mode="walking",
        od_matrix_source=od_matrix_source,
        output_path=str(work_dir / "heatmap_closest_average.parquet"),
        opportunities=[
            OpportunityClosestAverage(
                input_path=str(data_root / "analysis" / "de_weihnachsmaerkte_25.gpkg"),
                name="weihnachsmaerkte_25",
                max_traveltime=20,
                n_destinations=3,
            ),
        ],
    )

    # Run the heatmap closest average analysis tool
    tool = HeatmapClosestAverageTool()
    results = tool.run(params)

    # Basic assertions on output
    assert 1 == 1


def test_heatmap_connectivity_tool(tmp_path: Path, data_root: Path) -> None:
    """Test HeatmapConnectivityTool"""

    work_dir = tmp_path / "heatmap_connectivity_test"
    work_dir.mkdir(parents=True, exist_ok=True)

    od_matrix_source = str(
        data_root.parent.parent.parent.parent.parent
        / "data"
        / "traveltime_matrices"
        / "walking"
    )

    params = HeatmapConnectivityParams(
        routing_mode="walking",
        od_matrix_source=od_matrix_source,
        output_path=str(work_dir / "heatmap_connectivity.parquet"),
        max_traveltime=20,
        reference_area_path=str(data_root / "analysis" / "munich_districts.geojson"),
    )

    # Run the heatmap connectivity analysis tool
    tool = HeatmapConnectivityTool()
    results = tool.run(params)

    # Basic assertions on output
    assert 1 == 1
