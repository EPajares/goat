from abc import ABC, abstractmethod
from typing import Self

from goatlib.routing.schemas.ab_routing import ABRoutingRequest, ABRoutingResponse


class RoutingServiceTarget(ABC):
    """
    The Target interface defines the domain-specific interface used by the client code.
    This represents our standardized routing interface that all routing services should conform to.
    """

    @abstractmethod
    def route(self: Self, request: ABRoutingRequest) -> ABRoutingResponse:
        """
        Execute a routing request and return standardized routes.

        Args:
            request: Standardized routing request following our internal schema

        Returns:
            List of standardized ABRoute objects

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the routing service is unavailable or returns an error
        """
        pass
