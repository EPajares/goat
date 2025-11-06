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
    """
    Standardized routing modes aligned with GTFS route_type values.
    """

    # Active mobility
    WALK = "WALK"
    BIKE = "BIKE"

    # Public transport
    TRAM = "TRAM"
    SUBWAY = "SUBWAY"
    RAIL = "RAIL"
    BUS = "BUS"
    FERRY = "FERRY"
    CABLE_CAR = "CABLE_CAR"
    FUNICULAR = "FUNICULAR"

    # Private transport
    CAR = "CAR"

    # Meta-modes
    TRANSIT = "TRANSIT"  # Any public transport mode
    OTHER = "OTHER"  # Fallback for unknown modes


class Location(BaseModel):
    """Geographic location using WGS84 coordinates."""

    lat: float = Field(..., description="Latitude", ge=-90.0, le=90.0)
    lon: float = Field(..., description="Longitude", ge=-180.0, le=180.0)


class Route(BaseModel):
    """Base model for a route."""

    distance: float = Field(..., description="Distance in meters", ge=0)
    duration: float = Field(..., description="Duration in seconds", ge=0)
    departure_time: datetime = Field(..., description="Departure time")


class RoutingRequestBase(BaseModel):
    """Base fields for routing requests."""

    origin: Location = Field(..., description="Start location")
    destination: Location = Field(..., description="End location")
    provider: RoutingProvider = Field(default=RoutingProvider.MOTIS)
    modes: Optional[List[TransportMode]] = Field(default=[TransportMode.WALK])
    time: Optional[datetime] = Field(default=None, description="Departure time")

    @model_validator(mode="after")
    def validate_locations_are_distinct(self: Self) -> Self:
        if (
            self.origin
            and self.destination
            and self.origin.lat == self.destination.lat
            and self.origin.lon == self.destination.lon
        ):
            raise ValueError("Origin and destination cannot be the same")
        return self

    @model_validator(mode="after")
    def normalize_time(self: Self) -> Self:
        """Normalize timezone-naive datetime to UTC."""
        if self.time and self.time.tzinfo is None:
            self.time = self.time.replace(tzinfo=timezone.utc)
        return self


class RoutingResponse(BaseModel):
    """Base routing response."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    routes: List[Route] = Field(..., description="List of routes", min_length=0)
    processing_time_ms: Optional[int] = Field(default=None, ge=0)
