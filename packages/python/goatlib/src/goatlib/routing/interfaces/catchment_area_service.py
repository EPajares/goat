"""
Catchment Area Service Interface.

This module defines the abstract interface for catchment area routing services.
Different providers (R5, GOAT Routing, MOTIS) implement this interface to
provide isochrone/catchment area calculations.
"""

from abc import ABC, abstractmethod
from typing import Self

from goatlib.analysis.schemas.catchment_area import (
    CatchmentAreaActiveMobilityRequest,
    CatchmentAreaCarRequest,
    CatchmentAreaPTRequest,
    CatchmentAreaResponse,
)


class CatchmentAreaService(ABC):
    """
    Abstract interface for catchment area routing services.

    This interface defines the contract for services that compute catchment areas
    (isochrones) for different transport modes. Implementations may use various
    backends like R5, GOAT Routing, or MOTIS.
    """

    @abstractmethod
    async def compute_active_mobility_catchment(
        self: Self, request: CatchmentAreaActiveMobilityRequest
    ) -> CatchmentAreaResponse:
        """
        Compute catchment area for active mobility modes (walk, bike, etc.).

        Args:
            request: Active mobility catchment area request

        Returns:
            CatchmentAreaResponse with isochrone polygons

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the service is unavailable
        """
        pass

    @abstractmethod
    async def compute_car_catchment(
        self: Self, request: CatchmentAreaCarRequest
    ) -> CatchmentAreaResponse:
        """
        Compute catchment area for car mode.

        Args:
            request: Car catchment area request

        Returns:
            CatchmentAreaResponse with isochrone polygons

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the service is unavailable
        """
        pass

    @abstractmethod
    async def compute_pt_catchment(
        self: Self, request: CatchmentAreaPTRequest
    ) -> CatchmentAreaResponse:
        """
        Compute catchment area for public transport mode.

        Args:
            request: Public transport catchment area request

        Returns:
            CatchmentAreaResponse with isochrone polygons

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the service is unavailable
        """
        pass


class R5Service(ABC):
    """
    Abstract interface for R5 routing service.

    R5 is a routing engine used for public transport and active mobility
    accessibility analysis. This interface defines the contract for making
    R5 API requests.
    """

    @abstractmethod
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
        """
        Make a request to R5 analysis API.

        This method follows the R5 request format used in GOAT core.

        Args:
            access_modes: Access modes (e.g., "WALK", "BICYCLE")
            transit_modes: Transit modes (e.g., "BUS,RAIL,TRAM")
            direct_modes: Direct modes for non-transit routes
            egress_modes: Egress modes from transit
            from_lat: Starting latitude
            from_lon: Starting longitude
            bounds: Bounding box dict with north, east, south, west
            date: Date in YYYY-MM-DD format
            from_time: Start time in seconds from midnight
            to_time: End time in seconds from midnight
            max_trip_duration_minutes: Maximum trip duration
            walk_speed: Walking speed in km/h
            bike_speed: Bicycle speed in km/h (optional)
            decay_function: Decay function configuration
            zoom: Zoom level for R5 grid
            percentiles: Percentiles for travel time calculation
            monte_carlo_draws: Number of Monte Carlo draws
            max_walk_time: Maximum walking time in minutes
            max_bike_time: Maximum biking time in minutes
            max_rides: Maximum number of transit rides

        Returns:
            dict: R5 response data with travel times

        Raises:
            RuntimeError: If R5 service is unavailable
        """
        pass


class GoatRoutingService(ABC):
    """
    Abstract interface for GOAT Routing service (Rust-based).

    This service provides fast routing for active mobility and car modes
    using the Rust-based routing engine.
    """

    @abstractmethod
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
        """
        Request isochrone calculation from GOAT Routing service.

        Args:
            mode: Transport mode (walk, bicycle, car, etc.)
            starting_points: Starting points configuration
            travel_cost: Travel cost configuration (time or distance based)
            output_format: Output format (geojson, parquet, grid)
            polygon_difference: Whether to return difference polygons
            h3_resolution: H3 resolution for grid output

        Returns:
            dict: Isochrone response (GeoJSON or grid data)

        Raises:
            RuntimeError: If routing service is unavailable
        """
        pass
