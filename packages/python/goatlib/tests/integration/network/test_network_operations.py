import logging
from pathlib import Path

import pytest
from goatlib.analysis.network.network_processor import (
    InMemoryNetworkParams,
    InMemoryNetworkProcessor,
)

logger = logging.getLogger(__name__)


class TestNetworkOperations:
    """Tests for the logical correctness of InMemoryNetworkProcessor operations."""

    @pytest.fixture
    def processor(self, network_file: Path) -> InMemoryNetworkProcessor:
        """A pytest fixture that yields a processor within a context manager."""
        params = InMemoryNetworkParams(network_path=str(network_file))
        with InMemoryNetworkProcessor(params) as proc:
            yield proc
        # Cleanup is handled automatically as the 'with' block exits

    def test_network_loading_and_stats(self, processor: InMemoryNetworkProcessor):
        """Test that the network loads correctly with valid stats."""
        stats = processor.get_network_stats()
        assert stats["edge_count"] > 0
        assert stats["min_length_m"] <= stats["avg_length_m"] <= stats["max_length_m"]

    def test_operation_chaining_with_correctness_checks(
        self, processor: InMemoryNetworkProcessor
    ):
        """Tests chaining non-destructive operations and verifies intermediate results."""
        filtered = processor.apply_sql_query(
            "SELECT * FROM network WHERE length_m > 150"
        )

        transformed = processor.apply_sql_query(
            "SELECT *, length_m * 1.1 as adjusted_length FROM network",
            base_table=filtered,
        )

        summary = processor.apply_sql_query(
            "SELECT COUNT(*) as total_edges FROM network",
            base_table=transformed,
        )

        filtered_stats = processor.get_network_stats(filtered)
        transformed_stats = processor.get_network_stats(transformed)
        summary_count = processor.con.execute(
            f"SELECT total_edges FROM {summary}"
        ).fetchone()[0]

        # Assert that intermediate tables still exist and are correct
        assert filtered_stats["edge_count"] > 0
        assert transformed_stats["edge_count"] == filtered_stats["edge_count"]
        assert summary_count == transformed_stats["edge_count"]

    def test_cleanup_intermediate_tables(self, processor: InMemoryNetworkProcessor):
        """Test that explicit cleanup removes intermediate tables but leaves the base network."""
        # Create intermediate tables
        table1 = processor.apply_sql_query("SELECT * FROM network WHERE length_m > 100")
        table2 = processor.apply_sql_query("SELECT * FROM network WHERE cost > 50")

        # Verify they exist
        all_tables_before = {
            t[0]
            for t in processor.con.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
        }
        assert table1 in all_tables_before
        assert table2 in all_tables_before

        # Perform cleanup
        processor.cleanup_intermediate_tables()

        # Verify they are gone, but the main table remains
        all_tables_after = {
            t[0]
            for t in processor.con.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
        }
        assert table1 not in all_tables_after
        assert table2 not in all_tables_after
        assert processor.network_table_name in all_tables_after
