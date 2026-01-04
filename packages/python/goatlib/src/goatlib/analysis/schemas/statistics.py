"""Schemas for statistical analysis operations."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ClassBreakMethod(StrEnum):
    """Classification methods for calculating breaks."""

    quantile = "quantile"
    equal_interval = "equal_interval"
    standard_deviation = "standard_deviation"
    heads_and_tails = "heads_and_tails"


class SortOrder(StrEnum):
    """Sort order for unique values."""

    ascendent = "ascendent"
    descendent = "descendent"


class AreaOperation(StrEnum):
    """Statistical operations for area calculations."""

    sum = "sum"
    mean = "mean"
    min = "min"
    max = "max"


# Input models


class FeatureCountInput(BaseModel):
    """Input for feature count operation."""

    filter: str | None = Field(default=None, description="CQL2 filter expression")


class AreaStatisticsInput(BaseModel):
    """Input for area statistics operation."""

    operation: AreaOperation = Field(description="Statistical operation")
    filter: str | None = Field(default=None, description="CQL2 filter expression")


class UniqueValuesInput(BaseModel):
    """Input for unique values operation."""

    attribute: str = Field(description="Attribute/column name")
    order: SortOrder = Field(
        default=SortOrder.descendent, description="Sort order by count"
    )
    filter: str | None = Field(default=None, description="CQL2 filter expression")
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum values to return"
    )
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class ClassBreaksInput(BaseModel):
    """Input for class breaks operation."""

    attribute: str = Field(description="Numeric attribute/column name")
    method: ClassBreakMethod = Field(
        default=ClassBreakMethod.quantile, description="Classification method"
    )
    breaks: int = Field(default=5, ge=2, le=20, description="Number of classes")
    filter: str | None = Field(default=None, description="CQL2 filter expression")
    strip_zeros: bool = Field(default=False, description="Exclude zero values")


# Result models


class FeatureCountResult(BaseModel):
    """Result of feature count operation."""

    count: int = Field(..., description="Number of features matching the criteria")


class UniqueValue(BaseModel):
    """Single unique value with its count."""

    value: Any = Field(..., description="The unique value")
    count: int = Field(..., description="Number of occurrences")


class UniqueValuesResult(BaseModel):
    """Result of unique values operation."""

    attribute: str = Field(..., description="The attribute/column analyzed")
    total: int = Field(..., description="Total number of unique values")
    values: list[UniqueValue] = Field(
        default_factory=list, description="List of unique values with counts"
    )


class ClassBreaksResult(BaseModel):
    """Result of class breaks calculation."""

    attribute: str = Field(..., description="The attribute/column analyzed")
    method: str = Field(..., description="Classification method used")
    breaks: list[float] = Field(
        default_factory=list, description="Classification break values"
    )
    min: float | None = Field(None, description="Minimum value")
    max: float | None = Field(None, description="Maximum value")
    mean: float | None = Field(None, description="Mean value")
    std_dev: float | None = Field(None, description="Standard deviation")


class AreaStatisticsResult(BaseModel):
    """Result of area statistics calculation."""

    result: float | None = Field(
        None, description="Result of the statistical operation"
    )
    total_area: float | None = Field(None, description="Total area of all features")
    feature_count: int = Field(0, description="Number of features")
    unit: str = Field("m²", description="Unit of area measurement")
