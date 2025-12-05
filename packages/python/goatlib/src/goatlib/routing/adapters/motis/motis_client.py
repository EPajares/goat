import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional, Self

import httpx

logger = logging.getLogger(__name__)


class MotisServiceClient:
    """
    Client for MOTIS routing services.

    Handles both real API requests and fixture data loading for development/testing.
    Uses the standard MOTIS API format for requests and responses.
    """

    base_url: str
    plan_endpoint: str
    use_fixtures: bool
    _fixture_path: Path | None
    _fixture_cache: Dict[Path, Any]
    _rng: random.Random
    _http_client: httpx.AsyncClient

    def __init__(
        self: Self,
        base_url: str = "https://api.transitous.org",
        plan_endpoint: str = "/api/v5/plan",
        one_to_all_endpoint: str = "/api/v1/one-to-all",
        use_fixtures: bool = True,
        fixture_path: Path | str | None = None,
        seed: int | None = 42,
    ) -> None:
        self.base_url = base_url
        self.plan_endpoint = plan_endpoint
        self.one_to_all_endpoint = one_to_all_endpoint
        self.use_fixtures = use_fixtures
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._fixture_cache = {}
        self._rng = random.Random()
        if self.use_fixtures and seed is not None:
            self._rng.seed(seed)

        if self.use_fixtures and self._fixture_path is None:
            raise ValueError(
                "`fixture_path` must be provided when `use_fixtures` is True."
            )
        if not self.use_fixtures:
            self._http_client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def __aenter__(self: Self) -> Self:
        """
        Enter the runtime context related to this object.
        Initializes the client if needed and returns itself.
        """
        return self

    async def __aexit__(
        self: Self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        """
        Exit the runtime context and close resources.
        This is called automatically when exiting an `async with` block.
        """
        await self.close()

    async def plan(self: Self, motis_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a routing plan request.

        Args:
            motis_request: Request in MOTIS-specific format

        Returns:
            Raw MOTIS response data

        Raises:
            RuntimeError: If the MOTIS service is unavailable or returns an error
        """
        if self.use_fixtures:
            return self._load_fixture_response()
        else:
            return await self._make_plan_api_request(motis_request)

    async def one_to_all(self: Self, motis_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a one-to-all routing request.

        Args:
            motis_request: Request in MOTIS one-to-all specific format

        Returns:
            Raw MOTIS one-to-all response data

        Raises:
            RuntimeError: If the MOTIS service is unavailable or returns an error
        """
        # For now, one-to-all only supports real API calls, not fixtures
        return await self._make_one_to_all_api_request(motis_request)

    async def _make_plan_api_request(
        self: Self, api_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"Making async MOTIS plan request to {self.plan_endpoint}")
        try:
            response = await self._http_client.get(
                self.plan_endpoint,
                params=api_params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

        except httpx.RequestError as e:
            if isinstance(e, httpx.TimeoutException):
                log_msg = f"Request to MOTIS service timed out at {e.request.url}"
            if isinstance(e, httpx.HTTPStatusError):
                log_msg = f"MOTIS service returned error {e.response.status_code} for request to {e.request.url}"
            if isinstance(e, httpx.ConnectionError):
                log_msg = f"Connection error occurred while requesting MOTIS service at {e.request.url}"
            else:
                log_msg = f"An unexpected request error occurred: {e}"
            logger.error(log_msg)
            raise RuntimeError("MOTIS service request failed to complete.") from e

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from MOTIS service: {e}")
            raise RuntimeError("Invalid response format from MOTIS service.") from e

    async def _make_one_to_all_api_request(
        self: Self, api_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"Making async MOTIS one-to-all request to {self.one_to_all_endpoint}")
        try:
            response = await self._http_client.get(
                self.one_to_all_endpoint,
                params=api_params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

        except httpx.RequestError as e:
            if isinstance(e, httpx.TimeoutException):
                log_msg = f"Request to MOTIS one-to-all service timed out at {e.request.url}"
            if isinstance(e, httpx.HTTPStatusError):
                log_msg = f"MOTIS one-to-all service returned error {e.response.status_code} for request to {e.request.url}"
            if isinstance(e, httpx.ConnectionError):
                log_msg = f"Connection error occurred while requesting MOTIS one-to-all service at {e.request.url}"
            else:
                log_msg = f"An unexpected request error occurred: {e}"
            logger.error(log_msg)
            raise RuntimeError("MOTIS one-to-all service request failed to complete.") from e

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from MOTIS one-to-all service: {e}")
            raise RuntimeError("Invalid response format from MOTIS one-to-all service.") from e

    async def close(self: Self) -> None:
        """Closes the underlying HTTP client."""
        if not self.use_fixtures and hasattr(self, "_http_client"):
            await self._http_client.aclose()

    def _load_fixture_response(self: Self) -> Dict[str, Any]:
        """Load a fixture response for development/testing."""
        try:
            fixtures_dir = self._get_fixtures_directory()

            fixture_files = list(fixtures_dir.glob("*.json"))
            if not fixture_files:
                raise FileNotFoundError(f"No fixture files found in: {fixtures_dir}")

            selected_fixture = self._rng.choice(fixture_files)
            logger.info(f"Using fixture file: {selected_fixture.name}")

            if selected_fixture in self._fixture_cache:
                return self._fixture_cache[selected_fixture]

            # Load and cache the new fixture data
            json_text = selected_fixture.read_text(encoding="utf-8")
            fixture_data = json.loads(json_text)
            self._fixture_cache[selected_fixture] = fixture_data

            return fixture_data

        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load MOTIS fixture response: {e}")
            raise RuntimeError("Failed to load or parse MOTIS fixture data.") from e

    def _get_fixtures_directory(self: Self) -> Path:
        """Returns the fixtures directory provided during initialization."""
        if not self._fixture_path or not self._fixture_path.is_dir():
            raise FileNotFoundError(
                f"Provided fixture directory does not exist or was not provided: {self._fixture_path}"
            )
        return self._fixture_path
