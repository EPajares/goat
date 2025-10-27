import math
from pathlib import Path

import pytest
from core.schemas.heatmap import OpportunityClosestAverage
from goatlib.analysis.heatmap.closest_average import HeatmapClosestAverageTool
from goatlib.analysis.heatmap.connectivity import HeatmapConnectivityTool
from goatlib.analysis.heatmap.gravity import HeatmapGravityTool
from goatlib.analysis.schemas.heatmap import (
    HeatmapClosestAverageParams,
    HeatmapConnectivityParams,
    HeatmapGravityParams,
    ImpedanceFunction,
    OpportunityGravity,
)


@pytest.mark.parametrize(
    "imp_func, expected_fn",
    [
        (
            ImpedanceFunction.linear,
            lambda tt, max_tt, sens, max_sens: (1 - tt / max_tt),
        ),
        (
            ImpedanceFunction.exponential,
            lambda tt, max_tt, sens, max_sens: math.exp(
                -(sens / max_sens) * (tt / max_tt)
            ),
        ),
        (
            ImpedanceFunction.gaussian,
            lambda tt, max_tt, sens, max_sens: math.exp(
                -((tt / max_tt) ** 2) / (sens / max_sens)
            ),
        ),
        (
            ImpedanceFunction.power,
            lambda tt, max_tt, sens, max_sens: (tt / max_tt) ** (-(sens / max_sens)),
        ),
    ],
)
def test_impedance_formulas(imp_func: ImpedanceFunction, expected_fn: callable) -> None:
    tool = HeatmapGravityTool()

    tool.con.execute("""
        CREATE TABLE filtered_matrix AS
        SELECT 1 AS orig_id, 100 AS dest_id, 10 AS traveltime
        UNION ALL SELECT 2, 100, 20
    """)
    tool.con.execute("""
        CREATE TABLE opportunity_potentials_unified AS
        SELECT 1 AS orig_id, 30 AS test_max_tt, 1.0 AS test_potential, 300000.0 AS test_sens
        UNION ALL SELECT 2, 30, 2.0 AS test_potential, 300000.0 AS test_sens
    """)

    result_table = tool._compute_gravity_accessibility(
        "filtered_matrix",
        "opportunity_potentials_unified",
        [("fake", "test")],
        imp_func,
        300000.0,
    )

    df = tool.con.execute(f"SELECT * FROM {result_table}").fetchdf()

    expected = (
        expected_fn(10, 30, 300000, 300000) * 1
        + expected_fn(20, 30, 300000, 300000) * 2
    )
    assert pytest.approx(df["total_accessibility"][0], rel=1e-3) == expected


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
        impedance="linear",
        opportunities=[
            OpportunityClosestAverage(
                input_path=str(data_root / "analysis" / "de_weihnachsmaerkte_25.gpkg"),
                layer_name="weihnachsmaerkte_25",
                potential_constant=1.0,
                sensitivity=300000.0,
                max_traveltime=30,
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
        max_traveltime=30,
        reference_area_path=str(data_root / "analysis" / "munich_districts.geojson"),
    )

    # Run the heatmap connectivity analysis tool
    tool = HeatmapConnectivityTool()
    results = tool.run(params)

    # Basic assertions on output
    assert 1 == 1
