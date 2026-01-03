"""
Catchment Area schemas for goatlib analysis.

This module provides unified schemas for catchment area analysis across
different transport modes (active mobility, car, public transport).
"""

import logging
from datetime import time
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from goatlib.analysis.schemas.ui import (
    SECTION_CONFIGURATION,
    SECTION_INPUT,
    SECTION_OUTPUT,
    SECTION_ROUTING,
    SECTION_TIME,
    ui_field,
    ui_sections,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class RoutingProvider(StrEnum):
    """Supported routing providers."""

    r5 = "r5"
    goat_routing = "goat_routing"
    motis = "motis"
    otp = "otp"


class ActiveMobilityMode(StrEnum):
    """Active mobility transport modes."""

    walk = "walk"
    bicycle = "bicycle"
    pedelec = "pedelec"
    wheelchair = "wheelchair"


class CarMode(StrEnum):
    """Car transport modes."""

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
    """Access/egress modes for public transport."""

    walk = "walk"
    bicycle = "bicycle"
    car = "car"


class CatchmentAreaType(StrEnum):
    """Type of catchment area calculation."""

    polygon = "polygon"
    network = "network"
    rectangular_grid = "rectangular_grid"
    h3_grid = "rectangular_grid"  # Alias for rectangular_grid


class OutputFormat(StrEnum):
    """Output format for catchment area results."""

    geojson = "geojson"
    parquet = "parquet"


class DecayFunctionType(StrEnum):
    """Type of decay function for accessibility calculations."""

    step = "step"
    linear = "linear"
    logistic = "logistic"
    exponential = "exponential"


# =============================================================================
# Starting Points
# =============================================================================


class Coordinates(BaseModel):
    """A single coordinate point."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class StartingPoints(BaseModel):
    """Starting points for catchment area analysis."""

    # Support list of coordinates
    coordinates: list[Coordinates] | None = Field(
        default=None, description="List of coordinate points"
    )

    # Legacy support: separate lat/lon lists
    latitude: list[float] | None = Field(default=None, description="List of latitudes")
    longitude: list[float] | None = Field(
        default=None, description="List of longitudes"
    )

    @model_validator(mode="after")
    def validate_points(self: Self) -> Self:
        """Ensure either coordinates or lat/lon lists are provided."""
        has_coords = self.coordinates is not None and len(self.coordinates) > 0
        has_legacy = (
            self.latitude is not None
            and self.longitude is not None
            and len(self.latitude) > 0
        )

        if not has_coords and not has_legacy:
            raise ValueError(
                "Either 'coordinates' or both 'latitude' and 'longitude' must be provided"
            )

        if has_legacy:
            if len(self.latitude) != len(self.longitude):
                raise ValueError("latitude and longitude lists must have same length")

        return self

    def to_coordinates(self: Self) -> list[Coordinates]:
        """Convert to list of Coordinates."""
        if self.coordinates:
            return self.coordinates
        return [
            Coordinates(lat=lat, lon=lon)
            for lat, lon in zip(self.latitude, self.longitude)
        ]


# =============================================================================
# Travel Cost Configuration
# =============================================================================


class TravelTimeCost(BaseModel):
    """Travel time cost configuration."""

    max_traveltime: int = Field(
        ...,
        ge=1,
        le=120,
        description="Maximum travel time in minutes",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=10,
        ),
    )
    traveltime_step: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Step size for travel time intervals in minutes",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=11,
        ),
    )


class TravelDistanceCost(BaseModel):
    """Travel distance cost configuration."""

    max_distance: int = Field(
        ...,
        ge=50,
        le=50000,
        description="Maximum travel distance in meters",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=10,
        ),
    )
    distance_step: int = Field(
        default=100,
        ge=50,
        le=5000,
        description="Step size for distance intervals in meters",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=11,
        ),
    )


class DecayFunction(BaseModel):
    """Decay function configuration for PT routing."""

    type: DecayFunctionType = Field(
        default=DecayFunctionType.step, description="Type of decay function"
    )
    standard_deviation_minutes: int | None = Field(
        default=12, description="Standard deviation for logistic decay"
    )
    width_minutes: int | None = Field(
        default=10, description="Width for exponential decay"
    )


class TravelTimeCostPT(BaseModel):
    """Travel time cost configuration for public transport."""

    max_traveltime: int = Field(
        ...,
        ge=1,
        le=120,
        description="Maximum total travel time in minutes",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=10,
        ),
    )
    steps: list[int] | None = Field(
        default=None,
        description="Custom travel time cutoffs in minutes (e.g., [15, 30, 45, 60])",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=11,
        ),
    )
    decay_function: DecayFunction = Field(
        default_factory=DecayFunction,
        description="Decay function for accessibility weighting",
    )


# =============================================================================
# Mode-Specific Settings
# =============================================================================


class ActiveMobilitySettings(BaseModel):
    """Settings specific to active mobility modes."""

    speed: float | None = Field(
        default=None,
        ge=1.0,
        le=30.0,
        description="Travel speed in km/h (uses mode default if not set)",
        json_schema_extra=ui_field(
            section="routing",
            field_order=5,
        ),
    )


class CarSettings(BaseModel):
    """Settings specific to car routing."""

    traffic_factor: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Traffic congestion factor (1.0 = free flow)",
        json_schema_extra=ui_field(
            section="routing",
            field_order=5,
        ),
    )


class PTTimeWindow(BaseModel):
    """Time window configuration for public transport."""

    weekday: Literal["weekday", "saturday", "sunday"] = Field(
        default="weekday",
        description="Day type for PT schedule",
        json_schema_extra=ui_field(
            section="time",
            field_order=1,
        ),
    )
    from_time: time | int = Field(
        ...,
        description="Start time (HH:MM or seconds from midnight)",
        json_schema_extra=ui_field(
            section="time",
            field_order=2,
        ),
    )
    to_time: time | int = Field(
        ...,
        description="End time (HH:MM or seconds from midnight)",
        json_schema_extra=ui_field(
            section="time",
            field_order=3,
        ),
    )

    @field_validator("from_time", "to_time", mode="before")
    @classmethod
    def normalize_time(cls: type[Self], v: time | int) -> int:
        """Convert time to seconds from midnight if needed."""
        if isinstance(v, time):
            return v.hour * 3600 + v.minute * 60 + v.second
        return v


class PTSettings(BaseModel):
    """Settings specific to public transport routing."""

    time_window: PTTimeWindow = Field(
        ...,
        description="Time window for PT schedule queries",
    )
    access_mode: AccessEgressMode = Field(
        default=AccessEgressMode.walk,
        description="Mode used to access transit stops",
        json_schema_extra=ui_field(
            section="routing",
            field_order=5,
        ),
    )
    egress_mode: AccessEgressMode = Field(
        default=AccessEgressMode.walk,
        description="Mode used after leaving transit",
        json_schema_extra=ui_field(
            section="routing",
            field_order=6,
        ),
    )
    transit_modes: list[PTMode] = Field(
        default_factory=lambda: list(PTMode),
        description="Transit modes to include in routing",
        json_schema_extra=ui_field(
            section="routing",
            field_order=7,
        ),
    )
    max_access_time: int = Field(
        default=15,
        ge=1,
        le=60,
        description="Maximum time to access transit in minutes",
        json_schema_extra=ui_field(
            section="routing",
            field_order=8,
        ),
    )
    max_egress_time: int = Field(
        default=15,
        ge=1,
        le=60,
        description="Maximum time after leaving transit in minutes",
        json_schema_extra=ui_field(
            section="routing",
            field_order=9,
        ),
    )
    max_transfers: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of transfers allowed",
        json_schema_extra=ui_field(
            section="routing",
            field_order=10,
        ),
    )


# =============================================================================
# Catchment Area Request Models
# =============================================================================


class CatchmentAreaBase(BaseModel):
    """Base parameters shared by all catchment area requests."""

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            SECTION_ROUTING,
            SECTION_TIME,
            SECTION_CONFIGURATION,
            SECTION_OUTPUT,
        )
    )

    starting_points: StartingPoints = Field(
        ...,
        description="Starting points for catchment area analysis",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
        ),
    )
    catchment_area_type: CatchmentAreaType = Field(
        default=CatchmentAreaType.polygon,
        description="Type of catchment area output",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=1,
        ),
    )
    polygon_difference: bool | None = Field(
        default=None,
        description="Whether to compute difference between time steps (only for polygon type)",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
        ),
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.geojson,
        description="Output format for results",
        json_schema_extra=ui_field(
            section="output",
            field_order=1,
        ),
    )

    @model_validator(mode="after")
    def validate_polygon_difference(self: Self) -> Self:
        """Ensure polygon_difference is only set for polygon type."""
        if (
            self.polygon_difference is not None
            and self.catchment_area_type != CatchmentAreaType.polygon
        ):
            raise ValueError(
                "polygon_difference can only be set when catchment_area_type is 'polygon'"
            )
        return self


class CatchmentAreaActiveMobilityRequest(CatchmentAreaBase):
    """Catchment area request for active mobility modes."""

    mode: Literal["active_mobility"] = Field(
        default="active_mobility",
        description="Mode discriminator",
        json_schema_extra=ui_field(section="routing", hidden=True),
    )
    routing_mode: ActiveMobilityMode = Field(
        ...,
        description="Active mobility transport mode",
        json_schema_extra=ui_field(
            section="routing",
            field_order=1,
        ),
    )
    travel_cost: TravelTimeCost | TravelDistanceCost = Field(
        ...,
        description="Travel cost configuration (time or distance based)",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=5,
        ),
    )
    settings: ActiveMobilitySettings = Field(
        default_factory=ActiveMobilitySettings,
        description="Mode-specific settings",
    )
    scenario_id: str | None = Field(
        default=None,
        description="Scenario ID for network modifications",
        json_schema_extra=ui_field(
            section="scenario",
            field_order=1,
        ),
    )
    routing_provider: Literal[RoutingProvider.goat_routing] = Field(
        default=RoutingProvider.goat_routing,
        description="Routing provider (goat_routing for active mobility)",
        json_schema_extra=ui_field(section="routing", hidden=True),
    )


class CatchmentAreaCarRequest(CatchmentAreaBase):
    """Catchment area request for car mode."""

    mode: Literal["car"] = Field(
        default="car",
        description="Mode discriminator",
        json_schema_extra=ui_field(section="routing", hidden=True),
    )
    routing_mode: CarMode = Field(
        default=CarMode.car,
        description="Car transport mode",
        json_schema_extra=ui_field(
            section="routing",
            field_order=1,
        ),
    )
    travel_cost: TravelTimeCost | TravelDistanceCost = Field(
        ...,
        description="Travel cost configuration (time or distance based)",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=5,
        ),
    )
    settings: CarSettings = Field(
        default_factory=CarSettings,
        description="Mode-specific settings",
    )
    scenario_id: str | None = Field(
        default=None,
        description="Scenario ID for network modifications",
        json_schema_extra=ui_field(
            section="scenario",
            field_order=1,
        ),
    )
    routing_provider: Literal[RoutingProvider.goat_routing] = Field(
        default=RoutingProvider.goat_routing,
        description="Routing provider (goat_routing for car)",
        json_schema_extra=ui_field(section="routing", hidden=True),
    )


class CatchmentAreaPTRequest(CatchmentAreaBase):
    """Catchment area request for public transport."""

    mode: Literal["pt"] = Field(
        default="pt",
        description="Mode discriminator",
        json_schema_extra=ui_field(section="routing", hidden=True),
    )
    travel_cost: TravelTimeCostPT = Field(
        ...,
        description="Travel cost configuration for PT",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=5,
        ),
    )
    settings: PTSettings = Field(
        ...,
        description="PT-specific settings including time window",
    )
    routing_provider: RoutingProvider = Field(
        default=RoutingProvider.r5,
        description="Routing provider for PT (r5, motis, otp)",
        json_schema_extra=ui_field(
            section="routing",
            field_order=1,
        ),
    )


# Union type for all catchment area requests
CatchmentAreaRequest = Annotated[
    CatchmentAreaActiveMobilityRequest
    | CatchmentAreaCarRequest
    | CatchmentAreaPTRequest,
    Field(discriminator="mode"),
]


# =============================================================================
# Response Models
# =============================================================================


class CatchmentAreaPolygon(BaseModel):
    """A single catchment area polygon result."""

    travel_cost: int = Field(..., description="Travel cost value for this polygon")
    geometry: dict = Field(..., description="GeoJSON geometry")
    area_sqm: float | None = Field(default=None, description="Area in square meters")


class CatchmentAreaResponse(BaseModel):
    """Response from catchment area analysis."""

    model_config = ConfigDict(extra="allow")

    starting_point: Coordinates = Field(..., description="The starting point used")
    catchment_area_type: CatchmentAreaType = Field(
        ..., description="Type of catchment area"
    )
    polygons: list[CatchmentAreaPolygon] | None = Field(
        default=None, description="Catchment area polygons (for polygon type)"
    )
    network: dict | None = Field(
        default=None, description="Network edges GeoJSON (for network type)"
    )
    grid: dict | None = Field(
        default=None, description="Grid cells GeoJSON (for rectangular_grid type)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (timing, provider, etc.)",
    )
