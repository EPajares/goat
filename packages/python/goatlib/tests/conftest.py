import logging
import urllib.request
from pathlib import Path
from typing import Literal

import pytest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global root
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def data_root() -> Path:
    """Base directory containing all static test data (data/io)."""
    return Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# Raster
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def raster_valid(data_root: Path) -> Path:
    """Valid raster GeoTIFF."""
    return data_root / "io" / "raster" / "imagery.tif"


# ---------------------------------------------------------------------------
# Tabular (CSV / Excel)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def tabular_valid_csv(data_root: Path) -> Path:
    return data_root / "io" / "tabular" / "valid" / "table.csv"


@pytest.fixture(scope="session")
def tabular_valid_csv_wkt_wgs84(data_root: Path) -> Path:
    """CSV with valid WKT geometry in WGS84."""
    return data_root / "io" / "tabular" / "valid" / "wkt_geometry_wgs84.csv"


@pytest.fixture(scope="session")
def tabular_invalid_csv_wkt_epsg3857(data_root: Path) -> Path:
    """CSV with WKT geometry in EPSG:3857 (outside WGS84 bounds)."""
    return data_root / "io" / "tabular" / "invalid" / "wkt_geometry_epsg3857.csv"


@pytest.fixture(scope="session")
def tabular_valid_xlsx(data_root: Path) -> Path:
    return data_root / "io" / "tabular" / "valid" / "table.xlsx"


@pytest.fixture(scope="session")
def tabular_valid_tsv(data_root: Path) -> Path:
    return data_root / "io" / "tabular" / "valid" / "table.tsv"


@pytest.fixture(scope="session")
def example_valid_txt(data_root: Path) -> Path:
    return data_root / "io" / "tabular" / "valid" / "example.txt"


@pytest.fixture(scope="session")
def tabular_invalid_no_header(data_root: Path) -> Path:
    return data_root / "io" / "tabular" / "invalid" / "no_header.csv"


@pytest.fixture(scope="session")
def tabular_invalid_bad_xlsx(data_root: Path) -> Path:
    return data_root / "io" / "tabular" / "invalid" / "bad_formed.xlsx"


# ---------------------------------------------------------------------------
# Vector (GeoJSON / GPKG / KML / KMZ / GPX / Shapefile)
# ---------------------------------------------------------------------------

VectorType = Literal["geojson", "gpkg", "kml", "shapefile"]


@pytest.fixture(scope="session", params=["geojson", "gpkg", "kml", "shapefile"])
def vector_type(request: pytest.FixtureRequest) -> VectorType:  # type: ignore[return-type]
    """Enumerate supported vector types."""
    return request.param


@pytest.fixture(scope="session")
def vector_valid_dir(data_root: Path, vector_type: VectorType) -> Path:
    """Sub‑directory with valid vector files for each format."""
    return data_root / "io" / "vector" / "valid" / vector_type


@pytest.fixture(scope="session")
def vector_invalid_zip(data_root: Path) -> Path:
    """Corrupted zipped shapefile (negative tests)."""
    return data_root / "io" / "vector" / "invalid" / "shapefile_missing_file.zip"


# ---------------------------------------------------------------------------
# Single‑file vector shortcuts (used by converter tests)
# ---------------------------------------------------------------------------


def _collect_vector_files(fmt: str) -> list[Path]:
    base = Path(__file__).parent / "data" / "io" / "vector" / "valid" / fmt
    if fmt == "shapefile":
        return sorted(base.glob("*.zip"))
    return sorted(base.glob(f"*.{fmt}"))


@pytest.fixture(
    params=_collect_vector_files("geojson"), ids=lambda p: p.name, scope="session"
)
def geojson_path(request: pytest.FixtureRequest) -> Path:
    """Each GeoJSON file (points, lines, polygons)."""
    return request.param


@pytest.fixture(
    params=_collect_vector_files("gpkg"), ids=lambda p: p.name, scope="session"
)
def gpkg_path(request: pytest.FixtureRequest) -> Path:
    """Each GeoPackage file."""
    return request.param


@pytest.fixture(
    params=_collect_vector_files("kml"), ids=lambda p: p.name, scope="session"
)
def kml_path(request: pytest.FixtureRequest) -> Path:
    """Each KML file."""
    return request.param


@pytest.fixture(
    params=_collect_vector_files("kmz"), ids=lambda p: p.name, scope="session"
)
def kmz_path(request: pytest.FixtureRequest) -> Path:
    """Each KMZ file."""
    return request.param


@pytest.fixture(
    params=_collect_vector_files("gpx"), ids=lambda p: p.name, scope="session"
)
def gpx_path(request: pytest.FixtureRequest) -> Path:
    """Each GPX file."""
    return request.param


@pytest.fixture(
    params=_collect_vector_files("shapefile"), ids=lambda p: p.name, scope="session"
)
def shapefile_path(request: pytest.FixtureRequest) -> Path:
    """Each zipped shapefile."""
    return request.param


@pytest.fixture(
    params=_collect_vector_files("mixed"), ids=lambda p: p.name, scope="session"
)
def mixed_content_path(request: pytest.FixtureRequest) -> Path:
    """Each mixed content file."""
    return request.param


# ---------------------------------------------------------------------------
# MOTIS adapter fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def motis_fixtures_dir(data_root: Path) -> Path:
    """Directory containing MOTIS fixture data for routing tests."""
    return data_root / "routing" / "motis"


@pytest.fixture(scope="session")
def buffered_stations_dir(data_root: Path) -> Path:
    """Directory containing buffered bus station test data."""
    return data_root / "routing" / "buffered_stations"


# ---------------------------------------------------------------------------
# Network extractor fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def network_extractor_data_dir(data_root: Path) -> Path:
    """Directory containing network extractor test data."""
    return data_root / "network"


@pytest.fixture(scope="session")
def network_file(network_extractor_data_dir: Path) -> Path:
    """Path to the test network parquet file."""
    return network_extractor_data_dir / "network.parquet"


@pytest.fixture(scope="session")
def extracted_network_file(network_extractor_data_dir: Path) -> Path:
    """Path to the test network parquet file."""
    return network_extractor_data_dir / "extracted_network.parquet"


# ---------------------------------------------------------------------------
# Travel time matrices fixtures (auto-download from S3 if not present)
# ---------------------------------------------------------------------------

TRAVELTIME_MATRICES_BASE_URL = (
    "https://assets.plan4better.de/goat/fixtures/traveltime_matrices"
)
TRAVELTIME_MATRICES_FILES = [
    "walking/h3_3=8077/h3_r10_munich.parquet",
]


def _download_file(url: str, dest: Path) -> None:
    """Download a file from URL to destination path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} to {dest}...")
    urllib.request.urlretrieve(url, dest)
    logger.info(f"Downloaded {dest.name} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")


@pytest.fixture(scope="session")
def traveltime_matrices_dir() -> Path:
    """
    Directory containing travel time matrices for heatmap tests.

    Downloads the matrices from S3 if not already present locally.
    The matrices are stored in /app/data/traveltime_matrices/ with hive partitioning.
    """
    # Use root data folder for shared test data
    matrices_dir = (
        Path(__file__).parent.parent.parent.parent.parent
        / "data"
        / "traveltime_matrices"
    )

    for rel_path in TRAVELTIME_MATRICES_FILES:
        local_path = matrices_dir / rel_path
        if not local_path.exists():
            url = f"{TRAVELTIME_MATRICES_BASE_URL}/{rel_path}"
            _download_file(url, local_path)

    return matrices_dir


@pytest.fixture(scope="session")
def walking_matrix_dir(traveltime_matrices_dir: Path) -> Path:
    """Directory containing walking travel time matrices."""
    return traveltime_matrices_dir / "walking"
