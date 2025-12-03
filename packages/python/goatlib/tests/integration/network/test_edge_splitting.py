import logging
from pathlib import Path

import pytest
from goatlib.analysis.network.network_processor import (
    InMemoryNetworkParams,
    InMemoryNetworkProcessor,
)

logger = logging.getLogger(__name__)


class TestEdgeSplitting:
    """A consolidated and robust test suite for edge splitting."""

    @pytest.fixture
    def processor(self, network_file: Path) -> InMemoryNetworkProcessor:
        """
        A pytest fixture that yields a processor within a context manager.
        This provides a clean, ready-to-use processor for each test and
        guarantees that setup and teardown are handled correctly and in isolation.
        """
        params = InMemoryNetworkParams(network_path=str(network_file))
        with InMemoryNetworkProcessor(params) as proc:
            yield proc
        # Cleanup is handled automatically when the 'with' block exits

    def test_split_output_and_properties(self, processor: InMemoryNetworkProcessor):
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

    def test_split_topology_and_invariance(self, processor: InMemoryNetworkProcessor):
        """
        Tests the resulting table for topological correctness and metric invariance.
        This combines 'test_split_creates_correct_topology', 'test_split_preserves_total_length',
        and 'test_split_removes_original_edge'.
        """
        original_stats = processor.get_network_stats()

        split_table, split_info = processor.split_edge_at_point(
            latitude=48.13, longitude=11.58
        )
        split_stats = processor.get_network_stats(split_table)

        # 1. Test Stat Invariance
        assert split_stats["edge_count"] == original_stats["edge_count"] + 1
        assert (
            abs(split_stats["total_length_m"] - original_stats["total_length_m"]) < 1.0
        )

        # 2. Test Original Edge Removal
        original_edge_id = split_info["original_edge_split"]
        count = processor.con.execute(
            f"SELECT COUNT(*) FROM {split_table} WHERE edge_id = '{original_edge_id}'"
        ).fetchone()[0]
        assert count == 0

        # 3. Test New Topology
        new_node_id = split_info["artificial_node_id"]
        split_edges = processor.con.execute(f"""
            SELECT source, target FROM {split_table}
            WHERE edge_id LIKE '{original_edge_id}_part_%' ORDER BY edge_id
        """).fetchall()

        assert len(split_edges) == 2
        edge_a, edge_b = split_edges
        assert edge_a[1] == new_node_id  # target of part_a
        assert edge_b[0] == new_node_id  # source of part_b

    def test_comprehensive_workflow(self, processor: InMemoryNetworkProcessor):
        """
        Tests a realistic, chained workflow: filter -> split -> filter again.
        This confirms that the non-destructive design works as intended.
        """
        original_stats = processor.get_network_stats()

        # Step 1: Filter
        filtered_table = processor.apply_sql_query(
            "SELECT * FROM network WHERE length_m > 50"
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
            "SELECT * FROM network WHERE cost > 10", base_table=split_table
        )
        final_stats = processor.get_network_stats(final_table)
        assert final_stats["edge_count"] <= split_stats["edge_count"]

    def test_edge_case_far_away_point(self, processor: InMemoryNetworkProcessor):
        """
        Tests behavior when splitting at a point far from the network.
        The operation should still succeed and produce a valid network state.
        """
        original_stats = processor.get_network_stats()

        split_table, split_info = processor.split_edge_at_point(
            latitude=0.0, longitude=0.0
        )
        split_stats = processor.get_network_stats(split_table)

        # Should return a result even if no split occurred
        assert split_table is not None

        # If no split occurred, edge count should be the same
        # If a split occurred, edge count should be +1
        assert split_stats["edge_count"] >= original_stats["edge_count"]
        assert split_stats["edge_count"] <= original_stats["edge_count"] + 1
        assert "new_node_coords" in split_info
