import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional, Self

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
    _fixture_path: Optional[Path]
    _fixture_cache: Dict[Path, Any]
    _rng: random.Random

    def __init__(
        self: Self,
        base_url: str = "https://api.transitous.org",
        plan_endpoint: str = "/api/v5/plan",
        use_fixtures: bool = True,
        fixture_path: Optional[Path | str] = None,
        seed: Optional[int] = 42,
    ) -> None:
        self.base_url = base_url
        self.plan_endpoint = plan_endpoint
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

    def plan(self: Self, motis_request: Dict[str, Any]) -> Dict[str, Any]:
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
            return self._make_plan_api_request(motis_request)

    def _make_plan_api_request(
        self: Self, api_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Makes a real HTTP GET request to the MOTIS service."""
        import requests

        endpoint = f"{self.base_url}{self.plan_endpoint}"
        logger.info(f"Making MOTIS plan request to {endpoint}")
        try:
            response = requests.get(
                endpoint,
                params=api_params,
                headers={
                    "Accept": "application/json",
                },
                timeout=30,  # 30 second timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.Timeout):
                log_msg = f"Request to MOTIS service timed out at {endpoint}"
            elif isinstance(e, requests.exceptions.ConnectionError):
                log_msg = f"Failed to connect to MOTIS service at {endpoint}"
            elif isinstance(e, requests.exceptions.HTTPError):
                log_msg = f"MOTIS service returned an error: {e.response.status_code} {e.response.reason} for url {e.response.url}"
            else:
                log_msg = f"An unexpected request error occurred: {e}"

            logger.error(log_msg)
            raise RuntimeError("MOTIS service request failed to complete.") from e

        except json.JSONDecodeError as e:
            # Catching JSONDecodeError for invalid JSON responses
            logger.error(f"Failed to parse JSON response from MOTIS service: {e}")
            raise RuntimeError("Invalid response format from MOTIS service.") from e

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
