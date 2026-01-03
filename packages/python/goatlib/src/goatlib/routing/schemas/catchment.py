"""
Unified catchment area schemas for routing in goatlib.

This module provides unified request/response models for catchment area
computations across all transport modes (active mobility, car, PT).
"""

from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from goatlib.routing.schemas.base import (
    AccessEgressMode,
    ActiveMobilityMode,
    CarMode,
    CatchmentAreaType,
    Coordinates,
    OutputFormat,
    PTMode,
    PTTimeWindow,
    RoutingProvider,
    StartingPoints,
)
from goatlib.routing.schemas.travel_cost import (
    DecayFunction,
    TravelCostActiveMobility,
    TravelCostMotorized,
    TravelTimeCostPT,
)


# =============================================================================
# Mode-Specific Settings
# =============================================================================


class ActiveMobilitySettings(BaseModel):
    """Settings specific to active mobility routing."""

    routing_type: ActiveMobilityMode = Field(
        ...,
        title="Routing Type",
        description="The active mobility routing mode.",
    )


class CarSettings(BaseModel):
    """Settings specific to car routing."""

    routing_type: CarMode = Field(
        default=CarMode.car,
        title="Routing Type",
        description="The car routing mode.",
    )


class PTSettings(BaseModel):
    """Settings specific to public transport routing."""

    transit_modes: List[PTMode] = Field(
        ...,
        title="Transit Modes",
        description="List of transit modes to include in routing.",
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
    time_window: PTTimeWindow = Field(
        ...,
        title="Time Window",
        description="Time window for PT routing.",
    )
    decay_function: Optional[DecayFunction] = Field(
        default_factory=DecayFunction,
        title="Decay Function",
        description="Decay function for accessibility calculations.",
    )
    # R5-specific defaults
    walk_speed: float = Field(default=1.39, description="Walking speed in m/s")
    max_walk_time: int = Field(default=20, description="Max walk time in minutes")
    bike_speed: float = Field(default=4.17, description="Bike speed in m/s")
    max_bike_time: int = Field(default=20, description="Max bike time in minutes")
    bike_traffic_stress: int = Field(default=4, description="Bike traffic stress level")
    max_rides: int = Field(default=4, description="Maximum number of rides/transfers")


# =============================================================================
# Street Network Configuration
# =============================================================================


class StreetNetworkConfig(BaseModel):
    """Configuration for custom street network layers."""

    edge_layer_project_id: int = Field(
        ...,
        title="Edge Layer Project ID",
        description="The layer project ID of the street network edge layer.",
    )
    node_layer_project_id: Optional[int] = Field(
        default=None,
        title="Node Layer Project ID",
        description="The layer project ID of the street network node layer.",
    )


# =============================================================================
# Catchment Area Request Models
# =============================================================================


class CatchmentAreaActiveMobilityRequest(BaseModel):
    """Request model for active mobility catchment area computation."""

    starting_points: StartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting points for catchment area computation.",
    )
    routing_type: ActiveMobilityMode = Field(
        ...,
        title="Routing Type",
        description="The active mobility routing mode.",
    )
    travel_cost: TravelCostActiveMobility = Field(
        ...,
        title="Travel Cost",
        description="Travel cost configuration (time or distance based).",
    )
    catchment_area_type: CatchmentAreaType = Field(
        ...,
        title="Catchment Area Type",
        description="The output geometry type.",
    )
    polygon_difference: Optional[bool] = Field(
        None,
        title="Polygon Difference",
        description="If true, return geometrical difference between consecutive isochrones.",
    )
    scenario_id: Optional[UUID] = Field(
        None,
        title="Scenario ID",
        description="Optional scenario ID for network modifications.",
    )
    street_network: Optional[StreetNetworkConfig] = Field(
        None,
        title="Street Network",
        description="Custom street network configuration.",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.geojson,
        title="Output Format",
        description="Output format for results.",
    )

    @model_validator(mode="after")
    def validate_polygon_difference(self) -> Self:
        """Validate polygon_difference is set correctly based on catchment_area_type."""
        if self.catchment_area_type == CatchmentAreaType.polygon:
            if self.polygon_difference is None:
                raise ValueError(
                    "polygon_difference must be set when catchment_area_type is 'polygon'."
                )
        else:
            if self.polygon_difference is not None:
                raise ValueError(
                    "polygon_difference should not be set when catchment_area_type is not 'polygon'."
                )
        return self


class CatchmentAreaCarRequest(BaseModel):
    """Request model for car catchment area computation."""

    starting_points: StartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting points for catchment area computation.",
    )
    routing_type: CarMode = Field(
        default=CarMode.car,
        title="Routing Type",
        description="The car routing mode.",
    )
    travel_cost: TravelCostMotorized = Field(
        ...,
        title="Travel Cost",
        description="Travel cost configuration (time or distance based).",
    )
    catchment_area_type: CatchmentAreaType = Field(
        ...,
        title="Catchment Area Type",
        description="The output geometry type.",
    )
    polygon_difference: Optional[bool] = Field(
        None,
        title="Polygon Difference",
        description="If true, return geometrical difference between consecutive isochrones.",
    )
    scenario_id: Optional[UUID] = Field(
        None,
        title="Scenario ID",
        description="Optional scenario ID for network modifications.",
    )
    street_network: Optional[StreetNetworkConfig] = Field(
        None,
        title="Street Network",
        description="Custom street network configuration.",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.geojson,
        title="Output Format",
        description="Output format for results.",
    )

    @model_validator(mode="after")
    def validate_polygon_difference(self) -> Self:
        """Validate polygon_difference is set correctly based on catchment_area_type."""
        if self.catchment_area_type == CatchmentAreaType.polygon:
            if self.polygon_difference is None:
                raise ValueError(
                    "polygon_difference must be set when catchment_area_type is 'polygon'."
                )
        else:
            if self.polygon_difference is not None:
                raise ValueError(
                    "polygon_difference should not be set when catchment_area_type is not 'polygon'."
                )
        return self


class CatchmentAreaPTRequest(BaseModel):
    """Request model for public transport catchment area computation."""

    starting_points: StartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting point for catchment area computation (single point only for PT).",
    )
    pt_settings: PTSettings = Field(
        ...,
        title="PT Settings",
        description="Public transport routing settings.",
    )
    travel_cost: TravelTimeCostPT = Field(
        ...,
        title="Travel Cost",
        description="Travel time cost configuration with cutoffs.",
    )
    catchment_area_type: CatchmentAreaType = Field(
        default=CatchmentAreaType.polygon,
        title="Catchment Area Type",
        description="The output geometry type (polygon or rectangular_grid for PT).",
    )
    polygon_difference: Optional[bool] = Field(
        None,
        title="Polygon Difference",
        description="If true, return geometrical difference between consecutive isochrones.",
    )
    scenario_id: Optional[UUID] = Field(
        None,
        title="Scenario ID",
        description="Optional scenario ID for network modifications.",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.geojson,
        title="Output Format",
        description="Output format for results.",
    )

    @model_validator(mode="after")
    def validate_single_starting_point(self) -> Self:
        """Validate that only one starting point is provided for PT."""
        if self.starting_points.count > 1:
            raise ValueError(
                "Public transport catchment areas support only a single starting point."
            )
        return self

    @model_validator(mode="after")
    def validate_polygon_difference(self) -> Self:
        """Validate polygon_difference is set correctly based on catchment_area_type."""
        if self.catchment_area_type == CatchmentAreaType.polygon:
            if self.polygon_difference is None:
                raise ValueError(
                    "polygon_difference must be set when catchment_area_type is 'polygon'."
                )
        else:
            if self.polygon_difference is not None:
                raise ValueError(
                    "polygon_difference should not be set when catchment_area_type is not 'polygon'."
                )
        return self


# =============================================================================
# Unified Catchment Area Request
# =============================================================================


class CatchmentAreaRequest(BaseModel):
    """
    Unified catchment area request that can handle all transport modes.

    This is the main entry point for catchment area computations. The mode
    field determines which backend and settings to use.
    """

    mode: Literal["active_mobility", "car", "pt"] = Field(
        ...,
        title="Mode",
        description="The transport mode category for routing.",
    )
    provider: RoutingProvider = Field(
        default=RoutingProvider.goat_routing,
        title="Provider",
        description="The routing provider to use.",
    )
    starting_points: StartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting points for catchment area computation.",
    )
    catchment_area_type: CatchmentAreaType = Field(
        ...,
        title="Catchment Area Type",
        description="The output geometry type.",
    )
    polygon_difference: Optional[bool] = Field(
        None,
        title="Polygon Difference",
        description="If true, return geometrical difference between consecutive isochrones.",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.geojson,
        title="Output Format",
        description="Output format for results.",
    )
    scenario_id: Optional[UUID] = Field(
        None,
        title="Scenario ID",
        description="Optional scenario ID for network modifications.",
    )
    street_network: Optional[StreetNetworkConfig] = Field(
        None,
        title="Street Network",
        description="Custom street network configuration.",
    )

    # Mode-specific settings (only one should be set based on mode)
    active_mobility: Optional[ActiveMobilitySettings] = Field(
        None,
        title="Active Mobility Settings",
        description="Settings for active mobility mode.",
    )
    car: Optional[CarSettings] = Field(
        None,
        title="Car Settings",
        description="Settings for car mode.",
    )
    pt: Optional[PTSettings] = Field(
        None,
        title="PT Settings",
        description="Settings for public transport mode.",
    )

    # Travel cost - type depends on mode
    travel_cost: Dict[str, Any] = Field(
        ...,
        title="Travel Cost",
        description="Travel cost configuration (structure depends on mode).",
    )

    @model_validator(mode="after")
    def validate_mode_settings(self) -> Self:
        """Ensure the correct settings object is provided for the selected mode."""
        if self.mode == "active_mobility" and self.active_mobility is None:
            raise ValueError(
                "active_mobility settings must be provided when mode is 'active_mobility'."
            )
        if self.mode == "car" and self.car is None:
            # Car settings have defaults, so auto-create if not provided
            self.car = CarSettings()
        if self.mode == "pt" and self.pt is None:
            raise ValueError("pt settings must be provided when mode is 'pt'.")
        return self

    @model_validator(mode="after")
    def validate_polygon_difference(self) -> Self:
        """Validate polygon_difference is set correctly based on catchment_area_type."""
        if self.catchment_area_type == CatchmentAreaType.polygon:
            if self.polygon_difference is None:
                raise ValueError(
                    "polygon_difference must be set when catchment_area_type is 'polygon'."
                )
        else:
            if self.polygon_difference is not None:
                raise ValueError(
                    "polygon_difference should not be set when catchment_area_type is not 'polygon'."
                )
        return self


# =============================================================================
# Catchment Area Response Models
# =============================================================================


class CatchmentAreaPolygon(BaseModel):
    """A single catchment area polygon with its properties."""

    travel_cost: int = Field(
        ...,
        title="Travel Cost",
        description="Travel cost value (time in minutes or distance in meters).",
    )
    geometry: Dict[str, Any] = Field(
        ...,
        title="Geometry",
        description="GeoJSON geometry of the catchment area.",
    )


class CatchmentAreaResponse(BaseModel):
    """Response model for catchment area computation."""

    polygons: List[CatchmentAreaPolygon] = Field(
        default_factory=list,
        title="Polygons",
        description="List of catchment area polygons.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        title="Metadata",
        description="Additional metadata about the computation.",
    )
    request_id: Optional[str] = Field(
        None,
        title="Request ID",
        description="Unique identifier for this request.",
    )


# =============================================================================
# Type Aliases
# =============================================================================

CatchmentAreaRequestType = Union[
    CatchmentAreaActiveMobilityRequest,
    CatchmentAreaCarRequest,
    CatchmentAreaPTRequest,
    CatchmentAreaRequest,
]
