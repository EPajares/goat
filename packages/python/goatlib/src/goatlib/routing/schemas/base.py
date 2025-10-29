# In your_package/schemas/base.py

import logging
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import List, Optional, Self

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class RoutingProvider(StrEnum):
    """Supported routing service providers."""

    MOTIS = "motis"


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


class Route(BaseModel):
    """Base model for a route."""

    distance: float = Field(..., description="Distance in meters", ge=0)
    duration: float = Field(..., description="Duration in seconds", ge=0)
    departure_time: datetime = Field(..., description="Departure time (UTC)")


class RoutingRequestBase(BaseModel):
    """Base fields shared across all routing-style requests."""

    origin: Location = Field(..., description="Start location")
    destination: Location = Field(..., description="End location")
    provider: RoutingProvider = Field(
        default=RoutingProvider.MOTIS, description="Routing service provider."
    )

    # TODO: Clarify default behavior for modes field (default WALK?)
    modes: Optional[List[TransportMode]] = Field(
        default=[TransportMode.WALK],
        description="List of transport modes. Can be provided, defaulting to WALK if not specified.",
    )
    # TODO: Clarify default behavior for time field (None or now)
    time: Optional[datetime] = Field(
        default=None,
        description="Departure time. If not provided, defaults to None (immediate departure).",
    )

    @model_validator(mode="after")
    def validate_locations_are_distinct(self: Self) -> Self:
        if self.origin and self.destination and self.origin == self.destination:
            raise ValueError("Origin and destination cannot be the same")
        return self

    @model_validator(mode="after")
    def warn_on_mixed_car_mode(self: Self) -> Self:
        if self.modes and TransportMode.CAR in self.modes and len(self.modes) > 1:
            logger.warning(
                f"Request includes 'CAR' along with other modes ({self.modes}). "
            )
        return self

    @model_validator(mode="after")
    def validate_departure_time_properties(self: Self) -> Self:
        """
        1. Warns if a 'naive' datetime (without a timezone) is provided. It safely assumes UTC for processing.
        2. Warns if the provided datetime is in the past.
        """
        if self.time is None:
            return self

        user_time = self.time
        if self.time.tzinfo is None:
            logger.warning(
                "The provided 'time' is naive (lacks a timezone). Assuming UTC for processing."
            )
            user_time = self.time.replace(tzinfo=timezone.utc)

        utcnow = datetime.now(timezone.utc)

        if user_time < utcnow:
            logger.warning(
                f"The specified departure time '{self.time}' is in the past."
            )

        return self


class RoutingResponse(BaseModel):
    """
    Generic, reusable routing response base class.
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), title="Unique Request ID"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        title="Timestamp of the response generation (UTC)",
    )
    routes: List[Route] = Field(
        ..., description="A list of found routes.", min_length=0
    )

    processing_time_ms: Optional[int] = Field(
        default=None, description="Total processing time in milliseconds.", ge=0
    )
