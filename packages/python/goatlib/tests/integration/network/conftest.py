from pathlib import Path

import pytest
from goatlib.analysis.network.network_processor import (
    InMemoryNetworkParams,
    InMemoryNetworkProcessor,
)


@pytest.fixture
def processor(network_file: Path) -> InMemoryNetworkProcessor:
    """A pytest fixture that yields a processor within a context manager."""
    params = InMemoryNetworkParams(network_path=str(network_file))
    with InMemoryNetworkProcessor(params) as proc:
        yield proc
    # Cleanup is handled automatically as the 'with' block exits
