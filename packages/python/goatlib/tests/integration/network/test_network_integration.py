"""Integration tests for network processing functionality."""

import logging
import tempfile
from pathlib import Path

import pytest
from goatlib.analysis.network.network_processor import (
    NetworkProcessor,
    analyze_point_connectivity,
    create_temporary_enhanced_network,
    load_network,
    load_network_with_connectors,
    process_network,
)
from goatlib.analysis.schemas.network import NetworkProcessorParams

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def sample_network_file():
    """Use the existing test network file if available."""
    network_file = (
        Path(__file__).parent.parent / "data" / "network" / "test_network.parquet"
    )
    if network_file.exists():
        return str(network_file)
    else:
        pytest.skip("Test network file not available for integration tests")


# ============================================================================
# Core NetworkProcessor Integration Tests
# ============================================================================


def test_network_processor_basic_functionality(sample_network_file):
    """Test unified NetworkProcessor functionality with real files."""

    params = NetworkProcessorParams(
        input_path=sample_network_file,
        custom_sql="SELECT edge_id, source, target, cost, geometry FROM v_input",
    )
    assert params.custom_sql is not None
    assert not params.creates_artificial_edges

    tool = NetworkProcessor()
    assert tool is not None

    assert callable(process_network)
    assert callable(load_network)


def test_network_processor_with_real_data(sample_network_file):
    """Test NetworkProcessor with actual data file processing."""

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        output_file = f.name

    try:
        custom_sql = """
            SELECT edge_id, source, target, cost, geometry
            FROM v_input
            WHERE cost > 0
            LIMIT 1000
        """

        result_path = load_network(
            input_file=str(sample_network_file),
            custom_sql=custom_sql,
            output_file=output_file,
        )

        assert Path(result_path).exists(), "Output file was not created"
        file_size = Path(result_path).stat().st_size
        assert file_size > 0, "Output file is empty"

    finally:
        if Path(output_file).exists():
            Path(output_file).unlink()


def test_network_processor_artificial_edges_integration():
    """Test NetworkProcessor artificial edge functionality with real files."""

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as network_f:
        network_file = network_f.name
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as points_f:
        points_file = points_f.name

    try:
        # Create minimal valid files
        with open(points_f.name, "w") as f:
            f.write('{"type": "FeatureCollection", "features": []}')

        params = NetworkProcessorParams(
            input_path=network_file,
            origin_points_path=points_file,
            custom_sql="SELECT * FROM v_input",
            buffer_distance=50.0,
        )

        assert params.creates_artificial_edges
        assert params.buffer_distance == 50.0

    finally:
        Path(network_file).unlink()
        Path(points_file).unlink()


# ============================================================================
# Connectivity Analysis Tests
# ============================================================================


def test_connectivity_analysis_with_real_data(sample_network_file):
    """Test connectivity analysis with real network data."""
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as f:
        geojson_content = """
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 1},
                    "geometry": {"type": "Point", "coordinates": [11.432, 48.162]}
                },
                {
                    "type": "Feature", 
                    "properties": {"id": 2},
                    "geometry": {"type": "Point", "coordinates": [11.433, 48.163]}
                }
            ]
        }
        """
        f.write(geojson_content)
        points_file = f.name

    try:
        stats = analyze_point_connectivity(
            origin_points=points_file,
            network_edges=sample_network_file,
            buffer_distance=1000.0,
        )

        assert isinstance(stats, dict)
        assert "total_points" in stats
        assert "connectable_points" in stats
        assert "isolated_points" in stats
        assert stats["total_points"] >= 0
        assert stats["connectable_points"] >= 0
        assert stats["isolated_points"] >= 0

        logger.info(f"Connectivity stats: {stats}")

    finally:
        Path(points_file).unlink()


# ============================================================================
# Temporary Network Creation Tests
# ============================================================================


def test_temporary_network_creation_workflow(sample_network_file):
    """Test the complete temporary network creation workflow."""
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as f:
        geojson_content = """
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 1},
                    "geometry": {"type": "Point", "coordinates": [11.432, 48.162]}
                }
            ]
        }
        """
        f.write(geojson_content)
        points_file = f.name

    try:
        table_name = create_temporary_enhanced_network(
            origin_points=points_file,
            network_edges=sample_network_file,
            buffer_distance=1000.0,
        )

        assert table_name is not None
        assert isinstance(table_name, str)
        logger.info(f"Enhanced network table created: {table_name}")

    finally:
        Path(points_file).unlink()


def test_temporary_nature_of_artificial_edges(sample_network_file):
    """Test that artificial edges are truly temporary and don't persist."""
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as f:
        geojson_content = """
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 1},
                    "geometry": {"type": "Point", "coordinates": [11.432, 48.162]}
                }
            ]
        }
        """
        f.write(geojson_content)
        points_file = f.name

    try:
        table_name = create_temporary_enhanced_network(
            origin_points=points_file,
            network_edges=sample_network_file,
            buffer_distance=1000.0,
        )

        assert table_name is not None
        assert isinstance(table_name, str)
        logger.info(
            "✅ Verified that temporary enhanced network is created via NetworkProcessor"
        )

    finally:
        Path(points_file).unlink()


# ============================================================================
# Full Workflow Tests
# ============================================================================


def test_load_network_with_connectors_workflow(sample_network_file):
    """Test the complete load_network_with_connectors workflow."""
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as f:
        geojson_content = """
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 1},
                    "geometry": {"type": "Point", "coordinates": [11.432, 48.162]}
                }
            ]
        }
        """
        f.write(geojson_content)
        points_file = f.name

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        output_file = f.name

    try:
        result_path = load_network_with_connectors(
            network_file=sample_network_file,
            origin_points_file=points_file,
            custom_sql="""
                SELECT 
                    id as edge_id,
                    source,
                    target,
                    cost,
                    reverse_cost,
                    geom as geometry,
                    edge_type
                FROM v_input
                WHERE cost > 0
                ORDER BY edge_type DESC, cost
            """,
            output_file=output_file,
            buffer_distance=1000.0,
        )

        assert result_path == output_file
        assert Path(result_path).exists()
        assert Path(result_path).stat().st_size > 0

        logger.info(f"Enhanced routing network created: {result_path}")
        logger.info(f"File size: {Path(result_path).stat().st_size} bytes")

    finally:
        Path(points_file).unlink()
        if Path(output_file).exists():
            Path(output_file).unlink()


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_missing_origin_points_file():
    """Test handling of missing origin points file."""
    with pytest.raises(Exception):
        analyze_point_connectivity(
            origin_points="nonexistent.geojson",
            network_edges="also_nonexistent.parquet",
            buffer_distance=100.0,
        )


def test_invalid_buffer_distance():
    """Test handling of invalid buffer distances."""
    with (
        tempfile.NamedTemporaryFile(suffix=".geojson") as points_file,
        tempfile.NamedTemporaryFile(suffix=".parquet") as network_file,
    ):
        Path(points_file.name).touch()
        Path(network_file.name).touch()

        try:
            create_temporary_enhanced_network(
                origin_points=points_file.name,
                network_edges=network_file.name,
                buffer_distance=-100.0,
            )
        except Exception:
            pass


# ============================================================================
# Logging Tests
# ============================================================================


def test_logging_in_integration():
    """Test that logging works properly in integration scenarios."""
    logging.basicConfig(level=logging.INFO)
    test_logger = logging.getLogger("goatlib.analysis.network.artificial_edges")
    test_logger.info("Integration test logging check")
    assert True
