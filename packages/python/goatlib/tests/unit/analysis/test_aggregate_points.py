"""Unit tests for Aggregate Points Tool.

Tests aggregation of point features onto polygons and H3 grids
with various statistics operations.
"""

from pathlib import Path

import duckdb
import pytest

from goatlib.analysis.geoanalysis.aggregate_points import AggregatePointsTool
from goatlib.analysis.schemas.aggregate import (
    AggregatePointsParams,
    AggregationAreaType,
)
from goatlib.analysis.schemas.base import (
    FieldStatistic,
    StatisticOperation,
)


# Test data paths
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "vector"
POINTS_WITH_CATEGORY = str(TEST_DATA_DIR / "points_with_category.parquet")
ZIPCODE_POLYGON = str(TEST_DATA_DIR / "zipcode_polygon.parquet")


class TestAggregatePointsPolygon:
    """Tests for polygon-based point aggregation."""

    def test_aggregate_points_sum(self, tmp_path: Path) -> None:
        """Test aggregating points with SUM operation."""
        output_path = str(tmp_path / "aggregate_sum.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.sum,
                field="value",
            ),
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        # Verify output file was created
        assert len(results) == 1
        assert Path(output_path).exists()

        # Verify results
        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Should have 10 polygons (zipcodes)
        assert len(df) == 10
        # Should have sum_value column
        assert "sum_value" in df.columns
        # All sum values should be >= 0
        assert (df["sum_value"] >= 0).all()

    def test_aggregate_points_count(self, tmp_path: Path) -> None:
        """Test aggregating points with COUNT operation."""
        output_path = str(tmp_path / "aggregate_count.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.count,
            ),
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1
        assert Path(output_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        assert len(df) == 10
        assert "count" in df.columns
        # Total count should equal source point count (550)
        assert df["count"].sum() <= 550  # Some points may not fall in any polygon

    def test_aggregate_points_mean(self, tmp_path: Path) -> None:
        """Test aggregating points with MEAN operation."""
        output_path = str(tmp_path / "aggregate_mean.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.mean,
                field="value",
            ),
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        assert len(df) == 10
        assert "mean_value" in df.columns

    def test_aggregate_points_min_max(self, tmp_path: Path) -> None:
        """Test aggregating points with MIN and MAX operations."""
        output_path_min = str(tmp_path / "aggregate_min.parquet")
        output_path_max = str(tmp_path / "aggregate_max.parquet")

        # Test MIN
        params_min = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.min,
                field="value",
            ),
            output_path=output_path_min,
        )

        tool = AggregatePointsTool()
        tool.run(params_min)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df_min = con.execute(
            f"SELECT * FROM read_parquet('{output_path_min}')"
        ).fetchdf()

        assert "min_value" in df_min.columns

        # Test MAX
        params_max = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.max,
                field="value",
            ),
            output_path=output_path_max,
        )

        tool = AggregatePointsTool()
        tool.run(params_max)

        df_max = con.execute(
            f"SELECT * FROM read_parquet('{output_path_max}')"
        ).fetchdf()
        con.close()

        assert "max_value" in df_max.columns

    def test_aggregate_points_with_group_by(self, tmp_path: Path) -> None:
        """Test aggregating points with GROUP BY on category field."""
        output_path = str(tmp_path / "aggregate_grouped.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.sum,
                field="value",
            ),
            group_by_field=["category"],
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        assert len(df) == 10
        # Should have total sum and grouped sum columns
        assert "sum_value" in df.columns
        assert "sum_value_grouped" in df.columns

    def test_aggregate_preserves_area_attributes(self, tmp_path: Path) -> None:
        """Test that aggregation preserves area layer attributes."""
        output_path = str(tmp_path / "aggregate_attrs.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.count,
            ),
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        tool.run(params)

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Original zipcode_polygon has: plz, note, zipcode columns
        assert "plz" in df.columns
        assert "zipcode" in df.columns
        assert "geom" in df.columns


class TestAggregatePointsH3:
    """Tests for H3 grid-based point aggregation."""

    def test_aggregate_points_h3_sum(self, tmp_path: Path) -> None:
        """Test aggregating points to H3 grid with SUM."""
        output_path = str(tmp_path / "aggregate_h3_sum.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.h3_grid,
            h3_resolution=8,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.sum,
                field="value",
            ),
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1
        assert Path(output_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Should have H3 index column and sum column
        assert "h3_8" in df.columns
        assert "sum_value" in df.columns
        assert "geom" in df.columns
        # Should have some H3 cells
        assert len(df) > 0

    def test_aggregate_points_h3_count(self, tmp_path: Path) -> None:
        """Test aggregating points to H3 grid with COUNT."""
        output_path = str(tmp_path / "aggregate_h3_count.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.h3_grid,
            h3_resolution=6,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.count,
            ),
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        assert "h3_6" in df.columns
        assert "count" in df.columns
        # Total count should equal source points (550)
        assert df["count"].sum() == 550

    def test_aggregate_points_h3_with_group_by(self, tmp_path: Path) -> None:
        """Test aggregating points to H3 grid with GROUP BY."""
        output_path = str(tmp_path / "aggregate_h3_grouped.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.h3_grid,
            h3_resolution=7,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.sum,
                field="value",
            ),
            group_by_field=["category"],
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        assert "h3_7" in df.columns
        assert "sum_value" in df.columns
        assert "sum_value_grouped" in df.columns

    def test_aggregate_points_h3_different_resolutions(self, tmp_path: Path) -> None:
        """Test H3 aggregation at different resolutions."""
        for resolution in [5, 8, 10]:
            output_path = str(tmp_path / f"aggregate_h3_res{resolution}.parquet")

            params = AggregatePointsParams(
                source_path=POINTS_WITH_CATEGORY,
                area_type=AggregationAreaType.h3_grid,
                h3_resolution=resolution,
                column_statistics=FieldStatistic(
                    operation=StatisticOperation.count,
                ),
                output_path=output_path,
            )

            tool = AggregatePointsTool()
            tool.run(params)

            con = duckdb.connect()
            con.execute("INSTALL spatial; LOAD spatial;")
            df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
            con.close()

            assert f"h3_{resolution}" in df.columns
            # Higher resolution = more cells
            assert len(df) > 0


class TestAggregatePointsEdgeCases:
    """Edge case tests for aggregate points tool."""

    def test_no_points_in_polygon(self, tmp_path: Path) -> None:
        """Test behavior when no points fall within polygons."""
        # Create a polygon that doesn't contain any points
        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        empty_polygon_path = str(tmp_path / "empty_polygon.parquet")
        con.execute(f"""
            COPY (
                SELECT
                    1 AS id,
                    ST_GeomFromText('POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))') AS geom
            ) TO '{empty_polygon_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
        con.close()

        output_path = str(tmp_path / "aggregate_empty.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=empty_polygon_path,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.count,
            ),
            output_path=output_path,
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        df = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchdf()
        con.close()

        # Should have the polygon with count = 0
        assert len(df) == 1
        assert df["count"].iloc[0] == 0

    def test_output_path_auto_generated(self, tmp_path: Path) -> None:
        """Test that output path is auto-generated when not specified."""
        # Copy source to tmp_path so output goes there
        source_in_tmp = str(tmp_path / "source_points.parquet")

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute(
            f"COPY (SELECT * FROM read_parquet('{POINTS_WITH_CATEGORY}')) "
            f"TO '{source_in_tmp}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        con.close()

        params = AggregatePointsParams(
            source_path=source_in_tmp,
            area_type=AggregationAreaType.h3_grid,
            h3_resolution=6,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.count,
            ),
            # No output_path specified
        )

        tool = AggregatePointsTool()
        results = tool.run(params)

        assert len(results) == 1
        output_path = results[0][0]
        assert output_path.exists()
        assert "aggregated" in output_path.name

    def test_context_manager_cleanup(self, tmp_path: Path) -> None:
        """Test that context manager properly cleans up resources."""
        output_path = str(tmp_path / "aggregate_ctx.parquet")

        params = AggregatePointsParams(
            source_path=POINTS_WITH_CATEGORY,
            area_type=AggregationAreaType.polygon,
            area_layer_path=ZIPCODE_POLYGON,
            column_statistics=FieldStatistic(
                operation=StatisticOperation.count,
            ),
            output_path=output_path,
        )

        with AggregatePointsTool() as tool:
            results = tool.run(params)
            assert len(results) == 1

        # After context exit, connection should be closed
        # (tool.con will be None or closed)
        assert Path(output_path).exists()
