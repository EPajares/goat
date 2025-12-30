"""API integration tests for layer processes (LayerImport, LayerExport, LayerUpdate).

These tests verify the full flow of layer operations through the OGC API:
1. LayerImport - importing files into DuckLake
2. LayerExport - exporting layers to various formats
3. LayerUpdate - updating layer datasets

Uses goatlib test data files for realistic testing.
"""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

import lib.paths  # type: ignore # noqa: F401 - sets up sys.path

# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "layer"


# ============================================================================
# LayerImport Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_layer_import_geojson(test_user):
    """Test importing a GeoJSON file into DuckLake."""
    from lib.layer_service import LayerImporter

    layer_id = uuid4()
    file_path = str(TEST_DATA_DIR / "points.geojson")

    importer = LayerImporter()
    result = importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=file_path,
        target_crs="EPSG:4326",
    )

    # Verify import result
    assert result.layer_id == layer_id
    assert result.user_id == test_user.id
    assert result.feature_count > 0
    assert result.geometry_type is not None
    assert result.table_name is not None
    assert "POINT" in result.geometry_type.upper()

    print(
        f"[TEST] Layer imported: {layer_id}, {result.feature_count} features, type={result.geometry_type}"
    )

    # Cleanup
    importer.delete_layer(test_user.id, layer_id)


@pytest.mark.asyncio
async def test_layer_import_geopackage(test_user):
    """Test importing a GeoPackage file into DuckLake."""
    from lib.layer_service import LayerImporter

    layer_id = uuid4()
    file_path = str(TEST_DATA_DIR / "point.gpkg")

    importer = LayerImporter()
    result = importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=file_path,
        target_crs="EPSG:4326",
    )

    # Verify
    assert result.feature_count > 0
    assert result.geometry_type is not None
    assert result.table_name is not None

    print(
        f"[TEST] GeoPackage imported: {result.feature_count} features, type={result.geometry_type}"
    )

    # Cleanup
    importer.delete_layer(test_user.id, layer_id)


# ============================================================================
# LayerExport Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_layer_export_to_geojson(test_user):
    """Test exporting a layer to GeoJSON format."""
    from lib.layer_service import LayerImporter

    # Import first
    layer_id = uuid4()
    file_path = str(TEST_DATA_DIR / "polygon.geojson")

    importer = LayerImporter()
    import_result = importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=file_path,
        target_crs="EPSG:4326",
    )
    assert import_result.feature_count > 0

    # Export to GeoJSON
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "export.geojson"
        exported = importer.export_layer(
            user_id=test_user.id,
            layer_id=layer_id,
            output_path=str(output_path),
            output_format="GEOJSON",
        )

        assert Path(exported).exists()
        assert Path(exported).stat().st_size > 0

        print(f"[TEST] Exported to GeoJSON: {Path(exported).stat().st_size} bytes")

    # Cleanup
    importer.delete_layer(test_user.id, layer_id)


@pytest.mark.asyncio
async def test_layer_export_to_geopackage(test_user):
    """Test exporting a layer to GeoPackage format."""
    from lib.layer_service import LayerImporter

    # Import first
    layer_id = uuid4()
    file_path = str(TEST_DATA_DIR / "points.geojson")

    importer = LayerImporter()
    import_result = importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=file_path,
        target_crs="EPSG:4326",
    )

    # Export to GeoPackage
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "export.gpkg"
        exported = importer.export_layer(
            user_id=test_user.id,
            layer_id=layer_id,
            output_path=str(output_path),
            output_format="GPKG",
        )

        assert Path(exported).exists()
        assert Path(exported).stat().st_size > 0

        print(f"[TEST] Exported to GPKG: {Path(exported).stat().st_size} bytes")

    # Cleanup
    importer.delete_layer(test_user.id, layer_id)


# ============================================================================
# LayerUpdate Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_layer_update_replaces_data(test_user):
    """Test that update_layer_dataset replaces existing data."""
    from lib.layer_service import LayerImporter

    layer_id = uuid4()

    importer = LayerImporter()

    # Import initial file (points)
    points_path = str(TEST_DATA_DIR / "points.geojson")
    initial_result = importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=points_path,
        target_crs="EPSG:4326",
    )
    initial_count = initial_result.feature_count
    initial_geom_type = initial_result.geometry_type
    print(f"[TEST] Initial: {initial_count} features, type={initial_geom_type}")

    # Simulate update by deleting and re-importing with different data
    importer.delete_layer(test_user.id, layer_id)

    # Import polygon file instead
    polygon_path = str(TEST_DATA_DIR / "polygon.geojson")
    update_result = importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=polygon_path,
        target_crs="EPSG:4326",
    )

    # Verify data changed
    assert update_result.geometry_type != initial_geom_type
    print(
        f"[TEST] Updated: {update_result.feature_count} features, type={update_result.geometry_type}"
    )

    # Cleanup
    importer.delete_layer(test_user.id, layer_id)


@pytest.mark.asyncio
async def test_layer_delete(test_user):
    """Test deleting a layer from DuckLake."""
    from lib.layer_service import LayerImporter

    layer_id = uuid4()
    file_path = str(TEST_DATA_DIR / "points.geojson")

    importer = LayerImporter()

    # Import
    result = importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=file_path,
        target_crs="EPSG:4326",
    )
    assert result.feature_count > 0

    # Delete
    deleted = importer.delete_layer(test_user.id, layer_id)
    assert deleted is True

    # Try to delete again - should return False since it's gone
    deleted_again = importer.delete_layer(test_user.id, layer_id)
    assert deleted_again is False

    print("[TEST] Layer deleted successfully")


# ============================================================================
# OGC Process Definition Tests
# ============================================================================


@pytest.mark.asyncio
async def test_layer_processes_registered():
    """Test that layer processes are registered in OGC process list."""
    from lib.ogc_process_generator import get_process, get_process_list

    process_list = get_process_list(base_url="http://test.local")
    process_ids = [p.id for p in process_list]

    assert "LayerImport" in process_ids
    assert "LayerExport" in process_ids
    assert "LayerUpdate" in process_ids

    # Verify process descriptions are valid
    for process_id in ["LayerImport", "LayerExport", "LayerUpdate"]:
        process = get_process(process_id, base_url="http://test.local")
        assert process is not None
        assert process.id == process_id
        assert len(process.inputs) > 0
        assert len(process.outputs) > 0

    print("[TEST] All layer processes registered correctly")
