"""Pytest fixtures for GeoAPI tests."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_ducklake_manager():
    """Mock DuckLake manager for tests."""
    with patch("geoapi.ducklake.ducklake_manager") as mock:
        mock_conn = MagicMock()
        mock.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock.connection.return_value.__exit__ = MagicMock(return_value=None)
        yield mock


@pytest.fixture
def mock_layer_service():
    """Mock layer service for tests."""
    with patch("geoapi.services.layer_service.layer_service") as mock:
        mock.init = AsyncMock()
        mock.close = AsyncMock()
        yield mock


@pytest.fixture
def mock_schema_cache():
    """Mock the schema cache to avoid DuckLake queries in tests."""
    # Patch get_schema_for_layer to return a fixed schema
    with patch("geoapi.dependencies.get_schema_for_layer") as mock:
        mock.return_value = "user_123456789012345678901234567890ab"
        yield mock


@pytest.fixture
def test_client(
    mock_ducklake_manager, mock_layer_service, mock_schema_cache
) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies."""
    from geoapi.main import app

    # Override lifespan to avoid real connections
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture
def sample_layer_metadata():
    """Sample layer metadata for tests."""
    from geoapi.services.layer_service import LayerMetadata

    return LayerMetadata(
        layer_id="abc123de-f456-7890-1234-5678901234ab",
        name="Test Layer",
        geometry_type="Point",
        bounds=[-180, -90, 180, 90],
        columns=[
            {"name": "id", "type": "uuid", "json_type": "string"},
            {"name": "name", "type": "varchar", "json_type": "string"},
            {"name": "value", "type": "integer", "json_type": "integer"},
            {"name": "geom", "type": "geometry", "json_type": "geometry"},
        ],
        user_id="12345678-9012-3456-7890-1234567890ab",
    )


@pytest.fixture
def sample_features():
    """Sample features for tests."""
    return [
        {
            "type": "Feature",
            "id": "feature-1",
            "geometry": {"type": "Point", "coordinates": [10.0, 52.0]},
            "properties": {"name": "Berlin", "value": 100},
        },
        {
            "type": "Feature",
            "id": "feature-2",
            "geometry": {"type": "Point", "coordinates": [11.5, 48.1]},
            "properties": {"name": "Munich", "value": 200},
        },
    ]
