from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field

from core.schemas.colors import ColorRangeType
from core.schemas.layer import ToolType
from core.schemas.toolbox_base import (
    DefaultResultLayerName,
    PTTimeWindow,
    input_layer_type_polygon,
)


class ITripCountStation(BaseModel):
    """Model for the trip count."""

    reference_area_layer_project_id: int = Field(
        ...,
        title="The layer project serving reference Area for the calculation.",
        description="The reference area for the trip count.",
    )
    time_window: PTTimeWindow = Field(
        ...,
        title="Time Window",
        description="The time window for the trip count.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )

    @property
    def tool_type(self) -> ToolType:
        return ToolType.trip_count_station

    @property
    def input_layer_types(self) -> Dict[str, Any]:
        return {"reference_area_layer_project_id": input_layer_type_polygon}

    @property
    def geofence_table(self) -> str:
        return "basic.geofence_pt"

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.trip_count_station: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": "total", "type": "number"},
                "color_scale": "quantile",
            }
        }


public_transport_types = {
    "bus": {
        3: "Bus",
        11: "Trolleybus",
        700: "Bus Service",
        702: "Express Bus Service",
        704: "Local Bus Service",
        705: "Night Bus Service",
        710: "Sightseeing Bus",
        712: "School Bus",
        715: "Demand and Response Bus Service",
        800: "Trolleybus Service",
    },
    "tram": {
        0: "Tram, Streetcar, Light rail",
        5: "Cable Tram",
        900: "Tram Service",
    },
    "metro": {
        1: "Subway, Metro",
        400: "Metro Service",
        401: "Underground Service",
        402: "Urban Railway Service",
    },
    "rail": {
        2: "Rail",
        100: "Railway Service",
        101: "High Speed Rail Service",
        102: "Long Distance Trains",
        103: "Inter Regional Rail Service",
        105: "Sleeper Rail Service",
        106: "Regional Rail Service",
        107: "Tourist Railway Service",
        109: "Suburban Railway",
        202: "National Coach Service",
        403: "All Urban Railway Services",
    },
    "other": {
        4: "Ferry",
        6: "Aerial lift",
        7: "Funicular",
        1000: "Water Transport Service",
        1300: "Aerial Lift Service",
        1400: "Funicular Service",
        1500: "Taxi Service",
        1700: "Gondola, Suspended cable car",
    },
}
