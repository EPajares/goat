import logging
from pathlib import Path

from goatlib.analysis.schemas.routing import RoutingParams, RoutingTool, extract_network

logger = logging.getLogger(__name__)


def test_network_extractor(test_network_file: Path) -> None:
    """
    Short test to validate the RoutingTool functionality.
    """
    logger.info("🧪 Testing RoutingTool...")

    try:
        # Test 1: Tool creation
        tool = RoutingTool()
        assert tool is not None, "RoutingTool instance should not be None"

        # Test 2: RoutingParams creation
        params = RoutingParams(
            input_path=test_network_file,  # Path object works with str|Path union
            custom_sql="SELECT edge_id, source, target, cost, geometry FROM test_table",
        )
        assert params.custom_sql is not None, "Should have custom_sql"
        logger.info("RoutingParams created successfully")

        # Test 3: Extract function exists
        assert callable(extract_network), "extract_network should be callable"
        logger.info("extract_network function is available")

        logger.info("\nAll basic tests passed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


def test_network_extractor_with_data(
    test_network_file: Path, test_extracted_network_file: Path
) -> None:
    """
    Test the RoutingTool with actual network data file.
    Expects a test network file to be available in the repository.
    """
    logger.info("🛣️  Testing RoutingTool with network data...")

    # Expected path for test network data (to be added to repo)
    try:
        if not test_network_file.exists():
            logger.info(
                f"Skipping data test - network file not found: {test_network_file}"
            )
            return

        logger.info(f"Found network file: {test_network_file}")

        logger.info("🔄 Extracting network data...")

        # Use the extract_network function directly
        custom_sql = """
        SELECT
            edge_id,
            source,
            target,
            cost,
            geometry
        FROM v_input
        WHERE cost > 0
        LIMIT 1000
        """

        # Now that geometry validation is more flexible, this should work directly
        result_path = extract_network(
            input_file=str(test_network_file),
            custom_sql=custom_sql,
            output_file=str(test_extracted_network_file),
        )

        logger.info(f"Network extraction completed: {result_path}")

        # Verify output file exists
        if Path(result_path).exists():
            file_size = Path(result_path).stat().st_size
            logger.info(f"Output file created successfully ({file_size} bytes)")
        else:
            raise AssertionError("Output file was not created")

        logger.info("🎉 Network data test passed!")
    except Exception as e:
        logger.info(f"❌ Network data test failed: {e}")
        import traceback

        traceback.print_exc()
        logger.info("💡 To enable this test, add a test network file at:")
        logger.info("tests/data/network/test_network.parquet")
        raise
