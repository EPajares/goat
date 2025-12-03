import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.models.io import DatasetMetadata
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class InMemoryNetworkParams(BaseModel):
    network_path: str = Field(..., description="Path to the network file")


class InMemoryNetworkProcessor(AnalysisTool):
    """
    High-performance in-memory network processor for routing.

    The recommended usage is via the context manager pattern, which guarantees
    that all resources are safely cleaned up.

    Example:
        params = InMemoryNetworkParams(network_path="/path/to/network.parquet")
        with InMemoryNetworkProcessor(params) as proc:
            # The network is loaded and ready.
            # ... perform operations on the network ...
    """

    def __init__(self, params: InMemoryNetworkParams):
        """Initializes the processor. Requires network parameters to be valid."""
        super().__init__(db_path=":memory:")
        self.params = params
        self.network_table_name = "in_memory_network"
        self._is_loaded = False
        self.geometry_column = (
            "geometry"  # For simplicity, assuming a fixed schema name.
        )

    def __enter__(self):
        """Enters the context, loading the network and returning the processor instance."""
        self._load_network()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exits the context, automatically cleaning up all database resources."""
        super().cleanup()

    def _load_network(self) -> str:
        """Loads the network from Parquet and converts geometry to a native type."""
        if self._is_loaded:
            return self.network_table_name

        self.con.execute(f"""
            CREATE TABLE {self.network_table_name} AS
            SELECT edge_id, source, target, length_m, cost, ST_GeomFromText({self.geometry_column}) as {self.geometry_column}
            FROM read_parquet('{self.params.network_path}')
        """)
        self._is_loaded = True
        return self.network_table_name

    def _ensure_loaded(self) -> None:
        if not self._is_loaded:
            self._load_network()

    def _generate_table_name(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def cleanup_intermediate_tables(self) -> None:
        """
        Explicitly cleans all generated tables, keeping only the original network table.
        This allows for manual memory management during long, complex workflows.
        """
        all_tables = self.con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        for (table_name,) in all_tables:
            # Do not drop the main table or DuckDB's internal spatial reference table
            if table_name not in [self.network_table_name, "spatial_ref_sys"]:
                self.con.execute(f"DROP TABLE IF EXISTS {table_name}")
        logger.info(f"Cleaned up intermediate tables. Kept: {self.network_table_name}")

    def apply_sql_query(self, sql_query: str, base_table: str = None) -> str:
        """Applies SQL and returns a NEW table, without destroying the input."""
        self._ensure_loaded()
        result_table = self._generate_table_name("query_result")
        source_table = base_table or self.network_table_name
        processed_query = sql_query.replace("network", source_table)
        self.con.execute(f"CREATE TABLE {result_table} AS {processed_query}")
        return result_table

    def split_edge_at_point(
        self,
        latitude: float,
        longitude: float,
        base_table: str = None,
    ) -> tuple[str, dict[str, Any]]:
        self._ensure_loaded()
        source_table = base_table or self.network_table_name
        split_table_name = self._generate_table_name("split_network")
        new_node_id = f"split_node_{uuid.uuid4().hex[:8]}"

        # Find closest edge and split it
        closest_edge_query = f"""
        CREATE TEMP TABLE closest_edge AS
        SELECT *, 
               ST_Distance({self.geometry_column}, ST_Point({longitude}, {latitude})) as distance,
               ST_LineLocatePoint({self.geometry_column}, ST_Point({longitude}, {latitude})) as split_fraction
        FROM {source_table}
        ORDER BY distance ASC
        LIMIT 1
        """
        self.con.execute(closest_edge_query)

        # Create the split network
        split_query = f"""
        CREATE TABLE {split_table_name} AS
        WITH new_split_edges AS (
            SELECT
                edge_id || '_part_a' as edge_id, source, '{new_node_id}' as target,
                length_m * split_fraction AS length_m, cost * split_fraction AS cost,
                ST_LineSubstring({self.geometry_column}, 0.0, split_fraction) as {self.geometry_column}
            FROM closest_edge
            WHERE split_fraction > 0.0
            UNION ALL
            SELECT
                edge_id || '_part_b' as edge_id, '{new_node_id}' as source, target,
                length_m * (1.0 - split_fraction) AS length_m, cost * (1.0 - split_fraction) AS cost,
                ST_LineSubstring({self.geometry_column}, split_fraction, 1.0) as {self.geometry_column}
            FROM closest_edge
            WHERE split_fraction < 1.0
        ),
        unchanged_edges AS (
            SELECT edge_id, source, target, length_m, cost, {self.geometry_column} FROM {source_table}
            WHERE edge_id != (SELECT edge_id FROM closest_edge)
        )
        SELECT edge_id, source, target, length_m, cost, {self.geometry_column} FROM unchanged_edges 
        UNION ALL 
        SELECT edge_id, source, target, length_m, cost, {self.geometry_column} FROM new_split_edges
        """
        self.con.execute(split_query)

        # Get split info
        info_res = self.con.execute("""
            SELECT edge_id, split_fraction,
                   ST_X(ST_LineInterpolatePoint(geometry, split_fraction)) as lon,
                   ST_Y(ST_LineInterpolatePoint(geometry, split_fraction)) as lat
            FROM closest_edge
        """).fetchone()

        # Clean up temp table
        self.con.execute("DROP TABLE closest_edge")

        split_info = {
            "artificial_node_id": new_node_id,
            "original_edge_split": info_res[0],
            "split_fraction": info_res[1],
            "new_node_coords": {"lon": info_res[2], "lat": info_res[3]},
        }
        return split_table_name, split_info

    # ... other methods like save_table_to_file, get_network_stats etc.
    def get_network_stats(self, table_name: str = None) -> Dict[str, Any]:
        """Get basic statistics about the network."""
        target_table = table_name or self.network_table_name

        result = self.con.execute(f"""
            SELECT
                COUNT(*) as edge_count,
                SUM(length_m) as total_length_m,
                AVG(length_m) as avg_length_m,
                MIN(length_m) as min_length_m,
                MAX(length_m) as max_length_m
            FROM {target_table}
        """).fetchone()

        return {
            "edge_count": result[0],
            "total_length_m": float(result[1]) if result[1] else 0,
            "avg_length_m": float(result[2]) if result[2] else 0,
            "min_length_m": float(result[3]) if result[3] else 0,
            "max_length_m": float(result[4]) if result[4] else 0,
        }

    def save_table_to_file(self, table_name: str, output_path: str) -> None:
        """Save table to parquet file."""
        self.con.execute(
            f"COPY {table_name} TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )


# ==================== CONVENIENCE FUNCTIONS ====================


def create_in_memory_network(network_path: str) -> InMemoryNetworkProcessor:
    """Create in-memory network processor. Don't forget to call cleanup() when done."""
    params = InMemoryNetworkParams(network_path=network_path)
    processor = InMemoryNetworkProcessor(params)
    processor._load_network()
    return processor


def process_network_with_sql(
    network_path: str, sql_query: str, output_path: str
) -> List[Tuple[Path, DatasetMetadata]]:
    """Process network with SQL query and save results."""
    params = InMemoryNetworkParams(
        network_path=network_path, sql_query=sql_query, output_path=output_path
    )
    processor = InMemoryNetworkProcessor()
    return processor.run(params)


def process_and_save_results(
    network_path: str,
    operations: List[Dict[str, Any]],
    output_dir: str,
) -> Dict[str, str]:
    """Process network with operations and save results."""
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create processor and load network
    params = InMemoryNetworkParams(network_path=network_path)
    processor = InMemoryNetworkProcessor(params)
    processor._load_network()

    # Process operations sequentially
    current_table = processor.network_table_name
    for op in operations:
        if op["type"] == "filter":
            filter_sql = f"SELECT * FROM network WHERE {op['condition']}"
            current_table = processor.apply_sql_query(
                filter_sql, base_table=current_table
            )
        elif op["type"] == "split_at_point":
            current_table, _ = processor.split_edge_at_point(
                op["lat"], op["lon"], base_table=current_table
            )
        elif op["type"] == "transform":
            current_table = processor.apply_sql_query(
                op["sql"], base_table=current_table
            )

    # Save results
    saved_files = {}
    base_name = Path(network_path).stem

    network_path_out = os.path.join(output_dir, f"{base_name}_processed.parquet")
    processor.save_table_to_file(current_table, network_path_out)
    saved_files["processed_network"] = network_path_out

    processor.cleanup()
    return saved_files
