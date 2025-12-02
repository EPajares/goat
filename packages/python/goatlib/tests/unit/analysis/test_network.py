import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from goatlib.analysis.network.network_processor import (
    NetworkProcessor,
    analyze_point_connectivity,
    create_temporary_enhanced_network,
)
from goatlib.analysis.schemas.network import NetworkProcessorParams

logger = logging.getLogger(__name__)


# ============================================================================
# Schema Validation Tests
# ============================================================================


def test_network_processor_params_validation():
    """Test NetworkProcessorParams validation logic."""
    # Test with non-existent file
    with pytest.raises(ValueError, match="Input file does not exist"):
        NetworkProcessorParams(
            input_path="/nonexistent/path.parquet", custom_sql="SELECT * FROM v_input"
        )

    # Test with empty SQL
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_file = f.name

    try:
        with pytest.raises(ValueError, match="custom_sql cannot be empty"):
            NetworkProcessorParams(input_path=temp_file, custom_sql="")

        # Test with invalid buffer distance
        with pytest.raises(ValueError, match="Buffer distance must be positive"):
            NetworkProcessorParams(
                input_path=temp_file,
                custom_sql="SELECT * FROM v_input",
                buffer_distance=-10.0,
            )

        # Test with invalid max connections
        with pytest.raises(
            ValueError, match="Must connect to at least 1 edge per point"
        ):
            NetworkProcessorParams(
                input_path=temp_file,
                custom_sql="SELECT * FROM v_input",
                max_connections_per_point=0,
            )

    finally:
        Path(temp_file).unlink()


def test_creates_artificial_edges_property():
    """Test the creates_artificial_edges property logic."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_file = f.name

    try:
        # Without origin points - should not create artificial edges
        params = NetworkProcessorParams(
            input_path=temp_file, custom_sql="SELECT * FROM v_input"
        )
        assert not params.creates_artificial_edges

        # With origin points - should create artificial edges
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as points_f:
            points_file = points_f.name

        try:
            params_with_points = NetworkProcessorParams(
                input_path=temp_file,
                origin_points_path=points_file,
                custom_sql="SELECT * FROM v_input",
            )
            assert params_with_points.creates_artificial_edges
        finally:
            Path(points_file).unlink()

    finally:
        Path(temp_file).unlink()


def test_default_parameter_values():
    """Test that default parameter values are correctly set."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_file = f.name

    try:
        params = NetworkProcessorParams(
            input_path=temp_file, custom_sql="SELECT * FROM v_input"
        )

        # Test default values
        assert params.output_crs == "EPSG:4326"
        assert params.buffer_distance == 100.0
        assert params.max_connections_per_point == 3
        assert params.artificial_node_id_start == 1_000_000_000
        assert params.artificial_edge_id_start == 2_000_000_000
        assert params.output_path is None

    finally:
        Path(temp_file).unlink()


# ============================================================================
# NetworkProcessor Logic Tests
# ============================================================================


@patch("goatlib.analysis.network.network_processor.NetworkProcessor.import_input")
@patch(
    "goatlib.analysis.network.network_processor.NetworkProcessor._execute_sql_and_save"
)
def test_network_processor_basic_workflow(mock_save, mock_import):
    """Test basic NetworkProcessor workflow without artificial edges."""
    # Setup mocks
    mock_metadata = Mock()
    mock_metadata.geometry_column = "geom"
    mock_metadata.crs.to_string.return_value = "EPSG:4326"
    mock_import.return_value = (mock_metadata, "test_table")

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_file = f.name

    try:
        params = NetworkProcessorParams(
            input_path=temp_file, custom_sql="SELECT * FROM v_input"
        )

        processor = NetworkProcessor()
        processor.con = Mock()  # Mock the connection

        # Call the implementation method directly
        result = processor._run_implementation(params)

        # Verify behavior
        mock_import.assert_called_once_with(temp_file)
        mock_save.assert_called_once()
        assert len(result) == 1
        assert result[0][1].crs == "EPSG:4326"

    finally:
        Path(temp_file).unlink()


@patch("goatlib.analysis.network.network_processor.NetworkProcessor.import_input")
def test_network_processor_enhanced_workflow(mock_import):
    """Test NetworkProcessor workflow with artificial edges."""
    # Setup mocks
    mock_metadata = Mock()
    mock_metadata.geometry_column = "geom"
    mock_metadata.crs.to_string.return_value = "EPSG:4326"
    mock_import.side_effect = [
        (mock_metadata, "network_table"),
        (mock_metadata, "points_table"),
    ]

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as network_f:
        network_file = network_f.name
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as points_f:
        points_file = points_f.name

    try:
        params = NetworkProcessorParams(
            input_path=network_file,
            origin_points_path=points_file,
            custom_sql="SELECT * FROM v_input",
            buffer_distance=150.0,
        )

        processor = NetworkProcessor()
        processor.con = Mock()

        # Mock the enhanced network creation
        with patch.object(
            processor,
            "_create_enhanced_network_with_points",
            return_value="enhanced_table",
        ) as mock_enhance:
            with patch.object(processor, "_execute_sql_and_save") as mock_save:
                result = processor._run_implementation(params)

                # Verify enhanced network was created
                mock_enhance.assert_called_once_with(
                    "points_table",
                    "network_table",
                    150.0,
                    3,
                    1_000_000_000,
                    2_000_000_000,
                )
                mock_save.assert_called_once()

    finally:
        Path(network_file).unlink()
        Path(points_file).unlink()


def test_sql_replacement_logic():
    """Test that v_input is properly replaced in SQL queries."""
    processor = NetworkProcessor()
    processor.con = Mock()

    params = Mock()
    params.custom_sql = "SELECT * FROM v_input WHERE cost > 0"

    output_path = Path("/tmp/test.parquet")

    # Call the method
    processor._execute_sql_and_save(params, "actual_table", output_path)

    # Verify the SQL was modified correctly
    expected_query = "COPY (SELECT * FROM actual_table WHERE cost > 0) TO '/tmp/test.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)"
    processor.con.execute.assert_called_once_with(expected_query)


# ============================================================================
# Point Connector Tests
# ============================================================================


@patch("goatlib.analysis.network.point_connector.NetworkProcessor")
def test_create_temporary_enhanced_network(mock_processor_class):
    """Test temporary enhanced network creation."""
    mock_processor = Mock()
    mock_processor_class.return_value = mock_processor
    mock_processor._create_enhanced_network_temporary.return_value = "enhanced_table"

    result = create_temporary_enhanced_network(
        origin_points="points.geojson",
        network_edges="network.parquet",
        buffer_distance=200.0,
    )

    # Verify processor was called correctly
    mock_processor._create_enhanced_network_temporary.assert_called_once_with(
        origin_points="points.geojson",
        network_edges="network.parquet",
        buffer_distance=200.0,
    )
    assert result == "enhanced_table"


@patch("goatlib.analysis.network.point_connector.NetworkProcessor")
def test_analyze_point_connectivity(mock_processor_class):
    """Test point connectivity analysis."""
    mock_processor = Mock()
    mock_processor_class.return_value = mock_processor
    mock_processor.import_input.side_effect = [
        (Mock(), "points_table"),
        (Mock(), "network_table"),
    ]

    # Mock the SQL result
    mock_result = (100, 80, 20, 2.5, 5)  # total, connectable, isolated, avg, max
    mock_processor.con.execute.return_value.fetchone.return_value = mock_result

    result = analyze_point_connectivity(
        origin_points="points.geojson",
        network_edges="network.parquet",
        buffer_distance=150.0,
    )

    # Verify the result structure
    expected = {
        "total_points": 100,
        "connectable_points": 80,
        "isolated_points": 20,
        "avg_nearby_edges": 2.5,
        "max_nearby_edges": 5,
    }
    assert result == expected
    #
