import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Self

from goatlib.routing.schemas.base import (
    Location,
    Route,
    RoutingRequestBase,
    RoutingResponse,
    TransportMode,
)
from pydantic import BaseModel, Field, computed_field, model_validator

logger = logging.getLogger(__name__)


class ABRouteLeg(BaseModel):
    """Individual leg of an AB route."""

    leg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mode: TransportMode = Field(..., description="Transport mode for this leg.")
    origin: Location = Field(..., description="Starting location of the leg.")
    destination: Location = Field(..., description="Ending location of the leg.")
    departure_time: datetime = Field(..., description="Departure time of the leg.")
    arrival_time: datetime = Field(..., description="Arrival time of the leg.")
    duration: float = Field(..., description="Duration of the leg in seconds", ge=0)
    distance: Optional[float] = Field(
        None, description="Distance of the leg in meters", ge=0
    )
    geometry: Optional[Dict[str, Any]] = Field(None)

    @model_validator(mode="after")
    def validate_leg_times(self: Self) -> Self:
        """Validate that arrival time is after departure time."""
        if self.arrival_time <= self.departure_time:
            raise ValueError("Arrival time must be after departure time")
        return self


# class ABRouteProperties(BaseModel):
#     """Properties of a single route, used within a GeoJSON Feature."""

#     duration: float = Field(..., description="Total route duration in seconds, > 0.")
#     distance: float = Field(..., description="Total route distance in meters, >= 0.")
#     departure_time: datetime


class ABRoute(Route):
    """A complete AB route with all its constituent legs."""

    route_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    legs: List[ABRouteLeg] = Field(..., min_length=1)
    # properties: ABRouteProperties

    @computed_field
    @property
    def geometry(self: Self) -> Dict[str, Any]:
        """Generates the GeoJSON LineString geometry for the route."""
        if not self.legs:
            return {"type": "LineString", "coordinates": []}

        coordinates = [[self.legs[0].origin.lon, self.legs[0].origin.lat]]
        coordinates.extend(
            [leg.destination.lon, leg.destination.lat] for leg in self.legs
        )

        return {"type": "LineString", "coordinates": coordinates}

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


class ABRoutingRequest(RoutingRequestBase):
    """A-B routing request."""

    max_results: Optional[int] = Field(default=3, ge=1, le=10)
    max_travel_time: Optional[int] = Field(None, ge=1, le=480)
    max_transfers: Optional[int] = Field(None, ge=0, le=10)
    max_walking_distance: Optional[int] = Field(None, ge=0, le=5000)
    include_geometry: Optional[bool] = Field(default=True)


class ABRoutingResponse(RoutingResponse):
    """A-B routing response structured as a GeoJSON FeatureCollection.."""

    # Override the type of routes from the base class
    routes: List[ABRoute] = Field(..., description="List of routes as ABRoute objects.")

    # Standard GeoJSON field
    type: str = Field("FeatureCollection", frozen=True)

    @computed_field(alias="features")
    @property
    def features_property(self: Self) -> List[ABRoute]:
        return self.routes

    def to_geojson_str(self: Self, indent: Optional[int] = 2) -> str:
        """
        Serializes the response object to a GeoJSON compliant string.

        Args:
            indent: The number of spaces to use for JSON indentation.
                    Set to None for a compact string.

        Returns:
            A string containing the GeoJSON FeatureCollection.
        """
        return self.model_dump_json(
            indent=indent,
            exclude={"routes"},
        )

    def to_geojson_file(
        self: Self, file_path: Path | str, indent: Optional[int] = 2
    ) -> None:
        """
        Serializes the response to a GeoJSON compliant file.

        Args:
            file_path: The path to the output .geojson file.
            indent: The number of spaces for JSON indentation.
        """
        path = Path(file_path)

        path.parent.mkdir(parents=True, exist_ok=True)
        geojson_str = self.to_geojson_str(indent=indent)
        path.write_text(geojson_str, encoding="utf-8")
