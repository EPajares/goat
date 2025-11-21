from typing import Any, Optional, Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator
from routing.core.config import settings

from goatlib.routing.schemas.base import (
    CatchmentAreaRoutingTypeActiveMobility,
    CatchmentAreaRoutingTypeCar,
    CatchmentAreaStartingPoints,
    CatchmentAreaType,
)


class _BaseTravelTimeCost(BaseModel):
    """Internal base schema for travel time cost."""

    max_traveltime: int

    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )

    # This validator is now generic
    @field_validator("steps")
    @classmethod
    def valid_num_steps(cls, v: int) -> int:
        """
        Validate that the number of steps does not exceed the `le` constraint
        defined on the `max_traveltime` field for this specific model.
        """
        # Dynamically get the 'le' value from the max_traveltime field definition
        max_traveltime_limit = cls.model_fields["max_traveltime"].le

        if max_traveltime_limit is None:
            # Failsafe in case 'le' is not set on the field
            return v

        if v > max_traveltime_limit:
            raise ValueError(
                f"The number of steps ({v}) must not exceed the maximum travel time ({max_traveltime_limit})."
            )
        return v


class CatchmentAreaTravelTimeCostActiveMobility(_BaseTravelTimeCost):
    """Travel time cost schema for active mobility."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=45,
    )

    speed: int = Field(
        ...,
        title="Speed",
        description="The speed in km/h.",
        ge=1,
        le=25,
    )


class CatchmentAreaTravelTimeCostMotorizedMobility(_BaseTravelTimeCost):
    """Travel time cost schema for motorized mobility."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=90,
    )


# TODO: Check how to treat miles
class CatchmentAreaTravelDistanceCost(BaseModel):
    """Travel distance cost schema, applicable to any mobility type."""

    max_distance: int = Field(
        ...,
        title="Max Distance",
        description="The maximum distance in meters.",
        ge=50,
        le=20000,  # The validator will read this value automatically
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )

    @field_validator("steps")
    @classmethod
    def valid_num_steps(cls, v: int) -> int:
        """
        Validate that the number of steps does not exceed the `le` constraint
        defined on the `max_distance` field.
        """
        max_distance_limit = cls.model_fields["max_distance"].le

        if max_distance_limit is None:
            return v  # Failsafe

        if v > max_distance_limit:
            raise ValueError(
                f"The number of steps ({v}) must not exceed the maximum distance ({max_distance_limit})."
            )
        return v


class CatchmentAreaStreetNetwork(BaseModel):
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.node_layer_project_id is None:
            self.node_layer_project_id = (
                settings.DEFAULT_STREET_NETWORK_NODE_LAYER_PROJECT_ID
            )

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


class _BaseICatchmentArea(BaseModel):
    """Internal base model for all catchment area requests."""

    starting_points: CatchmentAreaStartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the base network.",
    )
    street_network: CatchmentAreaStreetNetwork | None = Field(
        None,
        title="Street Network Layer Config",
        description="The configuration of the street network layers to use.",
    )
    catchment_area_type: CatchmentAreaType = Field(
        ..., title="Return Type", description="The return type of the catchment area."
    )
    polygon_difference: bool | None = Field(
        None,
        title="Polygon Difference",
        description="If true, the polygons returned will be the geometrical difference of two following calculations.",
    )
    result_table: str = Field(
        ...,
        title="Result Table",
        description="The table name the results should be saved.",
    )
    layer_id: UUID | None = Field(
        ...,
        title="Layer ID",
        description="The ID of the layer the results should be saved.",
    )

    routing_type: str
    travel_cost: Any

    @model_validator(mode="after")
    def _model_validator(self) -> Self:
        scenario_id = self.scenario_id
        street_network = self.street_network
        polygon_difference = self.polygon_difference
        catchment_area_type = self.catchment_area_type
        # Ensure street network is specified if a scenario ID is provided
        if scenario_id is not None and street_network is None:
            raise ValueError(
                "The street network must be set if a scenario ID is provided."
            )
        # Check that polygon difference exists if catchment area type is polygon
        if (
            catchment_area_type == CatchmentAreaType.polygon.value
            and polygon_difference is None
        ):
            raise ValueError(
                "The polygon difference must be set if the catchment area type is polygon."
            )
        # Check that polygon difference is not specified if catchment area type is not polygon
        if (
            catchment_area_type != CatchmentAreaType.polygon.value
            and polygon_difference is not None
        ):
            raise ValueError(
                "The polygon difference must not be set if the catchment area type is not polygon."
            )
        return self


class ICatchmentAreaActiveMobility(_BaseICatchmentArea):
    """Model for the active mobility catchment area request."""

    routing_type: CatchmentAreaRoutingTypeActiveMobility = Field(
        ..., title="Routing Type", description="The routing type of the catchment area."
    )
    travel_cost: (
        CatchmentAreaTravelTimeCostActiveMobility | CatchmentAreaTravelDistanceCost
    ) = Field(
        ..., title="Travel Cost", description="The travel cost of the catchment area."
    )


class ICatchmentAreaCar(_BaseICatchmentArea):
    """Model for the car catchment area request."""

    routing_type: CatchmentAreaRoutingTypeCar = Field(
        ..., title="Routing Type", description="The routing type of the catchment area."
    )
    travel_cost: (
        CatchmentAreaTravelTimeCostMotorizedMobility | CatchmentAreaTravelDistanceCost
    ) = Field(
        ..., title="Travel Cost", description="The travel cost of the catchment area."
    )


request_examples: dict[str, Any] = {
    "catchment_area_active_mobility": {
        # 1. Single catchment area for walking (time based)
        "single_point_walking_time": {
            "summary": "Single point catchment area walking (time based)",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 5,
                    "speed": 5,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 2. Single catchment area for walking (distance based)
        "single_point_walking_distance": {
            "summary": "Single point catchment area walking (distance based)",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "walking",
                "travel_cost": {
                    "max_distance": 2500,
                    "steps": 100,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 3. Single catchment area for cycling
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
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 4. Single catchment area for walking with scenario
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
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "scenario_id": "e7dcaae4-1750-49b7-89a5-9510bf2761ad",
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 5. Multi-catchment area walking with more than one starting point
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
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 6. Multi-catchment area cycling with more than one starting point
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
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
    },
    "catchment_area_motorized_mobility": {
        # 1. Single catchment area for car (time based)
        "single_point_car_time": {
            "summary": "Single point catchment area car (time based)",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "car",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 5,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 2. Single catchment area for car (distance based)
        "single_point_car_distance": {
            "summary": "Single point catchment area car (distance based)",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "car",
                "travel_cost": {
                    "max_distance": 10000,
                    "steps": 100,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 3. Single catchment area for car with scenario
        "single_point_car_scenario": {
            "summary": "Single point catchment area car",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "car",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "scenario_id": "e7dcaae4-1750-49b7-89a5-9510bf2761ad",
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 4. Multi-catchment area car with more than one starting point
        "multi_point_car": {
            "summary": "Multi point catchment area car",
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
                "routing_type": "car",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
    },
}
