"""Unit tests for geoprocessing schema validators.

Tests custom validation logic in geoprocessing parameter schemas.
Only tests @model_validator/@field_validator logic - basic Pydantic
validation (required fields, types, enums) is already tested by Pydantic.
"""

import pytest

from goatlib.analysis.schemas.geoprocessing import BufferParams, DistanceType


class TestBufferParamsValidation:
    """Test custom validators in BufferParams."""

    def test_constant_requires_distances(self):
        """distance_type='constant' requires distances list."""
        with pytest.raises(ValueError, match="distances must be set"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distance_type=DistanceType.constant,
                distances=None,
            )

    def test_constant_with_empty_distances_fails(self):
        """distance_type='constant' with empty distances list fails."""
        with pytest.raises(ValueError, match="distances must be set"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distance_type=DistanceType.constant,
                distances=[],
            )

    def test_field_requires_distance_field(self):
        """distance_type='field' requires distance_field."""
        with pytest.raises(ValueError, match="distance_field must be set"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distance_type=DistanceType.field,
                distance_field=None,
            )

    def test_distances_must_be_positive(self):
        """All distances must be positive numbers."""
        with pytest.raises(ValueError, match="positive"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distance_type=DistanceType.constant,
                distances=[-100.0],
            )

    def test_distances_zero_fails(self):
        """Zero distance is not allowed."""
        with pytest.raises(ValueError, match="positive"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distance_type=DistanceType.constant,
                distances=[0],
            )

    def test_polygon_difference_requires_union(self):
        """polygon_difference requires polygon_union=True."""
        with pytest.raises(ValueError, match="polygon_difference can only be True"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distances=[100],
                polygon_union=False,
                polygon_difference=True,
            )

    def test_mitre_limit_only_for_mitre_join(self):
        """mitre_limit only valid when join_style='JOIN_MITRE'."""
        with pytest.raises(ValueError, match="mitre_limit is only applicable"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distances=[100],
                join_style="JOIN_ROUND",
                mitre_limit=2.0,  # Invalid for non-MITRE join
            )

    def test_num_triangles_must_be_positive(self):
        """num_triangles must be > 0."""
        with pytest.raises(ValueError, match="num_triangles"):
            BufferParams(
                input_path="/tmp/in.parquet",
                output_path="/tmp/out.parquet",
                distances=[100],
                num_triangles=0,
            )

    # Valid cases - ensure no exceptions
    def test_valid_constant_params(self):
        """Valid constant distance params should pass."""
        params = BufferParams(
            input_path="/tmp/in.parquet",
            output_path="/tmp/out.parquet",
            distance_type=DistanceType.constant,
            distances=[100, 200, 500],
        )
        assert params.distances == [100, 200, 500]

    def test_valid_field_params(self):
        """Valid field-based distance params should pass."""
        params = BufferParams(
            input_path="/tmp/in.parquet",
            output_path="/tmp/out.parquet",
            distance_type=DistanceType.field,
            distance_field="buffer_dist",
        )
        assert params.distance_field == "buffer_dist"

    def test_valid_polygon_difference_with_union(self):
        """polygon_difference with polygon_union=True should pass."""
        params = BufferParams(
            input_path="/tmp/in.parquet",
            output_path="/tmp/out.parquet",
            distances=[100, 200],
            polygon_union=True,
            polygon_difference=True,
        )
        assert params.polygon_difference is True

    def test_valid_mitre_limit_with_mitre_join(self):
        """mitre_limit with JOIN_MITRE should pass."""
        params = BufferParams(
            input_path="/tmp/in.parquet",
            output_path="/tmp/out.parquet",
            distances=[100],
            join_style="JOIN_MITRE",
            mitre_limit=2.5,
        )
        assert params.mitre_limit == 2.5
