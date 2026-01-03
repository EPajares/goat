"""
Base schemas for routing in goatlib.

This module provides the foundational types and enums used across all routing
operations - catchment areas, A-B routing, and isochrones.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Routing Providers
# =============================================================================


class RoutingProvider(StrEnum):
    """Supported routing service providers."""

    r5 = "r5"
    goat_routing = "goat_routing"  # Our Rust-based routing in apps/routing
    motis = "motis"
    otp = "otp"


# =============================================================================
# Transport Modes
# =============================================================================


class ActiveMobilityMode(StrEnum):
    """Active mobility routing modes."""

    walk = "walk"
    bicycle = "bicycle"
    pedelec = "pedelec"
    wheelchair = "wheelchair"


class CarMode(StrEnum):
    """Car routing modes."""

    car = "car"


class PTMode(StrEnum):
    """Public transport modes."""

    bus = "bus"
    tram = "tram"
    rail = "rail"
    subway = "subway"
    ferry = "ferry"
    cable_car = "cable_car"
    gondola = "gondola"
    funicular = "funicular"


class AccessEgressMode(StrEnum):
    """Access and egress modes for transit routing."""

    walk = "walk"
    bicycle = "bicycle"
    car = "car"


class TransportMode(StrEnum):
    """
    All transport modes in a single enum.
    Use this for general mode references, use specific enums
    (ActiveMobilityMode, PTMode, etc.) for typed routing requests.
    """

    # Active mobility
    walk = "walk"
    bicycle = "bicycle"
    pedelec = "pedelec"
    wheelchair = "wheelchair"

    # Public transport
    bus = "bus"
    tram = "tram"
    rail = "rail"
    subway = "subway"
    ferry = "ferry"
    cable_car = "cable_car"
    gondola = "gondola"
    funicular = "funicular"

    # Private transport
    car = "car"

    # Meta-modes
    transit = "transit"  # Any public transport mode


# =============================================================================
# Catchment Area Types
# =============================================================================


class CatchmentAreaType(StrEnum):
    """Output geometry type for catchment areas."""

    polygon = "polygon"
    network = "network"
    rectangular_grid = "rectangular_grid"


class OutputFormat(StrEnum):
    """Output format for routing results."""

    geojson = "geojson"
    parquet = "parquet"


# =============================================================================
# Geographic Types
# =============================================================================


class Coordinates(BaseModel):
    """Geographic coordinates using WGS84."""

    lat: float = Field(..., description="Latitude", ge=-90.0, le=90.0)
    lon: float = Field(..., description="Longitude", ge=-180.0, le=180.0)


class StartingPoints(BaseModel):
    """
    Starting points for routing computations.

    Supports both the legacy lat/lon list format (for compatibility with core)
    and the new Coordinates list format.
    """

    # Legacy format (compatible with core)
    latitude: Optional[List[float]] = Field(
        None,
        title="Latitude",
        description="List of latitudes for starting points (legacy format).",
    )
    longitude: Optional[List[float]] = Field(
        None,
        title="Longitude",
        description="List of longitudes for starting points (legacy format).",
    )

    # New format
    coordinates: Optional[List[Coordinates]] = Field(
        None,
        title="Coordinates",
        description="List of coordinate objects for starting points.",
    )

    def to_coordinates(self) -> List[Coordinates]:
        """Convert to list of Coordinates, handling both formats."""
        if self.coordinates:
            return self.coordinates
        if self.latitude and self.longitude:
            return [
                Coordinates(lat=lat, lon=lon)
                for lat, lon in zip(self.latitude, self.longitude)
            ]
        return []

    @property
    def count(self) -> int:
        """Get the number of starting points."""
        return len(self.to_coordinates())


# =============================================================================
# Time Window (for PT routing)
# =============================================================================


class PTTimeWindow(BaseModel):
    """Time window configuration for public transport routing."""

    weekday: str = Field(
        ...,
        title="Weekday",
        description="The weekday type: 'weekday', 'saturday', or 'sunday'.",
    )
    from_time: int = Field(
        ...,
        title="From Time",
        description="Start time in seconds from midnight (e.g., 25200 = 7:00 AM).",
        ge=0,
        le=86400,
    )
    to_time: int = Field(
        ...,
        title="To Time",
        description="End time in seconds from midnight (e.g., 32400 = 9:00 AM).",
        ge=0,
        le=86400,
    )

    @property
    def weekday_date(self) -> str:
        """Get a representative date for the weekday type."""
        # Use fixed reference dates for consistent routing
        weekday_dates = {
            "weekday": "2024-01-15",  # Monday
            "saturday": "2024-01-13",
            "sunday": "2024-01-14",
        }
        return weekday_dates.get(self.weekday, "2024-01-15")


# =============================================================================
# Route Response Types
# =============================================================================


class Route(BaseModel):
    """Base model for a computed route."""

    route_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique route identifier",
    )
    duration: float = Field(..., description="Total duration in seconds", ge=0)
    distance: Optional[float] = Field(
        None, description="Total distance in meters", ge=0
    )
    departure_time: datetime = Field(..., description="Route departure time")
    arrival_time: Optional[datetime] = Field(None, description="Route arrival time")


# =============================================================================
# Legacy Aliases (for backward compatibility)
# =============================================================================

# These aliases help with migration from older code
Location = Coordinates  # Alias for older code using Location
CatchmentAreaRoutingTypeActiveMobility = ActiveMobilityMode
CatchmentAreaRoutingTypeCar = CarMode
CatchmentAreaRoutingModePT = PTMode
