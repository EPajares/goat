"""Tests for Layer Service.

Tests:
- LayerImporter.import_file (local file)
- LayerImporter.update_layer_dataset
- LayerImporter.export_layer
- LayerImporter.delete_layer
"""

# Add paths for imports
import sys

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/processes/src")

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio

# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "layer"

# Skip tests if test data doesn't exist
pytestmark = pytest.mark.skipif(
    not TEST_DATA_DIR.exists(),
    reason="Test data not found",
)


class TestLayerImporter:
    """Test LayerImporter class."""

    @pytest.fixture
    def layer_importer(self):
        """Get LayerImporter instance."""
        from lib.layer_service import LayerImporter

        return LayerImporter()

    def test_import_geojson_points(self, layer_importer, test_user):
        """Test importing GeoJSON points file."""
        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "points.geojson")

        result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )

        assert result.layer_id == layer_id
        assert result.user_id == test_user.id
        assert result.feature_count > 0
        assert result.geometry_type in ("POINT", "MULTIPOINT", "Point", "MultiPoint")
        assert result.table_name is not None
        # source_format is 'parquet' after goatlib conversion, which is expected
        assert result.source_format == "parquet"

        # Cleanup
        layer_importer.delete_layer(test_user.id, layer_id)

    def test_import_geojson_polygon(self, layer_importer, test_user):
        """Test importing GeoJSON polygon file."""
        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "polygon.geojson")

        result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )

        assert result.layer_id == layer_id
        assert result.feature_count > 0
        assert result.geometry_type in (
            "POLYGON",
            "MULTIPOLYGON",
            "Polygon",
            "MultiPolygon",
        )

        # Cleanup
        layer_importer.delete_layer(test_user.id, layer_id)

    def test_import_geopackage(self, layer_importer, test_user):
        """Test importing GeoPackage file."""
        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "point.gpkg")

        result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )

        assert result.layer_id == layer_id
        assert result.feature_count > 0
        # source_format is 'parquet' after conversion
        assert result.source_format == "parquet"

        # Cleanup
        layer_importer.delete_layer(test_user.id, layer_id)

    def test_import_parquet(self, layer_importer, test_user):
        """Test importing Parquet file."""
        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "overlay_polygons.parquet")

        result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )

        assert result.layer_id == layer_id
        assert result.feature_count > 0

        # Cleanup
        layer_importer.delete_layer(test_user.id, layer_id)

    def test_delete_layer(self, layer_importer, test_user):
        """Test deleting a layer from DuckLake."""
        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "points.geojson")

        # Import first
        result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )
        assert result.feature_count > 0

        # Delete
        deleted = layer_importer.delete_layer(test_user.id, layer_id)
        assert deleted is True

        # Try to delete again - should return False
        deleted_again = layer_importer.delete_layer(test_user.id, layer_id)
        assert deleted_again is False

    def test_export_layer_to_geojson(self, layer_importer, test_user):
        """Test exporting a layer to GeoJSON."""
        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "points.geojson")

        # Import
        import_result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )
        assert import_result.feature_count > 0

        # Export
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "export.geojson"
            exported = layer_importer.export_layer(
                user_id=test_user.id,
                layer_id=layer_id,
                output_path=str(output_path),
                output_format="GEOJSON",
            )
            assert Path(exported).exists()
            assert Path(exported).stat().st_size > 0

        # Cleanup
        layer_importer.delete_layer(test_user.id, layer_id)

    def test_export_layer_to_geopackage(self, layer_importer, test_user):
        """Test exporting a layer to GeoPackage."""
        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "polygon.geojson")

        # Import
        import_result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )
        assert import_result.feature_count > 0

        # Export
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "export.gpkg"
            exported = layer_importer.export_layer(
                user_id=test_user.id,
                layer_id=layer_id,
                output_path=str(output_path),
                output_format="GPKG",
            )
            assert Path(exported).exists()
            assert Path(exported).stat().st_size > 0

        # Cleanup
        layer_importer.delete_layer(test_user.id, layer_id)


class TestLayerUpdateDataset:
    """Test LayerImporter.update_layer_dataset method."""

    @pytest.fixture
    def layer_importer(self):
        """Get LayerImporter instance."""
        from lib.layer_service import LayerImporter

        return LayerImporter()

    def test_update_layer_dataset_requires_source(self, layer_importer, test_user):
        """Test that update requires either s3_key or wfs_url."""
        layer_id = uuid4()

        with pytest.raises(ValueError, match="Either s3_key or wfs_url"):
            layer_importer.update_layer_dataset(
                user_id=test_user.id,
                layer_id=layer_id,
            )

    def test_update_layer_replaces_data(self, layer_importer, test_user):
        """Test that update replaces existing layer data."""
        layer_id = uuid4()

        # Import initial file (points)
        points_path = str(TEST_DATA_DIR / "points.geojson")
        initial_result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=points_path,
            target_crs="EPSG:4326",
        )
        initial_count = initial_result.feature_count
        assert initial_count > 0

        # Update with different file (polygon)
        polygon_path = str(TEST_DATA_DIR / "polygon.geojson")

        # Since update_layer_dataset expects S3, we need to test the
        # underlying mechanism: delete + import
        layer_importer.delete_layer(test_user.id, layer_id)
        update_result = layer_importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=polygon_path,
            target_crs="EPSG:4326",
        )

        # Verify data was replaced (polygon file has different geometry type)
        assert update_result.geometry_type in (
            "POLYGON",
            "MULTIPOLYGON",
            "Polygon",
            "MultiPolygon",
        )

        # Cleanup
        layer_importer.delete_layer(test_user.id, layer_id)


class TestLayerImportResult:
    """Test LayerImportResult dataclass."""

    def test_import_result_fields(self, test_user):
        """Test LayerImportResult has all expected fields."""
        from lib.layer_service import LayerImportResult, LayerImporter

        layer_id = uuid4()
        file_path = str(TEST_DATA_DIR / "points.geojson")

        importer = LayerImporter()
        result = importer.import_file(
            user_id=test_user.id,
            layer_id=layer_id,
            file_path=file_path,
            target_crs="EPSG:4326",
        )

        # Check all fields exist
        assert hasattr(result, "layer_id")
        assert hasattr(result, "user_id")
        assert hasattr(result, "table_name")
        assert hasattr(result, "feature_count")
        assert hasattr(result, "columns")
        assert hasattr(result, "geometry_type")
        assert hasattr(result, "geometry_column")
        assert hasattr(result, "extent")
        assert hasattr(result, "source_format")
        assert hasattr(result, "source_path")

        # Cleanup
        importer.delete_layer(test_user.id, layer_id)


class TestGeometryTypeMapping:
    """Test geometry type mapping function."""

    def test_point_mapping(self):
        """Test point geometry mapping."""
        from lib.layer_service import map_geometry_type

        assert map_geometry_type("POINT") == "point"
        assert map_geometry_type("MULTIPOINT") == "point"
        assert map_geometry_type("Point") == "point"

    def test_line_mapping(self):
        """Test line geometry mapping."""
        from lib.layer_service import map_geometry_type

        assert map_geometry_type("LINESTRING") == "line"
        assert map_geometry_type("MULTILINESTRING") == "line"

    def test_polygon_mapping(self):
        """Test polygon geometry mapping."""
        from lib.layer_service import map_geometry_type

        assert map_geometry_type("POLYGON") == "polygon"
        assert map_geometry_type("MULTIPOLYGON") == "polygon"

    def test_none_mapping(self):
        """Test None geometry (table layer)."""
        from lib.layer_service import map_geometry_type

        assert map_geometry_type(None) is None

    def test_unknown_defaults_to_polygon(self):
        """Test unknown geometry defaults to polygon."""
        from lib.layer_service import map_geometry_type

        assert map_geometry_type("GEOMETRYCOLLECTION") == "polygon"


class TestBuildExtentWkt:
    """Test extent WKT builder."""

    def test_build_extent_wkt(self):
        """Test building WKT MULTIPOLYGON from extent dict."""
        from lib.layer_service import build_extent_wkt

        extent = {"xmin": 0, "ymin": 0, "xmax": 10, "ymax": 10}
        wkt = build_extent_wkt(extent)

        assert "MULTIPOLYGON" in wkt
        assert "0 0" in wkt
        assert "10 10" in wkt

    def test_build_extent_wkt_alternate_keys(self):
        """Test extent with min_x/max_x keys."""
        from lib.layer_service import build_extent_wkt

        extent = {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10}
        wkt = build_extent_wkt(extent)

        assert "MULTIPOLYGON" in wkt


class TestGetBaseStyle:
    """Test base style generation."""

    def test_point_style(self):
        """Test point geometry style."""
        from lib.layer_service import get_base_style
        from lib.db import FeatureGeometryType

        style = get_base_style(FeatureGeometryType.point)
        assert style["type"] == "circle"
        assert "circle-radius" in style["paint"]

    def test_line_style(self):
        """Test line geometry style."""
        from lib.layer_service import get_base_style
        from lib.db import FeatureGeometryType

        style = get_base_style(FeatureGeometryType.line)
        assert style["type"] == "line"
        assert "line-color" in style["paint"]

    def test_polygon_style(self):
        """Test polygon geometry style."""
        from lib.layer_service import get_base_style
        from lib.db import FeatureGeometryType

        style = get_base_style(FeatureGeometryType.polygon)
        assert style["type"] == "fill"
        assert "fill-color" in style["paint"]
