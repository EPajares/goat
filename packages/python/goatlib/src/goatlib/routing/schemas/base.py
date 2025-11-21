# In your_package/schemas/base.py

import uuid
from datetime import datetime
from enum import StrEnum
from typing import List

from pydantic import BaseModel, Field


class RoutingProvider(StrEnum):
    """Supported routing service providers."""

    MOTIS = "motis"
    OTP = "otp"
    R5 = "r5"


class CatchmentAreaType(StrEnum):
    """Catchment area type schema."""

    polygon = "polygon"
    network = "network"
    rectangular_grid = "rectangular_grid"


class CatchmentAreaRoutingTypeActiveMobility(StrEnum):
    """Routing active mobility type schema."""

    walking = "walking"
    wheelchair = "wheelchair"
    bicycle = "bicycle"
    pedelec = "pedelec"


class CatchmentAreaRoutingTypeCar(StrEnum):
    """Routing car type schema."""

    car = "car"


class CatchmentAreaRoutingModePT(StrEnum):
    """Routing public transport mode schema."""

    bus = "bus"
    tram = "tram"
    rail = "rail"
    subway = "subway"
    ferry = "ferry"
    cable_car = "cable_car"
    gondola = "gondola"
    funicular = "funicular"


class Mode(StrEnum):
    # Active mobility
    WALK = "walk"
    BIKE = "bicycle"

    # Public transport
    TRAM = "tram"
    SUBWAY = "subway"
    RAIL = "rail"
    BUS = "bus"
    FERRY = "ferry"
    CABLE_CAR = "cable_car"
    GONDOLA = "gondola"
    FUNICULAR = "funicular"

    # Private transport
    CAR = "car"

    # TODO decide if keep it and define which public transportation modes are included
    # Meta-modes
    TRANSIT = "transit"  # Any public transport mode
    OTHER = "other"  # Fallback for unknown modes


# --- Constants for Validation ---
MAX_SPEEDS_KMH = {
    Mode.BUS: 120,
    Mode.TRAM: 80,
    Mode.SUBWAY: 120,
    Mode.RAIL: 400,
}
DEFAULT_MAX_SPEED_KMH = 250


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


class CatchmentAreaStartingPoints(BaseModel):
    """Base model for catchment area attributes."""

    latitude: List[float] | None = Field(
        None,
        title="Latitude",
        description="The latitude of the catchment area center.",
    )
    longitude: List[float] | None = Field(
        None,
        title="Longitude",
        description="The longitude of the catchment area center.",
    )
