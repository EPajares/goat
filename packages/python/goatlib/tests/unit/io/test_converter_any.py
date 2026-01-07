import logging
from pathlib import Path

import duckdb
import pytest
from goatlib.io.ingest import convert_any
from goatlib.models.io import DatasetMetadata

# =====================================================================
#  VALID  INPUT  TESTS
# =====================================================================
# ----------------------------- Tabular ------------------------------


@pytest.mark.parametrize(
    "fixture_name",
    [
        "tabular_valid_csv",
        "tabular_valid_xlsx",
        "tabular_valid_tsv",
        "example_valid_txt",
    ],
)
def test_tabular_to_parquet(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    fixture_name: str,
) -> None:
    """Convert tabular formats → Parquet."""
    src: Path = request.getfixturevalue(fixture_name)
    results = convert_any(str(src), tmp_path)
    assert results, "convert_any() returned empty list"
    out, meta = results[0]
    assert out.exists() and out.suffix == ".parquet"
    assert isinstance(meta, DatasetMetadata)
    assert meta.source_type in ("tabular", "vector")


# ----------------------------- Vector -------------------------------


def _check_vector(tmp_path: Path, path: Path) -> None:
    """Helper used by all vector tests."""
    results = convert_any(str(path), tmp_path)
    assert results and isinstance(results[0][1], DatasetMetadata)
    out, meta = results[0]
    assert out.exists() and out.suffix == ".parquet"
    assert meta.source_type in ("vector", "tabular")


def test_geojson_conversion(tmp_path: Path, geojson_path: Path) -> None:
    """Each GeoJSON sample → Parquet."""
    _check_vector(tmp_path, geojson_path)


def test_gpkg_conversion(tmp_path: Path, gpkg_path: Path) -> None:
    """Each GeoPackage sample → Parquet."""
    _check_vector(tmp_path, gpkg_path)


def test_kml_conversion(tmp_path: Path, kml_path: Path) -> None:
    """Each KML sample → Parquet."""
    _check_vector(tmp_path, kml_path)


def test_kmz_conversion(tmp_path: Path, kmz_path: Path) -> None:
    """Each KMZ sample → Parquet."""
    _check_vector(tmp_path, kmz_path)


def test_gpx_conversion(tmp_path: Path, gpx_path: Path) -> None:
    """Each GPX sample → Parquet."""
    _check_vector(tmp_path, gpx_path)


def test_shapefile_conversion(tmp_path: Path, shapefile_path: Path) -> None:
    """Each Shapefile (ZIP) sample → Parquet."""
    _check_vector(tmp_path, shapefile_path)


def test_crs_autodetect_and_transform(tmp_path: Path, geojson_path: Path) -> None:
    """Ensure convert_any handles CRS autodetection & transformation."""
    src = geojson_path
    # auto CRS
    results = convert_any(str(src), tmp_path)
    out_auto, meta_auto = results[0]
    assert meta_auto is not None and hasattr(meta_auto, "crs")

    # reprojection
    results_tx = convert_any(str(src), tmp_path, target_crs="EPSG:3857")
    out_tx, meta_tx = results_tx[0]
    assert meta_tx.crs == "EPSG:3857"
    assert out_tx.exists()


# ----------------------------- Raster -------------------------------


def test_raster_to_cog(tmp_path: Path, raster_valid: Path) -> None:
    """GeoTIFF → COG TIFF conversion."""
    results = convert_any(str(raster_valid), tmp_path)
    out, meta = results[0]
    assert out.exists() and out.suffix == ".tif"
    assert meta.source_type == "raster"


def test_raster_reproject_via_convert_any(tmp_path: Path, raster_valid: Path) -> None:
    """Ensure convert_any reprojects rasters when target_crs is passed."""
    results = convert_any(str(raster_valid), tmp_path, target_crs="EPSG:3857")
    out, meta = results[0]
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


# =====================================================================
#  CSV WITH WKT GEOMETRY TESTS
# =====================================================================


def test_csv_wkt_geometry_wgs84_valid(
    tmp_path: Path, tabular_valid_csv_wkt_wgs84: Path
) -> None:
    """CSV with valid WKT geometry in WGS84 should convert successfully."""
    results = convert_any(str(tabular_valid_csv_wkt_wgs84), tmp_path)
    assert results, "convert_any() returned empty list"
    out, meta = results[0]
    assert out.exists() and out.suffix == ".parquet"
    assert isinstance(meta, DatasetMetadata)
    assert meta.source_type == "vector"
    assert meta.crs == "EPSG:4326"


def test_csv_wkt_geometry_epsg3857_fails(
    tmp_path: Path, tabular_invalid_csv_wkt_epsg3857: Path
) -> None:
    """CSV with WKT geometry in EPSG:3857 coordinates should fail validation.

    CSV files with WKT geometry are assumed to be WGS84 (EPSG:4326).
    Coordinates outside WGS84 bounds indicate the data is in a projected
    coordinate system and should be rejected.
    """
    with pytest.raises(ValueError) as exc_info:
        convert_any(str(tabular_invalid_csv_wkt_epsg3857), tmp_path)
    assert "outside WGS84 bounds" in str(exc_info.value)
    assert "EPSG:4326" in str(exc_info.value)


# =====================================================================
#  MIXED CONTENT INPUT TESTS
# =====================================================================


def test_mixed_content_real_dataset_epsg4326(tmp_path: Path, data_root: Path) -> None:
    """
    End‑to‑end test verifying that a real mixed‑content archive (raster + vector)
    can be converted *and* reprojected to EPSG:4326.

    Assertions:
      • convert_any() runs with target CRS = EPSG:4326
      • one or more raster and vector outputs are produced
      • each output exists, is non‑empty, and metadata.crs includes "4326"
    """
    src = data_root / "io" / "mixed" / "mixed_content.zip"
    if not src.exists():
        src = data_root / "io" / "mixed" / "mixed_content"
    assert src.exists(), "Expected tests/data/io/mixed/mixed_content(.zip)"

    # Run the unified conversion with reprojection
    results = convert_any(str(src), tmp_path, target_crs="EPSG:4326")
    assert isinstance(results, list)
    assert results, "No results returned from convert_any"

    raster_files, vector_files = [], []
    seen = set()

    for out, meta in results:
        # --- Basic file & metadata checks
        assert isinstance(meta, DatasetMetadata), f"{out}: bad metadata"
        assert out.exists(), f"Output missing: {out}"
        assert out.stat().st_size > 0, f"{out}: empty file"
        assert out not in seen, f"Duplicate output path: {out}"
        seen.add(out)

        # --- CRS: ensure reprojection actually happened
        assert meta.crs and "4326" in meta.crs, f"{out}: wrong CRS {meta.crs}"

        # --- Type / extension consistency
        ext = out.suffix.lower()
        if ext == ".tif":
            raster_files.append(out)
            assert meta.source_type == "raster"
            assert meta.format == "tif"
        elif ext == ".parquet":
            vector_files.append(out)
            assert meta.source_type in {"vector", "tabular"}
            assert meta.format == "parquet"
        else:
            pytest.fail(f"Unexpected extension {ext} for {out}")

    # --- Global expectations
    assert raster_files, "No raster outputs produced"
    assert vector_files, "No vector/tabular outputs produced"

    log = logging.getLogger(__name__)
    log.info(
        "Mixed content conversion to EPSG:4326 → %d outputs (%d rasters, %d vectors)",
        len(results),
        len(raster_files),
        len(vector_files),
    )


# =====================================================================
#  REMOTE URL INPUT TESTS
# =====================================================================

# small public sample files
GEOJSON_URL = "https://assets.plan4better.de/goat/fixtures/geofence_street.geojson"
KML_URL = "https://assets.plan4better.de/goat/fixtures/kml_sample.kml"
PARQUET_URL = "https://assets.plan4better.de/goat/fixtures/poi.parquet"


@pytest.mark.network
@pytest.mark.parametrize("url", [GEOJSON_URL, KML_URL, PARQUET_URL])
def test_remote_vector_urls_to_parquet(tmp_path: Path, url: str) -> None:
    """Integration test for remote URLs → Parquet."""
    out, meta = convert_any(url, tmp_path, target_crs="EPSG:4326")[0]

    assert out.exists(), f"Output not found for {url}"
    assert out.suffix == ".parquet"
    assert meta.source_type in {
        "vector",
        "tabular",
    }, f"Unexpected source_type {meta.source_type}"

    # quick content sanity check
    con = duckdb.connect(database=":memory:")
    con.execute("INSTALL spatial; LOAD spatial;")
    nrows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    assert nrows > 0, f"No rows written for {url}"
