from enum import StrEnum
from typing import List, Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator

from goatlib.analysis.schemas.base import (
    ALL_GEOMETRY_TYPES,
    POLYGON_TYPES,
    GeometryType,
)


class BufferParams(BaseModel):
    """
    Parameters for performing buffer operation
    """

    # Input and output configuration
    input_path: str = Field(..., description="Path to the input dataset.")
    output_path: str = Field(
        ..., description="Destination file path or table for buffered output."
    )

    # Buffer distance parameters
    distances: Optional[List[float]] = Field(
        None,
        description="List of buffer distances. Required unless 'field' is specified. "
        "Each distance should be a positive number using the specified 'units'.",
    )
    field: Optional[str] = Field(
        None,
        description="Optional field name in the dataset that provides a per-feature buffer distance.",
    )

    units: Literal[
        "meters", "kilometers", "feet", "miles", "nautical_miles", "yards"
    ] = Field(
        "meters",
        description="Measurement units for buffer distances.",
    )

    # Controls whether overlapping buffers are dissolved into a single geometry
    dissolve: bool = Field(
        False,
        description="If True, overlapping buffers will be merged (dissolved) into a single geometry.",
    )

    # Parameters corresponding to GEOS / ST_Buffer options
    num_triangles: int = Field(
        8,
        description="Number of triangles used to approximate a quarter circle. "
        "Higher values yield smoother buffer edges but increase computation cost.",
    )
    cap_style: Literal["CAP_ROUND", "CAP_FLAT", "CAP_SQUARE"] = Field(
        "CAP_ROUND",
        description="Style for line endpoints: 'CAP_ROUND', 'CAP_FLAT', or 'CAP_SQUARE'.",
    )
    join_style: Literal["JOIN_ROUND", "JOIN_MITRE", "JOIN_BEVEL"] = Field(
        "JOIN_ROUND",
        description="Corner join style between line segments. Options: 'JOIN_ROUND', 'JOIN_MITRE', 'JOIN_BEVEL'.",
    )
    mitre_limit: float = Field(
        1.0,
        description="Ratio controlling the length of mitred joins. "
        "Only applicable when join_style='JOIN_MITRE'. Default = 1.0.",
    )

    # Output metadata
    output_crs: Optional[str] = Field(
        "EPSG:4326",
        description="Target coordinate reference system for the output geometry.",
    )
    output_name: Optional[str] = Field(
        None, description="Optional name of the output dataset."
    )

    # Validation logic
    @model_validator(mode="after")
    def validate_all(self: Self) -> "BufferParams":
        # Must provide either distances or a distance field
        if not self.distances and not self.field:
            raise ValueError("You must supply either 'distances' or 'field'.")

        # If distances provided, validate that all are positive
        if self.distances:
            if not all(isinstance(d, (int, float)) and d > 0 for d in self.distances):
                raise ValueError("All buffer distances must be positive numbers.")

        # Validate field type
        if self.field and not isinstance(self.field, str):
            raise ValueError("'field' must be a string.")

        # Validate mitre_limit usage
        if self.join_style != "JOIN_MITRE" and self.mitre_limit != 1.0:
            raise ValueError(
                "mitre_limit is only applicable when join_style='JOIN_MITRE'."
            )

        # num_triangles must be > 0
        if self.num_triangles <= 0:
            raise ValueError("'num_triangles' must be greater than 0.")

        return self


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


class ClipParams(BaseModel):
    """
    Parameters for performing clip (zuschneiden) operation
    """

    input_path: str = Field(..., description="Path to the input dataset to be clipped.")
    overlay_path: str = Field(
        ..., description="Path to the overlay dataset used for clipping."
    )
    output_path: Optional[str] = Field(
        None,
        description="Destination file path for clipped output. If not provided, will be auto-generated.",
    )
    output_crs: Optional[str] = Field(
        None, description="Target coordinate reference system for the output geometry."
    )

    # Hardcoded accepted geometry types for each layer
    @property
    def accepted_input_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for input layer in clip operation."""
        return ALL_GEOMETRY_TYPES

    @property
    def accepted_overlay_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for overlay layer in clip operation (must be polygon)."""
        return POLYGON_TYPES


class IntersectionParams(BaseModel):
    """
    Parameters for performing intersection (verschneiden) operation
    """

    input_path: str = Field(..., description="Path to the input dataset.")
    overlay_path: str = Field(
        ..., description="Path to the overlay dataset to intersect with."
    )
    output_path: Optional[str] = Field(
        None,
        description="Destination file path for intersection output. If not provided, will be auto-generated.",
    )
    input_fields: Optional[List[str]] = Field(
        None,
        description="List of field names from input layer to keep in output. If None, all fields are kept.",
    )
    overlay_fields: Optional[List[str]] = Field(
        None,
        description="List of field names from overlay layer to keep in output. If None, all fields are kept.",
    )
    overlay_fields_prefix: Optional[str] = Field(
        "intersection_",
        description="Prefix to add to overlay field names to avoid naming conflicts. Default is 'intersection_'.",
    )
    output_crs: Optional[str] = Field(
        None, description="Target coordinate reference system for the output geometry."
    )

    # Hardcoded accepted geometry types for each layer
    @property
    def accepted_input_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for input layer in intersection operation."""
        return ALL_GEOMETRY_TYPES

    @property
    def accepted_overlay_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for overlay layer in intersection operation."""
        return ALL_GEOMETRY_TYPES


class UnionParams(BaseModel):
    """
    Parameters for performing union (vereinigen) operation
    """

    input_path: str = Field(..., description="Path to the input dataset.")
    overlay_path: Optional[str] = Field(
        None,
        description="Path to the overlay dataset to union with. If None, performs self-union on input.",
    )
    output_path: Optional[str] = Field(
        None,
        description="Destination file path for union output. If not provided, will be auto-generated.",
    )
    overlay_fields_prefix: Optional[str] = Field(
        None,
        description="Prefix to add to overlay field names to avoid naming conflicts.",
    )
    output_crs: Optional[str] = Field(
        None, description="Target coordinate reference system for the output geometry."
    )

    # Hardcoded accepted geometry types for each layer
    @property
    def accepted_input_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for input layer in union operation."""
        return ALL_GEOMETRY_TYPES

    @property
    def accepted_overlay_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for overlay layer in union operation."""
        return ALL_GEOMETRY_TYPES


class DifferenceParams(BaseModel):
    """
    Parameters for performing difference (differenz) operation
    """

    input_path: str = Field(
        ..., description="Path to the input dataset to subtract from."
    )
    overlay_path: str = Field(
        ..., description="Path to the overlay dataset to subtract."
    )
    output_path: Optional[str] = Field(
        None,
        description="Destination file path for difference output. If not provided, will be auto-generated.",
    )
    output_crs: Optional[str] = Field(
        None, description="Target coordinate reference system for the output geometry."
    )

    # Hardcoded accepted geometry types for each layer
    @property
    def accepted_input_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for input layer in difference operation."""
        return ALL_GEOMETRY_TYPES

    @property
    def accepted_overlay_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for overlay layer in difference operation (typically polygon)."""
        return POLYGON_TYPES


class CentroidParams(BaseModel):
    """
    Parameters for computing centroid of features.
    """

    input_path: str = Field(..., description="Path to the input dataset.")
    output_path: Optional[str] = Field(
        None,
        description="Destination file path for centroid output. If not provided, will be auto-generated.",
    )
    output_crs: Optional[str] = Field(
        None, description="Target coordinate reference system for the output geometry."
    )

    @property
    def accepted_input_geometry_types(self) -> List[GeometryType]:
        """Geometry types accepted for input layer."""
        return ALL_GEOMETRY_TYPES


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


class OriginDestinationParams(BaseModel):
    """
    Parameters for performing origin-destination analysis.
    """

    geometry_path: str = Field(
        ...,
        description="Path to the geometry layer (points or polygons) containing origins and destinations.",
    )
    matrix_path: str = Field(
        ...,
        description="Path to the origin-destination matrix file (parquet/csv).",
    )
    unique_id_column: str = Field(
        ...,
        description="The column that contains the unique IDs in geometry layer.",
    )
    origin_column: str = Field(
        ...,
        description="The column that contains the origins in the origin destination matrix.",
    )
    destination_column: str = Field(
        ...,
        description="The column that contains the destinations in the origin destination matrix.",
    )
    weight_column: str = Field(
        ...,
        description="The column that contains the weights in the origin destination matrix.",
    )
    output_path_lines: Optional[str] = Field(
        None,
        description="Destination file path for the lines output. If not provided, will be auto-generated.",
    )
    output_path_points: Optional[str] = Field(
        None,
        description="Destination file path for the points output. If not provided, will be auto-generated.",
    )
