import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import requests
from duckdb import DuckDBPyConnection

logger = logging.getLogger(__name__)


PathType = Literal["local", "s3", "http"]


def detect_path_type(path: str) -> PathType:
    """
    Detect the type of the given path: local, s3, or http.
    """
    scheme = urlparse(path).scheme.lower()
    if scheme in {"s3"}:
        return "s3"
    if scheme in {"http", "https"}:
        return "http"
    return "local"


def download_if_remote(src_path: str, timeout: int | None = None) -> str:
    """
    Download HTTP/HTTPS sources to a local temp file.
    Returns the local path. If the path is local, returns it unchanged.
    """
    path_type = detect_path_type(src_path)
    if path_type == "local":
        return src_path
    if path_type != "http":
        return src_path  # Only handle HTTP/HTTPS

    effective_timeout = timeout if timeout is not None else 120
    logger.info("Downloading remote file: %s", src_path)

    response = requests.get(src_path, stream=True, timeout=effective_timeout)
    response.raise_for_status()

    tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_http_"))
    filename = Path(urlparse(src_path).path).name or "downloaded_file"
    tmp_file = tmp_dir / filename

    with open(tmp_file, "wb") as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)

    logger.info("Downloaded %s → %s", src_path, tmp_file)
    return str(tmp_file)


def get_parquet_metadata(con: DuckDBPyConnection, input_path: str) -> dict[str, Any]:
    """
    Extract metadata from a Parquet or GeoParquet file.

    Returns
    -------
    dict with:
        - geometry_column: str or None
        - crs: dict or None
        - columns: list of dicts {name, type, nullable}
        - raw_meta: raw GeoParquet metadata (if present)
    """

    input_path_str = str(input_path)
    suffix = Path(input_path_str).suffix.lower()

    meta: dict[str, Any] = {
        "geometry_column": None,
        "crs": None,
        "columns": [],
        "raw_meta": None,
    }

    # --- Only handle Parquet / GeoParquet files ---
    if suffix != ".parquet":
        return meta

    # --- Attempt to read GeoParquet metadata ---
    try:
        rows = con.execute(
            f"SELECT * FROM parquet_kv_metadata('{input_path_str}') WHERE key = 'geo'"
        ).fetchall()
    except Exception:
        rows = []

    if rows:
        try:
            geo_json = (
                rows[0][2].decode() if isinstance(rows[0][2], bytes) else rows[0][2]
            )
            geo = json.loads(geo_json)
            meta["raw_meta"] = geo

            # GeoParquet 1.0.0 fields
            primary = geo.get("primary_column")
            columns = geo.get("columns", {})
            geom_info = columns.get(primary, {}) if primary else {}

            meta["geometry_column"] = primary
            meta["crs"] = geom_info.get("crs")

        except Exception as e:
            # If JSON parsing or metadata extraction fails
            meta["raw_meta"] = {"error": str(e)}
            meta["geometry_column"] = None
            meta["crs"] = None

    # --- Always describe schema (DuckDB native types) ---
    try:
        cols = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{input_path_str}')"
        ).fetchall()
        meta["columns"] = [
            {"name": c[0], "type": c[1], "nullable": c[2] == "YES"} for c in cols
        ]
    except Exception as e:
        meta["columns"] = [{"error": str(e)}]

    # --- Fallback: if GeoParquet metadata missing but geometry column detected ---
    if not meta["geometry_column"]:
        # Try to detect WKB/WKT geometry columns
        geom_candidates = [
            c["name"]
            for c in meta["columns"]
            if "WKB" in c["type"].upper() or "GEOMETRY" in c["type"].upper()
        ]
        if geom_candidates:
            meta["geometry_column"] = geom_candidates[0]

    return meta
