"""Data management schemas.

This module contains parameter schemas for data management operations like
join operations between datasets.
"""

from enum import StrEnum
from typing import List, Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator


class SpatialRelationshipType(StrEnum):
    """Spatial relationship types for joining features"""

    intersects = "intersects"
    within_distance = "within_distance"
    identical_to = "identical_to"
    completely_contains = "completely_contains"
    completely_within = "completely_within"


class JoinOperationType(StrEnum):
    """Join operation types determining how multiple matches are handled"""

    one_to_one = "one_to_one"
    one_to_many = "one_to_many"


class MultipleMatchingRecordsType(StrEnum):
    """How to handle multiple matching records in one-to-one joins"""

    first_record = "first_record"
    calculate_statistics = "calculate_statistics"
    count_only = "count_only"


class JoinType(StrEnum):
    """Join type determining which records to include in output"""

    inner = "inner"  # Only matching features
    left = "left"  # All target features


class SortOrder(StrEnum):
    """Sort order for selecting first matching record"""

    ascending = "ascending"
    descending = "descending"


class StatisticOperation(StrEnum):
    """Statistical operations for field aggregation"""

    sum = "sum"
    min = "min"
    max = "max"
    mean = "mean"
    count = "count"
    standard_deviation = "standard_deviation"


class AttributeRelationship(BaseModel):
    """Defines an attribute relationship between target and join layers"""

    target_field: str = Field(
        ..., description="Field name in the target layer for the join relationship"
    )
    join_field: str = Field(
        ..., description="Field name in the join layer for the join relationship"
    )


class SortConfiguration(BaseModel):
    """Configuration for sorting when selecting first matching record"""

    field: str = Field(
        ..., description="Field name to sort by when selecting first matching record"
    )
    sort_order: SortOrder = Field(
        SortOrder.ascending, description="Sort order for the field"
    )


class FieldStatistic(BaseModel):
    """Configuration for field statistics calculation"""

    field: str = Field(..., description="Field name to calculate statistics for")
    operations: List[StatisticOperation] = Field(
        default=[StatisticOperation.sum],
        description="List of statistical operations to perform on the field",
    )

    @model_validator(mode="after")
    def validate_operations(self: Self) -> Self:
        if not self.operations:
            raise ValueError("At least one statistical operation must be specified")
        return self


class JoinParams(BaseModel):
    """
    Parameters for performing join operation between datasets.
    Designed for DuckDB processing engine with GeoParquet data format.
    """

    # Input configuration
    target_path: str = Field(
        ...,
        description="Path to the target GeoParquet file that will have records appended to it",
    )
    join_path: str = Field(
        ...,
        description="Path to the join GeoParquet file whose records will be appended to the target layer",
    )
    output_path: str = Field(
        ..., description="Destination path for the joined output GeoParquet file"
    )

    # Join settings
    use_spatial_relationship: bool = Field(
        False,
        description="Whether to create a spatial join. If false, use_attribute_relationship must be true",
    )
    use_attribute_relationship: bool = Field(
        True,
        description="Whether to create an attribute join. If false, use_spatial_relationship must be true",
    )

    # Spatial relationship configuration
    spatial_relationship: Optional[SpatialRelationshipType] = Field(
        None,
        description="How spatial features are joined to each other. Required when use_spatial_relationship=True",
    )
    distance: Optional[float] = Field(
        None,
        description="Distance for spatial join when spatial_relationship='within_distance'",
        gt=0,
    )
    distance_units: Literal[
        "meters", "kilometers", "feet", "miles", "nautical_miles", "yards"
    ] = Field("meters", description="Units for the distance parameter")

    # Attribute relationship configuration
    attribute_relationships: Optional[List[AttributeRelationship]] = Field(
        None,
        description="List of attribute relationships. Required when use_attribute_relationship=True",
    )

    # Join operation configuration
    join_operation: JoinOperationType = Field(
        JoinOperationType.one_to_one,
        description="How to handle multiple matching features between target and join layers",
    )

    multiple_matching_records: MultipleMatchingRecordsType = Field(
        MultipleMatchingRecordsType.first_record,
        description="How to handle multiple matching records in one-to-one joins",
    )

    # Sorting configuration for first record selection
    sort_configuration: Optional[SortConfiguration] = Field(
        None,
        description="Configuration for sorting when selecting first matching record",
    )

    # Field statistics configuration
    field_statistics: Optional[List[FieldStatistic]] = Field(
        None,
        description="Field statistics to calculate when multiple_matching_records='calculate_statistics'",
    )

    # Join type
    join_type: JoinType = Field(
        JoinType.inner,
        description="Whether to include only matching features (inner) or all target features (left)",
    )

    # Output configuration
    output_name: Optional[str] = Field(
        None, description="Optional name for the output dataset"
    )

    @model_validator(mode="after")
    def validate_join_configuration(self: Self) -> Self:
        """Validate the join configuration"""

        # Must use at least one relationship type
        if not self.use_spatial_relationship and not self.use_attribute_relationship:
            raise ValueError(
                "Either use_spatial_relationship or use_attribute_relationship must be enabled"
            )

        # Spatial relationship validation
        if self.use_spatial_relationship:
            if self.spatial_relationship is None:
                raise ValueError(
                    "spatial_relationship is required when use_spatial_relationship=True"
                )

            # Distance is required for within_distance relationship
            if self.spatial_relationship == SpatialRelationshipType.within_distance:
                if self.distance is None:
                    raise ValueError(
                        "distance is required when spatial_relationship='within_distance'"
                    )

        # Attribute relationship validation
        if self.use_attribute_relationship:
            if not self.attribute_relationships:
                raise ValueError(
                    "attribute_relationships is required when use_attribute_relationship=True"
                )

        # One-to-one join specific validations
        if self.join_operation == JoinOperationType.one_to_one:
            if (
                self.multiple_matching_records
                == MultipleMatchingRecordsType.first_record
            ):
                # For combined joins, sort_configuration is optional if we have spatial criteria to break ties
                if (
                    self.sort_configuration is None
                    and not self.use_spatial_relationship
                ):
                    raise ValueError(
                        "sort_configuration is required when multiple_matching_records='first_record' for attribute-only joins"
                    )

            elif (
                self.multiple_matching_records
                == MultipleMatchingRecordsType.calculate_statistics
            ):
                if not self.field_statistics:
                    raise ValueError(
                        "field_statistics is required when multiple_matching_records='calculate_statistics'"
                    )

        # Sort configuration is only relevant for first_record selection
        if (
            self.sort_configuration is not None
            and self.multiple_matching_records
            != MultipleMatchingRecordsType.first_record
        ):
            raise ValueError(
                "sort_configuration is only applicable when multiple_matching_records='first_record'"
            )

        # Field statistics only relevant for calculate_statistics
        if (
            self.field_statistics is not None
            and self.multiple_matching_records
            != MultipleMatchingRecordsType.calculate_statistics
        ):
            raise ValueError(
                "field_statistics is only applicable when multiple_matching_records='calculate_statistics'"
            )

        # Distance units only relevant when using within_distance
        if (
            self.distance is not None
            and self.spatial_relationship != SpatialRelationshipType.within_distance
        ):
            raise ValueError(
                "distance is only applicable when spatial_relationship='within_distance'"
            )

        return self


class MergeParams(BaseModel):
    """Parameters for merging multiple vector layers."""

    input_paths: List[str] = Field(
        ...,
        min_length=2,
        description="List of paths to vector layers to merge. Must be at least 2 layers.",
    )

    output_path: Optional[str] = Field(
        None,
        description="Output path for merged layer. If None, generates based on first input.",
    )

    output_crs: Optional[str] = Field(
        None,
        description=(
            "Target CRS for output (e.g., 'EPSG:4326'). "
            "If None, uses CRS of first input layer. All layers reprojected to match."
        ),
    )

    add_source_field: bool = Field(
        True,
        description=(
            "If True, adds a 'layer_source' field indicating which input layer "
            "each feature came from (0, 1, 2, etc.)."
        ),
    )

    validate_geometry_types: bool = Field(
        True,
        description=(
            "If True, validates all inputs have compatible geometry types:\n"
            "- All Point/MultiPoint (compatible)\n"
            "- All LineString/MultiLineString (compatible)\n"
            "- All Polygon/MultiPolygon (compatible)\n"
            "If False, allows mixing different types (e.g., Point + Polygon)."
        ),
    )

    promote_to_multi: bool = Field(
        True,
        description=(
            "If True, promotes single-part to multi-part geometries:\n"
            "- Point → MultiPoint\n"
            "- LineString → MultiLineString\n"
            "- Polygon → MultiPolygon\n"
            "Required when merging layers with mixed single/multi geometries."
        ),
    )
