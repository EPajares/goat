import math
from pathlib import Path

import pytest
from goatlib.analysis.heatmap.closest_average import HeatmapClosestAverageTool
from goatlib.analysis.heatmap.connectivity import HeatmapConnectivityTool
from goatlib.analysis.heatmap.gravity import HeatmapGravityTool
from goatlib.analysis.schemas.heatmap import (
    HeatmapClosestAverageParams,
    HeatmapConnectivityParams,
    HeatmapGravityParams,
    ImpedanceFunction,
    OpportunityClosestAverage,
    OpportunityGravity,
)


@pytest.mark.parametrize(
    "imp_func, expected_fn",
    [
        (
            ImpedanceFunction.linear,
            lambda cost, max_cost, sens, max_sens: (1 - cost / max_cost),
        ),
        (
            ImpedanceFunction.exponential,
            lambda cost, max_cost, sens, max_sens: math.exp(
                -(sens / max_sens) * (cost / max_cost)
            ),
        ),
        (
            ImpedanceFunction.gaussian,
            lambda cost, max_cost, sens, max_sens: math.exp(
                -((cost / max_cost) ** 2) / (sens / max_sens)
            ),
        ),
        (
            ImpedanceFunction.power,
            lambda cost, max_cost, sens, max_sens: (cost / max_cost)
            ** (-(sens / max_sens)),
        ),
    ],
)
def test_impedance_formulas(imp_func: ImpedanceFunction, expected_fn: callable) -> None:
    tool = HeatmapGravityTool()

    # Define OD matrix   (orig -> dest)
    tool.con.execute("""
        CREATE TABLE filtered_matrix AS
        SELECT 1 AS orig_id, 100 AS dest_id, 10 AS cost
        UNION ALL SELECT 2, 100, 20
        UNION ALL SELECT 1, 200, 15
        UNION ALL SELECT 2, 200, 25
    """)

    # Two opportunity destinations
    tool.con.execute("""
        CREATE TABLE opportunity_potentials_unified AS
        SELECT 100 AS dest_id, 30 AS test_max_cost, 1.0 AS test_potential, 300000.0 AS test_sens
        UNION ALL SELECT 200, 30, 2.0, 300000.0
    """)

    result_table = tool._compute_gravity_accessibility(
        "filtered_matrix",
        "opportunity_potentials_unified",
        [("fake", "test")],
        imp_func,
        300000.0,
    )

    df = tool.con.execute(f"SELECT * FROM {result_table}").fetchdf()

    # Compute expected accessibility for both destinations
    expected_dest_100 = (
        expected_fn(10, 30, 300000, 300000) * 1.0
        + expected_fn(20, 30, 300000, 300000) * 1.0
    )
    expected_dest_200 = (
        expected_fn(15, 30, 300000, 300000) * 2.0
        + expected_fn(25, 30, 300000, 300000) * 2.0
    )

    total_expected = expected_dest_100 + expected_dest_200

    assert "total_accessibility" in df.columns
    assert pytest.approx(df["total_accessibility"].sum(), rel=1e-3) == total_expected


def test_closest_average_computation() -> None:
    """Test the closest average computation logic in isolation."""
    tool = HeatmapClosestAverageTool()

    # OD matrix (orig_id, dest_id, cost)
    tool.con.execute("""
        CREATE TABLE filtered_matrix AS
        SELECT 1 AS orig_id, 100 AS dest_id, 10 AS cost
        UNION ALL SELECT 1, 200, 20
        UNION ALL SELECT 2, 100, 15
        UNION ALL SELECT 2, 200, 25
    """)

    # Unified opportunities: both have max_cost = 30, n_destinations = 1
    tool.con.execute("""
        CREATE TABLE opportunity_closest_avg_unified AS
        SELECT 100 AS dest_id, 30 AS test_max_cost, 1 AS test_n_dest
        UNION ALL SELECT 200, 30, 1
    """)

    std_tables = [("dummy", "test")]

    result_table = tool._compute_closest_average(
        "filtered_matrix", "opportunity_closest_avg_unified", std_tables
    )

    df = tool.con.execute(f"SELECT * FROM {result_table}").fetchdf()

    # Expected: average of closest 1 destination
    # Origin 1: closest = 10 → accessibility = 10
    # Origin 2: closest = 15 → accessibility = 15
    assert pytest.approx(df.loc[df.h3_index == 1, "test_accessibility"].iloc[0]) == 10
    assert pytest.approx(df.loc[df.h3_index == 2, "test_accessibility"].iloc[0]) == 15
    assert "total_accessibility" in df.columns


def test_connectivity_computation() -> None:
    tool = HeatmapConnectivityTool()

    # OD matrix: two origins, two destinations
    tool.con.execute("""
        CREATE TABLE filtered_matrix AS
        SELECT 1 AS orig_id, 10 AS dest_id, 5 AS cost
        UNION ALL SELECT 2, 10, 15
        UNION ALL SELECT 1, 20, 25
        UNION ALL SELECT 2, 20, 35
    """)

    # We’ll patch h3_cell_area to a constant to simplify verification
    tool.con.execute("CREATE OR REPLACE MACRO h3_cell_area(x, unit) AS 1000.0;")

    result_table = tool._compute_connectivity_scores(
        "filtered_matrix", 30, "connectivity_test"
    )

    df = tool.con.execute(f"SELECT * FROM {result_table}").fetchdf()

    # Expect: only destinations with cost <= 30 counted
    # reachable rows: (1,10), (2,10), (1,20)
    # So each dest_id (10, 20) → sum(area) per dest
    # dest 10: 2 * 1000 = 2000
    # dest 20: 1 * 1000 = 1000
    expected = {10: 2000, 20: 1000}
    for _, row in df.iterrows():
        assert pytest.approx(row.accessibility, rel=1e-6) == expected[row.h3_index]


@pytest.mark.parametrize(
    "imp_func",
    [
        ImpedanceFunction.linear,
        ImpedanceFunction.exponential,
        ImpedanceFunction.gaussian,
        ImpedanceFunction.power,
    ],
)
def test_gravity_tool_computes_expected_values(imp_func: ImpedanceFunction) -> None:
    tool = HeatmapGravityTool()

    # Create OD matrix: two origins (1, 2), two destinations (10, 20)
    tool.con.execute("""
        CREATE TABLE filtered_matrix AS
        SELECT 1 AS orig_id, 10 AS dest_id, 10 AS cost
        UNION ALL SELECT 2, 10, 20
        UNION ALL SELECT 1, 20, 15
        UNION ALL SELECT 2, 20, 25
    """)

    # Create opportunity table with known potentials
    tool.con.execute("""
        CREATE TABLE opportunity_potentials_unified AS
        SELECT 10 AS dest_id, 30 AS test_max_cost, 1.0 AS test_potential, 300000.0 AS test_sens
        UNION ALL SELECT 20, 30, 2.0, 300000.0
    """)

    # Compute accessibility
    result_table = tool._compute_gravity_accessibility(
        "filtered_matrix",
        "opportunity_potentials_unified",
        [("fake", "test")],
        imp_func,
        300000.0,
    )

    df = tool.con.execute(f"SELECT * FROM {result_table}").fetchdf()

    # Compute expected by hand for origin 1 and 2
    def impedance(
        cost: float,
        max_cost: float,
        sens: float,
        max_sens: float,
        imp_func: ImpedanceFunction,
    ) -> float:
        if imp_func == ImpedanceFunction.linear:
            return 1 - cost / max_cost
        elif imp_func == ImpedanceFunction.exponential:
            return math.exp(-(sens / max_sens) * (cost / max_cost))
        elif imp_func == ImpedanceFunction.gaussian:
            return math.exp(-((cost / max_cost) ** 2) / (sens / max_sens))
        elif imp_func == ImpedanceFunction.power:
            return (cost / max_cost) ** (-(sens / max_sens))
        else:
            raise ValueError(imp_func)

    def accessibility(orig_id: int) -> list[tuple[int, float, float]]:
        rows = [
            (10, 10 if orig_id == 1 else 20, 1.0),
            (20, 15 if orig_id == 1 else 25, 2.0),
        ]
        return sum(
            impedance(cost, 30, 300000, 300000, imp_func) * pot
            for dest, cost, pot in rows
        )

    expected1 = accessibility(1)
    expected2 = accessibility(2)

    assert (
        pytest.approx(df.loc[df.h3_index == 1, "total_accessibility"].iloc[0], rel=1e-6)
        == expected1
    )
    assert (
        pytest.approx(df.loc[df.h3_index == 2, "total_accessibility"].iloc[0], rel=1e-6)
        == expected2
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
        od_column_map={
            "cost": "traveltime",
            "orig_id": "orig_id",
            "dest_id": "dest_id",
        },
        output_path=str(work_dir / "heatmap_gravity.parquet"),
        impedance="linear",
        opportunities=[
            OpportunityGravity(
                input_path=str(data_root / "analysis" / "de_weihnachsmaerkte_25.gpkg"),
                name="weihnachsmaerkte_25",
                potential_constant=1.0,
                sensitivity=300000.0,
                max_cost=30,
            ),
        ],
    )

    # Run the heatmap gravity analysis tool
    tool = HeatmapGravityTool()
    path = tool.run(params)

    # Basic assertions on output
    assert path.exists()


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
        od_column_map={
            "cost": "traveltime",
            "orig_id": "orig_id",
            "dest_id": "dest_id",
        },
        output_path=str(work_dir / "heatmap_closest_average.parquet"),
        opportunities=[
            OpportunityClosestAverage(
                input_path=str(data_root / "analysis" / "de_weihnachsmaerkte_25.gpkg"),
                name="weihnachsmaerkte_25",
                max_cost=20,
                n_destinations=3,
            ),
        ],
    )

    # Run the heatmap closest average analysis tool
    tool = HeatmapClosestAverageTool()
    path = tool.run(params)

    # Basic assertions on output
    assert path.exists()


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
        od_column_map={
            "cost": "traveltime",
            "orig_id": "orig_id",
            "dest_id": "dest_id",
        },
        output_path=str(work_dir / "heatmap_connectivity.parquet"),
        max_cost=20,
        reference_area_path=str(data_root / "analysis" / "munich_districts.geojson"),
    )

    # Run the heatmap connectivity analysis tool
    tool = HeatmapConnectivityTool()
    path = tool.run(params)

    # Basic assertions on output
    assert path.exists()
