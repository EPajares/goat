"""Aggregate Points Tool.

This module provides a tool for aggregating point features onto polygons or H3 grids,
computing statistics like count, sum, mean, min, or max of point attributes.
"""

import logging
from pathlib import Path
from typing import List, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.aggregate import (
    AggregatePointsParams,
    AggregationAreaType,
)
from goatlib.io.parquet import write_optimized_parquet
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class AggregatePointsTool(AnalysisTool):
    """Tool for aggregating point features onto polygons or H3 grids.

    This tool performs spatial aggregation of point data, similar to GOAT Core's
    aggregate_point functionality. It supports:
    - Aggregation onto polygon layers (spatial join)
    - Aggregation onto H3 hexagonal grids
    - Statistical operations: count, sum, mean, min, max
    - Optional grouping by field(s) in the source layer

    Example:
        tool = AggregatePointsTool()
        results = tool.run(AggregatePointsParams(
            source_path="/data/points.parquet",
            area_type="polygon",
            area_layer_path="/data/districts.parquet",
            column_statistics=ColumnStatistic(operation="sum", field="population"),
            output_path="/data/aggregated.parquet",
        ))
    """

    def __init__(self: Self, db_path: Path | None = None) -> None:
        """Initialize the aggregate points tool."""
        super().__init__(db_path=db_path)
        self._setup_h3_extension()

    def _setup_h3_extension(self: Self) -> None:
        """Install H3 extension for hexagonal grid support."""
        self.con.execute("INSTALL h3 FROM community; LOAD h3;")
        logger.debug("H3 extension loaded.")

    def _run_implementation(
        self: Self, params: AggregatePointsParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Execute point aggregation.

        Args:
            params: Aggregation parameters

        Returns:
            List containing tuple of (output_path, metadata)
        """
        logger.info(
            "Starting point aggregation: source=%s, area_type=%s",
            params.source_path,
            params.area_type.value,
        )

        # Import source point layer
        source_meta, source_view = self.import_input(params.source_path, "source_data")
        source_geom = source_meta.geometry_column

        if not source_geom:
            raise ValueError(
                f"Could not detect geometry column for source: {params.source_path}"
            )

        # Validate source geometry types
        self.validate_geometry_types(
            source_view,
            source_geom,
            params.accepted_source_geometry_types,
            "source",
        )

        # Get CRS from source metadata
        crs = source_meta.crs
        if crs:
            crs_str = crs.to_string()
        else:
            crs_str = params.output_crs or "EPSG:4326"
            logger.warning(
                "Could not detect CRS for %s, using fallback: %s",
                params.source_path,
                crs_str,
            )

        # Define output path
        if not params.output_path:
            params.output_path = str(
                Path(params.source_path).parent
                / f"{Path(params.source_path).stem}_aggregated.parquet"
            )
        output_path = Path(params.output_path)

        # Execute aggregation based on area type
        if params.area_type == AggregationAreaType.polygon:
            self._aggregate_to_polygon(params, source_view, source_geom)
        else:
            self._aggregate_to_h3(params, source_view, source_geom)

        # Export results
        write_optimized_parquet(
            self.con,
            "aggregation_result",
            output_path,
            geometry_column="geometry",
        )

        logger.info("Aggregation completed. Output: %s", output_path)

        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            format="geoparquet",
            geometry_type="Polygon",
            crs=crs_str,
        )

        return [(output_path, metadata)]

    def _aggregate_to_polygon(
        self: Self,
        params: AggregatePointsParams,
        source_view: str,
        source_geom: str,
    ) -> None:
        """Aggregate points onto polygon layer.

        Args:
            params: Aggregation parameters
            source_view: Name of the source points view
            source_geom: Name of the source geometry column
        """
        # Import area layer
        area_meta, area_view = self.import_input(params.area_layer_path, "area_data")
        area_geom = area_meta.geometry_column

        if not area_geom:
            raise ValueError(
                f"Could not detect geometry column for area layer: {params.area_layer_path}"
            )

        # Validate area geometry types
        self.validate_geometry_types(
            area_view,
            area_geom,
            params.accepted_area_geometry_types,
            "area",
        )

        # Get statistics SQL and result column name
        stats_field = params.column_statistics.field
        stats_operation = params.column_statistics.operation
        stats_sql = self.get_statistics_sql(
            f"s.{stats_field}" if stats_field else "",
            stats_operation.value,
        )
        # Column name: "count" for count, otherwise "{operation}_{field}"
        if stats_operation.value == "count":
            result_col = "count"
        else:
            result_col = (
                f"{stats_operation.value}_{stats_field}"
                if stats_field
                else stats_operation.value
            )

        # Get all columns from area layer except geometry and bbox
        area_columns = self.con.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{area_view}'
            AND column_name != '{area_geom}'
            AND column_name != 'bbox'
        """).fetchall()
        area_col_names = [col[0] for col in area_columns]

        # Create a table with row IDs from area layer for joining
        self.con.execute(f"""
            CREATE OR REPLACE TEMP TABLE area_with_id AS
            SELECT
                ROW_NUMBER() OVER () AS area_id,
                *
            FROM {area_view}
        """)

        if params.group_by_field:
            # Build group by columns expression
            group_cols = ", ".join([f"s.{col}" for col in params.group_by_field])
            group_col_concat = " || '_' || ".join(
                [f"CAST(s.{col} AS VARCHAR)" for col in params.group_by_field]
            )

            # First compute stats grouped by area and group_by_field
            self.con.execute(f"""
                CREATE OR REPLACE TEMP TABLE grouped_stats AS
                SELECT
                    a.area_id,
                    {group_col_concat} AS group_name,
                    {stats_sql} AS stats
                FROM area_with_id a
                JOIN {source_view} s
                ON ST_Intersects(a.{area_geom}, s.{source_geom})
                GROUP BY a.area_id, {group_cols}
            """)

            # Aggregate into JSON object per area
            self.con.execute("""
                CREATE OR REPLACE TEMP TABLE grouped_json AS
                SELECT
                    area_id,
                    JSON_GROUP_OBJECT(group_name, stats) AS grouped_stats
                FROM grouped_stats
                GROUP BY area_id
            """)

            # Compute total stats per area
            self.con.execute(f"""
                CREATE OR REPLACE TEMP TABLE total_stats AS
                SELECT
                    a.area_id,
                    {stats_sql} AS total_stats
                FROM area_with_id a
                JOIN {source_view} s
                ON ST_Intersects(a.{area_geom}, s.{source_geom})
                GROUP BY a.area_id
            """)

            # Join everything together - quote column names for special characters
            area_select_with_prefix = ", ".join(
                [f'a."{col}"' for col in area_col_names]
            )
            self.con.execute(f"""
                CREATE OR REPLACE TABLE aggregation_result AS
                SELECT
                    a.{area_geom} AS geom,
                    {area_select_with_prefix},
                    COALESCE(t.total_stats, 0) AS {result_col},
                    g.grouped_stats AS {result_col}_grouped
                FROM area_with_id a
                LEFT JOIN total_stats t ON a.area_id = t.area_id
                LEFT JOIN grouped_json g ON a.area_id = g.area_id
            """)
        else:
            # Simple aggregation without grouping
            self.con.execute(f"""
                CREATE OR REPLACE TEMP TABLE total_stats AS
                SELECT
                    a.area_id,
                    {stats_sql} AS total_stats
                FROM area_with_id a
                JOIN {source_view} s
                ON ST_Intersects(a.{area_geom}, s.{source_geom})
                GROUP BY a.area_id
            """)

            # Quote column names for special characters
            area_select_with_prefix = ", ".join(
                [f'a."{col}"' for col in area_col_names]
            )
            self.con.execute(f"""
                CREATE OR REPLACE TABLE aggregation_result AS
                SELECT
                    a.{area_geom} AS geom,
                    {area_select_with_prefix},
                    COALESCE(t.total_stats, 0) AS {result_col}
                FROM area_with_id a
                LEFT JOIN total_stats t ON a.area_id = t.area_id
            """)

        logger.info("Polygon aggregation completed")

    def _aggregate_to_h3(
        self: Self,
        params: AggregatePointsParams,
        source_view: str,
        source_geom: str,
    ) -> None:
        """Aggregate points onto H3 hexagonal grid.

        Args:
            params: Aggregation parameters
            source_view: Name of the source points view
            source_geom: Name of the source geometry column
        """
        h3_resolution = params.h3_resolution

        # Get statistics SQL and result column name
        stats_field = params.column_statistics.field
        stats_operation = params.column_statistics.operation
        stats_sql = self.get_statistics_sql(
            stats_field if stats_field else "",
            stats_operation.value,
        )
        # Column name: "count" for count, otherwise "{operation}_{field}"
        if stats_operation.value == "count":
            result_col = "count"
        else:
            result_col = (
                f"{stats_operation.value}_{stats_field}"
                if stats_field
                else stats_operation.value
            )

        if params.group_by_field:
            # Build group by columns expression
            group_cols = ", ".join(params.group_by_field)
            group_col_concat = " || '_' || ".join(
                [f"CAST({col} AS VARCHAR)" for col in params.group_by_field]
            )

            # First compute stats grouped by H3 cell and group_by_field
            self.con.execute(f"""
                CREATE OR REPLACE TEMP TABLE grouped_stats AS
                SELECT
                    h3_latlng_to_cell(
                        ST_Y(ST_Centroid({source_geom})),
                        ST_X(ST_Centroid({source_geom})),
                        {h3_resolution}
                    ) AS h3_index,
                    {group_col_concat} AS group_name,
                    {stats_sql} AS stats
                FROM {source_view}
                GROUP BY h3_latlng_to_cell(
                    ST_Y(ST_Centroid({source_geom})),
                    ST_X(ST_Centroid({source_geom})),
                    {h3_resolution}
                ), {group_cols}
            """)

            # Aggregate into JSON object per H3 cell
            self.con.execute("""
                CREATE OR REPLACE TEMP TABLE grouped_json AS
                SELECT
                    h3_index,
                    JSON_GROUP_OBJECT(group_name, stats) AS grouped_stats
                FROM grouped_stats
                GROUP BY h3_index
            """)

            # Compute total stats per H3 cell
            self.con.execute(f"""
                CREATE OR REPLACE TEMP TABLE total_stats AS
                SELECT
                    h3_latlng_to_cell(
                        ST_Y(ST_Centroid({source_geom})),
                        ST_X(ST_Centroid({source_geom})),
                        {h3_resolution}
                    ) AS h3_index,
                    {stats_sql} AS total_stats
                FROM {source_view}
                GROUP BY h3_latlng_to_cell(
                    ST_Y(ST_Centroid({source_geom})),
                    ST_X(ST_Centroid({source_geom})),
                    {h3_resolution}
                )
            """)

            # Join and create H3 polygon geometries
            self.con.execute(f"""
                CREATE OR REPLACE TABLE aggregation_result AS
                SELECT
                    ST_GeomFromText(h3_cell_to_boundary_wkt(t.h3_index)) AS geom,
                    h3_h3_to_string(t.h3_index) AS h3_{h3_resolution},
                    t.total_stats AS {result_col},
                    g.grouped_stats AS {result_col}_grouped
                FROM total_stats t
                LEFT JOIN grouped_json g ON t.h3_index = g.h3_index
            """)
        else:
            # Simple aggregation without grouping
            self.con.execute(f"""
                CREATE OR REPLACE TEMP TABLE total_stats AS
                SELECT
                    h3_latlng_to_cell(
                        ST_Y(ST_Centroid({source_geom})),
                        ST_X(ST_Centroid({source_geom})),
                        {h3_resolution}
                    ) AS h3_index,
                    {stats_sql} AS total_stats
                FROM {source_view}
                GROUP BY h3_latlng_to_cell(
                    ST_Y(ST_Centroid({source_geom})),
                    ST_X(ST_Centroid({source_geom})),
                    {h3_resolution}
                )
            """)

            # Create H3 polygon geometries
            self.con.execute(f"""
                CREATE OR REPLACE TABLE aggregation_result AS
                SELECT
                    ST_GeomFromText(h3_cell_to_boundary_wkt(h3_index)) AS geom,
                    h3_h3_to_string(h3_index) AS h3_{h3_resolution},
                    total_stats AS {result_col}
                FROM total_stats
            """)

        logger.info("H3 aggregation completed at resolution %d", h3_resolution)
