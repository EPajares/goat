"""Unit tests for BatchGeocodingTool with mocked Pelias API."""

import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import duckdb
import pytest

from goatlib.analysis.geoanalysis import BatchGeocodingTool
from goatlib.analysis.schemas.geocoding import (
    BatchGeocodingParams,
    FieldSourceType,
    GeocodingInputMode,
)
from goatlib.models.io import DatasetMetadata


# =============================================================================
# Mock Pelias Responses
# =============================================================================


def create_pelias_response(
    lat: float | None,
    lon: float | None,
    confidence: float | None = 1.0,
    match_type: str | None = "exact",
) -> dict:
    """Create a mock Pelias GeoJSON response."""
    if lat is None or lon is None:
        return {"type": "FeatureCollection", "features": []}

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "confidence": confidence,
                    "match_type": match_type,
                    "label": f"Mocked Address at {lat}, {lon}",
                },
            }
        ],
    }


# Mock responses for different addresses
MOCK_RESPONSES = {
    "Marienplatz 1, München, Germany": create_pelias_response(48.137563, 11.574858),
    "Alexanderplatz 1, Berlin, Germany": create_pelias_response(52.521270, 13.412683),
    "Unknown Address, Nowhere": create_pelias_response(None, None),  # No match
}


def get_mock_response(query_text: str) -> dict:
    """Get mock response for a query."""
    # Check for exact match first
    if query_text in MOCK_RESPONSES:
        return MOCK_RESPONSES[query_text]

    # Default response with coordinates based on hash of query
    hash_val = hash(query_text) % 1000
    lat = 48.0 + (hash_val / 1000)
    lon = 11.0 + (hash_val / 1000)
    return create_pelias_response(lat, lon, confidence=0.8, match_type="interpolated")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_input_path(tmp_path: Path) -> Path:
    """Create a test input parquet file."""
    con = duckdb.connect(":memory:")
    con.execute("""
        CREATE TABLE test_addresses AS
        SELECT * FROM (VALUES
            (1, 'Marienplatz 1', 'München', '80331', 'Marienplatz 1, München, Germany'),
            (2, 'Alexanderplatz 1', 'Berlin', '10178', 'Alexanderplatz 1, Berlin, Germany'),
            (3, 'Königstraße 26', 'Stuttgart', '70173', 'Königstraße 26, Stuttgart, Germany')
        ) AS t(id, street, city, postal_code, full_address)
    """)

    output_path = tmp_path / "test_addresses.parquet"
    con.execute(f"COPY test_addresses TO '{output_path}' (FORMAT PARQUET)")
    con.close()

    return output_path


@pytest.fixture
def large_input_path(tmp_path: Path) -> Path:
    """Create a test input parquet file with more than 1000 rows."""
    con = duckdb.connect(":memory:")
    con.execute("""
        CREATE TABLE big_addresses AS
        SELECT
            i AS id,
            'Street ' || i AS street,
            'City' AS city,
            '12345' AS postal_code,
            'Street ' || i || ', City, Germany' AS full_address
        FROM generate_series(1, 1001) AS t(i)
    """)

    output_path = tmp_path / "big_addresses.parquet"
    con.execute(f"COPY big_addresses TO '{output_path}' (FORMAT PARQUET)")
    con.close()

    return output_path


# =============================================================================
# Tests
# =============================================================================


class TestBatchGeocodingTool:
    """Tests for BatchGeocodingTool."""

    def test_geocode_full_address_mode(self, test_input_path: Path, tmp_path: Path):
        """Test geocoding with full_address mode."""
        output_path = tmp_path / "geocoded_output.parquet"

        params = BatchGeocodingParams(
            input_path=str(test_input_path),
            input_mode=GeocodingInputMode.full_address,
            full_address_field="full_address",
            output_path=str(output_path),
            geocoder_url="https://mock.geocoder.test",
            geocoder_username="test_user",
            geocoder_password="test_pass",
        )

        # Create mock response
        def mock_get_side_effect(url, params=None, headers=None):
            query_text = params.get("text", "") if params else ""
            response_data = get_mock_response(query_text)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            return mock_response

        # Patch at the module level where httpx is imported
        with patch(
            "goatlib.analysis.geoanalysis.batch_geocoding.httpx.AsyncClient"
        ) as mock_client_class:
            # Create async mock that works with 'async with'
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=mock_get_side_effect)
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            tool = BatchGeocodingTool()
            results = tool.run(params)

        # Verify results structure
        assert len(results) == 1
        result_path, metadata = results[0]

        # Verify metadata
        assert isinstance(metadata, DatasetMetadata)
        assert metadata.source_type == "vector"
        assert metadata.format == "geoparquet"
        assert metadata.geometry_type == "Point"
        assert metadata.crs == "EPSG:4326"

        # Verify output file exists
        assert result_path.exists()

        # Verify output contents
        con = duckdb.connect(":memory:")
        con.execute("INSTALL spatial; LOAD spatial;")

        result = con.execute(f"""
            SELECT id, full_address, geocode_latitude, geocode_longitude,
                   geocode_confidence, geocode_match_type, ST_AsText(geometry) as geom
            FROM read_parquet('{result_path}')
            ORDER BY id
        """).fetchall()

        assert len(result) == 3

        # Check first row (Marienplatz)
        row = result[0]
        assert row[0] == 1  # id
        assert row[1] == "Marienplatz 1, München, Germany"  # full_address
        assert row[2] is not None  # latitude
        assert row[3] is not None  # longitude
        assert row[6] is not None  # geometry

        con.close()

    def test_geocode_structured_mode(self, test_input_path: Path, tmp_path: Path):
        """Test geocoding with structured mode."""
        output_path = tmp_path / "geocoded_structured.parquet"

        params = BatchGeocodingParams(
            input_path=str(test_input_path),
            input_mode=GeocodingInputMode.structured,
            address_field="street",
            locality_source_type=FieldSourceType.field,
            locality_field="city",
            postalcode_field="postal_code",
            country_source_type=FieldSourceType.constant,
            country_constant="Germany",
            output_path=str(output_path),
            geocoder_url="https://mock.geocoder.test",
            geocoder_username="test_user",
            geocoder_password="test_pass",
        )

        def mock_get_side_effect(url, params=None, headers=None):
            query_text = params.get("text", "") if params else ""
            response_data = get_mock_response(query_text)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            return mock_response

        with patch(
            "goatlib.analysis.geoanalysis.batch_geocoding.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=mock_get_side_effect)
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            tool = BatchGeocodingTool()
            results = tool.run(params)

        result_path, metadata = results[0]
        assert result_path.exists()

        # Verify the geocode_input_text is properly constructed
        con = duckdb.connect(":memory:")
        result = con.execute(f"""
            SELECT geocode_input_text
            FROM read_parquet('{result_path}')
            ORDER BY id
        """).fetchall()

        # Check that structured address was built correctly
        assert "Marienplatz 1" in result[0][0]
        assert "München" in result[0][0]
        assert "Germany" in result[0][0]

        con.close()

    def test_geocode_with_locality_constant(
        self, test_input_path: Path, tmp_path: Path
    ):
        """Test geocoding with both locality and country as constants."""
        output_path = tmp_path / "geocoded_constants.parquet"

        params = BatchGeocodingParams(
            input_path=str(test_input_path),
            input_mode=GeocodingInputMode.structured,
            address_field="street",
            locality_source_type=FieldSourceType.constant,
            locality_constant="Munich",
            country_source_type=FieldSourceType.constant,
            country_constant="Germany",
            output_path=str(output_path),
            geocoder_url="https://mock.geocoder.test",
            geocoder_username="test_user",
            geocoder_password="test_pass",
        )

        def mock_get_side_effect(url, params=None, headers=None):
            query_text = params.get("text", "") if params else ""
            response_data = get_mock_response(query_text)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            return mock_response

        with patch(
            "goatlib.analysis.geoanalysis.batch_geocoding.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=mock_get_side_effect)
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            tool = BatchGeocodingTool()
            results = tool.run(params)

        result_path, metadata = results[0]
        assert result_path.exists()

        # Verify all rows have "Munich" in the input text
        con = duckdb.connect(":memory:")
        result = con.execute(f"""
            SELECT geocode_input_text
            FROM read_parquet('{result_path}')
        """).fetchall()

        for row in result:
            assert "Munich" in row[0]
            assert "Germany" in row[0]

        con.close()

    def test_max_features_limit(self, large_input_path: Path, tmp_path: Path):
        """Test that geocoding fails when input exceeds MAX_FEATURES."""
        output_path = tmp_path / "geocoded_big.parquet"

        params = BatchGeocodingParams(
            input_path=str(large_input_path),
            input_mode=GeocodingInputMode.full_address,
            full_address_field="full_address",
            output_path=str(output_path),
            geocoder_url="https://mock.geocoder.test",
            geocoder_username="test_user",
            geocoder_password="test_pass",
        )

        tool = BatchGeocodingTool()

        with pytest.raises(ValueError) as exc_info:
            tool.run(params)

        assert "1001" in str(exc_info.value)
        assert "1000" in str(exc_info.value)

    def test_geocode_handles_no_match(self, tmp_path: Path):
        """Test that geocoding handles addresses with no match."""
        # Create input with an address that won't match
        con = duckdb.connect(":memory:")
        con.execute("""
            CREATE TABLE no_match AS
            SELECT 1 AS id, 'Unknown Address, Nowhere' AS full_address
        """)
        input_path = tmp_path / "no_match.parquet"
        con.execute(f"COPY no_match TO '{input_path}' (FORMAT PARQUET)")
        con.close()

        output_path = tmp_path / "geocoded_no_match.parquet"

        params = BatchGeocodingParams(
            input_path=str(input_path),
            input_mode=GeocodingInputMode.full_address,
            full_address_field="full_address",
            output_path=str(output_path),
            geocoder_url="https://mock.geocoder.test",
            geocoder_username="test_user",
            geocoder_password="test_pass",
        )

        def mock_get_side_effect(url, params=None, headers=None):
            query_text = params.get("text", "") if params else ""
            response_data = get_mock_response(query_text)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            return mock_response

        with patch(
            "goatlib.analysis.geoanalysis.batch_geocoding.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=mock_get_side_effect)
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            tool = BatchGeocodingTool()
            results = tool.run(params)

        result_path, metadata = results[0]

        # Verify output has null geometry for no-match address
        con = duckdb.connect(":memory:")
        con.execute("INSTALL spatial; LOAD spatial;")
        result = con.execute(f"""
            SELECT geocode_latitude, geocode_longitude, geometry
            FROM read_parquet('{result_path}')
        """).fetchone()

        assert result[0] is None  # latitude
        assert result[1] is None  # longitude
        assert result[2] is None  # geometry

        con.close()

    def test_geocode_handles_api_error(self, test_input_path: Path, tmp_path: Path):
        """Test that geocoding handles API errors gracefully."""
        output_path = tmp_path / "geocoded_error.parquet"

        params = BatchGeocodingParams(
            input_path=str(test_input_path),
            input_mode=GeocodingInputMode.full_address,
            full_address_field="full_address",
            output_path=str(output_path),
            geocoder_url="https://mock.geocoder.test",
            geocoder_username="test_user",
            geocoder_password="test_pass",
        )

        # Mock client that returns 500 error
        def mock_error_response(url, params=None, headers=None):
            mock_response = MagicMock()
            mock_response.status_code = 500
            return mock_response

        with patch(
            "goatlib.analysis.geoanalysis.batch_geocoding.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=mock_error_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            tool = BatchGeocodingTool()
            results = tool.run(params)

        result_path, metadata = results[0]

        # Should still produce output, but with null coordinates
        assert result_path.exists()

        con = duckdb.connect(":memory:")
        result = con.execute(f"""
            SELECT COUNT(*) as total,
                   COUNT(geocode_latitude) as with_coords
            FROM read_parquet('{result_path}')
        """).fetchone()

        assert result[0] == 3  # All rows present
        assert result[1] == 0  # No coordinates due to errors

        con.close()

    def test_authorization_header(self, test_input_path: Path, tmp_path: Path):
        """Test that authorization header is correctly generated."""
        tool = BatchGeocodingTool()

        params = BatchGeocodingParams(
            input_path=str(test_input_path),
            input_mode=GeocodingInputMode.full_address,
            full_address_field="full_address",
            output_path=str(tmp_path / "output.parquet"),
            geocoder_url="https://mock.geocoder.test",
            geocoder_username="admin",
            geocoder_password="secret123",
        )

        auth = tool._get_authorization(params)

        # Verify it's a valid Basic auth header
        assert auth.startswith("Basic ")
        decoded = base64.b64decode(auth.replace("Basic ", "")).decode()
        assert decoded == "admin:secret123"


class TestBatchGeocodingParams:
    """Tests for BatchGeocodingParams schema."""

    def test_build_query_text_full_address(self):
        """Test query text building in full_address mode."""
        params = BatchGeocodingParams(
            input_path="/tmp/test.parquet",
            input_mode=GeocodingInputMode.full_address,
            full_address_field="address",
            output_path="/tmp/output.parquet",
            geocoder_url="https://test.geocoder",
            geocoder_username="user",
            geocoder_password="pass",
        )

        row = {"address": "Marienplatz 1, Munich, Germany", "id": 1}
        query = params.build_query_text(row)

        assert query == "Marienplatz 1, Munich, Germany"

    def test_build_query_text_structured(self):
        """Test query text building in structured mode."""
        params = BatchGeocodingParams(
            input_path="/tmp/test.parquet",
            input_mode=GeocodingInputMode.structured,
            address_field="street",
            locality_source_type=FieldSourceType.field,
            locality_field="city",
            postalcode_field="zip",
            country_source_type=FieldSourceType.constant,
            country_constant="Germany",
            output_path="/tmp/output.parquet",
            geocoder_url="https://test.geocoder",
            geocoder_username="user",
            geocoder_password="pass",
        )

        row = {"street": "Marienplatz 1", "city": "Munich", "zip": "80331"}
        query = params.build_query_text(row)

        assert "Marienplatz 1" in query
        assert "Munich" in query
        assert "80331" in query
        assert "Germany" in query

    def test_required_fields(self):
        """Test that required fields are enforced."""
        # geocoder_url, geocoder_username, geocoder_password are required
        with pytest.raises(Exception):
            BatchGeocodingParams(
                input_path="/tmp/test.parquet",
                input_mode=GeocodingInputMode.full_address,
                full_address_field="address",
                output_path="/tmp/output.parquet",
                # Missing geocoder_url, geocoder_username, geocoder_password
            )
