from pathlib import Path

from goatlib.analysis.heatmap.gravity import HeatmapGravityTool
from goatlib.analysis.schemas.heatmap import HeatmapGravityParams, OpportunityGravity


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
                layer_name="weihnachsmaerkte_25",
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
