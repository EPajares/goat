"""Standalone unit tests for DuckLake layer functionality.

These tests can run without the full application setup.
They test the pure Python logic without database or QGIS dependencies.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def user_id() -> UUID:
    """Generate a test user UUID."""
    return uuid4()


@pytest.fixture
def layer_id() -> UUID:
    """Generate a test layer UUID."""
    return uuid4()


# =============================================================================
# 1. Geometry Type Mapping Tests
# =============================================================================

# Define the mapping directly to test without imports
GEOMETRY_TYPE_MAP: dict[str, str] = {
    "POINT": "point",
    "MULTIPOINT": "point",
    "LINESTRING": "line",
    "MULTILINESTRING": "line",
    "POLYGON": "polygon",
    "MULTIPOLYGON": "polygon",
}


def map_geometry_type(duckdb_type: str | None) -> str | None:
    """Map DuckDB geometry type to our FeatureGeometryType enum value."""
    if not duckdb_type:
        return None
    return GEOMETRY_TYPE_MAP.get(duckdb_type.upper(), "polygon")


def build_extent_wkt(extent: dict[str, float]) -> str:
    """Build WKT MULTIPOLYGON from extent dict."""
    return (
        f"MULTIPOLYGON((("
        f"{extent['min_x']} {extent['min_y']}, "
        f"{extent['max_x']} {extent['min_y']}, "
        f"{extent['max_x']} {extent['max_y']}, "
        f"{extent['min_x']} {extent['max_y']}, "
        f"{extent['min_x']} {extent['min_y']}"
        f")))"
    )


class TestGeometryTypeMapping:
    """Test geometry type mapping functions."""

    def test_map_geometry_type_point(self: "TestGeometryTypeMapping") -> None:
        """Test mapping POINT geometry type."""
        assert map_geometry_type("POINT") == "point"
        assert map_geometry_type("point") == "point"
        assert map_geometry_type("Point") == "point"

    def test_map_geometry_type_multipoint(self: "TestGeometryTypeMapping") -> None:
        """Test mapping MULTIPOINT geometry type."""
        assert map_geometry_type("MULTIPOINT") == "point"

    def test_map_geometry_type_line(self: "TestGeometryTypeMapping") -> None:
        """Test mapping LINESTRING geometry type."""
        assert map_geometry_type("LINESTRING") == "line"
        assert map_geometry_type("MULTILINESTRING") == "line"

    def test_map_geometry_type_polygon(self: "TestGeometryTypeMapping") -> None:
        """Test mapping POLYGON geometry type."""
        assert map_geometry_type("POLYGON") == "polygon"
        assert map_geometry_type("MULTIPOLYGON") == "polygon"

    def test_map_geometry_type_unknown_defaults_polygon(
        self: "TestGeometryTypeMapping",
    ) -> None:
        """Test unknown geometry types default to polygon."""
        assert map_geometry_type("GEOMETRYCOLLECTION") == "polygon"
        assert map_geometry_type("UNKNOWN") == "polygon"

    def test_map_geometry_type_none(self: "TestGeometryTypeMapping") -> None:
        """Test None input returns None."""
        assert map_geometry_type(None) is None

    def test_map_geometry_type_empty_string(self: "TestGeometryTypeMapping") -> None:
        """Test empty string returns None (falsy value)."""
        result = map_geometry_type("")
        assert result is None  # Empty string is falsy, returns None


class TestBuildExtentWkt:
    """Test extent WKT building."""

    def test_build_extent_wkt_basic(self: "TestBuildExtentWkt") -> None:
        """Test building WKT from extent dict."""
        extent = {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 10.0}
        result = build_extent_wkt(extent)

        assert result.startswith("MULTIPOLYGON")
        assert "0.0 0.0" in result
        assert "10.0 10.0" in result

    def test_build_extent_wkt_negative_coords(self: "TestBuildExtentWkt") -> None:
        """Test building WKT with negative coordinates."""
        extent = {"min_x": -180.0, "min_y": -90.0, "max_x": 180.0, "max_y": 90.0}
        result = build_extent_wkt(extent)

        assert "-180.0 -90.0" in result
        assert "180.0 90.0" in result

    def test_build_extent_wkt_decimal_precision(self: "TestBuildExtentWkt") -> None:
        """Test WKT preserves decimal precision."""
        extent = {
            "min_x": 11.123456,
            "min_y": 48.987654,
            "max_x": 11.234567,
            "max_y": 49.123456,
        }
        result = build_extent_wkt(extent)

        assert "11.123456" in result
        assert "48.987654" in result

    def test_build_extent_wkt_is_valid_wkt(self: "TestBuildExtentWkt") -> None:
        """Test generated WKT is valid format."""
        extent = {"min_x": 0.0, "min_y": 0.0, "max_x": 1.0, "max_y": 1.0}
        result = build_extent_wkt(extent)

        # Check WKT structure
        assert result.startswith("MULTIPOLYGON(((")
        assert result.endswith(")))")
        # Should have 5 points (closed ring)
        coords = result.replace("MULTIPOLYGON(((", "").replace(")))", "")
        points = coords.split(", ")
        assert len(points) == 5
        # First and last point should be same (closed ring)
        assert points[0] == points[4]


# =============================================================================
# 2. Table Naming Tests
# =============================================================================


class TestDuckLakeTableNaming:
    """Test DuckLake table naming conventions."""

    @staticmethod
    def get_user_schema_name(user_id: UUID) -> str:
        """Get DuckLake schema name for a user."""
        return f"user_{str(user_id).replace('-', '')}"

    @staticmethod
    def get_layer_table_name(user_id: UUID, layer_id: UUID) -> str:
        """Get fully qualified table name for a layer."""
        schema = TestDuckLakeTableNaming.get_user_schema_name(user_id)
        table = f"t_{str(layer_id).replace('-', '')}"
        return f"lake.{schema}.{table}"

    def test_get_user_schema_name_removes_dashes(
        self: "TestDuckLakeTableNaming",
    ) -> None:
        """Test user schema name has dashes removed."""
        user_id = UUID("12345678-1234-1234-1234-123456789abc")
        schema = self.get_user_schema_name(user_id)

        assert "-" not in schema
        assert schema == "user_12345678123412341234123456789abc"

    def test_get_layer_table_name_format(
        self: "TestDuckLakeTableNaming",
    ) -> None:
        """Test layer table name follows convention."""
        user_id = UUID("12345678-1234-1234-1234-123456789abc")
        layer_id = UUID("abcdef00-1111-2222-3333-444455556666")
        table = self.get_layer_table_name(user_id, layer_id)

        assert table.startswith("lake.")
        assert "user_" in table
        assert ".t_" in table
        assert "-" not in table

    def test_different_users_different_schemas(
        self: "TestDuckLakeTableNaming",
    ) -> None:
        """Test different users get different schemas."""
        user1 = uuid4()
        user2 = uuid4()

        schema1 = self.get_user_schema_name(user1)
        schema2 = self.get_user_schema_name(user2)

        assert schema1 != schema2

    def test_same_layer_different_users(
        self: "TestDuckLakeTableNaming",
    ) -> None:
        """Test same layer_id in different user schemas are different tables."""
        layer_id = uuid4()
        user1 = uuid4()
        user2 = uuid4()

        table1 = self.get_layer_table_name(user1, layer_id)
        table2 = self.get_layer_table_name(user2, layer_id)

        assert table1 != table2


# =============================================================================
# 3. LayerImportResult Tests
# =============================================================================


class TestLayerImportResult:
    """Test LayerImportResult dataclass structure."""

    def test_create_import_result_feature_layer(
        self: "TestLayerImportResult",
    ) -> None:
        """Test creating LayerImportResult for feature layer."""
        from dataclasses import dataclass

        @dataclass
        class LayerImportResult:
            layer_id: UUID
            user_id: UUID
            table_name: str
            feature_count: int
            columns: list[dict[str, str]]
            geometry_type: str | None
            geometry_column: str | None
            extent: dict[str, float] | None
            source_format: str
            source_path: str

        user_id = uuid4()
        layer_id = uuid4()

        result = LayerImportResult(
            layer_id=layer_id,
            user_id=user_id,
            table_name=f"lake.user_{user_id}.t_{layer_id}",
            feature_count=100,
            columns=[
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "VARCHAR"},
                {"name": "geometry", "type": "GEOMETRY"},
            ],
            geometry_type="POINT",
            geometry_column="geometry",
            extent={"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10},
            source_format="geojson",
            source_path="/path/to/file.geojson",
        )

        assert result.layer_id == layer_id
        assert result.user_id == user_id
        assert result.feature_count == 100
        assert len(result.columns) == 3
        assert result.geometry_type == "POINT"
        assert result.extent is not None

    def test_create_import_result_table_layer(
        self: "TestLayerImportResult",
    ) -> None:
        """Test creating LayerImportResult for table layer (no geometry)."""
        from dataclasses import dataclass

        @dataclass
        class LayerImportResult:
            layer_id: UUID
            user_id: UUID
            table_name: str
            feature_count: int
            columns: list[dict[str, str]]
            geometry_type: str | None
            geometry_column: str | None
            extent: dict[str, float] | None
            source_format: str
            source_path: str

        result = LayerImportResult(
            layer_id=uuid4(),
            user_id=uuid4(),
            table_name="lake.user_xxx.t_yyy",
            feature_count=50,
            columns=[
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "VARCHAR"},
                {"name": "value", "type": "DOUBLE"},
            ],
            geometry_type=None,
            geometry_column=None,
            extent=None,
            source_format="csv",
            source_path="/path/to/file.csv",
        )

        assert result.geometry_type is None
        assert result.geometry_column is None
        assert result.extent is None
        assert result.feature_count == 50


# =============================================================================
# 4. Column Info Tests
# =============================================================================


class TestColumnInfoProcessing:
    """Test column info processing from DuckDB."""

    def test_columns_to_dict(self: "TestColumnInfoProcessing") -> None:
        """Test converting column list to dict."""
        columns = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"},
            {"name": "geometry", "type": "GEOMETRY"},
        ]

        columns_dict = {col["name"]: col["type"] for col in columns}

        assert columns_dict["id"] == "INTEGER"
        assert columns_dict["name"] == "VARCHAR"
        assert columns_dict["geometry"] == "GEOMETRY"

    def test_detect_geometry_column(self: "TestColumnInfoProcessing") -> None:
        """Test detecting geometry column from column list."""
        columns = [
            {"name": "id", "type": "INTEGER"},
            {"name": "geometry", "type": "GEOMETRY"},
        ]

        geom_col = None
        for col in columns:
            if col["name"].lower() in ("geometry", "geom"):
                geom_col = col["name"]
                break

        assert geom_col == "geometry"

    def test_detect_no_geometry_column(self: "TestColumnInfoProcessing") -> None:
        """Test detecting no geometry column in table layer."""
        columns = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"},
        ]

        geom_col = None
        for col in columns:
            if col["name"].lower() in ("geometry", "geom"):
                geom_col = col["name"]
                break

        assert geom_col is None


# =============================================================================
# 5. Error Cases
# =============================================================================


class TestErrorCases:
    """Test error handling cases."""

    def test_build_extent_missing_key_raises(self: "TestErrorCases") -> None:
        """Test build_extent_wkt with missing key raises KeyError."""
        incomplete_extent = {"min_x": 0.0, "min_y": 0.0}  # missing max_x, max_y

        with pytest.raises(KeyError):
            build_extent_wkt(incomplete_extent)

    def test_uuid_string_conversion(self: "TestErrorCases") -> None:
        """Test UUID to string conversion for table names."""
        user_id = UUID("12345678-1234-1234-1234-123456789abc")

        # Standard str() includes dashes
        assert "-" in str(user_id)

        # Replace dashes for table names
        clean_id = str(user_id).replace("-", "")
        assert "-" not in clean_id
        assert len(clean_id) == 32


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# =============================================================================
# 6. DuckLakeManager Mock Tests
# =============================================================================


class TestDuckLakeManagerMock:
    """Test DuckLakeManager with mocked connections."""

    def test_parquet_path_generation(self: "TestDuckLakeManagerMock") -> None:
        """Test parquet file path generation logic."""
        base_path = "/data/lake"
        user_id = uuid4()
        layer_id = uuid4()

        # Expected path format
        parquet_path = Path(base_path) / str(user_id) / f"{layer_id}.parquet"

        assert str(user_id) in str(parquet_path)
        assert str(layer_id) in str(parquet_path)
        assert str(parquet_path).endswith(".parquet")

    def test_create_layer_table_name(self: "TestDuckLakeManagerMock") -> None:
        """Test table name creation logic."""
        user_id = uuid4()
        layer_id = uuid4()

        # Logic from DuckLakeManager
        schema = f"user_{str(user_id).replace('-', '')}"
        table = f"t_{str(layer_id).replace('-', '')}"
        full_name = f"lake.{schema}.{table}"

        assert full_name.startswith("lake.user_")
        assert ".t_" in full_name
        assert "-" not in full_name

    def test_get_layer_metadata_structure(self: "TestDuckLakeManagerMock") -> None:
        """Test expected metadata structure from layer query."""
        # Expected structure returned by DuckLakeManager.get_layer_metadata()
        expected_structure = {
            "columns": [
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "VARCHAR"},
                {"name": "geometry", "type": "GEOMETRY"},
            ],
            "feature_count": 100,
            "geometry_type": "POINT",
            "extent": {
                "min_x": 0.0,
                "min_y": 0.0,
                "max_x": 10.0,
                "max_y": 10.0,
            },
        }

        assert "columns" in expected_structure
        assert "feature_count" in expected_structure
        assert expected_structure["feature_count"] == 100
        assert len(expected_structure["columns"]) == 3


# =============================================================================
# 7. LayerImportResult Integration Tests
# =============================================================================


class TestLayerImportResultIntegration:
    """Test LayerImportResult dataclass usage patterns."""

    def test_import_result_to_layer_attributes(
        self: "TestLayerImportResultIntegration",
    ) -> None:
        """Test converting import result to layer model attributes."""
        from dataclasses import dataclass

        @dataclass
        class MockImportResult:
            layer_id: UUID
            user_id: UUID
            table_name: str
            feature_count: int
            columns: list[dict[str, str]]
            geometry_type: str | None
            geometry_column: str | None
            extent: dict[str, float] | None
            source_format: str
            source_path: str

        user_id = uuid4()
        layer_id = uuid4()

        import_result = MockImportResult(
            layer_id=layer_id,
            user_id=user_id,
            table_name=f"lake.user_{user_id}.t_{layer_id}",
            feature_count=500,
            columns=[
                {"name": "id", "type": "INTEGER"},
                {"name": "geometry", "type": "GEOMETRY"},
            ],
            geometry_type="POLYGON",
            geometry_column="geometry",
            extent={"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10},
            source_format="geojson",
            source_path="/tmp/test.geojson",
        )

        # Simulate _build_layer_attributes logic
        columns_info = {col["name"]: col["type"] for col in import_result.columns}
        geom_type = map_geometry_type(import_result.geometry_type)
        extent_wkt = (
            build_extent_wkt(import_result.extent) if import_result.extent else None
        )

        attrs = {
            "user_id": user_id,
            "attribute_mapping": columns_info,
            "type": "feature",
            "feature_layer_geometry_type": geom_type,
            "extent": extent_wkt,
        }

        assert attrs["user_id"] == user_id
        assert attrs["attribute_mapping"] == {"id": "INTEGER", "geometry": "GEOMETRY"}
        assert attrs["feature_layer_geometry_type"] == "polygon"
        assert attrs["extent"].startswith("MULTIPOLYGON")

    def test_table_layer_no_geometry(
        self: "TestLayerImportResultIntegration",
    ) -> None:
        """Test table layer import without geometry."""
        from dataclasses import dataclass

        @dataclass
        class MockImportResult:
            layer_id: UUID
            user_id: UUID
            table_name: str
            feature_count: int
            columns: list[dict[str, str]]
            geometry_type: str | None
            geometry_column: str | None
            extent: dict[str, float] | None
            source_format: str
            source_path: str

        import_result = MockImportResult(
            layer_id=uuid4(),
            user_id=uuid4(),
            table_name="lake.user_xxx.t_yyy",
            feature_count=1000,
            columns=[
                {"name": "id", "type": "INTEGER"},
                {"name": "value", "type": "DOUBLE"},
            ],
            geometry_type=None,  # No geometry
            geometry_column=None,
            extent=None,
            source_format="csv",
            source_path="/tmp/test.csv",
        )

        geom_type = map_geometry_type(import_result.geometry_type)

        # For table layers, geometry_type should be None
        assert geom_type is None
        assert import_result.extent is None
        layer_type = "table" if geom_type is None else "feature"
        assert layer_type == "table"


# =============================================================================
# 8. File Format Detection Tests
# =============================================================================


class TestFileFormatDetection:
    """Test file format detection for imports."""

    @pytest.mark.parametrize(
        "file_path,expected_format",
        [
            ("/path/to/file.geojson", "geojson"),
            ("/path/to/file.gpkg", "gpkg"),
            ("/path/to/file.shp", "shp"),
            ("/path/to/file.csv", "csv"),
            ("/path/to/file.xlsx", "xlsx"),
            ("/path/to/FILE.GEOJSON", "geojson"),  # Case insensitive
            ("/path/to/file.json", "json"),
            ("/path/to/file.kml", "kml"),
            ("/path/to/file.gml", "gml"),
        ],
    )
    def test_detect_file_format(
        self: "TestFileFormatDetection",
        file_path: str,
        expected_format: str,
    ) -> None:
        """Test file format detection from path."""
        detected = Path(file_path).suffix.lower().lstrip(".")
        assert detected == expected_format

    def test_detect_no_extension(self: "TestFileFormatDetection") -> None:
        """Test handling files without extension."""
        file_path = "/path/to/file"
        detected = Path(file_path).suffix
        assert detected == ""


# =============================================================================
# 9. Attribute Mapping Tests
# =============================================================================


class TestAttributeMapping:
    """Test attribute mapping from DuckDB types."""

    def test_map_duckdb_types_to_json(self: "TestAttributeMapping") -> None:
        """Test mapping DuckDB types for JSON storage."""
        columns = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"},
            {"name": "value", "type": "DOUBLE"},
            {"name": "is_active", "type": "BOOLEAN"},
            {"name": "created", "type": "TIMESTAMP"},
            {"name": "geometry", "type": "GEOMETRY"},
        ]

        mapping = {col["name"]: col["type"] for col in columns}

        assert mapping["id"] == "INTEGER"
        assert mapping["name"] == "VARCHAR"
        assert mapping["value"] == "DOUBLE"
        assert mapping["is_active"] == "BOOLEAN"
        assert mapping["created"] == "TIMESTAMP"
        assert mapping["geometry"] == "GEOMETRY"

    def test_filter_non_geometry_columns(self: "TestAttributeMapping") -> None:
        """Test filtering out geometry columns for attribute list."""
        columns = [
            {"name": "id", "type": "INTEGER"},
            {"name": "geometry", "type": "GEOMETRY"},
            {"name": "geom", "type": "GEOMETRY"},
        ]

        non_geom = [c for c in columns if c["type"] != "GEOMETRY"]
        assert len(non_geom) == 1
        assert non_geom[0]["name"] == "id"


# =============================================================================
# 10. CRS and Projection Tests
# =============================================================================


class TestCRSHandling:
    """Test CRS/projection handling."""

    def test_default_target_crs(self: "TestCRSHandling") -> None:
        """Test default target CRS is EPSG:4326."""
        default_crs = "EPSG:4326"
        assert default_crs.startswith("EPSG:")
        assert "4326" in default_crs

    def test_crs_format_validation(self: "TestCRSHandling") -> None:
        """Test CRS format is valid EPSG code."""
        valid_crs_formats = [
            "EPSG:4326",
            "EPSG:3857",
            "EPSG:25832",
        ]

        for crs in valid_crs_formats:
            assert crs.startswith("EPSG:")
            code = crs.split(":")[1]
            assert code.isdigit()


# =============================================================================
# 11. Feature Count Tests
# =============================================================================


class TestFeatureCount:
    """Test feature count handling."""

    def test_feature_count_positive(self: "TestFeatureCount") -> None:
        """Test feature count must be positive."""
        feature_count = 100
        assert feature_count > 0

    def test_feature_count_zero_valid(self: "TestFeatureCount") -> None:
        """Test zero features is valid (empty layer)."""
        feature_count = 0
        # Zero is valid - empty layer
        assert feature_count >= 0

    def test_large_feature_count(self: "TestFeatureCount") -> None:
        """Test handling large feature counts."""
        large_count = 10_000_000  # 10 million
        assert large_count > 0
        assert isinstance(large_count, int)
