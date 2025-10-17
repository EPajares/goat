from pathlib import Path

import duckdb
import pytest
from goatlib.io.ingest import convert_any

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
