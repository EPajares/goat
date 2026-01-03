"""
Mock implementations of routing service interfaces.

These mock implementations can be used for testing without requiring actual
backend services (R5, GOAT Routing, etc.). They return realistic-looking
response structures for development and testing purposes.
"""

from datetime import datetime
from typing import Any, Self

from goatlib.analysis.schemas.catchment_area import (
    CatchmentAreaActiveMobilityRequest,
    CatchmentAreaCarRequest,
    CatchmentAreaPTRequest,
    CatchmentAreaResponse,
    CatchmentAreaPolygon,
    CatchmentAreaType,
    Coordinates,
)

from .catchment_area_service import CatchmentAreaService, GoatRoutingService, R5Service


def _create_mock_polygon(center_lat: float, center_lon: float, size: float) -> dict:
    """Create a simple square polygon GeoJSON geometry around a center point."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [center_lon - size, center_lat - size],
                [center_lon + size, center_lat - size],
                [center_lon + size, center_lat + size],
                [center_lon - size, center_lat + size],
                [center_lon - size, center_lat - size],
            ]
        ],
    }


class MockCatchmentAreaService(CatchmentAreaService):
    """
    Mock implementation of CatchmentAreaService for testing.

    Returns simplified polygon responses that mimic the structure of real
    catchment area responses without performing actual routing calculations.
    """

    def __init__(
        self: Self,
        latency_ms: int = 0,
        fail_after: int | None = None,
    ) -> None:
        """
        Initialize mock service.

        Args:
            latency_ms: Simulated latency in milliseconds (not implemented yet)
            fail_after: Fail after this many calls (for testing error handling)
        """
        self.latency_ms = latency_ms
        self.fail_after = fail_after
        self._call_count = 0
        self._call_history: list[dict] = []

    @property
    def call_history(self: Self) -> list[dict]:
        """Get the history of calls made to this mock service."""
        return self._call_history

    def reset(self: Self) -> None:
        """Reset call history and call count."""
        self._call_history = []
        self._call_count = 0

    def _record_call(self: Self, method: str, request: Any) -> None:
        """Record a call to the mock service."""
        self._call_history.append({"method": method, "request": request})

    def _check_fail(self: Self) -> None:
        """Check if we should simulate a failure."""
        self._call_count += 1
        if self.fail_after is not None and self._call_count > self.fail_after:
            raise RuntimeError(
                f"Mock service failed after {self.fail_after} calls (simulated)"
            )

    async def compute_active_mobility_catchment(
        self: Self, request: CatchmentAreaActiveMobilityRequest
    ) -> CatchmentAreaResponse:
        """Return mock catchment area for active mobility."""
        self._check_fail()
        self._record_call("compute_active_mobility_catchment", request)

        # Get starting point
        starting_points = request.starting_points
        if starting_points.latitude and starting_points.longitude:
            lat = starting_points.latitude[0]
            lon = starting_points.longitude[0]
        elif starting_points.coordinates:
            lat = starting_points.coordinates[0].lat
            lon = starting_points.coordinates[0].lon
        else:
            lat, lon = 48.1351, 11.5820  # Munich default

        # Create mock polygons based on travel cost steps
        travel_cost = request.travel_cost
        if hasattr(travel_cost, "max_traveltime"):
            max_value = travel_cost.max_traveltime
            step_size = getattr(travel_cost, "traveltime_step", 5)
        else:
            max_value = travel_cost.max_distance
            step_size = getattr(travel_cost, "distance_step", 100)

        polygons = []
        for i, step in enumerate(range(step_size, max_value + 1, step_size)):
            size = 0.005 * (i + 1)  # Progressively larger polygons
            polygon_geom = _create_mock_polygon(lat, lon, size)
            polygons.append(
                CatchmentAreaPolygon(
                    travel_cost=step,
                    geometry=polygon_geom,
                    area_sqm=size * size * 111000 * 111000,  # Rough area estimate
                )
            )

        return CatchmentAreaResponse(
            starting_point=Coordinates(lat=lat, lon=lon),
            catchment_area_type=CatchmentAreaType.polygon,
            polygons=polygons,
            metadata={
                "mode": request.routing_mode.value,
                "provider": "mock",
                "computed_at": datetime.utcnow().isoformat(),
            },
        )

    async def compute_car_catchment(
        self: Self, request: CatchmentAreaCarRequest
    ) -> CatchmentAreaResponse:
        """Return mock catchment area for car mode."""
        self._check_fail()

        starting_points = request.starting_points
        if starting_points.latitude and starting_points.longitude:
            lat = starting_points.latitude[0]
            lon = starting_points.longitude[0]
        elif starting_points.coordinates:
            lat = starting_points.coordinates[0].lat
            lon = starting_points.coordinates[0].lon
        else:
            lat, lon = 48.1351, 11.5820

        travel_cost = request.travel_cost
        if hasattr(travel_cost, "max_traveltime"):
            max_value = travel_cost.max_traveltime
            step_size = getattr(travel_cost, "traveltime_step", 5)
        else:
            max_value = travel_cost.max_distance
            step_size = getattr(travel_cost, "distance_step", 100)

        polygons = []
        for i, step in enumerate(range(step_size, max_value + 1, step_size)):
            size = 0.01 * (i + 1)  # Car polygons are larger
            polygon_geom = _create_mock_polygon(lat, lon, size)
            polygons.append(
                CatchmentAreaPolygon(
                    travel_cost=step,
                    geometry=polygon_geom,
                    area_sqm=size * size * 111000 * 111000,
                )
            )

        return CatchmentAreaResponse(
            starting_point=Coordinates(lat=lat, lon=lon),
            catchment_area_type=CatchmentAreaType.polygon,
            polygons=polygons,
            metadata={
                "mode": "car",
                "provider": "mock",
                "computed_at": datetime.utcnow().isoformat(),
            },
        )

    async def compute_pt_catchment(
        self: Self, request: CatchmentAreaPTRequest
    ) -> CatchmentAreaResponse:
        """
        Mock PT catchment - raises NotImplementedError.

        PT catchment uses R5 grid data (.bin files) and cannot be meaningfully
        mocked with simple polygons. Use MockR5Service instead if you need to
        test PT-related functionality at the R5 API level.
        """
        raise NotImplementedError(
            "PT catchment requires R5 grid processing and cannot be mocked "
            "with simple polygons. Use MockR5Service for low-level R5 API testing."
        )


class MockR5Service(R5Service):
    """
    Mock implementation of R5 service for testing.

    Returns response structures that mimic R5's analysis API without
    actually running R5.
    """

    def __init__(
        self: Self,
        fail_on_call: bool = False,
        custom_response: dict | None = None,
    ) -> None:
        """
        Initialize mock R5 service.

        Args:
            fail_on_call: Whether to raise an error on any call
            custom_response: Custom response to return instead of default
        """
        self.fail_on_call = fail_on_call
        self.custom_response = custom_response
        self.last_request: dict[str, Any] | None = None

    async def post_analysis(
        self: Self,
        *,
        access_modes: str,
        transit_modes: str | None = None,
        direct_modes: str | None = None,
        egress_modes: str | None = None,
        from_lat: float,
        from_lon: float,
        bounds: dict,
        date: str,
        from_time: int,
        to_time: int,
        max_trip_duration_minutes: int,
        walk_speed: float,
        bike_speed: float | None = None,
        decay_function: dict | None = None,
        zoom: int = 9,
        percentiles: list[int] | None = None,
        monte_carlo_draws: int = 200,
        max_walk_time: int | None = None,
        max_bike_time: int | None = None,
        max_rides: int | None = None,
    ) -> dict:
        """Return mock R5 analysis response."""
        # Store request for inspection in tests
        self.last_request = {
            "accessModes": access_modes,
            "transitModes": transit_modes,
            "directModes": direct_modes,
            "egressModes": egress_modes,
            "fromLat": from_lat,
            "fromLon": from_lon,
            "bounds": bounds,
            "date": date,
            "fromTime": from_time,
            "toTime": to_time,
            "maxTripDurationMinutes": max_trip_duration_minutes,
            "walkSpeed": walk_speed,
            "bikeSpeed": bike_speed,
            "decayFunction": decay_function,
            "zoom": zoom,
            "percentiles": percentiles or [1],
            "monteCarloDraws": monte_carlo_draws,
            "maxWalkTime": max_walk_time,
            "maxBikeTime": max_bike_time,
            "maxRides": max_rides,
        }

        if self.fail_on_call:
            raise RuntimeError("Mock R5 service failure (simulated)")

        if self.custom_response:
            return self.custom_response

        # Return a minimal mock response structure
        # R5 returns grid-based travel time data
        return {
            "data": [
                {
                    "key": "TRAVEL_TIME",
                    "value": {
                        "zoom": zoom,
                        "west": bounds["west"],
                        "north": bounds["north"],
                        "width": 100,
                        "height": 100,
                        "depth": 1,
                        "data": [],  # Would contain travel time values
                        "errors": [],
                        "warnings": [],
                    },
                }
            ],
            "scenarioApplicationInfo": None,
            "scenarioApplicationWarnings": [],
            "request": self.last_request,
        }


class MockGoatRoutingService(GoatRoutingService):
    """
    Mock implementation of GOAT Routing service for testing.

    Returns response structures that mimic the Rust-based routing service
    without actually calling it.
    """

    def __init__(
        self: Self,
        fail_on_call: bool = False,
        custom_response: dict | None = None,
    ) -> None:
        """
        Initialize mock GOAT Routing service.

        Args:
            fail_on_call: Whether to raise an error on any call
            custom_response: Custom response to return instead of default
        """
        self.fail_on_call = fail_on_call
        self.custom_response = custom_response
        self.last_request: dict[str, Any] | None = None

    async def get_isochrone(
        self: Self,
        *,
        mode: str,
        starting_points: dict,
        travel_cost: dict,
        output_format: str = "geojson",
        polygon_difference: bool | None = None,
        h3_resolution: int | None = None,
    ) -> dict:
        """Return mock isochrone response."""
        self.last_request = {
            "mode": mode,
            "starting_points": starting_points,
            "travel_cost": travel_cost,
            "output_format": output_format,
            "polygon_difference": polygon_difference,
            "h3_resolution": h3_resolution,
        }

        if self.fail_on_call:
            raise RuntimeError("Mock GOAT Routing service failure (simulated)")

        if self.custom_response:
            return self.custom_response

        # Get center point for mock polygon
        if "latitude" in starting_points and starting_points["latitude"]:
            lat = starting_points["latitude"][0]
            lon = starting_points["longitude"][0]
        else:
            lat, lon = 48.1351, 11.5820

        # Create mock GeoJSON response
        if output_format == "geojson":
            polygon = _create_mock_polygon(lat, lon, 0.01)
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": polygon,
                        "properties": {
                            "mode": mode,
                            "travel_cost": travel_cost,
                        },
                    }
                ],
            }
        elif output_format == "grid":
            return {
                "type": "grid",
                "h3_resolution": h3_resolution or 9,
                "cells": [
                    {"h3_index": "891f1d48173ffff", "travel_time": 300},
                    {"h3_index": "891f1d48177ffff", "travel_time": 450},
                ],
            }
        else:
            # Parquet would be binary, return mock metadata
            return {
                "type": "parquet",
                "row_count": 100,
                "columns": ["geometry", "travel_time", "mode"],
            }
