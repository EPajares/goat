"""
Catchment Area schemas for goatlib analysis.

This module provides schemas for catchment area analysis across
different transport modes (active mobility, car, public transport).
"""

import logging
from datetime import time
from enum import StrEnum
from typing import Literal, Self

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


class CatchmentAreaRoutingMode(StrEnum):
    """Routing modes for catchment area analysis."""

    walking = "walking"
    bicycle = "bicycle"
    pedelec = "pedelec"
    wheelchair = "wheelchair"
    car = "car"
    pt = "pt"  # Public transport


# =============================================================================
# PT Time Window
# =============================================================================


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


# =============================================================================
# Tool Parameters Schema
# =============================================================================


class CatchmentAreaToolParams(BaseModel):
    """
    Parameters for CatchmentAreaTool.

    This schema defines the input parameters for computing catchment areas
    (isochrones) via routing services.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            SECTION_ROUTING,
            SECTION_TIME,
            SECTION_CONFIGURATION,
            SECTION_OUTPUT,
        )
    )

    # === Starting Point ===
    latitude: float | list[float] = Field(
        ...,
        description="Starting point latitude(s)",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
        ),
    )
    longitude: float | list[float] = Field(
        ...,
        description="Starting point longitude(s)",
        json_schema_extra=ui_field(
            section="input",
            field_order=2,
        ),
    )

    # === Routing Configuration ===
    routing_mode: CatchmentAreaRoutingMode = Field(
        default=CatchmentAreaRoutingMode.walking,
        description="Transport mode for routing",
        json_schema_extra=ui_field(
            section="routing",
            field_order=1,
        ),
    )
    travel_time: int = Field(
        default=15,
        ge=1,
        le=120,
        description="Maximum travel time in minutes",
        json_schema_extra=ui_field(
            section="routing",
            field_order=2,
        ),
    )
    steps: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of isochrone steps",
        json_schema_extra=ui_field(
            section="routing",
            field_order=3,
        ),
    )
    speed: float | None = Field(
        default=None,
        ge=1.0,
        le=50.0,
        description="Travel speed in km/h (active mobility only, uses default if not set)",
        json_schema_extra=ui_field(
            section="routing",
            field_order=4,
            visible_when={
                "routing_mode": {"$in": ["walking", "bicycle", "pedelec", "wheelchair"]}
            },
        ),
    )

    # === PT-specific settings ===
    transit_modes: list[PTMode] | None = Field(
        default=None,
        description="Transit modes to include (required for PT routing)",
        json_schema_extra=ui_field(
            section="routing",
            field_order=5,
            visible_when={"routing_mode": "pt"},
        ),
    )
    time_window: PTTimeWindow | None = Field(
        default=None,
        description="Time window for PT schedule queries (required for PT routing)",
        json_schema_extra=ui_field(
            section="time",
            field_order=1,
            visible_when={"routing_mode": "pt"},
        ),
    )
    access_mode: AccessEgressMode = Field(
        default=AccessEgressMode.walk,
        description="Mode to access transit stops",
        json_schema_extra=ui_field(
            section="routing",
            field_order=6,
            visible_when={"routing_mode": "pt"},
        ),
    )
    egress_mode: AccessEgressMode = Field(
        default=AccessEgressMode.walk,
        description="Mode from transit stops to destination",
        json_schema_extra=ui_field(
            section="routing",
            field_order=7,
            visible_when={"routing_mode": "pt"},
        ),
    )

    # === Output Configuration ===
    catchment_area_type: CatchmentAreaType = Field(
        default=CatchmentAreaType.polygon,
        description="Output geometry type",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
        ),
    )
    polygon_difference: bool = Field(
        default=True,
        description="Whether to compute difference between time steps",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=3,
            visible_when={"catchment_area_type": "polygon"},
        ),
    )
    output_path: str = Field(
        ...,
        description="Output path for results (parquet or geojson)",
        json_schema_extra=ui_field(
            section="output",
            field_order=1,
            hidden=True,  # Internal field, auto-populated
        ),
    )

    # === Routing Service Configuration (internal) ===
    routing_url: str = Field(
        ...,
        description="Routing service URL",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=20,
            hidden=True,  # Internal field, set by tool runner
        ),
    )
    authorization: str | None = Field(
        default=None,
        description="Authorization header for routing services",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=21,
            hidden=True,  # Internal field, set by tool runner
        ),
    )
    r5_region_mapping_path: str | None = Field(
        default=None,
        description="Path to parquet file with R5 region boundaries for automatic region lookup",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=22,
            hidden=True,  # Internal field, set by tool runner
        ),
    )

    # === Optional Settings ===
    scenario_id: str | None = Field(
        default=None,
        description="Scenario ID for network modifications",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=10,
            hidden=True,  # Advanced setting
        ),
    )

    @model_validator(mode="after")
    def validate_pt_settings(self: Self) -> Self:
        """Validate PT-specific settings when routing_mode is 'pt'."""
        if self.routing_mode == CatchmentAreaRoutingMode.pt:
            if not self.transit_modes:
                raise ValueError("transit_modes is required when routing_mode is 'pt'")
            if not self.time_window:
                raise ValueError("time_window is required when routing_mode is 'pt'")
        return self

    @model_validator(mode="after")
    def validate_polygon_difference(self: Self) -> Self:
        """Ensure polygon_difference is only set for polygon type."""
        if (
            self.polygon_difference
            and self.catchment_area_type != CatchmentAreaType.polygon
        ):
            # Reset to False for non-polygon types
            self.polygon_difference = False
        return self
