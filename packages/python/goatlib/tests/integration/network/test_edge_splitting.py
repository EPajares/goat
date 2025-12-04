import logging

from goatlib.analysis.network.network_processor import (
    InMemoryNetworkProcessor,
)

logger = logging.getLogger(__name__)


def test_split_output_and_properties(processor: InMemoryNetworkProcessor) -> None:
    """
    Tests the `split_info` dictionary for correctness and reasonable values.
    This combines 'test_basic_edge_split' and 'test_split_info_coordinates'.
    """
    _, split_info = processor.split_edge_at_point(latitude=48.13, longitude=11.58)

    # Verify structure and existence of keys
    assert split_info["artificial_node_id"] is not None
    assert split_info["original_edge_split"] is not None
    assert "new_node_coords" in split_info

    # Verify values and types
    assert 0.0 <= split_info["split_fraction"] <= 1.0
    coords = split_info["new_node_coords"]
    assert isinstance(coords["lon"], float)
    assert isinstance(coords["lat"], float)

    # Verify reasonable coordinate range
    assert 11.0 < coords["lon"] < 12.0
    assert 48.0 < coords["lat"] < 49.0


def test_split_topology_and_invariance(processor: InMemoryNetworkProcessor) -> None:
    """
    Comprehensive test for split operation correctness:
    - Network metrics are preserved (length, edge count +1)
    - Topology is correct (original edge removed, 2 new edges added)
    - New edges have correct naming and connectivity
    """
    original_stats = processor.get_network_stats()
    original_table_name = processor.network_table_name

    split_table, split_info = processor.split_edge_at_point(
        latitude=48.13, longitude=11.58
    )
    split_stats = processor.get_network_stats(split_table)
    original_edge_id = split_info["original_edge_split"]
    new_node_id = split_info["artificial_node_id"]

    # 1. Test Network Metrics Invariance
    assert split_stats["edge_count"] == original_stats["edge_count"] + 1
    assert abs(split_stats["total_length_m"] - original_stats["total_length_m"]) < 1.0
    assert split_stats["avg_length_m"] < original_stats["avg_length_m"]

    # 2. Test Original Edge Removal
    original_edge_count = processor.con.execute(
        f"SELECT COUNT(*) FROM {split_table} WHERE edge_id = '{original_edge_id}'"
    ).fetchone()[0]
    assert original_edge_count == 0

    # 3. Test New Edge Creation and Naming
    split_edges = processor.con.execute(f"""
        SELECT edge_id, source, target FROM {split_table}
        WHERE edge_id LIKE '{original_edge_id}_part_%' ORDER BY edge_id
    """).fetchall()

    assert len(split_edges) == 2
    edge_a, edge_b = split_edges

    # Check naming pattern
    assert edge_a[0] == f"{original_edge_id}_part_a"
    assert edge_b[0] == f"{original_edge_id}_part_b"

    # Check connectivity topology
    assert edge_a[2] == new_node_id  # target of part_a
    assert edge_b[1] == new_node_id  # source of part_b

    # 4. Test Edge Set Differences (verify exactly what changed)
    removed_edges = processor.con.execute(f"""
        SELECT edge_id FROM {original_table_name}
        EXCEPT SELECT edge_id FROM {split_table}
    """).fetchall()
    assert len(removed_edges) == 1
    assert str(removed_edges[0][0]) == str(original_edge_id)

    added_edges = processor.con.execute(f"""
        SELECT edge_id FROM {split_table}
        EXCEPT SELECT edge_id FROM {original_table_name}
    """).fetchall()
    added_edge_ids = {row[0] for row in added_edges}
    assert len(added_edge_ids) == 2
    assert f"{original_edge_id}_part_a" in added_edge_ids
    assert f"{original_edge_id}_part_b" in added_edge_ids


def test_comprehensive_workflow(processor: InMemoryNetworkProcessor) -> None:
    """
    Tests a realistic, chained workflow: filter -> split -> filter again.
    This confirms that the non-destructive design works as intended.
    """
    original_stats = processor.get_network_stats()
    original_table = processor.network_table_name

    # Step 1: Filter
    filtered_table = processor.apply_sql_query(
        f"SELECT * FROM {original_table} WHERE length_m > 50"
    )
    filtered_stats = processor.get_network_stats(filtered_table)
    assert filtered_stats["edge_count"] < original_stats["edge_count"]

    # Step 2: Split on the filtered network
    split_table, _ = processor.split_edge_at_point(
        latitude=48.13, longitude=11.58, base_table=filtered_table
    )
    split_stats = processor.get_network_stats(split_table)
    assert split_stats["edge_count"] == filtered_stats["edge_count"] + 1

    # Step 3: Apply another operation on the split network
    final_table = processor.apply_sql_query(
        f"SELECT * FROM  {split_table} WHERE cost > 10",
    )
    final_stats = processor.get_network_stats(final_table)
    assert final_stats["edge_count"] <= split_stats["edge_count"]


def test_split_is_non_destructive(processor: InMemoryNetworkProcessor) -> None:
    """
    Tests that the original network table remains unchanged after a split operation.
    """
    original_stats = processor.get_network_stats()
    original_table_name = processor.network_table_name

    # Perform the split operation
    processor.split_edge_at_point(latitude=48.13, longitude=11.58)

    # Verify that the original table was not altered
    post_split_stats = processor.get_network_stats(original_table_name)
    import pytest

    # Use pytest.approx for floating-point comparisons to handle precision differences
    assert post_split_stats["edge_count"] == pytest.approx(original_stats["edge_count"])
    assert post_split_stats["total_length_m"] == pytest.approx(
        original_stats["total_length_m"]
    )
    assert post_split_stats["avg_length_m"] == pytest.approx(
        original_stats["avg_length_m"]
    )
    assert post_split_stats["min_length_m"] == pytest.approx(
        original_stats["min_length_m"]
    )
    assert post_split_stats["max_length_m"] == pytest.approx(
        original_stats["max_length_m"]
    )
    assert post_split_stats == original_stats
