from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from core.schemas.colors import ColorRangeType
from core.schemas.layer import ToolType
from core.schemas.toolbox_base import (
    CatchmentAreaStartingPointsBase,
    DefaultResultLayerName,
    PTTimeWindow,
    check_starting_points,
    input_layer_type_line,
    input_layer_type_point,
)

"""Catchment area starting point validators."""


class CatchmentAreaStartingPointsActiveMobility(CatchmentAreaStartingPointsBase):
    """Model for the active mobility catchment area starting points."""

    @model_validator(mode="after")
    def validate_starting_points(self) -> "CatchmentAreaStartingPointsActiveMobility":
        """Ensure that the number of starting points does not exceed 1000."""
        check_starting_points(1000, self.latitude, self.longitude)
        return self

class CatchmentAreaStartingPointsMotorizedMobility(CatchmentAreaStartingPointsBase):
    """Model for the active mobility catchment area starting points."""

    @model_validator(mode="after")
    def validate_starting_points(self) -> "CatchmentAreaStartingPointsMotorizedMobility":
        """Ensure that the number of starting points does not exceed 1."""
        check_starting_points(1, self.latitude, self.longitude)
        return self


"""Catchment area routing mode schemas."""


class CatchmentAreaRoutingModeActiveMobility(str, Enum):
    """Routing active mobility type schema."""

    walking = "walking"
    wheelchair = "wheelchair"
    bicycle = "bicycle"
    pedelec = "pedelec"


class CatchmentAreaRoutingModePT(str, Enum):
    """Routing public transport mode schema."""

    bus = "bus"
    tram = "tram"
    rail = "rail"
    subway = "subway"
    ferry = "ferry"
    cable_car = "cable_car"
    gondola = "gondola"
    funicular = "funicular"


class CatchmentAreaRoutingEgressModePT(str, Enum):
    """Routing public transport egress mode schema."""

    walk = "walk"
    bicycle = "bicycle"


class CatchmentAreaRoutingAccessModePT(str, Enum):
    """Routing public transport access mode schema."""

    walk = "walk"
    bicycle = "bicycle"
    car = "car"


class CatchmentAreaRoutingModeConfigPT(BaseModel):
    """Routing public transport type schema."""

    mode: List[CatchmentAreaRoutingModePT] = Field(
        ...,
        title="Mode",
        description="The mode of the public transport.",
    )
    egress_mode: CatchmentAreaRoutingEgressModePT = Field(
        ...,
        title="Egress Mode",
        description="The egress mode of the public transport.",
    )
    access_mode: CatchmentAreaRoutingAccessModePT = Field(
        ...,
        title="Access Mode",
        description="The access mode of the public transport.",
    )


class CatchmentAreaRoutingModeCar(str, Enum):
    """Routing car type schema."""

    car = "car"


"""Catchment area travel cost schemas."""


class CatchmentAreaTravelTimeCostActiveMobility(BaseModel):
    """Travel time cost schema."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=45,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )
    speed: int = Field(
        ...,
        title="Speed",
        description="The speed in km/h.",
        ge=1,
        le=25,
    )

    # Ensure the number of steps doesn't exceed the maximum traveltime
    @field_validator("steps", mode="after", check_fields=True)
    @classmethod
    def valid_num_steps(
        cls: type["CatchmentAreaTravelTimeCostActiveMobility"], value: int
    ) -> int:
        if value > 45:
            raise ValueError(
                "The number of steps must not exceed the maximum potential traveltime."
            )
        return value


# TODO: Check how to treat miles
class CatchmentAreaTravelDistanceCostActiveMobility(BaseModel):
    """Travel distance cost schema."""

    max_distance: int = Field(
        ...,
        title="Max Distance",
        description="The maximum distance in meters.",
        ge=50,
        le=20000,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )

    # Ensure the number of steps doesn't exceed the maximum distance
    @field_validator("steps", mode="after", check_fields=True)
    @classmethod
    def valid_num_steps(
        cls: type["CatchmentAreaTravelDistanceCostActiveMobility"], value: int
    ) -> int:
        if value > 20000:
            raise ValueError(
                "The number of steps must not exceed the maximum potential distance."
            )
        return value


class CatchmentAreaTravelTimeCostMotorizedMobility(BaseModel):
    """Travel time cost schema."""

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


# TODO: Check how to treat miles
class CatchmentAreaTravelDistanceCostMotorizedMobility(BaseModel):
    """Travel distance cost schema."""

    max_distance: int = Field(
        ...,
        title="Max Distance",
        description="The maximum distance in meters.",
        ge=50,
        le=20000,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )

    # Ensure the number of steps doesn't exceed the maximum distance
    @field_validator("steps", mode="after", check_fields=True)
    @classmethod
    def valid_num_steps(
        cls: type["CatchmentAreaTravelDistanceCostMotorizedMobility"], value: int
    ) -> int:
        if value > 20000:
            raise ValueError(
                "The number of steps must not exceed the maximum distance."
            )
        return value


"""Catchment area decay function schemas."""


class CatchmentAreaDecayFunctionTypePT(str, Enum):
    LOGISTIC = "logistic"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    STEP = "step"


class CatchmentAreaDecayFunctionPT(BaseModel):
    type: Optional[CatchmentAreaDecayFunctionTypePT] = Field(
        default=CatchmentAreaDecayFunctionTypePT.LOGISTIC,
        description="Decay function type",
    )
    standard_deviation_minutes: Optional[int] = Field(
        default=12,
        description="Standard deviation in minutes",
    )
    width_minutes: Optional[int] = Field(
        default=10,
        description="Width in minutes",
    )


"""Catchment area type schemas."""


class CatchmentAreaTypeActiveMobility(str, Enum):
    """Catchment area type schema for active mobility."""

    polygon = "polygon"
    network = "network"
    rectangular_grid = "rectangular_grid"


class CatchmentAreaTypePT(str, Enum):
    """Catchment area type schema for public transport."""

    polygon = "polygon"
    rectangular_grid = "rectangular_grid"


class CatchmentAreaTypeCar(str, Enum):
    """Catchment area type schema for car."""

    polygon = "polygon"
    network = "network"
    rectangular_grid = "rectangular_grid"


class CatchmentAreaStreetNetwork(BaseModel):
    edge_layer_project_id: int = Field(
        ...,
        title="Edge Layer Project ID",
        description="The layer project ID of the street network edge layer.",
    )
    node_layer_project_id: int | None = Field(
        None,
        title="Node Layer Project ID",
        description="The layer project ID of the street network node layer.",
    )


"""User-configured catchment area payload schemas."""


class ICatchmentAreaActiveMobility(BaseModel):
    """Model for the active mobility catchment area"""

    starting_points: CatchmentAreaStartingPointsActiveMobility = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    routing_type: CatchmentAreaRoutingModeActiveMobility = Field(
        ...,
        title="Routing Type",
        description="The routing type of the catchment area.",
    )
    travel_cost: (
        CatchmentAreaTravelTimeCostActiveMobility
        | CatchmentAreaTravelDistanceCostActiveMobility
    ) = Field(
        ...,
        title="Travel Cost",
        description="The travel cost of the catchment area.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )
    street_network: Optional[CatchmentAreaStreetNetwork] = Field(
        None,
        title="Street Network Layer Config",
        description="The configuration of the street network layers to use.",
    )
    catchment_area_type: CatchmentAreaTypeActiveMobility = Field(
        ...,
        title="Return Type",
        description="The return type of the catchment area.",
    )
    polygon_difference: bool | None = Field(
        None,
        title="Polygon Difference",
        description="If true, the polygons returned will be the geometrical difference of two following calculations.",
    )

    # Check that polygon difference exists if catchment area type is polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference(
        cls: type["ICatchmentAreaActiveMobility"],
        value: bool | None,
        info: ValidationInfo,
    ) -> bool | None:
        if (
            info.data["catchment_area_type"]
            == CatchmentAreaTypeActiveMobility.polygon.value
            and value is None
        ):
            raise ValueError(
                "The polygon difference must be set if the catchment area type is polygon."
            )
        return value

    # Check that polygon difference is not specified if catchment area type is not polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference_not_specified(
        cls: type["ICatchmentAreaActiveMobility"],
        value: bool | None,
        info: ValidationInfo,
    ) -> bool | None:
        if (
            info.data["catchment_area_type"]
            != CatchmentAreaTypeActiveMobility.polygon.value
            and value is not None
        ):
            raise ValueError(
                "The polygon difference must not be set if the catchment area type is not polygon."
            )
        return value

    @property
    def tool_type(self) -> ToolType:
        return ToolType.catchment_area_active_mobility

    @property
    def geofence_table(self) -> str:
        mode = ToolType.catchment_area_active_mobility.value.replace(
            "catchment_area_", ""
        )
        return f"basic.geofence_{mode}"

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {
            "layer_project_id": input_layer_type_point,
            "edge_layer_project_id": input_layer_type_line,
            "node_layer_project_id": input_layer_type_point,
        }

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.catchment_area_active_mobility: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": "travel_cost", "type": "number"},
                "color_scale": "ordinal",
            }
        }


class ICatchmentAreaPT(BaseModel):
    """Model for the public transport catchment area"""

    starting_points: CatchmentAreaStartingPointsMotorizedMobility = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    routing_type: CatchmentAreaRoutingModeConfigPT = Field(
        ...,
        title="Routing Type",
        description="The routing type of the catchment area.",
    )
    travel_cost: CatchmentAreaTravelTimeCostMotorizedMobility = Field(
        ...,
        title="Travel Cost",
        description="The travel cost of the catchment area.",
    )
    time_window: PTTimeWindow = Field(
        ...,
        title="Time Window",
        description="The time window of the catchment area.",
    )
    catchment_area_type: CatchmentAreaTypePT = Field(
        ...,
        title="Return Type",
        description="The return type of the catchment area.",
    )
    polygon_difference: bool | None = Field(
        None,
        title="Polygon Difference",
        description="If true, the polygons returned will be the geometrical difference of two following calculations.",
    )
    decay_function: CatchmentAreaDecayFunctionPT = Field(
        CatchmentAreaDecayFunctionPT(),
        title="Decay Function",
        description="The decay function of the catchment area.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )

    # Defaults - not currently user configurable
    walk_speed: float = 1.39
    max_walk_time: int = 20
    bike_speed: float = 4.166666666666667
    max_bike_time: int = 20
    bike_traffic_stress: int = 4
    max_rides: int = 4
    zoom: int = 9
    percentiles: List[int] = [1]
    monte_carlo_draws: int = 200

    # Check that polygon difference exists if catchment area type is polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference(
        cls: type["ICatchmentAreaPT"], value: bool | None, info: ValidationInfo
    ) -> bool | None:
        if (
            info.data["catchment_area_type"] == CatchmentAreaTypePT.polygon.value
            and value is None
        ):
            raise ValueError(
                "The polygon difference must be set if the catchment area type is polygon."
            )
        return value

    # Check that polygon difference is not specified if catchment area type is not polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference_not_specified(
        cls: type["ICatchmentAreaPT"], value: bool | None, info: ValidationInfo
    ) -> bool | None:
        if (
            info.data["catchment_area_type"] != CatchmentAreaTypePT.polygon.value
            and value is not None
        ):
            raise ValueError(
                "The polygon difference must not be set if the catchment area type is not polygon."
            )
        return value

    @property
    def tool_type(self) -> ToolType:
        return ToolType.catchment_area_pt

    @property
    def geofence_table(self) -> str:
        mode = ToolType.catchment_area_pt.value.replace("catchment_area_", "")
        return f"basic.geofence_{mode}"

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {"layer_project_id": input_layer_type_point}

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.catchment_area_pt: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": "travel_cost", "type": "number"},
                "color_scale": "ordinal",
            }
        }


class ICatchmentAreaCar(BaseModel):
    """Model for the car catchment area"""

    starting_points: CatchmentAreaStartingPointsMotorizedMobility = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    routing_type: CatchmentAreaRoutingModeCar = Field(
        ...,
        title="Routing Type",
        description="The routing type of the catchment area.",
    )
    travel_cost: (
        CatchmentAreaTravelTimeCostMotorizedMobility
        | CatchmentAreaTravelDistanceCostMotorizedMobility
    ) = Field(
        ...,
        title="Travel Cost",
        description="The travel cost of the catchment area.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )
    street_network: Optional[CatchmentAreaStreetNetwork] = Field(
        None,
        title="Street Network Layer Config",
        description="The configuration of the street network layers to use.",
    )
    catchment_area_type: CatchmentAreaTypeCar = Field(
        ...,
        title="Return Type",
        description="The return type of the catchment area.",
    )
    polygon_difference: bool | None = Field(
        None,
        title="Polygon Difference",
        description="If true, the polygons returned will be the geometrical difference of two following calculations.",
    )

    # Check that polygon difference exists if catchment area type is polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference(
        cls: type["ICatchmentAreaCar"], value: bool | None, info: ValidationInfo
    ) -> bool | None:
        if (
            info.data["catchment_area_type"] == CatchmentAreaTypeCar.polygon.value
            and value is None
        ):
            raise ValueError(
                "The polygon difference must be set if the catchment area type is polygon."
            )
        return value

    # Check that polygon difference is not specified if catchment area type is not polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference_not_specified(
        cls: type["ICatchmentAreaCar"], value: bool | None, info: ValidationInfo
    ) -> bool | None:
        if (
            info.data["catchment_area_type"] != CatchmentAreaTypeCar.polygon.value
            and value is not None
        ):
            raise ValueError(
                "The polygon difference must not be set if the catchment area type is not polygon."
            )
        return value

    @property
    def tool_type(self) -> ToolType:
        return ToolType.catchment_area_car

    @property
    def geofence_table(self) -> str:
        mode = ToolType.catchment_area_active_mobility.value.replace(
            "catchment_area_", ""
        )
        return f"basic.geofence_{mode}"

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {
            "layer_project_id": input_layer_type_point,
            "edge_layer_project_id": input_layer_type_line,
            "node_layer_project_id": input_layer_type_point,
        }

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.catchment_area_car: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": "travel_cost", "type": "number"},
                "color_scale": "ordinal",
            }
        }


class CatchmentAreaNearbyStationAccess(BaseModel):
    """Model for the nearby stations (active mobility) catchment area"""

    starting_points: CatchmentAreaStartingPointsActiveMobility = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    routing_type: CatchmentAreaRoutingModeActiveMobility = Field(
        ...,
        title="Routing Type",
        description="The routing type of the catchment area.",
    )
    travel_cost: (
        CatchmentAreaTravelTimeCostActiveMobility
        | CatchmentAreaTravelDistanceCostActiveMobility
    ) = Field(
        ...,
        title="Travel Cost",
        description="The travel cost of the catchment area.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )
    street_network: Optional[CatchmentAreaStreetNetwork] = Field(
        None,
        title="Street Network Layer Config",
        description="The configuration of the street network layers to use.",
    )
    catchment_area_type: CatchmentAreaTypeActiveMobility = Field(
        ...,
        title="Return Type",
        description="The return type of the catchment area.",
    )
    polygon_difference: bool | None = Field(
        None,
        title="Polygon Difference",
        description="If true, the polygons returned will be the geometrical difference of two following calculations.",
    )

    # Check that polygon difference exists if catchment area type is polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference(
        cls: type["CatchmentAreaNearbyStationAccess"],
        value: bool | None,
        info: ValidationInfo,
    ) -> bool | None:
        if (
            info.data["catchment_area_type"]
            == CatchmentAreaTypeActiveMobility.polygon.value
            and value is None
        ):
            raise ValueError(
                "The polygon difference must be set if the catchment area type is polygon."
            )
        return value

    # Check that polygon difference is not specified if catchment area type is not polygon
    @field_validator("polygon_difference", mode="after", check_fields=True)
    @classmethod
    def check_polygon_difference_not_specified(
        cls: type["CatchmentAreaNearbyStationAccess"],
        value: bool | None,
        info: ValidationInfo,
    ) -> bool | None:
        if (
            info.data["catchment_area_type"]
            != CatchmentAreaTypeActiveMobility.polygon.value
            and value is not None
        ):
            raise ValueError(
                "The polygon difference must not be set if the catchment area type is not polygon."
            )
        return value

    @property
    def tool_type(self) -> ToolType:
        return ToolType.catchment_area_nearby_station_access

    @property
    def geofence_table(self) -> str:
        mode = ToolType.catchment_area_pt.value.replace("catchment_area_", "")
        return f"basic.geofence_{mode}"

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {
            "layer_project_id": input_layer_type_point,
            "edge_layer_project_id": input_layer_type_line,
            "node_layer_project_id": input_layer_type_point,
        }

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.nearby_station_access: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": "travel_cost", "type": "number"},
                "color_scale": "quantile",
                "breaks": self.travel_cost.steps,
            }
        }


request_examples_catchment_area_active_mobility = {
    "catchment_area_active_mobility": {
        "single_point_walking": {
            "summary": "Single point catchment area walking",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                    "speed": 5,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
            },
        },
        "single_point_cycling": {
            "summary": "Single point catchment area cycling",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "bicycle",
                "travel_cost": {
                    "max_traveltime": 15,
                    "steps": 5,
                    "speed": 15,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
            },
        },
        "single_point_walking_scenario": {
            "summary": "Single point catchment area walking",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                    "speed": 5,
                },
                "scenario_id": "e7dcaae4-1750-49b7-89a5-9510bf2761ad",
                "catchment_area_type": "polygon",
                "polygon_difference": True,
            },
        },
        "multi_point_walking": {
            "summary": "Multi point catchment area walking",
            "value": {
                "starting_points": {
                    "latitude": [
                        52.5200,
                        52.5210,
                        52.5220,
                        52.5230,
                        52.5240,
                        52.5250,
                        52.5260,
                        52.5270,
                        52.5280,
                        52.5290,
                    ],
                    "longitude": [
                        13.4050,
                        13.4060,
                        13.4070,
                        13.4080,
                        13.4090,
                        13.4100,
                        13.4110,
                        13.4120,
                        13.4130,
                        13.4140,
                    ],
                },
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                    "speed": 5,
                },
            },
        },
        "multi_point_cycling": {
            "summary": "Multi point catchment area cycling",
            "value": {
                "starting_points": {
                    "latitude": [
                        52.5200,
                        52.5210,
                        52.5220,
                        52.5230,
                        52.5240,
                        52.5250,
                        52.5260,
                        52.5270,
                        52.5280,
                        52.5290,
                    ],
                    "longitude": [
                        13.4050,
                        13.4060,
                        13.4070,
                        13.4080,
                        13.4090,
                        13.4100,
                        13.4110,
                        13.4120,
                        13.4130,
                        13.4140,
                    ],
                },
                "routing_type": "bicycle",
                "travel_cost": {
                    "max_traveltime": 15,
                    "steps": 5,
                    "speed": 15,
                },
            },
        },
        "layer_based_walking": {
            "summary": "Layer based catchment area walking",
            "value": {
                "starting_points": {
                    "layer_id": "39e16c27-2b03-498e-8ccc-68e798c64b8d"  # Sample UUID for the layer
                },
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                    "speed": 5,
                },
            },
        },
    }
}


request_examples_catchment_area_pt = {
    # 1. Catchment area for public transport with all modes
    "all_modes_pt": {
        "summary": "Catchment area using all PT modes",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "routing_type": {
                "mode": [
                    "bus",
                    "tram",
                    "rail",
                    "subway",
                ],
                "egress_mode": "walk",
                "access_mode": "walk",
            },
            "travel_cost": {"max_traveltime": 40, "steps": 10},
            "time_window": {"weekday": "weekday", "from_time": 25200, "to_time": 32400},
            "catchment_area_type": "polygon",
        },
    },
    # 2. Catchment area for public transport excluding bus mode
    "exclude_bus_mode_pt": {
        "summary": "Catchment area excluding bus mode",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "routing_type": {
                "mode": [
                    "tram",
                    "rail",
                    "subway",
                ],
                "egress_mode": "walk",
                "access_mode": "walk",
            },
            "travel_cost": {"max_traveltime": 35, "steps": 5},
            "time_window": {"weekday": "weekday", "from_time": 25200, "to_time": 32400},
            "catchment_area_type": "polygon",
        },
    },
}


request_examples_catchment_area_car = {
    # 1. Catchment area for car
    "single_point_car": {
        "summary": "Catchment area for a single starting point using car",
        "value": {
            "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
            "routing_type": "car",
            "travel_cost": {"max_traveltime": 30, "steps": 10},
        },
    },
    # 2. Multi catchment area for car
    "multi_point_car": {
        "summary": "Catchment area for multiple starting points using car",
        "value": {
            "starting_points": {
                "latitude": [52.5200, 52.5250, 52.5300],
                "longitude": [13.4050, 13.4150, 13.4250],
            },
            "routing_type": "car",
            "travel_cost": {"max_traveltime": 30, "steps": 10},
        },
    },
}
