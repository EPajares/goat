"""Unit tests for statistics analysis functions.

These tests use an in-memory DuckDB database with test data to verify
the correctness of the statistics calculation functions.
"""

import duckdb
import pytest
from goatlib.analysis.statistics import (
    AreaOperation,
    ClassBreakMethod,
    SortOrder,
    calculate_area_statistics,
    calculate_class_breaks,
    calculate_extent,
    calculate_feature_count,
    calculate_unique_values,
)


@pytest.fixture
def duckdb_connection():
    """Create an in-memory DuckDB connection with spatial extension."""
    con = duckdb.connect(":memory:")
    con.execute("INSTALL spatial; LOAD spatial;")
    return con


@pytest.fixture
def sample_data_table(duckdb_connection):
    """Create a sample data table for testing."""
    con = duckdb_connection

    # Create a table with numeric and categorical data
    con.execute("""
        CREATE TABLE test_data (
            id INTEGER,
            category VARCHAR,
            value DOUBLE,
            count INTEGER
        )
    """)

    # Insert test data
    con.execute("""
        INSERT INTO test_data VALUES
            (1, 'A', 10.0, 100),
            (2, 'A', 20.0, 200),
            (3, 'B', 30.0, 150),
            (4, 'B', 40.0, 250),
            (5, 'B', 50.0, 300),
            (6, 'C', 60.0, 175),
            (7, 'C', 70.0, 225),
            (8, 'C', 80.0, 125),
            (9, 'C', 90.0, 275),
            (10, 'D', 100.0, 350)
    """)

    return con


@pytest.fixture
def sample_polygon_table(duckdb_connection):
    """Create a sample polygon table for area statistics testing."""
    con = duckdb_connection

    # Create a table with polygon geometries (simple squares in EPSG:4326)
    con.execute("""
        CREATE TABLE test_polygons (
            id INTEGER,
            name VARCHAR,
            geometry GEOMETRY
        )
    """)

    # Insert simple square polygons (approximately 1 degree x 1 degree at equator)
    con.execute("""
        INSERT INTO test_polygons VALUES
            (1, 'Square 1', ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))')),
            (2, 'Square 2', ST_GeomFromText('POLYGON((2 0, 3 0, 3 1, 2 1, 2 0))')),
            (3, 'Square 3', ST_GeomFromText('POLYGON((4 0, 5 0, 5 1, 4 1, 4 0))'))
    """)

    return con


class TestFeatureCount:
    """Tests for calculate_feature_count function."""

    def test_count_all_features(self, sample_data_table):
        """Test counting all features without filter."""
        result = calculate_feature_count(sample_data_table, "test_data")

        assert result.count == 10

    def test_count_with_where_clause(self, sample_data_table):
        """Test counting features with a WHERE clause."""
        result = calculate_feature_count(
            sample_data_table, "test_data", where_clause="category = 'A'"
        )

        assert result.count == 2

    def test_count_with_numeric_filter(self, sample_data_table):
        """Test counting features with numeric filter."""
        result = calculate_feature_count(
            sample_data_table, "test_data", where_clause="value > 50"
        )

        assert result.count == 5

    def test_count_with_params(self, sample_data_table):
        """Test counting features with parameterized query."""
        result = calculate_feature_count(
            sample_data_table, "test_data", where_clause="category = ?", params=["B"]
        )

        assert result.count == 3

    def test_count_empty_result(self, sample_data_table):
        """Test counting when no features match."""
        result = calculate_feature_count(
            sample_data_table, "test_data", where_clause="category = 'Z'"
        )

        assert result.count == 0


class TestUniqueValues:
    """Tests for calculate_unique_values function."""

    def test_unique_values_basic(self, sample_data_table):
        """Test getting unique values of a column."""
        result = calculate_unique_values(sample_data_table, "test_data", "category")

        assert result.attribute == "category"
        assert result.total == 4  # A, B, C, D
        assert len(result.values) == 4

    def test_unique_values_descendent_order(self, sample_data_table):
        """Test unique values ordered by count descending."""
        result = calculate_unique_values(
            sample_data_table, "test_data", "category", order=SortOrder.descendent
        )

        # C has 4 entries, B has 3, A has 2, D has 1
        assert result.values[0].value == "C"
        assert result.values[0].count == 4
        assert result.values[-1].value == "D"
        assert result.values[-1].count == 1

    def test_unique_values_ascendent_order(self, sample_data_table):
        """Test unique values ordered by count ascending."""
        result = calculate_unique_values(
            sample_data_table, "test_data", "category", order=SortOrder.ascendent
        )

        # D has 1 entry, should be first
        assert result.values[0].value == "D"
        assert result.values[0].count == 1

    def test_unique_values_with_limit(self, sample_data_table):
        """Test unique values with limit."""
        result = calculate_unique_values(
            sample_data_table, "test_data", "category", limit=2
        )

        assert len(result.values) == 2
        assert result.total == 4  # Total unique values still 4

    def test_unique_values_with_offset(self, sample_data_table):
        """Test unique values with offset for pagination."""
        result = calculate_unique_values(
            sample_data_table, "test_data", "category", limit=2, offset=2
        )

        assert len(result.values) == 2

    def test_unique_values_with_filter(self, sample_data_table):
        """Test unique values with WHERE clause."""
        result = calculate_unique_values(
            sample_data_table, "test_data", "category", where_clause="value >= 30"
        )

        # Only B, C, D have values >= 30
        assert result.total == 3


class TestClassBreaks:
    """Tests for calculate_class_breaks function."""

    def test_equal_interval_breaks(self, sample_data_table):
        """Test equal interval classification."""
        result = calculate_class_breaks(
            sample_data_table,
            "test_data",
            "value",
            method=ClassBreakMethod.equal_interval,
            num_breaks=5,
        )

        assert result.attribute == "value"
        assert result.method == "equal_interval"
        assert len(result.breaks) == 5
        assert result.min == 10.0
        assert result.max == 100.0

        # Equal interval breaks should be evenly spaced
        expected_breaks = [28.0, 46.0, 64.0, 82.0, 100.0]
        for actual, expected in zip(result.breaks, expected_breaks):
            assert abs(actual - expected) < 0.1

    def test_quantile_breaks(self, sample_data_table):
        """Test quantile classification."""
        result = calculate_class_breaks(
            sample_data_table,
            "test_data",
            "value",
            method=ClassBreakMethod.quantile,
            num_breaks=5,
        )

        assert result.method == "quantile"
        assert len(result.breaks) == 5

    def test_standard_deviation_breaks(self, sample_data_table):
        """Test standard deviation classification."""
        result = calculate_class_breaks(
            sample_data_table,
            "test_data",
            "value",
            method=ClassBreakMethod.standard_deviation,
            num_breaks=4,
        )

        assert result.method == "standard_deviation"
        assert result.std_dev is not None
        assert result.mean is not None

    def test_heads_and_tails_breaks(self, sample_data_table):
        """Test heads and tails classification."""
        result = calculate_class_breaks(
            sample_data_table,
            "test_data",
            "value",
            method=ClassBreakMethod.heads_and_tails,
            num_breaks=3,
        )

        assert result.method == "heads_and_tails"
        # Heads and tails returns breaks based on iterative mean splitting
        assert len(result.breaks) <= 3

    def test_class_breaks_with_filter(self, sample_data_table):
        """Test class breaks with WHERE clause."""
        result = calculate_class_breaks(
            sample_data_table,
            "test_data",
            "value",
            method=ClassBreakMethod.equal_interval,
            num_breaks=3,
            where_clause="category IN ('A', 'B')",
        )

        # Only values 10-50 should be included
        assert result.min == 10.0
        assert result.max == 50.0

    def test_class_breaks_strip_zeros(self, duckdb_connection):
        """Test class breaks with strip_zeros option."""
        con = duckdb_connection

        # Create table with zero values
        con.execute("""
            CREATE TABLE test_zeros (value DOUBLE)
        """)
        con.execute("""
            INSERT INTO test_zeros VALUES (0), (0), (10), (20), (30), (40), (50)
        """)

        result = calculate_class_breaks(
            con, "test_zeros", "value", num_breaks=3, strip_zeros=True
        )

        # Zero values should be excluded
        assert result.min == 10.0

    def test_class_breaks_empty_result(self, duckdb_connection):
        """Test class breaks with no matching data."""
        con = duckdb_connection

        con.execute("CREATE TABLE empty_table (value DOUBLE)")

        result = calculate_class_breaks(con, "empty_table", "value", num_breaks=5)

        assert result.breaks == []
        assert result.min is None
        assert result.max is None


class TestAreaStatistics:
    """Tests for calculate_area_statistics function."""

    def test_area_sum(self, sample_polygon_table):
        """Test sum of polygon areas."""
        result = calculate_area_statistics(
            sample_polygon_table,
            "test_polygons",
            "geometry",
            operation=AreaOperation.sum,
        )

        assert result.feature_count == 3
        assert result.total_area is not None
        assert result.total_area > 0
        assert result.unit == "m²"

    def test_area_mean(self, sample_polygon_table):
        """Test mean of polygon areas."""
        result = calculate_area_statistics(
            sample_polygon_table,
            "test_polygons",
            "geometry",
            operation=AreaOperation.mean,
        )

        assert result.feature_count == 3
        assert result.result is not None
        # Mean should be approximately total_area / 3
        if result.total_area:
            expected_mean = result.total_area / 3
            assert abs(result.result - expected_mean) < 1.0

    def test_area_min(self, sample_polygon_table):
        """Test minimum polygon area."""
        result = calculate_area_statistics(
            sample_polygon_table,
            "test_polygons",
            "geometry",
            operation=AreaOperation.min,
        )

        assert result.result is not None
        assert result.result > 0

    def test_area_max(self, sample_polygon_table):
        """Test maximum polygon area."""
        result = calculate_area_statistics(
            sample_polygon_table,
            "test_polygons",
            "geometry",
            operation=AreaOperation.max,
        )

        assert result.result is not None
        assert result.result > 0

    def test_area_with_filter(self, sample_polygon_table):
        """Test area statistics with WHERE clause."""
        result = calculate_area_statistics(
            sample_polygon_table,
            "test_polygons",
            "geometry",
            operation=AreaOperation.sum,
            where_clause="id IN (1, 2)",
        )

        assert result.feature_count == 2

    def test_area_empty_result(self, duckdb_connection):
        """Test area statistics with no matching data."""
        con = duckdb_connection

        con.execute("""
            CREATE TABLE empty_polygons (
                id INTEGER,
                geometry GEOMETRY
            )
        """)

        result = calculate_area_statistics(
            con, "empty_polygons", "geometry", operation=AreaOperation.sum
        )

        assert result.feature_count == 0


class TestExtent:
    """Tests for calculate_extent function.
    
    Note: These tests use geometries without explicit SRID, so the ST_Transform
    in calculate_extent will treat them as WGS84. For production use, geometries
    should have proper SRID set.
    """

    @pytest.fixture
    def extent_polygon_table(self, duckdb_connection):
        """Create a polygon table with known coordinates for extent testing."""
        con = duckdb_connection

        # Create a table with polygon geometries
        con.execute("""
            CREATE TABLE test_extent_polygons (
                id INTEGER,
                name VARCHAR,
                geometry GEOMETRY
            )
        """)

        # Insert polygons with known coordinates
        # Polygon 1: covers (0,0) to (1,1)
        # Polygon 2: covers (2,2) to (4,3)
        # Polygon 3: covers (-1,-1) to (0,0)
        # Overall extent should be (-1, -1) to (4, 3)
        con.execute("""
            INSERT INTO test_extent_polygons VALUES
                (1, 'Polygon 1', ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))')),
                (2, 'Polygon 2', ST_GeomFromText('POLYGON((2 2, 4 2, 4 3, 2 3, 2 2))')),
                (3, 'Polygon 3', ST_GeomFromText('POLYGON((-1 -1, 0 -1, 0 0, -1 0, -1 -1))'))
        """)

        return con

    def _calculate_extent_no_transform(
        self, con, table_name, geometry_column="geometry", where_clause="TRUE", params=None
    ):
        """Calculate extent without CRS transform (for unit testing).
        
        Uses ST_Extent_Agg which is the correct aggregate function in DuckDB spatial.
        """
        query = f"""
            SELECT 
                ST_XMin(extent) as minx,
                ST_YMin(extent) as miny,
                ST_XMax(extent) as maxx,
                ST_YMax(extent) as maxy,
                cnt as feature_count
            FROM (
                SELECT ST_Extent_Agg({geometry_column}) as extent, COUNT(*) as cnt
                FROM {table_name}
                WHERE {where_clause}
            )
        """
        if params:
            result = con.execute(query, params).fetchone()
        else:
            result = con.execute(query).fetchone()

        if not result or result[4] == 0:
            from goatlib.analysis.statistics import ExtentResult
            return ExtentResult(bbox=None, feature_count=0)

        minx, miny, maxx, maxy, feature_count = result

        if minx is None or miny is None or maxx is None or maxy is None:
            from goatlib.analysis.statistics import ExtentResult
            return ExtentResult(bbox=None, feature_count=feature_count)

        from goatlib.analysis.statistics import ExtentResult
        return ExtentResult(
            bbox=[float(minx), float(miny), float(maxx), float(maxy)],
            feature_count=feature_count,
        )

    def test_extent_all_features(self, extent_polygon_table):
        """Test extent calculation for all features."""
        result = calculate_extent(
            extent_polygon_table, "test_extent_polygons", "geometry"
        )

        assert result.feature_count == 3
        assert result.bbox is not None
        assert len(result.bbox) == 4

        minx, miny, maxx, maxy = result.bbox
        assert abs(minx - (-1.0)) < 0.0001
        assert abs(miny - (-1.0)) < 0.0001
        assert abs(maxx - 4.0) < 0.0001
        assert abs(maxy - 3.0) < 0.0001

    def test_extent_with_filter(self, extent_polygon_table):
        """Test extent with WHERE clause filter."""
        result = calculate_extent(
            extent_polygon_table,
            "test_extent_polygons",
            "geometry",
            where_clause="id IN (1, 2)",
        )

        assert result.feature_count == 2
        assert result.bbox is not None

        minx, miny, maxx, maxy = result.bbox
        # Only polygons 1 and 2: extent should be (0, 0) to (4, 3)
        assert abs(minx - 0.0) < 0.0001
        assert abs(miny - 0.0) < 0.0001
        assert abs(maxx - 4.0) < 0.0001
        assert abs(maxy - 3.0) < 0.0001

    def test_extent_single_feature(self, extent_polygon_table):
        """Test extent for a single feature."""
        result = calculate_extent(
            extent_polygon_table,
            "test_extent_polygons",
            "geometry",
            where_clause="id = 1",
        )

        assert result.feature_count == 1
        assert result.bbox is not None

        minx, miny, maxx, maxy = result.bbox
        # Polygon 1: (0, 0) to (1, 1)
        assert abs(minx - 0.0) < 0.0001
        assert abs(miny - 0.0) < 0.0001
        assert abs(maxx - 1.0) < 0.0001
        assert abs(maxy - 1.0) < 0.0001

    def test_extent_with_params(self, extent_polygon_table):
        """Test extent with parameterized query."""
        result = calculate_extent(
            extent_polygon_table,
            "test_extent_polygons",
            "geometry",
            where_clause="name = ?",
            params=["Polygon 2"],
        )

        assert result.feature_count == 1
        assert result.bbox is not None

        minx, miny, maxx, maxy = result.bbox
        # Polygon 2: (2, 2) to (4, 3)
        assert abs(minx - 2.0) < 0.0001
        assert abs(miny - 2.0) < 0.0001
        assert abs(maxx - 4.0) < 0.0001
        assert abs(maxy - 3.0) < 0.0001

    def test_extent_empty_result(self, extent_polygon_table):
        """Test extent when no features match."""
        result = calculate_extent(
            extent_polygon_table,
            "test_extent_polygons",
            "geometry",
            where_clause="id = 999",
        )

        assert result.feature_count == 0
        assert result.bbox is None

    def test_extent_empty_table(self, duckdb_connection):
        """Test extent with empty table."""
        con = duckdb_connection

        con.execute("""
            CREATE TABLE empty_extent_table (
                id INTEGER,
                geometry GEOMETRY
            )
        """)

        result = calculate_extent(con, "empty_extent_table", "geometry")

        assert result.feature_count == 0
        assert result.bbox is None

    def test_extent_point_geometries(self, duckdb_connection):
        """Test extent calculation with point geometries."""
        con = duckdb_connection

        con.execute("""
            CREATE TABLE test_points (
                id INTEGER,
                geometry GEOMETRY
            )
        """)

        con.execute("""
            INSERT INTO test_points VALUES
                (1, ST_GeomFromText('POINT(10 20)')),
                (2, ST_GeomFromText('POINT(30 40)')),
                (3, ST_GeomFromText('POINT(15 25)'))
        """)

        result = calculate_extent(con, "test_points", "geometry")

        assert result.feature_count == 3
        assert result.bbox is not None

        minx, miny, maxx, maxy = result.bbox
        assert abs(minx - 10.0) < 0.0001
        assert abs(miny - 20.0) < 0.0001
        assert abs(maxx - 30.0) < 0.0001
        assert abs(maxy - 40.0) < 0.0001

    def test_extent_line_geometries(self, duckdb_connection):
        """Test extent calculation with line geometries."""
        con = duckdb_connection

        con.execute("""
            CREATE TABLE test_lines (
                id INTEGER,
                geometry GEOMETRY
            )
        """)

        con.execute("""
            INSERT INTO test_lines VALUES
                (1, ST_GeomFromText('LINESTRING(0 0, 5 5)')),
                (2, ST_GeomFromText('LINESTRING(10 10, 15 15)'))
        """)

        result = calculate_extent(con, "test_lines", "geometry")

        assert result.feature_count == 2
        assert result.bbox is not None

        minx, miny, maxx, maxy = result.bbox
        assert abs(minx - 0.0) < 0.0001
        assert abs(miny - 0.0) < 0.0001
        assert abs(maxx - 15.0) < 0.0001
        assert abs(maxy - 15.0) < 0.0001


class TestIntegration:
    """Integration tests combining multiple statistics functions."""

    def test_workflow_filter_then_classify(self, sample_data_table):
        """Test a workflow: count, get unique values, then classify."""
        con = sample_data_table

        # Step 1: Count features in category B
        count_result = calculate_feature_count(
            con, "test_data", where_clause="category = 'B'"
        )
        assert count_result.count == 3

        # Step 2: Get unique values of count column for category B
        unique_result = calculate_unique_values(
            con, "test_data", "count", where_clause="category = 'B'"
        )
        assert unique_result.total == 3  # 150, 250, 300

        # Step 3: Classify values for category B
        breaks_result = calculate_class_breaks(
            con,
            "test_data",
            "value",
            method=ClassBreakMethod.equal_interval,
            num_breaks=3,
            where_clause="category = 'B'",
        )
        assert breaks_result.min == 30.0
        assert breaks_result.max == 50.0
