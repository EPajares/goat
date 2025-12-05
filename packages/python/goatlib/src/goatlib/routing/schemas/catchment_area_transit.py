from typing import Any, Dict, List, Optional, Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from goatlib.routing.schemas.base import (
    AccessEgressMode,
    CatchmentAreaRoutingModePT,
    CatchmentAreaStartingPoints,
)


class TransitCatchmentAreaStartingPoints(CatchmentAreaStartingPoints):
    """Transit CatchmentArea starting points with single-point constraint."""

    @model_validator(mode="after")
    def validate_transit_constraints(
        self: "TransitCatchmentAreaStartingPoints",
    ) -> "TransitCatchmentAreaStartingPoints":
        """Ensure single starting point for transit CatchmentAreas."""
        if self.latitude and len(self.latitude) > 1:
            raise ValueError(
                "Transit CatchmentAreas support only single starting point."
            )
        return self


"""Travel time configuration """


class TransitCatchmentAreaTravelTimeCost(BaseModel):
    """Travel time configuration for transit CatchmentAreas with cutoffs instead of steps."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=90,
    )

    cutoffs: List[int] = Field(
        ...,
        title="Time Cutoffs",
        description="List of travel time cutoffs in minutes for CatchmentArea bands.",
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_cutoffs_against_max_time(self) -> Self:
        """Validate that cutoffs are within max_traveltime and sorted."""
        max_time = self.max_traveltime
        for cutoff in self.cutoffs:
            if cutoff > max_time:
                raise ValueError(
                    f"Cutoff {cutoff} exceeds maximum travel time {max_time}."
                )

        if not all(c > 0 for c in self.cutoffs):
            raise ValueError("All cutoffs must be positive.")

        if self.cutoffs != sorted(list(set(self.cutoffs))):
            raise ValueError("Cutoffs must be unique and in ascending order.")

        return self


class _ActiveMobilitySettings(BaseModel):
    """Base configuration for an active mobility leg of a journey."""

    max_time: int
    speed: float


class WalkSettings(_ActiveMobilitySettings):
    """Configuration for walking legs of the journey."""

    max_time: int = Field(15, title="Maximum Walk Time (minutes)", ge=1, le=30)

    speed: float = Field(
        5.0,
        title="Walking Speed (km/h)",
        description="Average walking speed in kilometers per hour.",
        ge=1.0,
        le=10.0,
    )


class BikeSettings(_ActiveMobilitySettings):
    """Configuration for biking legs of the journey."""

    max_time: int = Field(20, title="Maximum Bike Time (minutes)", ge=1, le=45)

    speed: float = Field(
        15.0,
        title="Biking Speed (km/h)",
        description="Average biking speed in kilometers per hour.",
        ge=5.0,
        le=30.0,
    )


class TransitRoutingSettings(BaseModel):
    """Advanced tuning parameters for the transit routing algorithm."""

    max_transfers: int = Field(4, title="Maximum Transfers", ge=0, le=10)
    walk_settings: WalkSettings = Field(default_factory=WalkSettings)
    bike_settings: BikeSettings = Field(default_factory=BikeSettings)


"""Main request schema."""


class TransitCatchmentAreaRequest(BaseModel):
    """Request model for transit CatchmentArea calculation."""

    starting_points: TransitCatchmentAreaStartingPoints = Field(
        ...,
        title="Starting Points",
        description="Starting points for CatchmentArea calculation.",
    )
    transit_modes: List[CatchmentAreaRoutingModePT] = Field(
        ...,
        title="Transit Modes",
        description="List of transit modes to include in the CatchmentArea calculation.",
        min_length=1,
    )
    access_mode: AccessEgressMode = Field(
        default=AccessEgressMode.walk,
        title="Access Mode",
        description="Mode of transportation to access transit stops.",
    )
    egress_mode: AccessEgressMode = Field(
        default=AccessEgressMode.walk,
        title="Egress Mode",
        description="Mode of transportation from transit stops to destination.",
    )
    travel_cost: TransitCatchmentAreaTravelTimeCost = Field(
        ...,
        title="Travel Cost Configuration",
        description="Travel time and cutoff configuration.",
    )
    network_id: Optional[UUID] = Field(
        default=None,
        title="Network ID",
        description="Optional ID of the transit network to use for routing calculations.",
    )

    routing_settings: TransitRoutingSettings = Field(
        default_factory=TransitRoutingSettings,
        title="Routing Settings",
        description="Advanced routing settings.",
    )


"""Response schemas."""


class CatchmentAreaPolygon(BaseModel):
    """A single catchment area polygon with its properties."""

    travel_time: int = Field(
        ...,
        title="Travel Time",
        description="Maximum travel time for this catchment area in minutes.",
    )
    geometry: Dict[str, Any] = Field(
        ...,
        title="Polygon Geometry",
        description="Polygon geometry data (coordinates, type, etc.)",
    )

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate basic polygon geometry structure."""
        if not isinstance(v, dict):
            raise ValueError("Geometry must be a dictionary.")

        required_fields = ["type", "coordinates"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Geometry must have a '{field}' field.")

        return v


class TransitCatchmentAreaResponse(BaseModel):
    """Response model for transit catchment area calculation."""

    polygons: List[CatchmentAreaPolygon] = Field(
        ...,
        title="Catchment Area Polygons",
        description="List of catchment area polygons with travel times.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        title="Metadata",
        description="Additional metadata about the calculation.",
    )
    request_id: Optional[str] = Field(
        default=None,
        title="Request ID",
        description="Unique identifier for the request.",
    )


"""Example requests."""


request_examples_transit_catchment_area = {
    "basic_transit_catchment_area": {
        "summary": "basic transit catchment area request",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "transit_modes": ["bus", "tram", "subway"],
            "travel_cost": {"max_traveltime": 60, "cutoffs": [15, 30, 45, 60]},
        },
    },
    "bike_access_catchment_area": {
        "summary": "bike access catchment area request",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "transit_modes": ["rail", "subway"],
            "access_mode": "bicycle",
            "travel_cost": {"max_traveltime": 45, "cutoffs": [15, 30, 45]},
            "routing_settings": {"bike_settings": {"max_time": 25}},
        },
    },
    "custom_speeds_catchment_area": {
        "summary": "custom speeds catchment area request",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "transit_modes": ["bus", "tram"],
            "egress_mode": "bicycle",
            "travel_cost": {"max_traveltime": 50, "cutoffs": [10, 20, 30, 40, 50]},
            "routing_settings": {
                "walk_settings": {"speed": 1.2},
                "bike_settings": {"speed": 5.0},
            },
        },
    },
}
