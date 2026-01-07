import logging

from goatlib.analysis.network.network_processor import (
    InMemoryNetworkProcessor,
)

logger = logging.getLogger(__name__)


def test_interpolate_long_edges(processor: InMemoryNetworkProcessor) -> None:
    """Test edge interpolation functionality."""
    # Get original network stats
    original_stats = processor.get_network_stats()

    # Find a reasonable threshold - use 75th percentile of edge lengths
    edge_lengths = processor.con.execute(f"""
        SELECT length_m FROM {processor.network_table_name} 
        ORDER BY length_m DESC
    """).fetchall()

    if len(edge_lengths) < 4:
        # Skip test if network is too small
        return

    # Use a threshold that will catch some but not all edges
    max_length = edge_lengths[len(edge_lengths) // 4][0]  # 75th percentile
    interpolation_distance = max_length / 3  # Create multiple segments

    # Perform interpolation
    interpolated_table, info = processor.interpolate_long_edges(
        max_edge_length=max_length, interpolation_distance=interpolation_distance
    )

    # Verify interpolation info
    assert info["original_edge_count"] == original_stats["edge_count"]
    assert info["max_edge_length_threshold"] == max_length
    assert info["interpolation_distance"] == interpolation_distance
    assert (
        info["final_edge_count"] >= info["original_edge_count"]
    )  # Should have more edges
    assert info["processing_time_seconds"] > 0

    # Verify the interpolated network has valid stats
    interpolated_stats = processor.get_network_stats(interpolated_table)
    assert interpolated_stats["edge_count"] == info["final_edge_count"]
    assert interpolated_stats["edge_count"] > 0

    # Check that no edge in the interpolated network exceeds the threshold
    long_edges_count = processor.con.execute(f"""
        SELECT COUNT(*) FROM {interpolated_table} WHERE length_m > {max_length}
    """).fetchone()[0]
    assert (
        long_edges_count == 0
    ), f"Found {long_edges_count} edges still longer than {max_length}m"

    # Verify intermediate nodes were created
    if info["new_intermediate_nodes"] > 0:
        intermediate_nodes = processor.con.execute(f"""
            SELECT COUNT(DISTINCT node_id) FROM (
                SELECT source as node_id FROM {interpolated_table} WHERE source LIKE 'interp_%'
                UNION 
                SELECT target as node_id FROM {interpolated_table} WHERE target LIKE 'interp_%'
            )
        """).fetchone()[0]
        assert intermediate_nodes > 0, "Should have created intermediate nodes"

    # Verify total length is preserved (approximately)
    original_total_length = original_stats["total_length_m"]
    interpolated_total_length = interpolated_stats["total_length_m"]
    length_diff = abs(original_total_length - interpolated_total_length)
    assert (
        length_diff / original_total_length < 0.01
    ), f"Total length changed too much: {length_diff}m"

    logger.info("Interpolation test completed:")
    logger.info(f"  Original edges: {info['original_edge_count']}")
    logger.info(f"  Long edges processed: {info['long_edges_processed']}")
    logger.info(f"  Final edges: {info['final_edge_count']}")
    logger.info(f"  New intermediate nodes: {info['new_intermediate_nodes']}")
    logger.info(f"  Max edge length threshold: {max_length:.1f}m")
    logger.info(f"  Processing time: {info['processing_time_seconds']:.2f}s")


def test_interpolate_with_custom_distance(processor: InMemoryNetworkProcessor) -> None:
    """Test edge interpolation with custom interpolation distance."""
    max_length = 200.0
    interpolation_distance = 50.0

    interpolated_table, info = processor.interpolate_long_edges(
        max_edge_length=max_length, interpolation_distance=interpolation_distance
    )

    # Verify configuration was used
    assert info["max_edge_length_threshold"] == max_length
    assert info["interpolation_distance"] == interpolation_distance

    # Check that edges are properly segmented
    max_edge_in_result = processor.con.execute(f"""
        SELECT MAX(length_m) FROM {interpolated_table}
    """).fetchone()[0]

    # Should be approximately equal to interpolation_distance (or less)
    assert (
        max_edge_in_result <= max_length
    ), f"Max edge length {max_edge_in_result} exceeds threshold {max_length}"


def test_interpolate_default_distance(processor: InMemoryNetworkProcessor) -> None:
    """Test edge interpolation with default interpolation distance."""
    max_length = 100.0

    interpolated_table, info = processor.interpolate_long_edges(
        max_edge_length=max_length
    )

    # Verify default interpolation distance was used (half of max_length)
    assert info["interpolation_distance"] == max_length / 2
    assert info["max_edge_length_threshold"] == max_length

    # Check that interpolation worked
    assert info["final_edge_count"] >= info["original_edge_count"]


# Interpolation test completed:
# Original edges:           375164
# Long edges processed:     93791
# Final edges:              1021482
# New intermediate nodes:   1279968
# Max edge length threshold: 51.2m
# Processing time:           0.16s
# PASSED
