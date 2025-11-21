import logging
import uuid
from datetime import datetime, timezone
from typing import List, Self

from pydantic import BaseModel, Field, computed_field, model_validator

from goatlib.routing.schemas.base import (
    Location,
    Mode,
    Route,
    RoutingProvider,
)

logger = logging.getLogger(__name__)


class ABLeg(BaseModel):
    """Individual leg of an AB route."""

    leg_id: str | None = Field(default=None, description="Optional leg identifier")
    origin: Location = Field(..., description="Starting location of the leg.")
    destination: Location = Field(..., description="Ending location of the leg.")
    mode: Mode = Field(..., description="Transport mode for this leg.")
    departure_time: datetime = Field(..., description="Departure time of the leg.")
    arrival_time: datetime = Field(..., description="Arrival time of the leg.")
    duration: float = Field(..., description="Duration of the leg in seconds", ge=0)
    distance: float | None = Field(
        None, description="Distance of the leg in meters", ge=0
    )

    def get_or_create_id(self: Self) -> str:
        """Get existing ID or create new one if needed."""
        if self.leg_id is None:
            self.leg_id = str(uuid.uuid4())
        return self.leg_i

    @model_validator(mode="after")
    def validate_leg_times(self: Self) -> Self:
        """Validate that arrival time is after departure time."""
        if self.arrival_time <= self.departure_time:
            raise ValueError("Arrival time must be after departure time")
        return self


class ABRoute(Route):
    """A complete AB route with all its constituent legs."""

    legs: List[ABLeg] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_route_consistency(self: Self) -> Self:
        """Validate route-level consistency."""
        if not self.legs:
            raise ValueError("Route must have at least one leg")

        # Check leg connectivity
        for i in range(len(self.legs) - 1):
            current_leg = self.legs[i]
            next_leg = self.legs[i + 1]

            if next_leg.departure_time < current_leg.arrival_time:
                logger.warning(f"Gap detected between legs {i} and {i+1}")

        return self


class ABRoutingRequest(BaseModel):
    """A-B routing request."""

    origin: Location = Field(..., description="Start location")
    destination: Location = Field(..., description="End location")
    # TODO: set it in the adapter
    provider: RoutingProvider = Field(
        default=RoutingProvider.MOTIS, description="Routing service provider"
    )
    modes: List[Mode] = Field(default=[Mode.WALK])
    time: datetime = Field(default=None, description="Departure time")
    # TODO: use it properly
    time_is_arrival: bool = Field(
        default=False, description="Whether the provided time is an arrival time"
    )
    detailed_transfers: bool = Field(
        default=False, description="Whether to include detailed transfer information"
    )
    max_results: int | None = Field(default=5, ge=1, le=10)
    max_transfers: int | None = Field(None, ge=0, le=10)
    max_walking_distance: int | None = Field(None, ge=0, le=5000)

    @model_validator(mode="after")
    def validate_locations_are_distinct(self: Self) -> Self:
        if (
            self.origin
            and self.destination
            and self.origin.lat == self.destination.lat
            and self.origin.lon == self.destination.lon
        ):
            raise ValueError("Origin and destination cannot be the same")
        return self

    @model_validator(mode="after")
    def normalize_time(self: Self) -> Self:
        """Normalize timezone-naive datetime to UTC."""
        if self.time and self.time.tzinfo is None:
            self.time = self.time.replace(tzinfo=timezone.utc)
        return self


class ABRoutingResponse(BaseModel):
    """A-B routing response structured as a GeoJSON FeatureCollection.."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    routes: List[Route] = Field(..., description="List of routes", min_length=0)
    # Standard GeoJSON field
    type: str = Field("FeatureCollection", frozen=True)

    @computed_field(alias="features")
    @property
    def features_property(self: Self) -> List[ABRoute]:
        return self.routes
