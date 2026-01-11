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


# =============================================================================
# Public Transport (PT) Time Window
# =============================================================================


class PTTimeWindow(BaseModel):
    """Public transport time window for analysis.

    Used by PT-based analysis tools like Trip Count Station and ÖV-Güteklassen.

    Attributes:
        weekday: Type of day - "weekday", "saturday", or "sunday"
        from_time: Start time in seconds from midnight (e.g., 25200 = 7:00)
        to_time: End time in seconds from midnight (e.g., 32400 = 9:00)
    """

    weekday: str = Field(
        ...,
        description="Type of day: 'weekday', 'saturday', or 'sunday'",
    )
    from_time: int = Field(
        ...,
        description="Start time in seconds from midnight",
    )
    to_time: int = Field(
        ...,
        description="End time in seconds from midnight",
    )

    @property
    def weekday_column(self) -> str:
        """Get the boolean column name for the weekday type."""
        mapping = {
            "weekday": "is_weekday",
            "saturday": "is_saturday",
            "sunday": "is_sunday",
        }
        return mapping.get(self.weekday, "is_weekday")

    @property
    def from_time_str(self) -> str:
        """Convert from_time to HH:MM:SS format."""
        hours = self.from_time // 3600
        minutes = (self.from_time % 3600) // 60
        seconds = self.from_time % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def to_time_str(self) -> str:
        """Convert to_time to HH:MM:SS format."""
        hours = self.to_time // 3600
        minutes = (self.to_time % 3600) // 60
        seconds = self.to_time % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def time_window_minutes(self) -> float:
        """Get the time window duration in minutes."""
        return (self.to_time - self.from_time) / 60


# =============================================================================
# Statistics
# =============================================================================


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
