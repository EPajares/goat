import logging
from pathlib import Path
from typing import Self

from goatlib.routing.errors import RoutingError
from goatlib.routing.schemas.ab_routing import (
    ABRoutingRequest,
    ABRoutingResponse,
)
from goatlib.routing.schemas.service import RoutingServiceTarget

from .motis_client import MotisServiceClient
from .motis_converters import (
    convert_request_to_api_params,
    convert_response_from_motis,
)

logger = logging.getLogger(__name__)


class MotisPlanApiAdapter(RoutingServiceTarget):
    """
    Adapter that makes the MOTIS service interface compatible with our
    standardized routing interface.

    This adapter translates between our internal ABRouting schemas and
    the MOTIS-specific API format, following the Adapter pattern.
    """

    def __init__(self: Self, motis_client: MotisServiceClient) -> None:
        """
        Initialize the adapter with a MOTIS service client.

        Args:
            motis_client: The MOTIS service client instance
        """
        self.motis_client = motis_client

    def route(self: Self, request: ABRoutingRequest) -> ABRoutingResponse:
        try:
            request_data = convert_request_to_api_params(request)
            motis_response = self.motis_client.plan(request_data)
            routes = convert_response_from_motis(motis_response)

            # TODO: investigate why MOTIS often ignores max_results parameter
            # MOMENTARY FIX:
            # Apply client-side limit since many MOTIS APIs don't respect server-side parameters
            if request.max_results and len(routes) > request.max_results:
                original_len = len(routes)
                routes = routes[: request.max_results]
                logger.debug(
                    f"Applied client-side limit: reduced {original_len} routes to {len(routes)}"
                )

            ab_response: ABRoutingResponse = ABRoutingResponse(routes=routes)
            return ab_response

        except Exception as e:
            logger.error(f"Failed to execute routing request via MOTIS: {e}")
            raise RoutingError("Failed to process routing request via MOTIS") from e


def create_motis_adapter(
    use_fixtures: bool = True,
    fixture_path: Path | str = None,
    base_url: str = "https://api.transitous.org",
) -> MotisPlanApiAdapter:
    """
    Convenience function to create a MOTIS adapter instance.

    Args:
        use_fixtures: Whether to use fixture data instead of real API calls
        fixture_path: Path to the directory containing MOTIS fixture data

    Returns:
        Configured MotisPlanApiAdapter instance

    """
    motis_client = MotisServiceClient(
        use_fixtures=use_fixtures,
        fixture_path=fixture_path,
        base_url=base_url,
    )
    return MotisPlanApiAdapter(motis_client)
