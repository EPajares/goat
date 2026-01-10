"""Unit tests for JoinTool to verify functionality."""

from pathlib import Path

import duckdb
import pytest

from goatlib.analysis.data_management.join import JoinTool
from goatlib.analysis.schemas.base import FieldStatistic, StatisticOperation
from goatlib.analysis.schemas.data_management import (
    AttributeRelationship,
    JoinOperationType,
    JoinParams,
    JoinType,
    MultipleMatchingRecordsType,
    SortConfiguration,
    SortOrder,
    SpatialRelationshipType,
)


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "vector"
RESULT_DIR = Path(__file__).parent.parent.parent / "result"


@pytest.fixture(autouse=True)
def ensure_result_dir() -> None:
    """Ensure the result directory exists."""
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


class TestAttributeJoin:
    """Tests for attribute-based joins."""

    def test_attribute_join_one_to_one_first_record(self) -> None:
        """Test attribute join with one-to-one, keeping first matching record."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_attr_one_to_one_first.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="department", join_field="department"
                ),
                AttributeRelationship(target_field="level", join_field="level"),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.left,
            sort_configuration=None,  # Should use default row order
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]
        assert Path(result_path).exists()

        # Validate result
        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        df = con.execute(f"SELECT * FROM read_parquet('{result_path}')").fetchdf()

        # Should have all 6 employees
        assert len(df) == 6, f"Expected 6 rows, got {len(df)}"

        # Check that salary fields were joined
        assert "join_min_salary" in df.columns
        assert "join_max_salary" in df.columns

        # Verify John Doe (Engineering, Senior) got correct salary band
        john = df[df["first_name"] == "John"].iloc[0]
        assert john["join_min_salary"] == 85000
        assert john["join_max_salary"] == 110000

        con.close()
        tool.cleanup()

    def test_attribute_join_with_sort_configuration(self) -> None:
        """Test attribute join with explicit sort configuration."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_attr_with_sort.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="department", join_field="department"
                ),
                AttributeRelationship(target_field="level", join_field="level"),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.left,
            sort_configuration=SortConfiguration(
                field="min_salary",
                sort_order=SortOrder.descending,
            ),
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]
        assert Path(result_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        row_count = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{result_path}')"
        ).fetchone()[0]
        assert row_count == 6

        con.close()
        tool.cleanup()

    def test_attribute_join_one_to_many(self) -> None:
        """Test attribute join with one-to-many, preserving all matches."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_attr_one_to_many.parquet")

        # Create params that will have multiple matches per target
        # (match only on department, not level)
        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="department", join_field="department"
                ),
            ],
            join_operation=JoinOperationType.one_to_many,
            join_type=JoinType.left,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]
        assert Path(result_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        # Each employee should have multiple salary bands (one per level in their department)
        row_count = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{result_path}')"
        ).fetchone()[0]
        # 3 Engineering employees * 3 levels + 2 Marketing employees * 3 levels + 1 Sales employee * 3 levels = 18
        assert (
            row_count > 6
        ), f"Expected more than 6 rows for one-to-many, got {row_count}"

        con.close()
        tool.cleanup()

    def test_attribute_join_inner(self) -> None:
        """Test attribute join with inner join type (only matching features)."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_attr_inner.parquet")

        # HR has only Senior level in salary_bands, so HR employees at other levels won't match
        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="department", join_field="department"
                ),
                AttributeRelationship(target_field="level", join_field="level"),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.inner,  # Only keep matching
            sort_configuration=None,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        df = con.execute(f"SELECT * FROM read_parquet('{result_path}')").fetchdf()

        # All employees have matching salary bands (Engineering, Marketing, Sales all have Senior/Manager/Junior)
        assert len(df) == 6, f"Expected 6 rows, got {len(df)}"

        # No NULL values in joined fields
        assert df["join_min_salary"].notna().all()

        con.close()
        tool.cleanup()

    def test_attribute_join_with_statistics(self) -> None:
        """Test attribute join calculating statistics for multiple matches."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_attr_statistics.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="department", join_field="department"
                ),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.calculate_statistics,
            join_type=JoinType.left,
            field_statistics=[
                FieldStatistic(field="min_salary", operation=StatisticOperation.sum),
                FieldStatistic(field="max_salary", operation=StatisticOperation.max),
            ],
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        df = con.execute(f"SELECT * FROM read_parquet('{result_path}')").fetchdf()

        # Should still have 6 rows (one per employee)
        assert len(df) == 6

        # Should have statistics columns
        assert any("sum" in col.lower() for col in df.columns)
        assert any("max" in col.lower() for col in df.columns)

        con.close()
        tool.cleanup()


class TestSpatialJoin:
    """Tests for spatial-based joins."""

    def test_spatial_join_intersects(self) -> None:
        """Test spatial join with intersects relationship."""
        target_path = str(TEST_DATA_DIR / "poi_points.parquet")
        join_path = str(TEST_DATA_DIR / "districts.parquet")
        output_path = str(RESULT_DIR / "join_spatial_intersects.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=True,
            use_attribute_relationship=False,
            spatial_relationship=SpatialRelationshipType.intersects,
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.left,
            sort_configuration=None,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]
        assert Path(result_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        df = con.execute(f"SELECT * FROM read_parquet('{result_path}')").fetchdf()

        # Should have district fields joined
        assert "join_district_id" in df.columns or "district_id" in df.columns

        con.close()
        tool.cleanup()

    def test_spatial_join_within_distance(self) -> None:
        """Test spatial join with within_distance relationship."""
        target_path = str(TEST_DATA_DIR / "poi_points.parquet")
        join_path = str(TEST_DATA_DIR / "poi_points.parquet")
        output_path = str(RESULT_DIR / "join_spatial_distance.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=True,
            use_attribute_relationship=False,
            spatial_relationship=SpatialRelationshipType.within_distance,
            distance=100.0,  # 100 meters
            distance_units="meters",
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.left,
            sort_configuration=None,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]
        assert Path(result_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        row_count = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{result_path}')"
        ).fetchone()[0]
        assert row_count > 0

        con.close()
        tool.cleanup()

    def test_spatial_join_with_distance_units(self) -> None:
        """Test that distance units are properly converted."""
        target_path = str(TEST_DATA_DIR / "poi_points.parquet")
        join_path = str(TEST_DATA_DIR / "poi_points.parquet")
        output_path = str(RESULT_DIR / "join_spatial_distance_km.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=True,
            use_attribute_relationship=False,
            spatial_relationship=SpatialRelationshipType.within_distance,
            distance=0.1,  # 0.1 kilometers = 100 meters
            distance_units="kilometers",
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.left,
            sort_configuration=None,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]
        assert Path(result_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        row_count = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{result_path}')"
        ).fetchone()[0]
        assert row_count > 0

        con.close()
        tool.cleanup()


class TestCombinedJoin:
    """Tests for combined spatial and attribute joins."""

    def test_combined_spatial_and_attribute_join(self) -> None:
        """Test join using both spatial and attribute relationships."""
        target_path = str(TEST_DATA_DIR / "poi_points.parquet")
        join_path = str(TEST_DATA_DIR / "districts.parquet")
        output_path = str(RESULT_DIR / "join_combined.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=True,
            use_attribute_relationship=True,
            spatial_relationship=SpatialRelationshipType.intersects,
            attribute_relationships=[
                AttributeRelationship(target_field="category", join_field="zone_type"),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.left,
            sort_configuration=None,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]
        assert Path(result_path).exists()

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        df = con.execute(f"SELECT * FROM read_parquet('{result_path}')").fetchdf()

        # All POI points should be preserved (left join)
        assert len(df) > 0

        con.close()
        tool.cleanup()


class TestValidation:
    """Tests for parameter validation."""

    def test_validation_requires_relationship(self) -> None:
        """Test that at least one relationship type must be enabled."""
        with pytest.raises(
            ValueError,
            match="Either use_spatial_relationship or use_attribute_relationship",
        ):
            JoinParams(
                target_path="/tmp/target.parquet",
                join_path="/tmp/join.parquet",
                output_path="/tmp/output.parquet",
                use_spatial_relationship=False,
                use_attribute_relationship=False,
            )

    def test_validation_spatial_requires_relationship_type(self) -> None:
        """Test that spatial join requires spatial_relationship type."""
        with pytest.raises(ValueError, match="spatial_relationship is required"):
            JoinParams(
                target_path="/tmp/target.parquet",
                join_path="/tmp/join.parquet",
                output_path="/tmp/output.parquet",
                use_spatial_relationship=True,
                use_attribute_relationship=False,
                spatial_relationship=None,
            )

    def test_validation_attribute_requires_relationships(self) -> None:
        """Test that attribute join requires attribute_relationships."""
        with pytest.raises(ValueError, match="attribute_relationships is required"):
            JoinParams(
                target_path="/tmp/target.parquet",
                join_path="/tmp/join.parquet",
                output_path="/tmp/output.parquet",
                use_spatial_relationship=False,
                use_attribute_relationship=True,
                attribute_relationships=None,
            )

    def test_validation_within_distance_requires_distance(self) -> None:
        """Test that within_distance relationship requires distance parameter."""
        with pytest.raises(ValueError, match="distance is required"):
            JoinParams(
                target_path="/tmp/target.parquet",
                join_path="/tmp/join.parquet",
                output_path="/tmp/output.parquet",
                use_spatial_relationship=True,
                use_attribute_relationship=False,
                spatial_relationship=SpatialRelationshipType.within_distance,
                distance=None,
            )

    def test_validation_statistics_requires_field_statistics(self) -> None:
        """Test that calculate_statistics requires field_statistics."""
        with pytest.raises(ValueError, match="field_statistics is required"):
            JoinParams(
                target_path="/tmp/target.parquet",
                join_path="/tmp/join.parquet",
                output_path="/tmp/output.parquet",
                use_spatial_relationship=True,
                use_attribute_relationship=False,
                spatial_relationship=SpatialRelationshipType.intersects,
                join_operation=JoinOperationType.one_to_one,
                multiple_matching_records=MultipleMatchingRecordsType.calculate_statistics,
                field_statistics=None,
            )

    def test_validation_sort_configuration_optional_for_first_record(self) -> None:
        """Test that sort_configuration is now optional for first_record."""
        # This should NOT raise an error
        params = JoinParams(
            target_path="/tmp/target.parquet",
            join_path="/tmp/join.parquet",
            output_path="/tmp/output.parquet",
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(target_field="id", join_field="id"),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            sort_configuration=None,  # Should be allowed
        )
        assert params.sort_configuration is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_join_with_no_matches_left_join(self) -> None:
        """Test left join preserves all target features even with no matches."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_no_matches_left.parquet")

        # Use a condition that won't match anything
        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="first_name", join_field="department"
                ),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.left,
            sort_configuration=None,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        df = con.execute(f"SELECT * FROM read_parquet('{result_path}')").fetchdf()

        # Left join should preserve all 6 employees
        assert len(df) == 6

        # Joined fields should be NULL
        assert df["join_min_salary"].isna().all()

        con.close()
        tool.cleanup()

    def test_join_with_no_matches_inner_join(self) -> None:
        """Test inner join returns empty result when no matches."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_no_matches_inner.parquet")

        # Use a condition that won't match anything
        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="first_name", join_field="department"
                ),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.first_record,
            join_type=JoinType.inner,
            sort_configuration=None,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        row_count = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{result_path}')"
        ).fetchone()[0]

        # Inner join with no matches should return 0 rows
        assert row_count == 0

        con.close()
        tool.cleanup()

    def test_join_count_only(self) -> None:
        """Test join with count_only mode."""
        target_path = str(TEST_DATA_DIR / "employees.parquet")
        join_path = str(TEST_DATA_DIR / "salary_bands.parquet")
        output_path = str(RESULT_DIR / "join_count_only.parquet")

        params = JoinParams(
            target_path=target_path,
            join_path=join_path,
            output_path=output_path,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=[
                AttributeRelationship(
                    target_field="department", join_field="department"
                ),
            ],
            join_operation=JoinOperationType.one_to_one,
            multiple_matching_records=MultipleMatchingRecordsType.count_only,
            join_type=JoinType.left,
        )

        tool = JoinTool()
        results = tool.run(params)

        assert len(results) == 1
        result_path, metadata = results[0]

        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")

        df = con.execute(f"SELECT * FROM read_parquet('{result_path}')").fetchdf()

        # Should have 6 employees
        assert len(df) == 6

        # Should have a match_count field
        assert "match_count" in df.columns

        # Engineering has 3 salary bands (Junior, Senior, Manager)
        eng_employee = df[df["department"] == "Engineering"].iloc[0]
        assert eng_employee["match_count"] == 3

        con.close()
        tool.cleanup()
