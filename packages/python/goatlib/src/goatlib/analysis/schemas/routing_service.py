"""
Routing service interfaces for catchment area analysis.

This module defines abstract interfaces for routing providers that can be
used for catchment area calculations. Implementations can be mocked for
testing or connected to real routing backends (R5, goat_routing, MOTIS, OTP).
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

    This interface defines the contract that all routing providers must
    implement to compute catchment areas. Each provider (R5, goat_routing,
    MOTIS, OTP) will have its own adapter implementing this interface.
    """

    @abstractmethod
    async def compute_catchment_area_active_mobility(
        self: Self, request: CatchmentAreaActiveMobilityRequest
    ) -> CatchmentAreaResponse:
        """
        Compute catchment area for active mobility modes.

        Args:
            request: Active mobility catchment area request

        Returns:
            CatchmentAreaResponse with computed catchment area

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the routing service is unavailable
        """
        pass

    @abstractmethod
    async def compute_catchment_area_car(
        self: Self, request: CatchmentAreaCarRequest
    ) -> CatchmentAreaResponse:
        """
        Compute catchment area for car mode.

        Args:
            request: Car catchment area request

        Returns:
            CatchmentAreaResponse with computed catchment area

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the routing service is unavailable
        """
        pass

    @abstractmethod
    async def compute_catchment_area_pt(
        self: Self, request: CatchmentAreaPTRequest
    ) -> CatchmentAreaResponse:
        """
        Compute catchment area for public transport.

        Args:
            request: PT catchment area request

        Returns:
            CatchmentAreaResponse with computed catchment area

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the routing service is unavailable
        """
        pass


class MockCatchmentAreaService(CatchmentAreaService):
    """
    Mock implementation of CatchmentAreaService for testing.

    Returns predefined responses without calling any external routing service.
    Useful for unit tests and development.
    """

    def __init__(
        self: Self, default_response: CatchmentAreaResponse | None = None
    ) -> None:
        """
        Initialize mock service.

        Args:
            default_response: Optional default response to return for all requests
        """
        self._default_response = default_response
        self._call_history: list[dict] = []

    @property
    def call_history(self: Self) -> list[dict]:
        """Get the history of calls made to this mock service."""
        return self._call_history

    def reset(self: Self) -> None:
        """Reset call history."""
        self._call_history = []

    def _record_call(self: Self, method: str, request: dict) -> None:
        """Record a call to the mock service."""
        self._call_history.append({"method": method, "request": request})

    def _create_mock_response(
        self: Self,
        starting_point: dict,
        catchment_area_type: str,
    ) -> CatchmentAreaResponse:
        """Create a mock response."""
        from goatlib.analysis.schemas.catchment_area import (
            CatchmentAreaPolygon,
            CatchmentAreaType,
            Coordinates,
        )

        coord = (
            starting_point.to_coordinates()[0]
            if hasattr(starting_point, "to_coordinates")
            else Coordinates(lat=0, lon=0)
        )

        # Create mock polygon
        mock_polygon = CatchmentAreaPolygon(
            travel_cost=15,
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        [coord.lon - 0.01, coord.lat - 0.01],
                        [coord.lon + 0.01, coord.lat - 0.01],
                        [coord.lon + 0.01, coord.lat + 0.01],
                        [coord.lon - 0.01, coord.lat + 0.01],
                        [coord.lon - 0.01, coord.lat - 0.01],
                    ]
                ],
            },
            area_sqm=1000000.0,
        )

        return CatchmentAreaResponse(
            starting_point=coord,
            catchment_area_type=CatchmentAreaType(catchment_area_type),
            polygons=[mock_polygon],
            metadata={"provider": "mock", "mock": True},
        )

    async def compute_catchment_area_active_mobility(
        self: Self, request: CatchmentAreaActiveMobilityRequest
    ) -> CatchmentAreaResponse:
        """Mock implementation for active mobility."""
        self._record_call(
            "compute_catchment_area_active_mobility",
            request.model_dump(),
        )

        if self._default_response:
            return self._default_response

        return self._create_mock_response(
            request.starting_points,
            request.catchment_area_type,
        )

    async def compute_catchment_area_car(
        self: Self, request: CatchmentAreaCarRequest
    ) -> CatchmentAreaResponse:
        """Mock implementation for car."""
        self._record_call(
            "compute_catchment_area_car",
            request.model_dump(),
        )

        if self._default_response:
            return self._default_response

        return self._create_mock_response(
            request.starting_points,
            request.catchment_area_type,
        )

    async def compute_catchment_area_pt(
        self: Self, request: CatchmentAreaPTRequest
    ) -> CatchmentAreaResponse:
        """Mock implementation for public transport."""
        self._record_call(
            "compute_catchment_area_pt",
            request.model_dump(),
        )

        if self._default_response:
            return self._default_response

        return self._create_mock_response(
            request.starting_points,
            request.catchment_area_type,
        )
