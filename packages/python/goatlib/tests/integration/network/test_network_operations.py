import logging

from goatlib.analysis.network.network_processor import (
    InMemoryNetworkProcessor,
)

logger = logging.getLogger(__name__)


def test_network_loading_and_stats(processor: InMemoryNetworkProcessor) -> None:
    """Test that the network loads correctly with valid stats."""
    stats = processor.get_network_stats()
    assert stats["edge_count"] > 0
    assert stats["min_length_m"] <= stats["avg_length_m"] <= stats["max_length_m"]


def test_operation_chaining_with_correctness_checks(
    processor: InMemoryNetworkProcessor,
) -> None:
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


def test_get_available_tables(processor: InMemoryNetworkProcessor) -> None:
    """Test that get_available_tables returns the correct list of tables."""
    # Initially, only the main network table should be present
    tables = processor.get_available_tables()
    assert processor.network_table_name in tables
    logger.info(f"Available tables: {tables}")
    # Create an intermediate table
    intermediate_table = processor.apply_sql_query(
        f"SELECT * FROM {processor.network_table_name} WHERE length_m > 100"
    )

    # Now both tables should be present
    tables_after = processor.get_available_tables()
    assert processor.network_table_name in tables_after
    assert intermediate_table in tables_after
    logger.info(f"Available tables: {tables_after}")


def test_cleanup_intermediate_tables(processor: InMemoryNetworkProcessor) -> None:
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


def test_save_to_file(processor: InMemoryNetworkProcessor, tmp_path: str) -> None:
    """Test saving a table to a parquet file."""
    output_file = tmp_path / "network_output.parquet"
    processor.save_table_to_file(processor.network_table_name, str(output_file))

    # Verify the file was created
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_save_to_tmp(processor: InMemoryNetworkProcessor) -> None:
    """Test saving a table to a temporary parquet file."""
    tmp_file_path = processor.save_table_to_tmp(processor.network_table_name)

    # Verify the file was created
    from pathlib import Path

    tmp_file = Path(tmp_file_path)
    assert tmp_file.exists()
    assert tmp_file.stat().st_size > 0


def test_concurrent_access(network_file: str) -> None:
    """Test that multiple processors can be created and used concurrently safely."""
    import concurrent.futures

    from goatlib.analysis.network.network_processor import (
        InMemoryNetworkParams,
        InMemoryNetworkProcessor,
    )

    def create_processor_and_get_stats() -> dict:
        # Each thread gets its own processor instance with its own connection
        params = InMemoryNetworkParams(network_path=str(network_file))
        with InMemoryNetworkProcessor(params) as proc:
            return proc.get_network_stats()

    # Use a smaller number of workers to avoid resource exhaustion
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(create_processor_and_get_stats) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Verify all processors got consistent results
    for stats in results:
        assert stats["edge_count"] > 0

    # All results should be identical since they're loading the same file
    edge_counts = [stats["edge_count"] for stats in results]
    assert (
        len(set(edge_counts)) == 1
    ), "All processors should report the same edge count"
