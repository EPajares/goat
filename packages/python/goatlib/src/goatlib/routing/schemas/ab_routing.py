import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Self

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

    leg_id: str = Field(..., title="Leg ID")
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

    route_id: str = Field(..., title="Route ID")
    optimization_score: Optional[float] = Field(
        None, title="Optimization Score", ge=0, le=1
    )
    accessibility_score: Optional[float] = Field(
        None, title="Accessibility Score", ge=0, le=1
    )
    environmental_score: Optional[float] = Field(
        None, title="Environmental Score", ge=0, le=1
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
    request_id: str = Field(..., title="Request ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, title="Timestamp")
    routes: List[ABRoute] = Field(..., title="Routes")
    total_routes: int = Field(..., title="Total Routes", ge=0)

    @model_validator(mode="after")
    def validate_route_counts(self: Self) -> Self:
        """
        Ensures data integrity between the number of routes and the total_routes field.
        """
        if self.total_routes != len(self.routes):
            logger.error(
                f"Mismatch in route count: 'total_routes' is {self.total_routes} "
                f"but {len(self.routes)} routes were provided."
            )
            raise ValueError("Internal data inconsistency: route count mismatch.")

        if self.total_routes == 0 and not self.routes:
            logger.info(f"Request {self.request_id} resulted in 0 routes found.")

        return self
