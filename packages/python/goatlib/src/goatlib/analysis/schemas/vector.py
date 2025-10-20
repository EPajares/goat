from typing import List, Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator


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
