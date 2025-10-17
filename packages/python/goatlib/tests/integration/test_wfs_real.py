# packages/python/goatlib/tests/unit/io/test_wfs_reader.py
from pathlib import Path

import pytest
from goatlib.io.remote_source.wfs import from_wfs

WFS_URL = (
    "https://geoservices.bayern.de/wfs/v1/ogc_atkis_basisdlm.cgi?"
    "SERVICE=WFS&VERSION=2.0.0"
)
LAYER_NAME = "adv:AX_Strasse"


@pytest.mark.network
def test_real_wfs(tmp_path: Path) -> None:
    """
    Full integration test against the Bavarian ATKIS WFS service.
    It downloads the layer via GDAL's WFS driver
    and converts it to Parquet through goatlib.convert_any.
    """

    try:
        out, meta = from_wfs(
            url=WFS_URL,
            out_dir=tmp_path,
            layer=LAYER_NAME,
            target_crs="EPSG:25832",  # UTM32N, Bavaria's projected CRS
        )
    except Exception as e:
        pytest.skip(f"WFS service not reachable or failed: {e}")

    # --- Basic assertions --------------------------------------------
    assert out and out.exists() and out.suffix == ".parquet"
    assert meta and meta.crs == "EPSG:25832"
    assert meta.source_type == "vector"

    # --- Spot‑check attribute + feature count -----------------------
    import duckdb

    con = duckdb.connect(database=":memory:")
    con.execute("INSTALL spatial; LOAD spatial;")
    cnt = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    assert cnt > 0, "No features returned from WFS service"
    con.close()
