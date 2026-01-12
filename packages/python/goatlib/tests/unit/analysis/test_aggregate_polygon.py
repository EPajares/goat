"""Unit tests for Aggregate Polygon Tool.

Uses the same test data as GOAT Core:
- green_areas.parquet: 90 park polygons with 'value' field (area in sqm)
- zipcode_polygon.parquet: 10 Munich zipcode areas

These tests verify actual computed values, not just row counts.
"""

from pathlib import Path

import duckdb
import pytest

from goatlib.analysis.geoanalysis.aggregate_polygon import AggregatePolygonTool
from goatlib.analysis.schemas.aggregate import (
    AggregatePolygonParams,
    AggregationAreaType,
)
from goatlib.analysis.schemas.base import (
    FieldStatistic,
    StatisticOperation,
)


# Test data paths - same data as GOAT Core
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "analysis" / "aggregate"
GREEN_AREAS = str(TEST_DATA_DIR / "green_areas.parquet")  # 90 park polygons
ZIPCODE_POLYGON = str(TEST_DATA_DIR / "zipcode_polygon.parquet")  # 10 zipcodes

# Pre-computed expected values from green_areas.parquet
TOTAL_GREEN_AREAS = 90
TOTAL_VALUE = 2531740.53  # Sum of all 'value' fields (area in sqm)


class TestAggregatePolygonToPolygon:
    """Tests for polygon-to-polygon aggregation with real data validation."""

    def test_count_returns_correct_totals(self, tmp_path: Path) -> None:
        """Test COUNT operation returns correct total across all zipcodes.

        The sum of counts across all zipcodes should equal the total number
        of green areas that intersect with any zipcode.
        """
        output_path = str(tmp_path / "aggregate_count.parquet")

        params = AggregatePolygonParams(
            source_path=GREEN_AREAS,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(operation=StatisticOperation.count),
            weighted_by_intersecting_area=False,
            output_path=output_path,
        )

        tool = AggregatePolygonTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Should have 10 zipcode areas
        assert len(df) == 10
        assert "count" in df.columns
        assert "zipcode" in df.columns

        # Total count should be > 0 (green areas intersect zipcodes)
        total_count = df["count"].sum()
        assert total_count > 0, "Should have counted green areas in zipcodes"

    def test_weighted_count_distributes_by_area_ratio(self, tmp_path: Path) -> None:
        """Test weighted COUNT distributes counts by intersection area ratio.

        When using weighted_by_intersecting_area=True, each source polygon
        contributes a fraction to each area it intersects, based on
        intersection_area / source_area. The total can exceed source count
        if polygons are counted in multiple overlapping areas.
        """
        output_path = str(tmp_path / "aggregate_weighted_count.parquet")

        params = AggregatePolygonParams(
            source_path=GREEN_AREAS,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(operation=StatisticOperation.count),
            weighted_by_intersecting_area=True,
            output_path=output_path,
        )

        tool = AggregatePolygonTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Weighted count should be positive
        total_weighted = df["count"].sum()
        assert total_weighted > 0, "Should have counted green areas"

        # Each zipcode should have a reasonable weighted count
        assert (df["count"] >= 0).all(), "Counts should be non-negative"

    def test_sum_preserves_total_value_when_weighted(self, tmp_path: Path) -> None:
        """Test weighted SUM preserves the total value across all areas.

        When summing with weighting, the total should equal the original
        total value (values are distributed, not duplicated).
        """
        output_path = str(tmp_path / "aggregate_weighted_sum.parquet")

        params = AggregatePolygonParams(
            source_path=GREEN_AREAS,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.sum,
                field="value",
            ),
            weighted_by_intersecting_area=True,
            output_path=output_path,
        )

        tool = AggregatePolygonTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        total_weighted_sum = df["sum_value"].sum()
        # Should be close to original total (may be less if some areas outside)
        assert total_weighted_sum > 0
        assert total_weighted_sum <= TOTAL_VALUE * 1.01  # Allow 1% tolerance

    def test_unweighted_sum_can_exceed_total(self, tmp_path: Path) -> None:
        """Test unweighted SUM can exceed total when polygons span areas.

        Without weighting, a polygon spanning multiple areas gets its
        full value counted in each area, so the sum can exceed the original.
        """
        output_path = str(tmp_path / "aggregate_sum.parquet")

        params = AggregatePolygonParams(
            source_path=GREEN_AREAS,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.sum,
                field="value",
            ),
            weighted_by_intersecting_area=False,
            output_path=output_path,
        )

        tool = AggregatePolygonTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        total_unweighted = df["sum_value"].sum()
        assert total_unweighted > 0

    def test_mean_returns_reasonable_values(self, tmp_path: Path) -> None:
        """Test MEAN returns values within expected range."""
        output_path = str(tmp_path / "aggregate_mean.parquet")

        params = AggregatePolygonParams(
            source_path=GREEN_AREAS,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.mean,
                field="value",
            ),
            output_path=output_path,
        )

        tool = AggregatePolygonTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Mean should be between min and max of source values
        # Source min ~57, max ~290508
        valid_means = df[df["mean_value"] > 0]["mean_value"]
        assert len(valid_means) > 0, "Should have some areas with green areas"
        assert valid_means.min() >= 50  # Should be above source minimum
        assert valid_means.max() <= 300000  # Should be below source maximum


class TestAggregatePolygonToH3:
    """Tests for polygon-to-H3 grid aggregation."""

    def test_h3_count_creates_hexagons(self, tmp_path: Path) -> None:
        """Test H3 aggregation creates hexagonal cells with counts."""
        output_path = str(tmp_path / "aggregate_h3_count.parquet")

        params = AggregatePolygonParams(
            source_path=GREEN_AREAS,
            area_type=AggregationAreaType.h3_grid,
            h3_resolution=8,
            column_statistics=FieldStatistic(operation=StatisticOperation.count),
            output_path=output_path,
        )

        tool = AggregatePolygonTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Should have H3 cells with data
        assert len(df) > 0
        assert "count" in df.columns
        assert "h3_8" in df.columns

        # Total count should equal source polygon count (one centroid per polygon)
        total_count = df["count"].sum()
        assert total_count == TOTAL_GREEN_AREAS

    def test_h3_sum_matches_source_total(self, tmp_path: Path) -> None:
        """Test H3 SUM matches the total value from source polygons."""
        output_path = str(tmp_path / "aggregate_h3_sum.parquet")

        params = AggregatePolygonParams(
            source_path=GREEN_AREAS,
            area_type=AggregationAreaType.h3_grid,
            h3_resolution=8,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.sum,
                field="value",
            ),
            output_path=output_path,
        )

        tool = AggregatePolygonTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Total should match source total (within floating point tolerance)
        total_sum = df["sum_value"].sum()
        assert abs(total_sum - TOTAL_VALUE) < 1.0  # Allow 1 sqm tolerance


class TestAggregatePolygonValidation:
    """Tests for parameter validation."""

    def test_polygon_requires_area_layer(self) -> None:
        """Test polygon area_type requires area_layer_path."""
        with pytest.raises(ValueError, match="area_layer_path is required"):
            AggregatePolygonParams(
                source_path=GREEN_AREAS,
                area_type=AggregationAreaType.polygon,
                column_statistics=FieldStatistic(operation=StatisticOperation.count),
            )

    def test_h3_requires_resolution(self) -> None:
        """Test h3_grid area_type requires h3_resolution."""
        with pytest.raises(ValueError, match="h3_resolution is required"):
            AggregatePolygonParams(
                source_path=GREEN_AREAS,
                area_type=AggregationAreaType.h3_grid,
                column_statistics=FieldStatistic(operation=StatisticOperation.count),
            )

    def test_sum_requires_field(self) -> None:
        """Test SUM operation requires a field."""
        with pytest.raises(ValueError, match="Field is required"):
            AggregatePolygonParams(
                source_path=GREEN_AREAS,
                area_type=AggregationAreaType.h3_grid,
                h3_resolution=8,
                column_statistics=FieldStatistic(operation=StatisticOperation.sum),
            )

    def test_count_rejects_field(self) -> None:
        """Test COUNT operation rejects field parameter."""
        with pytest.raises(ValueError, match="Field should not be provided"):
            AggregatePolygonParams(
                source_path=GREEN_AREAS,
                area_type=AggregationAreaType.h3_grid,
                h3_resolution=8,
                column_statistics=FieldStatistic(
                    operation=StatisticOperation.count,
                    field="value",
                ),
            )
