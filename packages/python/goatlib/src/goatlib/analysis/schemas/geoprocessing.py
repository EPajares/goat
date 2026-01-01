"""Geoprocessing analysis schemas.

This module contains parameter schemas for geoprocessing operations like
buffer, clip, intersection, union, difference, centroid, merge, and
origin-destination analysis.
"""

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
    output_crs: Optional[str] = Field(
        None, description="Target coordinate reference system for the output geometry."
    )
