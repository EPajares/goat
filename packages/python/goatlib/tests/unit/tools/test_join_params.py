"""Unit tests for JoinToolParams validators.

Tests custom validation logic in JoinToolParams.
"""

import pytest

from goatlib.analysis.schemas.data_management import (
    AttributeRelationship,
    FieldStatistic,
)
from goatlib.tools.join import JoinToolParams, SpatialRelationshipType


class TestJoinToolParamsValidation:
    """Test custom validators in JoinToolParams."""

    # Required test IDs for ToolInputBase
    BASE_PARAMS = {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "folder_id": "00000000-0000-0000-0000-000000000002",
        "target_layer_id": "00000000-0000-0000-0000-000000000003",
        "join_layer_id": "00000000-0000-0000-0000-000000000004",
    }

    # Valid attribute relationship for reuse
    VALID_ATTR_REL = [AttributeRelationship(target_field="city_id", join_field="id")]

    def test_requires_at_least_one_relationship_type(self):
        """Must enable spatial or attribute relationship."""
        with pytest.raises(
            ValueError,
            match="Either use_spatial_relationship or use_attribute_relationship",
        ):
            JoinToolParams(
                **self.BASE_PARAMS,
                use_spatial_relationship=False,
                use_attribute_relationship=False,
            )

    def test_spatial_requires_relationship_type(self):
        """Spatial relationship requires spatial_relationship field."""
        with pytest.raises(ValueError, match="spatial_relationship is required"):
            JoinToolParams(
                **self.BASE_PARAMS,
                use_spatial_relationship=True,
                use_attribute_relationship=False,
                spatial_relationship=None,
            )

    def test_within_distance_requires_distance(self):
        """within_distance relationship requires distance value."""
        with pytest.raises(
            ValueError, match="distance is required for within_distance"
        ):
            JoinToolParams(
                **self.BASE_PARAMS,
                use_spatial_relationship=True,
                use_attribute_relationship=False,
                spatial_relationship=SpatialRelationshipType.within_distance,
                distance=None,
            )

    def test_attribute_requires_relationships(self):
        """Attribute relationship requires at least one relationship."""
        with pytest.raises(ValueError, match="At least one attribute relationship"):
            JoinToolParams(
                **self.BASE_PARAMS,
                use_spatial_relationship=False,
                use_attribute_relationship=True,
                attribute_relationships=[],
            )

    def test_statistics_requires_field_statistics(self):
        """calculate_statistics requires field_statistics list."""
        with pytest.raises(ValueError, match="field_statistics is required"):
            JoinToolParams(
                **self.BASE_PARAMS,
                use_spatial_relationship=True,
                use_attribute_relationship=False,
                spatial_relationship=SpatialRelationshipType.intersects,
                calculate_statistics=True,
                field_statistics=[],
            )

    # Valid cases
    def test_valid_spatial_join(self):
        """Valid spatial join params should pass."""
        params = JoinToolParams(
            **self.BASE_PARAMS,
            use_spatial_relationship=True,
            use_attribute_relationship=False,
            spatial_relationship=SpatialRelationshipType.intersects,
        )
        assert params.use_spatial_relationship is True

    def test_valid_within_distance_join(self):
        """Valid within_distance join params should pass."""
        params = JoinToolParams(
            **self.BASE_PARAMS,
            use_spatial_relationship=True,
            use_attribute_relationship=False,
            spatial_relationship=SpatialRelationshipType.within_distance,
            distance=100.0,
        )
        assert params.distance == 100.0

    def test_valid_attribute_join(self):
        """Valid attribute join params should pass."""
        params = JoinToolParams(
            **self.BASE_PARAMS,
            use_spatial_relationship=False,
            use_attribute_relationship=True,
            attribute_relationships=self.VALID_ATTR_REL,
        )
        assert len(params.attribute_relationships) == 1

    def test_valid_combined_join(self):
        """Valid spatial + attribute join params should pass."""
        params = JoinToolParams(
            **self.BASE_PARAMS,
            use_spatial_relationship=True,
            spatial_relationship=SpatialRelationshipType.intersects,
            use_attribute_relationship=True,
            attribute_relationships=self.VALID_ATTR_REL,
        )
        assert params.use_spatial_relationship is True
        assert params.use_attribute_relationship is True

    def test_valid_join_with_statistics(self):
        """Valid join with statistics should pass."""
        params = JoinToolParams(
            **self.BASE_PARAMS,
            use_spatial_relationship=True,
            use_attribute_relationship=False,
            spatial_relationship=SpatialRelationshipType.intersects,
            calculate_statistics=True,
            field_statistics=[
                FieldStatistic(field="population", operation="sum"),
            ],
        )
        assert params.calculate_statistics is True
        assert len(params.field_statistics) == 1
