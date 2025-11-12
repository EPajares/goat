from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from goatlib.routing.adapters.motis import MotisPlanApiAdapter, create_motis_adapter
from goatlib.routing.errors import RoutingError
from goatlib.routing.schemas.ab_routing import ABRoutingRequest
from goatlib.routing.schemas.base import Location, Mode


@pytest_asyncio.fixture
async def adapter() -> AsyncGenerator[MotisPlanApiAdapter, None]:
    """
    An async fixture that provides a configured Motis adapter for error testing
    and properly cleans up its resources.
    """
    adapter = create_motis_adapter(use_fixtures=False)
    yield adapter
    await adapter.motis_client.close()


###########################################################################


async def test_invalid_api_url_handling() -> None:
    """Test handling of invalid API URLs."""
    # Create a separate adapter with invalid URL for this test
    adapter = create_motis_adapter(
        use_fixtures=False, base_url="https://nonexistent-api.example.com"
    )

    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=53.5511, lon=9.9937),
        modes=[Mode.TRANSIT],
        max_results=1,
    )

    try:
        with pytest.raises(RoutingError):
            await adapter.route(request)
    finally:
        await adapter.motis_client.close()


async def test_api_timeout_handling(adapter: MotisPlanApiAdapter) -> None:
    """Test handling of API timeouts."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Simulate timeout
        mock_get.side_effect = Exception("Connection timeout")

        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[Mode.TRANSIT],
            max_results=1,
        )

        with pytest.raises(RoutingError):
            await adapter.route(request)


async def test_malformed_api_response_handling(adapter: MotisPlanApiAdapter) -> None:
    """Test handling of malformed API responses."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Simulate malformed response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: {"invalid": "response"}
        mock_response.raise_for_status = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[Mode.TRANSIT],
            max_results=1,
        )

        response = await adapter.route(request)
        assert response.routes == []


async def test_http_error_status_handling(adapter: MotisPlanApiAdapter) -> None:
    """Test handling of HTTP error status codes."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Simulate HTTP 500 error
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = AsyncMock(
            side_effect=Exception("HTTP 500 Error")
        )
        mock_get.return_value = mock_response

        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[Mode.TRANSIT],
            max_results=1,
        )

        with pytest.raises(RoutingError):
            await adapter.route(request)


async def test_invalid_json_response_handling(adapter: MotisPlanApiAdapter) -> None:
    """Test handling of invalid JSON responses."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Simulate invalid JSON
        mock_response = AsyncMock()
        mock_response.status_code = 200

        def raise_json_error() -> None:
            raise ValueError("Invalid JSON")

        mock_response.json = raise_json_error
        mock_get.return_value = mock_response

        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[Mode.TRANSIT],
            max_results=1,
        )

        with pytest.raises(RoutingError):
            await adapter.route(request)


async def test_empty_fixture_directory(tmp_path: str) -> None:
    """Test handling of empty fixture directories."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    adapter = create_motis_adapter(use_fixtures=True, fixture_path=empty_dir)
    request = ABRoutingRequest(
        origin=Location(lat=48.1, lon=11.5),
        destination=Location(lat=48.2, lon=11.6),
        modes=[Mode.WALK],
        max_results=1,
    )

    try:
        with pytest.raises(RoutingError):
            await adapter.route(request)
    finally:
        # For fixture-based adapters, close might not be needed, but let's be safe
        if hasattr(adapter.motis_client, "close"):
            await adapter.motis_client.close()


async def test_corrupted_fixture_file_handling(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """Test handling of corrupted fixture files."""
    # Create a corrupted JSON file
    corrupted_file = tmp_path / "test_motis_routes_corrupted.json"
    corrupted_file.write_text("{ invalid json content")

    adapter = create_motis_adapter(use_fixtures=True, fixture_path=tmp_path)
    request = ABRoutingRequest(
        origin=Location(lat=48.1, lon=11.5),
        destination=Location(lat=48.2, lon=11.6),
        modes=[Mode.WALK],
        max_results=1,
    )

    try:
        with pytest.raises(RoutingError):
            await adapter.route(request)
    finally:
        if hasattr(adapter.motis_client, "close"):
            await adapter.motis_client.close()
