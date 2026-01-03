"""
Tests for catchment area endpoints with GeoJSON and Parquet output formats.
"""

import json
import os
from io import BytesIO
from typing import AsyncGenerator
from unittest.mock import patch

import numpy as np
import polars as pl
import pytest
import pytest_asyncio
from httpx import AsyncClient

from routing.core.config import settings
from routing.crud.crud_catchment_area import CRUDCatchmentArea
from routing.db.session import async_session
from routing.main import app
from routing.schemas.catchment_area import (
    CatchmentAreaRoutingTypeActiveMobility,
    CatchmentAreaStartingPoints,
    CatchmentAreaTravelTimeCostActiveMobility,
    ICatchmentAreaActiveMobility,
    OutputFormat,
)


# Test coordinates (any location within the test geofence)
TEST_LAT = 51.7167
TEST_LON = 14.3837

# Test geofence table (must exist in the database with street network data)
TEST_GEOFENCE_TABLE = "test_routing.geofence_cottbus"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestOutputFormat:
    """Tests for output format handling."""

    def test_output_format_enum(self):
        """Test OutputFormat enum values."""
        assert OutputFormat.geojson.value == "geojson"
        assert OutputFormat.parquet.value == "parquet"

    def test_default_output_format(self):
        """Test that default output format is geojson."""
        request = ICatchmentAreaActiveMobility(
            starting_points={"latitude": [TEST_LAT], "longitude": [TEST_LON]},
            routing_type="walking",
            travel_cost={
                "max_traveltime": 5,
                "steps": 1,
                "speed": 5,
            },
            catchment_area_type="polygon",
            polygon_difference=True,
        )
        assert request.output_format == OutputFormat.geojson


class TestCatchmentAreaValidation:
    """Tests for request validation."""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test that missing required fields are rejected."""
        response = await client.post(
            "/api/v2/routing/active-mobility/catchment-area",
            json={
                "starting_points": {"latitude": [TEST_LAT], "longitude": [TEST_LON]},
                # Missing routing_type, travel_cost, etc.
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_routing_type(self, client: AsyncClient):
        """Test that invalid routing type is rejected."""
        response = await client.post(
            "/api/v2/routing/active-mobility/catchment-area",
            json={
                "starting_points": {"latitude": [TEST_LAT], "longitude": [TEST_LON]},
                "routing_type": "invalid_type",
                "travel_cost": {
                    "max_traveltime": 5,
                    "steps": 1,
                    "speed": 5,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "output_format": "geojson",
            },
        )
        assert response.status_code == 422


class TestCatchmentAreaIntegration:
    """
    Integration tests for catchment area computation.

    These tests require:
    - A database connection with street network data
    - The test geofence table to exist (test_routing.geofence_cottbus)
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_geojson_output(self, client: AsyncClient):
        """Test catchment area returns valid GeoJSON."""
        with patch.object(settings, "NETWORK_REGION_TABLE", TEST_GEOFENCE_TABLE):
            response = await client.post(
                "/api/v2/routing/active-mobility/catchment-area",
                json={
                    "starting_points": {
                        "latitude": [TEST_LAT],
                        "longitude": [TEST_LON],
                    },
                    "routing_type": "walking",
                    "travel_cost": {
                        "max_traveltime": 5,
                        "steps": 1,
                        "speed": 5,
                    },
                    "catchment_area_type": "polygon",
                    "polygon_difference": True,
                    "output_format": "geojson",
                },
            )

        assert response.status_code == 200
        result = response.json()

        # Validate GeoJSON structure
        assert result["type"] == "FeatureCollection"
        assert "features" in result
        assert len(result["features"]) > 0

        # Validate features
        for feature in result["features"]:
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature
            assert feature["geometry"]["type"] in ["Polygon", "MultiPolygon"]
            assert "minute" in feature["properties"]
            assert "step" in feature["properties"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_polygon_difference_true(self, client: AsyncClient):
        """Test catchment area with polygon_difference=True returns incremental polygons."""
        with patch.object(settings, "NETWORK_REGION_TABLE", TEST_GEOFENCE_TABLE):
            response = await client.post(
                "/api/v2/routing/active-mobility/catchment-area",
                json={
                    "starting_points": {
                        "latitude": [TEST_LAT],
                        "longitude": [TEST_LON],
                    },
                    "routing_type": "walking",
                    "travel_cost": {
                        "max_traveltime": 10,
                        "steps": 2,
                        "speed": 5,
                    },
                    "catchment_area_type": "polygon",
                    "polygon_difference": True,
                    "output_format": "geojson",
                },
            )

        assert response.status_code == 200
        result_diff = response.json()

        # Now test with polygon_difference=False
        with patch.object(settings, "NETWORK_REGION_TABLE", TEST_GEOFENCE_TABLE):
            response = await client.post(
                "/api/v2/routing/active-mobility/catchment-area",
                json={
                    "starting_points": {
                        "latitude": [TEST_LAT],
                        "longitude": [TEST_LON],
                    },
                    "routing_type": "walking",
                    "travel_cost": {
                        "max_traveltime": 10,
                        "steps": 2,
                        "speed": 5,
                    },
                    "catchment_area_type": "polygon",
                    "polygon_difference": False,
                    "output_format": "geojson",
                },
            )

        assert response.status_code == 200
        result_full = response.json()

        # Both should have features
        assert len(result_diff["features"]) > 0
        assert len(result_full["features"]) > 0

        # The JSON representations should be different
        # (incremental vs full polygons have different geometries)
        json_diff = json.dumps(result_diff)
        json_full = json.dumps(result_full)
        assert json_diff != json_full

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parquet_output(self, client: AsyncClient):
        """Test catchment area returns valid Parquet."""
        with patch.object(settings, "NETWORK_REGION_TABLE", TEST_GEOFENCE_TABLE):
            response = await client.post(
                "/api/v2/routing/active-mobility/catchment-area",
                json={
                    "starting_points": {
                        "latitude": [TEST_LAT],
                        "longitude": [TEST_LON],
                    },
                    "routing_type": "walking",
                    "travel_cost": {
                        "max_traveltime": 5,
                        "steps": 1,
                        "speed": 5,
                    },
                    "catchment_area_type": "polygon",
                    "polygon_difference": True,
                    "output_format": "parquet",
                },
            )

        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/octet-stream"

        # Validate Parquet content
        content = response.content
        assert len(content) > 0

        df = pl.read_parquet(BytesIO(content))
        assert len(df) > 0
        assert "geometry" in df.columns
        assert "minute" in df.columns

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_steps(self, client: AsyncClient):
        """Test catchment area with multiple time steps."""
        with patch.object(settings, "NETWORK_REGION_TABLE", TEST_GEOFENCE_TABLE):
            response = await client.post(
                "/api/v2/routing/active-mobility/catchment-area",
                json={
                    "starting_points": {
                        "latitude": [TEST_LAT],
                        "longitude": [TEST_LON],
                    },
                    "routing_type": "walking",
                    "travel_cost": {
                        "max_traveltime": 15,
                        "steps": 3,
                        "speed": 5,
                    },
                    "catchment_area_type": "polygon",
                    "polygon_difference": True,
                    "output_format": "geojson",
                },
            )

        assert response.status_code == 200
        result = response.json()

        # Should have features for each step
        assert len(result["features"]) >= 3


class TestCatchmentAreaCRUD:
    """Direct tests for CRUDCatchmentArea class."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_crud_run_geojson(self):
        """Test CRUDCatchmentArea.run() returns GeoJSON dict."""
        crud = CRUDCatchmentArea(async_session(), None)

        request = ICatchmentAreaActiveMobility(
            starting_points=CatchmentAreaStartingPoints(
                latitude=[TEST_LAT], longitude=[TEST_LON]
            ),
            routing_type=CatchmentAreaRoutingTypeActiveMobility.walking,
            travel_cost=CatchmentAreaTravelTimeCostActiveMobility(
                max_traveltime=5, steps=1, speed=5
            ),
            catchment_area_type="polygon",
            polygon_difference=True,
            output_format=OutputFormat.geojson,
        )

        params_dict = json.loads(request.model_dump_json())

        with patch.object(settings, "NETWORK_REGION_TABLE", TEST_GEOFENCE_TABLE):
            result = await crud.run(params_dict)

        # Validate result is a dict (GeoJSON)
        assert isinstance(result, dict)
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) > 0

        # Validate JSON serialization works
        json_str = json.dumps(result)
        assert len(json_str) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_crud_run_parquet(self):
        """Test CRUDCatchmentArea.run() returns Parquet bytes."""
        crud = CRUDCatchmentArea(async_session(), None)

        request = ICatchmentAreaActiveMobility(
            starting_points=CatchmentAreaStartingPoints(
                latitude=[TEST_LAT], longitude=[TEST_LON]
            ),
            routing_type=CatchmentAreaRoutingTypeActiveMobility.walking,
            travel_cost=CatchmentAreaTravelTimeCostActiveMobility(
                max_traveltime=5, steps=1, speed=5
            ),
            catchment_area_type="polygon",
            polygon_difference=True,
            output_format=OutputFormat.parquet,
        )

        params_dict = json.loads(request.model_dump_json())

        with patch.object(settings, "NETWORK_REGION_TABLE", TEST_GEOFENCE_TABLE):
            result = await crud.run(params_dict)

        # Validate result is bytes (Parquet)
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Validate Parquet can be read
        df = pl.read_parquet(BytesIO(result))
        assert len(df) > 0
