import logging

from goatlib.analysis.network.network_processor import (
    InMemoryNetworkProcessor,
)

logger = logging.getLogger(__name__)


def test_network_loading_and_stats(processor: InMemoryNetworkProcessor):
    """Test that the network loads correctly with valid stats."""
    stats = processor.get_network_stats()
    assert stats["edge_count"] > 0
    assert stats["min_length_m"] <= stats["avg_length_m"] <= stats["max_length_m"]


def test_operation_chaining_with_correctness_checks(
    processor: InMemoryNetworkProcessor,
):
    """Tests chaining non-destructive operations and verifies intermediate results."""
    base_table_name = processor.network_table_name
    filtered = processor.apply_sql_query(
        f"SELECT * FROM {base_table_name} WHERE length_m > 150"
    )

    # 2. Use the result of the previous step ('filtered') directly in the next query
    #    The 'base_table' argument is no longer needed.
    transformed = processor.apply_sql_query(
        f"SELECT *, length_m * 1.1 as adjusted_length FROM {filtered}"
    )

    # 3. Use the result of the previous step ('transformed') directly in the next query
    summary = processor.apply_sql_query(
        f"SELECT COUNT(*) as total_edges FROM {transformed}"
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


def test_cleanup_intermediate_tables(processor: InMemoryNetworkProcessor):
    """Test that explicit cleanup removes intermediate tables but leaves the base network."""
    # Create intermediate tables explicitly using the base table name
    base_table_name = processor.network_table_name
    table1 = processor.apply_sql_query(
        f"SELECT * FROM {base_table_name} WHERE length_m > 100"
    )
    table2 = processor.apply_sql_query(
        f"SELECT * FROM {base_table_name} WHERE cost > 50"
    )

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
