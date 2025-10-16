from pathlib import Path

import pytest
from goatlib.io.ingest import convert_any
from goatlib.models.io import DatasetMetadata

# =====================================================================
#  VALID  CONVERSION  TESTS
# =====================================================================

# ----------------------------- Tabular ------------------------------


@pytest.mark.parametrize(
    "fixture_name",
    ["tabular_valid_csv", "tabular_valid_xlsx"],
)
def test_tabular_to_parquet(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    fixture_name: str,
) -> None:
    """Convert tabular formats → Parquet."""
    src: Path = request.getfixturevalue(fixture_name)
    out, meta = convert_any(str(src), tmp_path)
    assert out.exists() and out.suffix == ".parquet"
    assert isinstance(meta, DatasetMetadata)
    assert meta.source_type in ("tabular", "vector")


# ----------------------------- Vector -------------------------------


def _check_vector(tmp_path: Path, path: Path) -> None:
    """Helper used by all vector tests."""
    out, meta = convert_any(str(path), tmp_path)
    assert out.exists() and out.suffix == ".parquet"
    assert isinstance(meta, DatasetMetadata)
    assert meta.source_type == "vector"


def test_geojson_conversion(tmp_path: Path, geojson_path: Path) -> None:
    """Each GeoJSON sample → Parquet."""
    _check_vector(tmp_path, geojson_path)


def test_gpkg_conversion(tmp_path: Path, gpkg_path: Path) -> None:
    """Each GeoPackage sample → Parquet."""
    _check_vector(tmp_path, gpkg_path)


def test_kml_conversion(tmp_path: Path, kml_path: Path) -> None:
    """Each KML sample → Parquet."""
    _check_vector(tmp_path, kml_path)


def test_shapefile_conversion(tmp_path: Path, shapefile_path: Path) -> None:
    """Each Shapefile (ZIP) sample → Parquet."""
    _check_vector(tmp_path, shapefile_path)


def test_crs_autodetect_and_transform(tmp_path: Path, geojson_path: Path) -> None:
    """
    Ensure convert_any handles CRS autodetection & transformation.
    """
    src = geojson_path  # same thing the old fixture gave you
    out_auto, meta_auto = convert_any(str(src), tmp_path)
    assert meta_auto is not None
    assert hasattr(meta_auto, "crs")

    out_tx, meta_tx = convert_any(str(src), tmp_path, target_crs="EPSG:3857")
    assert meta_tx.crs == "EPSG:3857"
    assert out_tx.exists()


# ----------------------------- Raster -------------------------------


def test_raster_to_cog(tmp_path: Path, raster_valid: Path) -> None:
    """GeoTIFF → COG TIFF conversion."""
    out, meta = convert_any(str(raster_valid), tmp_path)
    assert out.exists() and out.suffix == ".tif"
    assert meta.source_type == "raster"


def test_raster_reproject_via_convert_any(tmp_path: Path, raster_valid: Path) -> None:
    """Ensure convert_any reprojects rasters when target_crs is passed."""
    out, meta = convert_any(str(raster_valid), tmp_path, target_crs="EPSG:3857")
    assert out.exists()
    assert meta.crs and "3857" in meta.crs


# =====================================================================
#  INVALID  INPUT  TESTS
# =====================================================================


def test_invalid_vector_zip_fails(tmp_path: Path, vector_invalid_zip: Path) -> None:
    """Corrupted shapefile ZIP should raise an exception."""
    with pytest.raises(Exception):
        convert_any(str(vector_invalid_zip), tmp_path)


def test_missing_path_fails(tmp_path: Path) -> None:
    """Non‑existent file should raise cleanly."""
    fake = tmp_path / "does_not_exist.geojson"
    with pytest.raises(Exception):
        convert_any(str(fake), tmp_path)
