from abc import ABC, abstractmethod
from typing import Self

from goatlib.routing.schemas.ab_routing import ABRoutingRequest, ABRoutingResponse
from goatlib.routing.schemas.isochrone_routing import (
    IsochroneRequest,
    IsochroneResponse,
)


class RoutingService(ABC):
    """
    The Target interface defines the domain-specific interface used by the client code.
    This represents our standardized routing interface that all routing services should conform to.
    """

    @abstractmethod
    async def route(self: Self, request: ABRoutingRequest) -> ABRoutingResponse:
        """
        Execute a routing request and return standardized routes.

        Args:
            request: Standardized routing request following our internal schema

        Returns:
            ABRoutingResponse: Standardized routing response containing routes

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the routing service is unavailable or returns an error
        """
        pass

    async def get_isochrone(self: Self, request: IsochroneRequest) -> IsochroneResponse:
        """
        Execute an isochrone request and return standardized isochrone data. Not yet implemented.
        Args:
            request: Standardized isochrone request following our internal schema
        Returns:
            IsochroneResponse: Standardized isochrone response containing isochrone data
        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the routing service is unavailable or returns an error
            NotImplementedError: If the isochrone functionality is not implemented
        """
        raise NotImplementedError("get_isochrone method is not implemented.")
