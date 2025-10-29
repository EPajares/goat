import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Self, Type

from goatlib.routing.schemas.base import (
    Location,
    Route,
    RoutingRequestBase,
    RoutingResponse,
    TransportMode,
)
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class ABRouteLeg(BaseModel):
    """Individual leg of an AB route."""

    leg_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), title="Unique Leg ID"
    )
    mode: TransportMode = Field(..., title="Mode")
    origin: Location = Field(..., title="Origin")
    destination: Location = Field(..., title="Destination")
    departure_time: datetime = Field(..., title="Departure Time")
    arrival_time: datetime = Field(..., title="Arrival Time")
    duration: int = Field(..., title="Duration in seconds", gt=0)

    distance: Optional[float] = Field(None, title="Distance in meters", ge=0)
    geometry: Optional[Dict[str, Any]] = Field(None, title="Geometry")
    instructions: Optional[List[Dict[str, Any]]] = Field(None, title="Instructions")


class ABRoute(Route):
    """A complete, detailed AB route with all its constituent legs."""

    route_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), title="Unique Route ID"
    )
    legs: List[ABRouteLeg] = Field(..., title="Legs")

    geometry: Optional[Dict[str, Any]] = Field(None, title="Complete route geometry")
    estimated_cost: Optional[float] = Field(None, title="Estimated Cost", ge=0)


class ABRoutingRequest(RoutingRequestBase):
    """The primary A-B routing request model."""

    # Optional travel preferences
    max_results: Optional[int] = Field(
        default=3, description="Maximum number of routes to return", ge=1, le=10
    )
    max_travel_time: Optional[int] = Field(None, title="Max Travel Time", ge=1, le=480)
    max_transfers: Optional[int] = Field(None, title="Max Transfers", ge=0, le=10)
    max_walking_distance: Optional[int] = Field(
        None, title="Max Walking Distance", ge=0, le=5000
    )
    include_geometry: Optional[bool] = Field(default=True, title="Include Geometry")
    include_instructions: Optional[bool] = Field(
        default=True, title="Include Instructions"
    )


class ABRoutingResponse(RoutingResponse):
    """Standardized A-B routing response following OGC API patterns."""

    type: str = Field("FeatureCollection", title="GeoJSON Type", frozen=True)

    # Re-declare 'routes' to use the specific ABRoute type.
    routes: List[ABRoute] = Field(
        ..., title="Routes", description="A list of found routes.", min_length=0
    )

    total_routes: int = Field(..., title="Total Routes Returned", ge=0)

    @model_validator(mode="before")
    @classmethod
    def calculate_total_routes(cls: Type[Self], data: Any) -> Any:
        """
        Automatically calculate 'total_routes' from the 'routes' list.
        This runs before validation and ensures data consistency.
        """
        if isinstance(data, dict) and "routes" in data:
            # We calculate the length and add/overwrite the 'total_routes' field.
            data["total_routes"] = len(data.get("routes", []))
        return data
