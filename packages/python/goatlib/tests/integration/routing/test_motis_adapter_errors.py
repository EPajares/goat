from unittest.mock import MagicMock, patch

import pytest
from goatlib.routing.adapters.motis import create_motis_adapter
from goatlib.routing.errors import RoutingError
from goatlib.routing.schemas.ab_routing import ABRoutingRequest
from goatlib.routing.schemas.base import Location, TransportMode

"""Test error handling and edge cases."""


def test_invalid_api_url_handling() -> None:
    """Test handling of invalid API URLs."""
    adapter = create_motis_adapter(
        use_fixtures=False, base_url="https://nonexistent-api.example.com"
    )

    request = ABRoutingRequest(
        origin=Location(lat=52.5200, lon=13.4050),
        destination=Location(lat=53.5511, lon=9.9937),
        modes=[TransportMode.TRANSIT],
        max_results=1,
    )

    with pytest.raises(RoutingError):
        adapter.route(request)


def test_api_timeout_handling() -> None:
    """Test handling of API timeouts."""
    with patch("requests.get") as mock_get:
        # Simulate timeout
        mock_get.side_effect = Exception("Connection timeout")

        adapter = create_motis_adapter(use_fixtures=False)
        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[TransportMode.TRANSIT],
            max_results=1,
        )

        with pytest.raises(RoutingError):
            adapter.route(request)


def test_malformed_api_response_handling() -> None:
    """Test handling of malformed API responses."""
    with patch("requests.get") as mock_get:
        # Simulate malformed response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}
        mock_get.return_value = mock_response

        adapter = create_motis_adapter(use_fixtures=False)
        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[TransportMode.TRANSIT],
            max_results=1,
        )

        # Should handle empty itineraries gracefully
        response = adapter.route(request)
        assert response.routes == []


def test_http_error_status_handling() -> None:
    """Test handling of HTTP error status codes."""
    with patch("requests.get") as mock_get:
        # Simulate HTTP 500 error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("HTTP 500 Error")
        mock_get.return_value = mock_response

        adapter = create_motis_adapter(use_fixtures=False)
        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[TransportMode.TRANSIT],
            max_results=1,
        )

        with pytest.raises(RoutingError):
            adapter.route(request)


def test_invalid_json_response_handling() -> None:
    """Test handling of invalid JSON responses."""
    with patch("requests.get") as mock_get:
        # Simulate invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        adapter = create_motis_adapter(use_fixtures=False)
        request = ABRoutingRequest(
            origin=Location(lat=52.5, lon=13.4),
            destination=Location(lat=53.5, lon=9.9),
            modes=[TransportMode.TRANSIT],
            max_results=1,
        )

        with pytest.raises(RoutingError):
            adapter.route(request)


def test_empty_fixture_directory(tmp_path: str) -> None:
    """Test handling of empty fixture directories."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    adapter = create_motis_adapter(use_fixtures=True, fixture_path=empty_dir)
    request = ABRoutingRequest(
        origin=Location(lat=48.1, lon=11.5),
        destination=Location(lat=48.2, lon=11.6),
        modes=[TransportMode.WALK],
        max_results=1,
    )

    with pytest.raises(RoutingError):
        adapter.route(request)


def test_corrupted_fixture_file_handling(tmp_path: str) -> None:
    """Test handling of corrupted fixture files."""
    # Create a corrupted JSON file
    corrupted_file = tmp_path / "test_motis_routes_corrupted.json"
    corrupted_file.write_text("{ invalid json content")

    adapter = create_motis_adapter(use_fixtures=True, fixture_path=tmp_path)
    request = ABRoutingRequest(
        origin=Location(lat=48.1, lon=11.5),
        destination=Location(lat=48.2, lon=11.6),
        modes=[TransportMode.WALK],
        max_results=1,
    )

    with pytest.raises(RoutingError):
        adapter.route(request)
