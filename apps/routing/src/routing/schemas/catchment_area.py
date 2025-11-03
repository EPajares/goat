from enum import Enum
from typing import Any, List, Optional
from uuid import UUID

import polars as pl
from pydantic import BaseModel, Field, field_validator, model_validator
from routing.core.config import settings
from typing_extensions import Self

SEGMENT_DATA_SCHEMA = {
    "id": pl.Int64,
    "length_m": pl.Float64,
    "length_3857": pl.Float64,
    "class_": pl.Utf8,
    "impedance_slope": pl.Float64,
    "impedance_slope_reverse": pl.Float64,
    "impedance_surface": pl.Float32,
    "coordinates_3857": pl.Utf8,
    "maxspeed_forward": pl.Int16,
    "maxspeed_backward": pl.Int16,
    "source": pl.Int64,
    "target": pl.Int64,
    "h3_3": pl.Int32,
    "h3_6": pl.Int32,
}

CONNECTOR_DATA_SCHEMA = {
    "id": pl.Int64,
    "h3_3": pl.Int32,
    "h3_6": pl.Int32,
}

VALID_WALKING_CLASSES = [
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "living_street",
    "trunk",
    "unclassified",
    "service",
    "pedestrian",
    "footway",
    "steps",
    "path",
    "track",
    "cycleway",
    "bridleway",
    "unknown",
]

VALID_BICYCLE_CLASSES = [
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "living_street",
    "trunk",
    "unclassified",
    "service",
    "pedestrian",
    "footway",
    "path",
    "track",
    "cycleway",
    "bridleway",
    "unknown",
]
BICYCLE_SPEED_FOOTWAYS = 5

VALID_WHEELCHAIR_CLASSES = [
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "living_street",
    "trunk",
    "unclassified",
    "service",
    "pedestrian",
    "footway",
    "path",
    "track",
    "cycleway",
    "bridleway",
    "unknown",
]

VALID_CAR_CLASSES = [
    "motorway",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "living_street",
    "trunk",
    "unclassified",
    "service",
    "track",
]


class CatchmentAreaType(str, Enum):
    """Catchment area type schema."""

    polygon = "polygon"
    network = "network"
    rectangular_grid = "rectangular_grid"


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


class CatchmentAreaRoutingTypeActiveMobility(str, Enum):
    """Routing active mobility type schema."""

    walking = "walking"
    bicycle = "bicycle"
    pedelec = "pedelec"
    wheelchair = "wheelchair"

class CatchmentAreaRoutingTypeCar(str, Enum):
    """Routing car type schema."""

    car = "car"


H3_CELL_RESOLUTION = {
    CatchmentAreaRoutingTypeActiveMobility.walking: 10,
    CatchmentAreaRoutingTypeActiveMobility.bicycle: 9,
    CatchmentAreaRoutingTypeActiveMobility.pedelec: 9,
    CatchmentAreaRoutingTypeCar.car: 8,
}


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
    @field_validator("steps", mode="before")
    @classmethod
    def valid_num_steps(cls, v: int) -> int:
        if v > 45:
            raise ValueError(
                "The number of steps must not exceed the maximum traveltime."
            )
        return v


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

    # Ensure the number of steps doesn't exceed the maximum traveltime
    @field_validator("steps", mode="before")
    @classmethod
    def valid_num_steps(cls, v: int) -> int:
        if v > 90:
            raise ValueError(
                "The number of steps must not exceed the maximum traveltime."
            )
        return v


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
    @field_validator("steps", mode="before")
    @classmethod
    def valid_num_steps(cls, v: int) -> int:
        if v > 20000:
            raise ValueError(
                "The number of steps must not exceed the maximum distance."
            )
        return v


# TODO: Check how to treat miles
class CatchmentAreaTravelDistanceCostCar(BaseModel):
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
    @field_validator("steps", mode="before")
    @classmethod
    def valid_num_steps(cls, v: int) -> int:
        if v > 20000:
            raise ValueError(
                "The number of steps must not exceed the maximum distance."
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


class ICatchmentAreaActiveMobility(BaseModel):
    """Model for the active mobility catchment area request."""

    starting_points: CatchmentAreaStartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    routing_type: CatchmentAreaRoutingTypeActiveMobility = Field(
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
        description="The ID of the scenario that is to be applied on the base network.",
    )
    street_network: CatchmentAreaStreetNetwork | None = Field(
        None,
        title="Street Network Layer Config",
        description="The configuration of the street network layers to use.",
    )
    catchment_area_type: CatchmentAreaType = Field(
        ...,
        title="Return Type",
        description="The return type of the catchment area.",
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


class ICatchmentAreaCar(BaseModel):
    """Model for the car catchment area request."""

    starting_points: CatchmentAreaStartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    routing_type: CatchmentAreaRoutingTypeCar = Field(
        ...,
        title="Routing Type",
        description="The routing type of the catchment area.",
    )
    travel_cost: (
        CatchmentAreaTravelTimeCostMotorizedMobility
        | CatchmentAreaTravelDistanceCostCar
    ) = Field(
        ...,
        title="Travel Cost",
        description="The travel cost of the catchment area.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is used for the routing.",
    )
    street_network: CatchmentAreaStreetNetwork | None = Field(
        None,
        title="Street Network Layer Config",
        description="The configuration of the street network layers to use.",
    )
    catchment_area_type: CatchmentAreaType = Field(
        ...,
        title="Return Type",
        description="The return type of the catchment area.",
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
