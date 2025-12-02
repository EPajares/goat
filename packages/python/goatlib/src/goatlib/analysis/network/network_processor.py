import logging
from pathlib import Path
from typing import Dict, List, Self, Tuple, Union

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.network import NetworkProcessorParams
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class NetworkProcessor(AnalysisTool):
    """
    Unified network processor that handles both basic network loading
    and artificial edge creation in a single tool.
    """

    def _run_implementation(
        self: Self, params: NetworkProcessorParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Process network data with optional artificial edge creation."""
        meta, network_table = self.import_input(params.input_path)
        crs_str = meta.crs.to_string() if meta.crs else "EPSG:4326"

        if not meta.geometry_column:
            logger.warning(
                f"No geometry column detected for {params.input_path}, assuming 'geometry'"
            )
        if not meta.crs:
            logger.warning(
                f"No CRS detected for {params.input_path}, assuming 'EPSG:4326'"
            )

        final_table = (
            self._create_enhanced_network(params, network_table)
            if params.creates_artificial_edges
            else network_table
        )

        # Set output path if not provided
        if not params.output_path:
            suffix = "_enhanced" if params.creates_artificial_edges else "_processed"
            params.output_path = str(
                Path(params.input_path).parent
                / f"{Path(params.input_path).stem}{suffix}.parquet"
            )
        output_path = Path(params.output_path)

        # Execute final SQL and save
        self._execute_sql_and_save(params, final_table, output_path)

        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            format="geoparquet",
            crs=crs_str or params.output_crs,
            geometry_type="LineString",
        )

        return [(output_path, metadata)]

    def _create_enhanced_network(
        self: Self, params: NetworkProcessorParams, network_table: str
    ) -> str:
        """Create enhanced network with artificial edges."""
        _, points_table = self.import_input(params.origin_points_path)
        return self._create_enhanced_network_with_points(
            points_table,
            network_table,
            params.buffer_distance,
            params.max_connections_per_point,
            params.artificial_node_id_start,
            params.artificial_edge_id_start,
        )

    def _execute_sql_and_save(
        self: Self,
        params: NetworkProcessorParams,
        table_name: str,
        output_path: Path,
    ) -> None:
        """Execute custom SQL and save results."""
        final_sql = params.custom_sql.replace("v_input", table_name)

        try:
            self.con.execute(
                f"COPY ({final_sql}) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            logger.info(f"Network saved: {output_path}")
        except Exception as e:
            logger.error(f"Failed to process network: {e}")
            raise

    def _create_enhanced_network_temporary(
        self,
        origin_points: Union[str, Path],
        network_edges: Union[str, Path],
        buffer_distance: float = 100.0,
        max_connections_per_point: int = 3,
        artificial_node_id_start: int = 1_000_000_000,
        artificial_edge_id_start: int = 2_000_000_000,
    ) -> str:
        """Create temporary enhanced network for routing operations."""
        if isinstance(origin_points, (str, Path)):
            _, points_table = self.import_input(origin_points)
        else:
            points_table = "origin_points"
            self.con.register(points_table, origin_points)

        if isinstance(network_edges, (str, Path)):
            _, edges_table = self.import_input(network_edges)
        else:
            edges_table = "network_edges"
            self.con.register(edges_table, network_edges)

        return self._create_enhanced_network_with_points(
            points_table,
            edges_table,
            buffer_distance,
            max_connections_per_point,
            artificial_node_id_start,
            artificial_edge_id_start,
        )

    def _create_enhanced_network_with_points(
        self,
        points_table: str,
        network_table: str,
        buffer_distance: float,
        max_connections_per_point: int,
        artificial_node_id_start: int,
        artificial_edge_id_start: int,
    ) -> str:
        """Create enhanced network with artificial edges."""
        enhanced_table_name = "enhanced_network"

        # Step 1: Find nearest edges for each point
        self._create_nearest_edges_table(points_table, network_table, buffer_distance)

        # Step 2: Limit connections per point
        self._create_ranked_connections_table(max_connections_per_point)

        # Step 3: Create artificial connector edges
        self._create_artificial_connectors_table(
            artificial_node_id_start, artificial_edge_id_start
        )

        # Step 4: Combine original and artificial edges
        self._create_combined_network_table(network_table, enhanced_table_name)

        return enhanced_table_name

    def _create_nearest_edges_table(
        self, points_table: str, network_table: str, buffer_distance: float
    ):
        """Create table with nearest edges for each point."""
        sql = f"""
        CREATE OR REPLACE TABLE nearest_edges AS
        SELECT 
            op.id as origin_id,
            op.geom as origin_geom,
            ne.id as edge_id,
            ne.geom as edge_geom,
            ne.source,
            ne.target,
            ST_Distance(op.geom, ne.geom) as distance,
            ST_ClosestPoint(ne.geom, op.geom) as connection_point,
            ST_LineLocatePoint(ne.geom, ST_ClosestPoint(ne.geom, op.geom)) as edge_fraction,
            ROW_NUMBER() OVER (
                PARTITION BY op.id 
                ORDER BY ST_Distance(op.geom, ne.geom)
            ) as rank
        FROM {points_table} op
        JOIN {network_table} ne ON ST_DWithin(op.geom, ne.geom, {buffer_distance})
        """
        self.con.execute(sql)

    def _create_ranked_connections_table(self, max_connections_per_point: int):
        """Create table with limited connections per point."""
        sql = f"""
        CREATE OR REPLACE TABLE ranked_connections AS
        SELECT * FROM nearest_edges WHERE rank <= {max_connections_per_point}
        """
        self.con.execute(sql)

    def _create_artificial_connectors_table(
        self, artificial_node_id_start: int, artificial_edge_id_start: int
    ):
        """Create artificial connector edges table."""
        sql = f"""
        CREATE OR REPLACE TABLE artificial_connectors AS
        WITH connector_geoms AS (
            SELECT *,
                ST_MakeLine(origin_geom, connection_point) as connector_geom,
                ST_Length(ST_MakeLine(origin_geom, connection_point)) as connector_length
            FROM ranked_connections
        )
        SELECT
            {artificial_edge_id_start} + origin_id * 1000 + rank as id,
            {artificial_node_id_start} + origin_id as source,
            {artificial_node_id_start} + 1000000 + edge_id + 
                CAST(edge_fraction * 1000 AS INTEGER) as target,
            connector_geom as geom,
            connector_length as length_m,
            (connector_length / 1000.0) / 5.0 * 60.0 as cost,
            (connector_length / 1000.0) / 5.0 * 60.0 as reverse_cost,
            'artificial' as edge_type
        FROM connector_geoms
        WHERE connector_length > 0.1
        """
        self.con.execute(sql)

    def _create_combined_network_table(
        self, network_table: str, enhanced_table_name: str
    ):
        """Combine original network with artificial edges."""
        sql = f"""
        CREATE OR REPLACE TABLE {enhanced_table_name} AS
        SELECT 
            id, source, target, geom,
            COALESCE(length_m, ST_Length(geom)) as length_m,
            COALESCE(cost, ST_Length(geom) / 1000.0 / 5.0 * 60.0) as cost,
            COALESCE(reverse_cost, cost) as reverse_cost,
            COALESCE(edge_type, 'original') as edge_type
        FROM {network_table}
        UNION ALL
        SELECT id, source, target, geom, length_m, cost, reverse_cost, edge_type
        FROM artificial_connectors
        """
        self.con.execute(sql)


# Convenience functions
def process_network(
    input_file: str,
    custom_sql: str,
    output_file: str = None,
    origin_points_file: str = None,
    buffer_distance: float = 100.0,
    **kwargs,
) -> str:
    """Unified network processing with optional artificial edges."""
    params = NetworkProcessorParams(
        input_path=input_file,
        output_path=output_file,
        custom_sql=custom_sql,
        origin_points_path=origin_points_file,
        buffer_distance=buffer_distance,
        **kwargs,
    )

    tool = NetworkProcessor()
    results = tool.run(params)
    return str(results[0][0])


# Backward compatibility functions
def load_network(input_file: str, custom_sql: str, output_file: str = None) -> str:
    """Load network data from file (backward compatibility)."""
    return process_network(
        input_file=input_file, custom_sql=custom_sql, output_file=output_file
    )


def load_network_with_connectors(
    network_file: str,
    points_file: str,
    custom_sql: str,
    output_file: str = None,
    buffer_distance: float = 100.0,
) -> str:
    """Load network with artificial connectors (backward compatibility)."""
    return process_network(
        input_file=network_file,
        custom_sql=custom_sql,
        output_file=output_file,
        origin_points_file=points_file,
        buffer_distance=buffer_distance,
    )


# Point connector creation function
def create_temporary_enhanced_network(
    origin_points: Union[str, Path],
    network_edges: Union[str, Path],
    buffer_distance: float = 100.0,
) -> str:
    """Create temporary enhanced network with artificial connector edges."""
    processor = NetworkProcessor()
    enhanced_table_name = processor._create_enhanced_network_temporary(
        origin_points=origin_points,
        network_edges=network_edges,
        buffer_distance=buffer_distance,
    )

    return enhanced_table_name


def analyze_point_connectivity(
    origin_points: Union[str, Path],
    network_edges: Union[str, Path],
    buffer_distance: float = 100.0,
) -> Dict[str, int]:
    """Analyze connectivity between points and network."""
    processor = NetworkProcessor()
    _, points_table = processor.import_input(origin_points)
    _, network_table = processor.import_input(network_edges)

    # Analyze connectivity using managed connection
    stats_query = f"""
    WITH connectivity AS (
        SELECT 
            p.geom as point_geom,
            COUNT(n.geom) as nearby_edges
        FROM {points_table} p
        LEFT JOIN {network_table} n ON ST_DWithin(p.geom, n.geom, {buffer_distance})
        GROUP BY p.geom
    )
    SELECT 
        COUNT(*) as total_points,
        SUM(CASE WHEN nearby_edges > 0 THEN 1 ELSE 0 END) as connectable_points,
        SUM(CASE WHEN nearby_edges = 0 THEN 1 ELSE 0 END) as isolated_points,
        AVG(nearby_edges) as avg_nearby_edges,
        MAX(nearby_edges) as max_nearby_edges
    FROM connectivity
    """

    result = processor.con.execute(stats_query).fetchone()

    stats = {
        "total_points": int(result[0]) if result[0] else 0,
        "connectable_points": int(result[1]) if result[1] else 0,
        "isolated_points": int(result[2]) if result[2] else 0,
        "avg_nearby_edges": float(result[3]) if result[3] else 0.0,
        "max_nearby_edges": int(result[4]) if result[4] else 0,
    }

    return stats
