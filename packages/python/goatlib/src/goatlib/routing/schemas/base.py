# In your_package/schemas/base.py

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RoutingProvider(StrEnum):
    """Supported routing service providers."""

    MOTIS = "motis"
    OTP = "otp"


class Mode(StrEnum):
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

    route_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    distance: float = Field(..., description="Distance in meters", ge=0)
    duration: float = Field(..., description="Duration in seconds", ge=0)
    departure_time: datetime = Field(..., description="Departure time")
