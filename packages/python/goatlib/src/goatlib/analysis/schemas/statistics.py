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


class StatisticsOperation(StrEnum):
    """Statistical operations for aggregation calculations."""

    count = "count"
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


class ExtentInput(BaseModel):
    """Input for extent calculation operation."""

    filter: str | None = Field(default=None, description="CQL2 filter expression")


class ExtentResult(BaseModel):
    """Result of extent calculation - bounding box in WGS84 (EPSG:4326)."""

    bbox: list[float] | None = Field(
        None,
        description="Bounding box as [minx, miny, maxx, maxy] in WGS84 coordinates",
    )
    feature_count: int = Field(0, description="Number of features in the extent")

# Aggregation Stats models

class AggregationStatsInput(BaseModel):
    """Input for aggregation statistics operation."""

    operation: StatisticsOperation = Field(
        default=StatisticsOperation.count,
        description="Statistical operation to perform",
    )
    operation_column: str | None = Field(
        default=None,
        description="Column to perform the operation on (required for sum, mean, min, max)",
    )
    group_by_column: str | None = Field(
        default=None, description="Column to group results by"
    )
    filter: str | None = Field(default=None, description="CQL2 filter expression")
    order: SortOrder = Field(
        default=SortOrder.descendent, description="Sort order by operation value"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of grouped values to return",
    )


class AggregationStatsItem(BaseModel):
    """Single aggregation result item."""

    grouped_value: str | None = Field(
        None, description="The grouped value (null if no grouping)"
    )
    operation_value: float = Field(
        ..., description="Result of the statistical operation"
    )


class AggregationStatsResult(BaseModel):
    """Result of aggregation statistics calculation."""

    items: list[AggregationStatsItem] = Field(
        default_factory=list, description="List of aggregation results"
    )
    total_items: int = Field(
        0, description="Total number of grouped items (before limit)"
    )
    total_count: int = Field(0, description="Total count of rows")


# Histogram models


class HistogramInput(BaseModel):
    """Input for histogram calculation."""

    column: str = Field(description="Numeric column to create histogram for")
    num_bins: int = Field(
        default=10, ge=1, le=100, description="Number of histogram bins"
    )
    filter: str | None = Field(default=None, description="CQL2 filter expression")
    order: SortOrder = Field(
        default=SortOrder.ascendent, description="Sort order of bins"
    )


class HistogramBin(BaseModel):
    """Single histogram bin."""

    range: tuple[float, float] = Field(..., description="Bin range [lower, upper)")
    count: int = Field(..., description="Number of values in this bin")


class HistogramResult(BaseModel):
    """Result of histogram calculation."""

    bins: list[HistogramBin] = Field(
        default_factory=list, description="List of histogram bins"
    )
    missing_count: int = Field(0, description="Count of NULL values")
    total_rows: int = Field(0, description="Total number of rows")
