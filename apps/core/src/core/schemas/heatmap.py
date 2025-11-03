from enum import Enum
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from core.core.config import settings
from core.schemas.colors import ColorRangeType
from core.schemas.layer import ToolType
from core.schemas.toolbox_base import (
    DefaultResultLayerName,
    input_layer_type_point_polygon,
    input_layer_type_polygon,
)


class ActiveRoutingHeatmapType(str, Enum):
    """Supported active mobility types for heatmaps."""

    walking = "walking"
    bicycle = "bicycle"
    pedelec = "pedelec"


class MotorizedRoutingHeatmapType(str, Enum):
    """Supported motorized mobility types for heatmaps."""

    public_transport = "public_transport"
    car = "car"


TRAVELTIME_MATRIX_TABLE = {
    ActiveRoutingHeatmapType.walking: "basic.traveltime_matrix_walking",
    ActiveRoutingHeatmapType.bicycle: "basic.traveltime_matrix_bicycle",
    ActiveRoutingHeatmapType.pedelec.value: "basic.traveltime_matrix_pedelec",
    MotorizedRoutingHeatmapType.public_transport.value: "basic.traveltime_matrix_pt",
    MotorizedRoutingHeatmapType.car.value: "basic.traveltime_matrix_car",
}


TRAVELTIME_MATRIX_RESOLUTION = {
    ActiveRoutingHeatmapType.walking.value: 10,
    ActiveRoutingHeatmapType.bicycle.value: 9,
    ActiveRoutingHeatmapType.pedelec.value: 9,
    MotorizedRoutingHeatmapType.public_transport.value: 9,
    MotorizedRoutingHeatmapType.car.value: 8,
}

ROUTING_MODE_DEFAULT_SPEED = {
    ActiveRoutingHeatmapType.walking.value: 5,
    ActiveRoutingHeatmapType.bicycle.value: 15,
    ActiveRoutingHeatmapType.pedelec.value: 23,
    MotorizedRoutingHeatmapType.car.value: 80,
}


class ImpedanceFunctionType(str, Enum):
    """Impedance function type schema."""

    gaussian = "gaussian"
    linear = "linear"
    exponential = "exponential"
    power = "power"


class MaxTravelTimeTransportMode(int, Enum):
    """Max travel time transport mode schema."""

    walking = 30
    bicycle = 30
    pedelec = 30
    public_transport = 60
    car = 60


class OpportunityBase(BaseModel):
    opportunity_layer_project_id: int = Field(
        ...,
        title="Layer Project ID of layer containing opportunities.",
        description="The ID of the layer project that contains the opportunities.",
    )
    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=60,
    )


class OpportunityClosestAverage(OpportunityBase):
    """Opportunity object for the gravity based heatmap."""

    number_of_destinations: int = Field(
        ...,
        title="Number of Destinations",
        description="The number of destinations to be included in the average.",
    )


class OpportunityGravityBased(OpportunityBase):
    """Opportunity object for the gravity based heatmap."""

    sensitivity: float = Field(
        ...,
        title="Sensitivity parameter for the opportunities and impedance function.",
        description="The sensitivity parameter for the opportunities and impedance function.",
    )
    destination_potential_column: str | None = Field(
        None,
        title="Destination Potential Column",
        description="The column name of the destination potential.",
    )

    # Ensure sensitivity doesn't exceed the configured limit
    @field_validator("sensitivity", mode="after", check_fields=True)
    @classmethod
    def valid_sensitivity(cls: type["OpportunityGravityBased"], value: float) -> float:
        if value > settings.HEATMAP_GRAVITY_MAX_SENSITIVITY:
            raise ValueError(
                f"The sensitivity must not exceed {settings.HEATMAP_GRAVITY_MAX_SENSITIVITY}."
            )
        return value


def _validate_max_traveltime(
    routing_type: ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType,
    values: Dict[str, Any],
) -> ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType:
    max_traveltime = MaxTravelTimeTransportMode[routing_type].value
    valid = True

    opportunities: List[OpportunityBase] | None = values.get("opportunities")
    max_traveltime_value: int | None = values.get("max_traveltime")

    if opportunities:
        for opportunity in opportunities:
            if opportunity.max_traveltime > max_traveltime:
                valid = False
                break
    elif max_traveltime_value:
        if max_traveltime_value > max_traveltime:
            valid = False
    else:
        raise ValueError(
            f"Max travel time must be specified for {routing_type} routing type."
        )

    if not valid:
        raise ValueError(
            f"Max supported travel time for {routing_type} is {max_traveltime} minutes."
        )

    return routing_type


class HeatmapGravityBase(BaseModel):
    """Gravity based heatmap schema."""

    impedance_function: ImpedanceFunctionType = Field(
        ...,
        title="Impedance Function",
        description="The impedance function of the heatmap.",
    )
    # TODO: Limit 10 opportunities layers
    opportunities: List[OpportunityGravityBased] = Field(
        ...,
        title="Opportunities",
        description="The opportunities the heatmap should be calculated for heatmap.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )
    opportunity_geofence_layer_project_id: int | None = Field(
        None,
        title="Opportunity geofence layer project ID",
        description="The layer project ID of a geofence to be used for limiting opportunities to a certain region.",
    )

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {
            "opportunity_layer_project_id": input_layer_type_point_polygon,
            "opportunity_geofence_layer_project_id": input_layer_type_polygon,
        }


class HeatmapClosestAverageBase(BaseModel):
    """Closest average based heatmap schema."""

    opportunities: List[OpportunityClosestAverage] = Field(
        ...,
        title="Opportunities",
        description="The opportunities the heatmap should be calculated for heatmap.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )
    opportunity_geofence_layer_project_id: int | None = Field(
        None,
        title="Opportunity geofence layer project ID",
        description="The layer project ID of a geofence to be used for limiting opportunities to a certain region.",
    )

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {
            "opportunity_layer_project_id": input_layer_type_point_polygon,
            "opportunity_geofence_layer_project_id": input_layer_type_polygon,
        }


class HeatmapConnectivityBase(BaseModel):
    """Connectivity based heatmap schema."""

    reference_area_layer_project_id: int = Field(
        ...,
        title="The layer project serving reference Area for the calculation.",
        description="The reference area for the connectivity heatmap.",
    )
    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=60,
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {"reference_area_layer_project_id": input_layer_type_polygon}


class IHeatmapGravityActive(HeatmapGravityBase):
    """Gravity based heatmap for active mobility schema."""

    routing_type: ActiveRoutingHeatmapType = Field(
        ...,
        title="Routing Type",
        description="The routing type of the heatmap.",
    )

    @field_validator("routing_type", mode="after")
    @classmethod
    def validate_routing_type(
        cls: type["IHeatmapGravityActive"],
        value: ActiveRoutingHeatmapType,
        info: ValidationInfo,
    ) -> ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType:
        return _validate_max_traveltime(value, info.data)

    @property
    def tool_type(self) -> ToolType:
        return ToolType.heatmap_gravity_active_mobility

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.heatmap_gravity_active_mobility: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": "accessibility",
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class IHeatmapGravityMotorized(HeatmapGravityBase):
    """Gravity based heatmap for motorized mobility schema."""

    routing_type: MotorizedRoutingHeatmapType = Field(
        ...,
        title="Routing Type",
        description="The routing type of the heatmap.",
    )

    @field_validator("routing_type", mode="after")
    @classmethod
    def validate_routing_type(
        cls: type["IHeatmapGravityMotorized"],
        value: MotorizedRoutingHeatmapType,
        info: ValidationInfo,
    ) -> ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType:
        return _validate_max_traveltime(value, info.data)

    @property
    def tool_type(self) -> ToolType:
        return ToolType.heatmap_gravity_motorized_mobility

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.heatmap_gravity_active_mobility: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": "accessibility",
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class IHeatmapClosestAverageActive(HeatmapClosestAverageBase):
    """Closest average based heatmap for active mobility schema."""

    routing_type: ActiveRoutingHeatmapType = Field(
        ...,
        title="Routing Type",
        description="The routing type of the heatmap.",
    )

    @field_validator("routing_type", mode="after")
    @classmethod
    def validate_routing_type(
        cls: type["IHeatmapClosestAverageActive"],
        value: ActiveRoutingHeatmapType,
        info: ValidationInfo,
    ) -> ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType:
        return _validate_max_traveltime(value, info.data)

    @property
    def tool_type(self) -> ToolType:
        return ToolType.heatmap_closest_average_active_mobility

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.heatmap_closest_average_active_mobility: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": "accessibility",
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class IHeatmapClosestAverageMotorized(HeatmapClosestAverageBase):
    """Closest average based heatmap for motorized mobility schema."""

    routing_type: MotorizedRoutingHeatmapType = Field(
        ...,
        title="Routing Type",
        description="The routing type of the heatmap.",
    )

    @field_validator("routing_type", mode="after")
    @classmethod
    def validate_routing_type(
        cls: type["IHeatmapClosestAverageMotorized"],
        value: MotorizedRoutingHeatmapType,
        info: ValidationInfo,
    ) -> ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType:
        return _validate_max_traveltime(value, info.data)

    @property
    def tool_type(self) -> ToolType:
        return ToolType.heatmap_closest_average_motorized_mobility

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.heatmap_closest_average_motorized_mobility: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": "accessibility",
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class IHeatmapConnectivityActive(HeatmapConnectivityBase):
    """Connectivity based heatmap for active mobility schema."""

    routing_type: ActiveRoutingHeatmapType = Field(
        ...,
        title="Routing Type",
        description="The routing type of the heatmap.",
    )

    @field_validator("routing_type", mode="after")
    @classmethod
    def validate_routing_type(
        cls: type["IHeatmapConnectivityActive"],
        value: ActiveRoutingHeatmapType,
        info: ValidationInfo,
    ) -> ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType:
        return _validate_max_traveltime(value, info.data)

    @property
    def tool_type(self) -> ToolType:
        return ToolType.heatmap_connectivity_active_mobility

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.heatmap_connectivity_active_mobility: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": "accessibility",
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class IHeatmapConnectivityMotorized(HeatmapConnectivityBase):
    """Connectivity based heatmap for motorized mobility schema."""

    routing_type: MotorizedRoutingHeatmapType = Field(
        ...,
        title="Routing Type",
        description="The routing type of the heatmap.",
    )

    @field_validator("routing_type", mode="after")
    @classmethod
    def validate_routing_type(
        cls: type["IHeatmapConnectivityMotorized"],
        value: MotorizedRoutingHeatmapType,
        info: ValidationInfo,
    ) -> ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType:
        return _validate_max_traveltime(value, info.data)

    @property
    def tool_type(self) -> ToolType:
        return ToolType.heatmap_connectivity_motorized_mobility

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.heatmap_connectivity_motorized_mobility: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": "accessibility",
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }
