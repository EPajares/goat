"""Integration tests for LayerExport tool.

Tests actual export functionality with DuckLake data:
- Export to various file formats (GPKG, GeoJSON, CSV, Parquet, SHP, KML, XLSX)
- CRS transformation validation (EPSG:4326 -> EPSG:3857, etc.)
- Filter/query support
- Column filtering (exclude unsupported types)

Note: These tests require running Docker containers (PostgreSQL, MinIO).

Test data:
- Uses german_cities.parquet with real WGS84 coordinates for CRS validation
- Uses overlay_polygons.parquet for polygon tests
"""

import json
import math
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.layer_export import LayerExportRunner

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# CRS Transformation Helper Functions
# ============================================================================

def wgs84_to_web_mercator(lon: float, lat: float) -> tuple[float, float]:
    """Convert WGS84 (EPSG:4326) coordinates to Web Mercator (EPSG:3857).

    This is the standard transformation formula used by mapping libraries.
    Coordinates in Web Mercator are in meters.

    Args:
        lon: Longitude in degrees (-180 to 180)
        lat: Latitude in degrees (-90 to 90, but typically -85 to 85 for Web Mercator)

    Returns:
        Tuple of (x, y) in Web Mercator meters
    """
    # Earth radius in meters
    R = 6378137.0

    # Convert longitude to x
    x = R * math.radians(lon)

    # Convert latitude to y using the Mercator projection formula
    # y = R * ln(tan(π/4 + φ/2))
    lat_rad = math.radians(lat)
    y = R * math.log(math.tan(math.pi / 4 + lat_rad / 2))

    return (x, y)


def wgs84_to_utm32n(lon: float, lat: float) -> tuple[float, float]:
    """Approximate conversion from WGS84 to UTM Zone 32N (EPSG:32632).

    This is a simplified approximation for testing purposes.
    UTM coordinates are in meters.

    Note: For precise conversion, use a proper geodetic library like pyproj.
    This approximation is sufficient to verify the order of magnitude.

    Args:
        lon: Longitude in degrees (should be around 6-12 for UTM 32N)
        lat: Latitude in degrees

    Returns:
        Tuple of (easting, northing) in UTM meters
    """
    # UTM Zone 32N central meridian is 9°E
    # This is a very rough approximation
    lon0 = 9.0  # Central meridian
    k0 = 0.9996  # Scale factor
    a = 6378137.0  # WGS84 semi-major axis

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    # Simplified UTM calculation (not accurate for testing exact values)
    # Just for order of magnitude validation
    x = 500000 + (lon - lon0) * 111320 * math.cos(lat_rad) * k0
    y = lat * 111320 * k0

    return (x, y)


def parse_wkt_point(wkt: str) -> tuple[float, float]:
    """Parse WKT POINT string to extract coordinates.

    Args:
        wkt: WKT string like "POINT (x y)" or "POINT(x y)"

    Returns:
        Tuple of (x, y)
    """
    # Remove "POINT" prefix and parentheses
    coords_str = wkt.replace("POINT", "").strip().strip("()")
    x, y = coords_str.split()
    return (float(x), float(y))


def parse_wkt_polygon_centroid(wkt: str) -> tuple[float, float]:
    """Estimate centroid of a WKT POLYGON.

    Args:
        wkt: WKT string like "POLYGON ((x1 y1, x2 y2, ...))"

    Returns:
        Tuple of approximate (x, y) centroid
    """
    # Simple average of coordinates
    coords_str = wkt.replace("POLYGON", "").strip().strip("()")
    coords_str = coords_str.strip("()")  # Remove outer ring parens
    
    coords = []
    for pair in coords_str.split(","):
        x, y = pair.strip().split()
        coords.append((float(x), float(y)))
    
    # Average (excluding last point which closes the polygon)
    if len(coords) > 1:
        coords = coords[:-1]
    
    avg_x = sum(c[0] for c in coords) / len(coords)
    avg_y = sum(c[1] for c in coords) / len(coords)
    
    return (avg_x, avg_y)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def export_test_points(
    create_layer_from_parquet,
    vector_data_dir: Path,
) -> tuple[str, int]:
    """Create test point layer for export tests using german_cities.parquet.

    Uses real WGS84 coordinates for CRS validation:
    - Munich (11.576124, 48.137154)
    - Berlin (13.404954, 52.520008)
    - Hamburg (9.993682, 53.551086)
    - Frankfurt (8.682127, 50.110922)
    - Cologne (6.953101, 50.935173)

    Returns:
        Tuple of (layer_id, feature_count)
    """
    layer_id = create_layer_from_parquet(
        parquet_path=vector_data_dir / "german_cities.parquet",
    )
    return (layer_id, 5)


@pytest.fixture
def export_test_polygons(
    create_layer_from_parquet,
    vector_data_dir: Path,
) -> tuple[str, int]:
    """Create test polygon layer for export tests using overlay_polygons.parquet.

    Returns:
        Tuple of (layer_id, feature_count)
    """
    layer_id = create_layer_from_parquet(
        parquet_path=vector_data_dir / "overlay_polygons.parquet",
    )
    # Count features in the file
    con = duckdb.connect()
    count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{vector_data_dir / 'overlay_polygons.parquet'}')"
    ).fetchone()[0]
    con.close()
    return (layer_id, count)


@pytest.fixture
def export_runner(tool_settings: ToolSettings) -> LayerExportRunner:
    """Create LayerExportRunner instance."""
    runner = LayerExportRunner()
    runner.settings = tool_settings
    return runner


# ============================================================================
# Export Format Tests
# ============================================================================

class TestLayerExportFormats:
    """Test export to various file formats."""

    def test_export_to_gpkg(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test export to GeoPackage format."""
        layer_id, feature_count = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.gpkg"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GPKG",
            )
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            # Verify content by reading with DuckDB
            con = duckdb.connect()
            con.execute("INSTALL spatial; LOAD spatial;")
            
            # GPKG layer name is typically the file stem
            result = con.execute(f"""
                SELECT * FROM ST_Read('{output_path}')
            """).fetchall()
            
            assert len(result) == feature_count
            con.close()

    def test_export_to_geojson(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test export to GeoJSON format."""
        layer_id, feature_count = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
            )
            
            assert output_path.exists()
            
            # Verify GeoJSON structure
            with open(output_path) as f:
                geojson = json.load(f)
            
            assert geojson["type"] == "FeatureCollection"
            assert len(geojson["features"]) == feature_count
            
            # Check feature properties (Munich from german_cities.parquet)
            munich = next(f for f in geojson["features"] if f["properties"]["name"] == "Munich")
            assert munich["properties"]["population"] == 1500000

    def test_export_to_csv(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test export to CSV format (geometry as WKT)."""
        layer_id, feature_count = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="CSV",
            )
            
            assert output_path.exists()
            
            # Read and verify CSV content
            con = duckdb.connect()
            result = con.execute(f"SELECT * FROM read_csv('{output_path}')").fetchdf()
            
            assert len(result) == feature_count
            assert "geometry" in result.columns
            
            # Geometry should be WKT
            munich_row = result[result["name"] == "Munich"].iloc[0]
            assert "POINT" in str(munich_row["geometry"])
            
            con.close()

    def test_export_to_parquet(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test export to Parquet format (native DuckDB)."""
        layer_id, feature_count = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="Parquet",
            )
            
            assert output_path.exists()
            
            # Read and verify Parquet content
            con = duckdb.connect()
            result = con.execute(f"SELECT * FROM read_parquet('{output_path}')").fetchall()
            
            assert len(result) == feature_count
            con.close()


# ============================================================================
# CRS Transformation Tests
# ============================================================================

class TestLayerExportCRS:
    """Test CRS transformation during export."""

    def test_export_to_web_mercator_epsg3857_coordinates_correct(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test CRS transformation from EPSG:4326 to EPSG:3857.

        Verifies that coordinate values after transformation are mathematically correct.
        """
        layer_id, _ = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
                crs="EPSG:3857",
            )
            
            assert output_path.exists()
            
            with open(output_path) as f:
                geojson = json.load(f)
            
            # Find Munich point
            munich_feature = next(
                f for f in geojson["features"]
                if f["properties"]["name"] == "Munich"
            )
            
            # Get exported coordinates (should be in EPSG:3857 / meters)
            exported_x, exported_y = munich_feature["geometry"]["coordinates"]
            
            # Calculate expected coordinates using formula
            # Munich: 11.576124°E, 48.137154°N
            expected_x, expected_y = wgs84_to_web_mercator(11.576124, 48.137154)
            
            # Allow small tolerance for floating point
            tolerance = 1.0  # 1 meter tolerance
            
            assert abs(exported_x - expected_x) < tolerance, (
                f"X coordinate mismatch: exported={exported_x}, expected={expected_x}"
            )
            assert abs(exported_y - expected_y) < tolerance, (
                f"Y coordinate mismatch: exported={exported_y}, expected={expected_y}"
            )
            
            # Verify all points are in reasonable Web Mercator range
            for feature in geojson["features"]:
                x, y = feature["geometry"]["coordinates"]
                # Web Mercator x should be roughly between -20M and 20M
                assert -20_000_000 < x < 20_000_000, f"X coordinate out of range: {x}"
                # Web Mercator y should be roughly between -20M and 20M
                assert -20_000_000 < y < 20_000_000, f"Y coordinate out of range: {y}"

    def test_export_to_utm32n_epsg32632_coordinates_reasonable(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test CRS transformation from EPSG:4326 to UTM Zone 32N (EPSG:32632).

        Verifies coordinate values are in reasonable UTM range.
        """
        layer_id, _ = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
                crs="EPSG:32632",
            )
            
            assert output_path.exists()
            
            with open(output_path) as f:
                geojson = json.load(f)
            
            # Munich point in UTM 32N
            munich_feature = next(
                f for f in geojson["features"]
                if f["properties"]["name"] == "Munich"
            )
            
            utm_x, utm_y = munich_feature["geometry"]["coordinates"]
            
            # UTM Zone 32N easting should be around 500,000 (false easting)
            # Munich is near 11.5°E, so easting ~691,000
            assert 400_000 < utm_x < 800_000, f"UTM easting out of range: {utm_x}"
            
            # UTM northing for Munich (48.1°N) should be around 5,333,000
            assert 5_000_000 < utm_y < 6_000_000, f"UTM northing out of range: {utm_y}"

    def test_export_csv_with_crs_wkt_correct(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test CSV export with CRS transformation (WKT geometry)."""
        layer_id, _ = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="CSV",
                crs="EPSG:3857",
            )
            
            assert output_path.exists()
            
            # Read CSV
            con = duckdb.connect()
            result = con.execute(f"SELECT * FROM read_csv('{output_path}')").fetchdf()
            
            # Find Munich row
            munich_row = result[result["name"] == "Munich"].iloc[0]
            wkt = munich_row["geometry"]
            
            # Parse WKT and verify coordinates
            exported_x, exported_y = parse_wkt_point(wkt)
            expected_x, expected_y = wgs84_to_web_mercator(11.576124, 48.137154)
            
            tolerance = 1.0
            assert abs(exported_x - expected_x) < tolerance
            assert abs(exported_y - expected_y) < tolerance
            
            con.close()

    def test_export_gpkg_with_crs_preserves_transformation(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test GeoPackage export with CRS transformation."""
        layer_id, _ = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.gpkg"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GPKG",
                crs="EPSG:3857",
            )
            
            assert output_path.exists()
            
            # Read GPKG and extract coordinates
            con = duckdb.connect()
            con.execute("INSTALL spatial; LOAD spatial;")
            
            result = con.execute(f"""
                SELECT name, ST_X(geom) as x, ST_Y(geom) as y
                FROM ST_Read('{output_path}')
                WHERE name = 'Munich'
            """).fetchone()
            
            assert result is not None
            name, exported_x, exported_y = result
            
            expected_x, expected_y = wgs84_to_web_mercator(11.576124, 48.137154)
            
            tolerance = 1.0
            assert abs(exported_x - expected_x) < tolerance, (
                f"GPKG X coordinate mismatch: {exported_x} vs {expected_x}"
            )
            assert abs(exported_y - expected_y) < tolerance, (
                f"GPKG Y coordinate mismatch: {exported_y} vs {expected_y}"
            )
            
            con.close()

    def test_export_without_crs_preserves_original(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test export without CRS transformation preserves EPSG:4326."""
        layer_id, _ = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
                crs=None,  # No CRS transformation
            )
            
            assert output_path.exists()
            
            with open(output_path) as f:
                geojson = json.load(f)
            
            # Find Munich point
            munich_feature = next(
                f for f in geojson["features"]
                if f["properties"]["name"] == "Munich"
            )
            
            # Should be original WGS84 coordinates
            x, y = munich_feature["geometry"]["coordinates"]
            
            # Original: 11.576124, 48.137154
            assert abs(x - 11.576124) < 0.0001
            assert abs(y - 48.137154) < 0.0001


# ============================================================================
# Filter/Query Tests
# ============================================================================

class TestLayerExportFilters:
    """Test export with filtering."""

    def test_export_with_sql_filter(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test export with SQL WHERE clause filter."""
        layer_id, _ = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
                query="population > 2000000",
            )
            
            assert output_path.exists()
            
            with open(output_path) as f:
                geojson = json.load(f)
            
            # Only Berlin (3.6M) should be included
            assert len(geojson["features"]) == 1
            assert geojson["features"][0]["properties"]["name"] == "Berlin"

    def test_export_with_name_filter(
        self,
        export_runner: LayerExportRunner,
        export_test_points: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test export with name filter."""
        layer_id, _ = export_test_points
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
                query="name = 'Munich'",
            )
            
            assert output_path.exists()
            
            with open(output_path) as f:
                geojson = json.load(f)
            
            assert len(geojson["features"]) == 1
            assert geojson["features"][0]["properties"]["name"] == "Munich"


# ============================================================================
# Polygon Export Tests
# ============================================================================

class TestLayerExportPolygons:
    """Test polygon layer export."""

    def test_export_polygons_to_geojson(
        self,
        export_runner: LayerExportRunner,
        export_test_polygons: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test polygon export to GeoJSON."""
        layer_id, feature_count = export_test_polygons
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
            )
            
            assert output_path.exists()
            
            with open(output_path) as f:
                geojson = json.load(f)
            
            assert len(geojson["features"]) == feature_count
            
            # Check geometry types
            for feature in geojson["features"]:
                assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon")

    def test_export_polygons_with_crs_transformation(
        self,
        export_runner: LayerExportRunner,
        export_test_polygons: tuple[str, int],
        test_user: dict[str, Any],
    ):
        """Test polygon export with CRS transformation."""
        layer_id, _ = export_test_polygons
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.geojson"
            
            export_runner._export_to_file(
                layer_id=layer_id,
                user_id=test_user["id"],
                output_path=str(output_path),
                output_format="GeoJSON",
                crs="EPSG:3857",
            )
            
            assert output_path.exists()
            
            with open(output_path) as f:
                geojson = json.load(f)
            
            # Verify coordinates are in Web Mercator range
            for feature in geojson["features"]:
                coords = feature["geometry"]["coordinates"][0]  # Outer ring
                for x, y in coords:
                    assert -20_000_000 < x < 20_000_000
                    assert -20_000_000 < y < 20_000_000
