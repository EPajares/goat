# In your_package/schemas/base.py

import logging
from datetime import datetime, timezone
from enum import StrEnum
from typing import List, Optional, Self

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class TransportMode(StrEnum):
    """Standardized routing modes for AB routing."""

    # Public Transport
    BUS = "BUS"
    TRAM = "TRAM"
    SUBWAY = "SUBWAY"
    RAIL = "RAIL"

    # All Public Transport
    TRANSIT = "TRANSIT"

    # Other Modes
    WALK = "WALK"
    BIKE = "BIKE"
    CAR = "CAR"


class Location(BaseModel):
    """Location coordinates."""

    lat: float = Field(..., description="Latitude coordinate", ge=-90.0, le=90.0)
    long: float = Field(..., description="Longitude coordinate", ge=-180.0, le=180.0)


class RoutingRequestBase(BaseModel):
    """Base fields shared across all routing-style requests."""

    origin: Location = Field(..., description="Start location")
    destination: Location = Field(..., description="End location")

    # TODO: Clarify default behavior for modes field (default WALK?)
    modes: Optional[List[TransportMode]] = Field(
        default=[TransportMode.WALK],
        description="List of transport modes. Must be provided, but can be None or an empty list.",
    )
    # TODO: Clarify default behavior for time field (None or now)
    time: Optional[datetime] = Field(
        default=None,
        description="Departure time. If not provided, defaults to None, signifying an immediate departure.",
    )

    @model_validator(mode="after")
    def validate_locations_are_distinct(self: Self) -> Self:
        """Validate that the origin and destination locations are not identical."""
        if self.origin and self.destination and self.origin == self.destination:
            raise ValueError("Origin and destination cannot be the same")
        return self

    @model_validator(mode="after")
    def warn_on_mixed_car_mode(self: Self) -> Self:
        """
        Warns if 'CAR' mode is combined with other public transport or walking modes,
        as this represents a potentially ambiguous request.
        """
        if self.modes and TransportMode.CAR in self.modes and len(self.modes) > 1:
            logger.warning(
                f"Request includes 'CAR' along with other modes ({self.modes}). "
                "This combination might produce unexpected results as 'CAR' is typically "
                "a unimodal trip. The routing engine's behavior may vary."
            )
        return self

    @model_validator(mode="after")
    def validate_departure_time_properties(self: Self) -> Self:
        """
        1. Warns if a 'naive' datetime (without a timezone) is provided, as this
            is ambiguous and violates OGC best practices. It safely assumes UTC
            in this case.
        2. Warns if the provided datetime is in the past, allowing for
            intentional historical queries while alerting users to potential mistakes.
        """
        if self.time is None:
            return self

        user_time = self.time
        if self.time.tzinfo is None:
            logger.warning(
                "The provided 'time' is naive (lacks a timezone). Assuming UTC for processing. "
                "It is highly recommended to provide timezone-aware datetimes conforming to RFC 3339 "
                "(e.g., ending with 'Z' for UTC)."
            )
            user_time = self.time.replace(tzinfo=timezone.utc)

        utcnow = datetime.now(timezone.utc)

        if user_time < utcnow:
            logger.warning(
                f"The specified departure time '{self.time}' is in the past. "
                "Proceeding with a historical routing query."
            )

        return self


class Route(BaseModel):
    """Computed route information."""

    duration: float = Field(..., description="Total travel time in minutes", gt=0)
    distance: float = Field(..., description="Total distance in meters", gt=0)
    time: datetime = Field(..., description="Departure time")


class RoutingResponse(BaseModel):
    """Routing response."""

    routes: List[Route] = Field(..., description="A list of found routes.")
    processing_time_ms: Optional[int] = Field(
        default=None, description="Total processing time in milliseconds.", ge=0
    )
