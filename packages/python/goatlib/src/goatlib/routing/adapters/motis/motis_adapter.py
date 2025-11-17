import logging
from pathlib import Path
from typing import Self

from goatlib.routing.errors import RoutingError
from goatlib.routing.interfaces.routing_service import RoutingService
from goatlib.routing.schemas.ab_routing import (
    ABRoutingRequest,
    ABRoutingResponse,
)

from .motis_client import MotisServiceClient
from .motis_converters import (
    parse_motis_response,
    tranlsate_to_motis_request,
)

logger = logging.getLogger(__name__)


class MotisPlanApiAdapter(RoutingService):
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

    async def route(self: Self, request: ABRoutingRequest) -> ABRoutingResponse:
        try:
            request_data = tranlsate_to_motis_request(request)
            motis_response = await self.motis_client.plan(request_data)
            response_data = parse_motis_response(motis_response)

            return response_data

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
