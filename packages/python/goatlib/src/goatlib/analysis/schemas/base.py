"""Base schemas for analysis operations."""

from enum import StrEnum
from typing import List, Optional, Self

from pydantic import BaseModel, Field, model_validator


class GeometryType(StrEnum):
    """Supported geometry types in DuckDB Spatial"""

    point = "POINT"
    multipoint = "MULTIPOINT"
    linestring = "LINESTRING"
    multilinestring = "MULTILINESTRING"
    polygon = "POLYGON"
    multipolygon = "MULTIPOLYGON"


# Common geometry type groups
ALL_GEOMETRY_TYPES: List[GeometryType] = [
    GeometryType.polygon,
    GeometryType.multipolygon,
    GeometryType.linestring,
    GeometryType.multilinestring,
    GeometryType.point,
    GeometryType.multipoint,
]

POLYGON_TYPES: List[GeometryType] = [
    GeometryType.polygon,
    GeometryType.multipolygon,
]


class StatisticOperation(StrEnum):
    """Statistical operations for field aggregation."""

    count = "count"
    sum = "sum"
    min = "min"
    max = "max"
    mean = "mean"
    standard_deviation = "standard_deviation"


class FieldStatistic(BaseModel):
    """Configuration for a statistical operation on a field.

    Used by join and aggregate tools for computing statistics.
    For 'count' operation, field is not required.
    For all other operations, field is required.
    """

    operation: StatisticOperation = Field(
        ...,
        description="The statistical operation to perform.",
    )
    field: Optional[str] = Field(
        None,
        description="Field name to compute statistics on. Required for all operations except 'count'.",
    )

    @model_validator(mode="after")
    def validate_field_requirement(self: Self) -> "FieldStatistic":
        """Validate that field is provided for non-count operations."""
        if self.operation == StatisticOperation.count:
            if self.field is not None:
                raise ValueError("Field should not be provided for 'count' operation.")
        else:
            if self.field is None:
                raise ValueError(f"Field is required for '{self.operation}' operation.")
        return self
