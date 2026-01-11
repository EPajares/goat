import logging
import uuid
from typing import Any, Dict

from goatlib.analysis.core.base import AnalysisTool
from goatlib.io.parquet import write_optimized_parquet
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

    def __enter__(self) -> "InMemoryNetworkProcessor":
        """Enters the context, loading the network and returning the processor instance."""
        self._load_network()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exits the context, automatically cleaning up all database resources."""
        super().cleanup()

    def _load_network(self) -> str:
        """Loads the network from Parquet and converts geometry to a native type."""
        if self._is_loaded:
            return self.network_table_name

        self.con.execute(f"""
            CREATE TABLE {self.network_table_name} AS
            SELECT edge_id, source, target, length_m, cost, ST_GeomFromText(geometry) as geometry
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

    def get_available_tables(self) -> list[str]:
        """Get list of available table names in the database."""
        tables = self.con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        return [table[0] for table in tables]

    def apply_sql_query(self, sql_query: str) -> str:
        """Applies SQL and returns a NEW table, without destroying the input."""
        self._ensure_loaded()
        result_table = self._generate_table_name("query_result")
        # WARNING: This does not sanitize input SQL - use with caution. Add validation as needed.
        self.con.execute(f"CREATE TABLE {result_table} AS {sql_query}")
        return result_table

    def split_edge_at_point(
        self,
        latitude: float,
        longitude: float,
        base_table: str = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Finds the closest edge to a point, splits it, and creates a new network table
        using DuckDB's spatial extension.

        This version uses CTEs instead of a temporary table to simplify the SQL
        and reduce database interactions.
        """
        self._ensure_loaded()
        source_table = base_table or self.network_table_name
        split_table_name = self._generate_table_name("split_network")
        new_node_id = f"split_node_{uuid.uuid4().hex[:8]}"
        point_geom = f"ST_Point({longitude}, {latitude})"

        # Create the split network table using a single CTE-based query
        split_query = f"""
        CREATE TABLE {split_table_name} AS
        WITH closest_edge AS (
            -- Find the single edge closest to the split point and calculate split position
            SELECT
                *,
                ST_LineLocatePoint(geometry, {point_geom}) as split_fraction
            FROM {source_table}
            ORDER BY ST_Distance(geometry, {point_geom}) ASC
            LIMIT 1
        ),
        new_split_parts AS (
            -- Create two new edge segments from the original edge at the split point
            -- Part A: from original source to new split node
            SELECT
                edge_id || '_part_a' as edge_id,
                source,
                '{new_node_id}' as target,
                length_m * split_fraction AS length_m,
                cost * split_fraction AS cost,
                ST_LineSubstring(geometry, 0.0, split_fraction) as geometry
            FROM closest_edge
            WHERE split_fraction > 1e-9 -- Only create if split point is not at start

            UNION ALL

            -- Part B: from new split node to original target
            SELECT
                edge_id || '_part_b' as edge_id,
                '{new_node_id}' as source,
                target,
                length_m * (1.0 - split_fraction) AS length_m,
                cost * (1.0 - split_fraction) AS cost,
                ST_LineSubstring(geometry, split_fraction, 1.0) as geometry
            FROM closest_edge
            WHERE split_fraction < 1.0 - 1e-9 -- Only create if split point is not at end
        )
        -- Combine all unchanged edges with the new split edge parts
        SELECT edge_id, source, target, length_m, cost, geometry FROM {source_table}
        WHERE edge_id <> (SELECT edge_id FROM closest_edge)
        UNION ALL
        SELECT edge_id, source, target, length_m, cost, geometry FROM new_split_parts;
        """
        self.con.execute(split_query)

        # Query to extract information about the split operation
        info_query = f"""
        WITH closest_edge AS (
            -- Re-find the closest edge to get split details (stateless approach)
            SELECT
                *,
                ST_LineLocatePoint(geometry, {point_geom}) as split_fraction
            FROM {source_table}
            ORDER BY ST_Distance(geometry, {point_geom}) ASC
            LIMIT 1
        )
        SELECT
            edge_id,                                                             -- Original edge ID
            split_fraction,                                                      -- Position along edge (0.0 to 1.0)
            ST_X(ST_LineInterpolatePoint(geometry, split_fraction)) as lon,      -- Longitude of split point
            ST_Y(ST_LineInterpolatePoint(geometry, split_fraction)) as lat       -- Latitude of split point
        FROM closest_edge;
        """
        info_res = self.con.execute(info_query).fetchone()

        # Package split operation results
        split_info = {
            "artificial_node_id": new_node_id,
            "original_edge_split": info_res[0],
            "split_fraction": info_res[1],
            "new_node_coords": {
                "lon": info_res[2],
                "lat": info_res[3],
            },
        }

        # The warning logic is adjusted to account for floating point inaccuracies.
        if not (1e-9 < split_info["split_fraction"] < 1.0 - 1e-9):
            logger.warning(
                f"Split point is at or very near an existing node (fraction={split_info['split_fraction']:.6f}). "
                "The original edge was effectively replaced, not split into two new segments."
            )

        return split_table_name, split_info

    def interpolate_long_edges(
        self,
        max_edge_length: float,
        base_table: str = None,
        interpolation_distance: float = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Interpolate nodes along edges that are longer than the specified threshold.
        Creates actual intermediate nodes with coordinates and splits edges accordingly.

        Args:
            max_edge_length: Maximum allowed edge length in meters
            base_table: Table to process (defaults to main network table)
            interpolation_distance: Distance between interpolated points (defaults to max_edge_length/2)

        Returns:
            Tuple of (table_name, interpolation_info) where interpolation_info contains
            statistics about the interpolation process
        """
        import time

        start_time = time.time()
        self._ensure_loaded()
        source_table = base_table or self.network_table_name
        interpolated_table = self._generate_table_name("interpolated_network")

        # Default interpolation distance
        if interpolation_distance is None:
            interpolation_distance = max_edge_length / 2

        interpolation_query = f"""
        CREATE TABLE {interpolated_table} AS
        WITH long_edges AS (
            -- Identify edges that need interpolation and calculate segments needed
            SELECT *,
                   CAST(CEIL(length_m / {interpolation_distance}) AS INTEGER) as num_segments
            FROM {source_table}
            WHERE length_m > {max_edge_length}
        ),
        interpolated_segments AS (
            -- Generate new edges with intermediate nodes
            SELECT 
                edge_id || '_seg_' || CAST(segment_id AS VARCHAR) as edge_id,
                CASE 
                    WHEN segment_id = 1 THEN CAST(source AS VARCHAR)
                    ELSE 'interp_' || edge_id || '_' || CAST((segment_id - 1) AS VARCHAR)
                END as source,
                CASE 
                    WHEN segment_id = num_segments THEN CAST(target AS VARCHAR)
                    ELSE 'interp_' || edge_id || '_' || CAST(segment_id AS VARCHAR)
                END as target,
                length_m / num_segments as length_m,
                cost / num_segments as cost,
                ST_LineSubstring(
                    geometry, 
                    (segment_id - 1.0) / num_segments, 
                    segment_id / num_segments
                ) as geometry
            FROM long_edges
            CROSS JOIN generate_series(1, num_segments) as t(segment_id)
        )
        -- Combine short edges (unchanged) with interpolated segments
        SELECT edge_id, source, target, length_m, cost, geometry
        FROM {source_table}
        WHERE length_m <= {max_edge_length}

        UNION ALL

        SELECT edge_id, source, target, length_m, cost, geometry
        FROM interpolated_segments
        ORDER BY edge_id;
        """

        self.con.execute(interpolation_query)

        processing_time = time.time() - start_time

        # Get interpolation statistics
        stats_query = f"""
        WITH original_stats AS (
            SELECT 
                COUNT(*) as original_edges,
                COUNT(*) FILTER (WHERE length_m > {max_edge_length}) as long_edges_count
            FROM {source_table}
        ),
        new_stats AS (
            SELECT COUNT(*) as new_edges FROM {interpolated_table}
        ),
        node_stats AS (
            SELECT 
                COUNT(DISTINCT source) + COUNT(DISTINCT target) as total_nodes,
                COUNT(DISTINCT source) FILTER (WHERE source LIKE 'interp_%') + 
                COUNT(DISTINCT target) FILTER (WHERE target LIKE 'interp_%') as new_nodes
            FROM {interpolated_table}
        )
        SELECT 
            o.original_edges,
            o.long_edges_count,
            n.new_edges,
            ns.new_nodes,
            ns.total_nodes
        FROM original_stats o, new_stats n, node_stats ns;
        """

        stats_result = self.con.execute(stats_query).fetchone()

        interpolation_info = {
            "original_edge_count": stats_result[0],
            "long_edges_processed": stats_result[1],
            "final_edge_count": stats_result[2],
            "new_intermediate_nodes": stats_result[3],
            "total_nodes": stats_result[4],
            "max_edge_length_threshold": max_edge_length,
            "interpolation_distance": interpolation_distance,
            "processing_time_seconds": processing_time,
        }

        return interpolated_table, interpolation_info

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
        write_optimized_parquet(
            self.con,
            table_name,
            output_path,
            geometry_column="geometry",
        )

    def save_table_to_tmp(self, table_name: str) -> str:
        """Save table to a temporary parquet file and return the path."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
            output_path = tmp_file.name
        self.save_table_to_file(table_name, output_path)
        return output_path
