"""pytest configuration for fast-routing Python tests."""

import pytest
from pathlib import Path


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "benchmark: marks tests as benchmarks")


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session") 
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"


@pytest.fixture(scope="session")
def network_file(data_dir):
    """Return the network file path if it exists."""
    network_path = data_dir / "network.parquet"
    if not network_path.exists():
        pytest.skip(f"Network file not found: {network_path}")
    return str(network_path)