from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

"""Transit-specific routing mode schemas."""


class BaseStartingPoints(BaseModel):
    """Base model for starting points."""

    latitude: List[float] | None = Field(
        None,
        title="Latitude",
        description="The latitude of the starting points.",
    )
    longitude: List[float] | None = Field(
        None,
        title="Longitude",
        description="The longitude of the starting points.",
    )


class BaseTravelTimeCost(BaseModel):
    """Base travel time cost schema."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=90,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )

    @field_validator("steps", mode="before")
    @classmethod
    def valid_num_steps(cls: type["BaseTravelTimeCost"], v: int) -> int:
        """Ensure the number of steps doesn't exceed the maximum traveltime."""
        if v > 90:
            raise ValueError(
                "The number of steps must not exceed the maximum traveltime."
            )
        return v


class TransitMode(str, Enum):
    """Transit mode options for isochrone calculation."""

    bus = "bus"
    tram = "tram"
    rail = "rail"
    subway = "subway"
    ferry = "ferry"
    cable_car = "cable_car"
    gondola = "gondola"
    funicular = "funicular"


class AccessEgressMode(str, Enum):
    """Access mode to reach transit stops."""

    walk = "walk"
    bicycle = "bicycle"


"""Transit isochrone starting points - extends catchment area with transit constraints."""


class TransitIsochroneStartingPoints(BaseStartingPoints):
    """Transit isochrone starting points with single-point constraint."""

    @model_validator(mode="after")
    def validate_transit_constraints(
        self: "TransitIsochroneStartingPoints",
    ) -> "TransitIsochroneStartingPoints":
        """Ensure single starting point for transit isochrones."""
        if self.latitude and len(self.latitude) > 1:
            raise ValueError("Transit isochrones support only single starting point.")
        return self


"""Travel time configuration - extends catchment area with isochrone-specific cutoffs."""


class TransitIsochroneTravelTimeCost(BaseTravelTimeCost):
    """Travel time configuration for transit isochrones with cutoffs instead of steps."""

    cutoffs: List[int] = Field(
        ...,
        title="Time Cutoffs",
        description="List of travel time cutoffs in minutes for isochrone bands.",
        min_length=1,
    )

    @field_validator("cutoffs", mode="after")
    @classmethod
    def validate_cutoffs(
        cls: type["TransitIsochroneTravelTimeCost"],
        cutoffs: List[int],
        info: ValidationInfo,
    ) -> List[int]:
        """Validate that cutoffs are within max_traveltime and sorted."""
        if "max_traveltime" in info.data:
            max_time = info.data["max_traveltime"]
            for cutoff in cutoffs:
                if cutoff > max_time:
                    raise ValueError(
                        f"Cutoff {cutoff} exceeds maximum travel time {max_time}."
                    )

        # Ensure cutoffs are positive and sorted
        if not all(c > 0 for c in cutoffs):
            raise ValueError("All cutoffs must be positive.")

        if cutoffs != sorted(cutoffs):
            raise ValueError("Cutoffs must be in ascending order.")

        return cutoffs


"""Main request schema."""


class TransitIsochroneRequest(BaseModel):
    """Request model for transit isochrone calculation."""

    starting_points: TransitIsochroneStartingPoints = Field(
        ...,
        title="Starting Points",
        description="Starting points for isochrone calculation.",
    )
    transit_modes: List[TransitMode] = Field(
        ...,
        title="Transit Modes",
        description="List of transit modes to include in the isochrone calculation.",
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
    travel_cost: TransitIsochroneTravelTimeCost = Field(
        ...,
        title="Travel Cost Configuration",
        description="Travel time and cutoff configuration.",
    )
    # UPDATE
    network_id: Optional[UUID] = Field(
        default=None,
        title="Network ID",
        description="",
    )

    # Transit-specific configuration
    max_walk_time: int = Field(
        default=15,
        title="Maximum Walk Time",
        description="Maximum walking time to/from transit stops in minutes.",
        ge=1,
        le=30,
    )
    max_bike_time: int = Field(
        default=20,
        title="Maximum Bike Time",
        description="Maximum biking time to/from transit stops in minutes.",
        ge=1,
        le=45,
    )
    max_transfers: int = Field(
        default=4,
        title="Maximum Transfers",
        description="Maximum number of transit transfers allowed.",
        ge=0,
        le=10,
    )
    walk_speed: float = Field(
        default=1.39,  # m/s, ~5 km/h
        title="Walking Speed",
        description="Walking speed in meters per second.",
        ge=0.5,
        le=3.0,
    )
    bike_speed: float = Field(
        default=4.17,  # m/s, ~15 km/h
        title="Biking Speed",
        description="Biking speed in meters per second.",
        ge=1.0,
        le=8.0,
    )


"""Response schemas."""


# TODO: remove the class and make it a validator
class IsochroneGeometry(BaseModel):
    """GeoJSON geometry for isochrone polygon."""

    type: str = Field(
        default="Polygon",
        title="Geometry Type",
        description="GeoJSON geometry type.",
    )
    coordinates: List[List[List[float]]] = Field(
        ...,
        title="Coordinates",
        description="Polygon coordinates in GeoJSON format.",
    )


class IsochroneProperties(BaseModel):
    """Properties of an isochrone polygon."""

    travel_time: int = Field(
        ...,
        title="Travel Time",
        description="Maximum travel time for this isochrone in minutes.",
    )
    area_km2: Optional[float] = Field(
        default=None,
        title="Area",
        description="Area of the isochrone polygon in square kilometers.",
        ge=0.0,
    )


class IsochroneFeature(BaseModel):
    """GeoJSON feature representing an isochrone polygon."""

    type: str = Field(
        default="Feature",
        title="Feature Type",
        description="GeoJSON feature type.",
    )
    geometry: IsochroneGeometry = Field(
        ...,
        title="Geometry",
        description="Isochrone polygon geometry.",
    )
    properties: IsochroneProperties = Field(
        ...,
        title="Properties",
        description="Isochrone properties and metadata.",
    )


class TransitIsochroneResponse(BaseModel):
    """Response model for transit isochrone calculation."""

    type: str = Field(
        default="FeatureCollection",
        title="Collection Type",
        description="GeoJSON FeatureCollection type.",
    )
    # features: List[IsochroneFeature] = Field(
    #     ...,
    #     title="Isochrone Features",
    #     description="List of isochrone polygon features.",
    # )
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


# response format?
# grid / network / polygon
## POLYGON


"""Example requests."""


request_examples_transit_isochrone = {
    "basic_transit_isochrone": {
        "summary": "Basic transit isochrone with multiple modes",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "transit_modes": ["bus", "tram", "subway"],
            "access_mode": "walk",
            "egress_mode": "walk",
            "travel_cost": {"max_traveltime": 60, "cutoffs": [15, 30, 45, 60]},
        },
    },
    "bike_access_isochrone": {
        "summary": "Transit isochrone with bicycle access",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "transit_modes": ["rail", "subway"],
            "access_mode": "bicycle",
            "egress_mode": "walk",
            "travel_cost": {"max_traveltime": 45, "cutoffs": [15, 30, 45]},
            "max_bike_time": 25,
        },
    },
    "custom_speeds_isochrone": {
        "summary": "Transit isochrone with custom walking and biking speeds",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "transit_modes": ["bus", "tram"],
            "access_mode": "walk",
            "egress_mode": "bicycle",
            "travel_cost": {"max_traveltime": 50, "cutoffs": [10, 20, 30, 40, 50]},
            "walk_speed": 1.2,
            "bike_speed": 5.0,
        },
    },
}
