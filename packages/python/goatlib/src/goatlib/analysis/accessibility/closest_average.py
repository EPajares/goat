import logging
import uuid
from pathlib import Path
from typing import Self

from goatlib.analysis.accessibility.base import HeatmapToolBase, sanitize_sql_name
from goatlib.analysis.schemas.heatmap import (
    HeatmapClosestAverageParams,
    OpportunityClosestAverage,
)
from goatlib.io.utils import Metadata
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class HeatmapClosestAverageTool(HeatmapToolBase):
    """
    Computes closest average heatmap - average value of the closest features within max cost.
    """

    def _run_implementation(self: Self, params: HeatmapClosestAverageParams) -> Path:
        logger.info("Starting Heatmap Closest Average Analysis")

        # Register OD matrix and detect H3 resolution
        od_table, h3_resolution = self._prepare_od_matrix(
            params.od_matrix_path, params.od_column_map
        )
        logger.info(
            "OD matrix ready: table=%s, h3_resolution=%s", od_table, h3_resolution
        )

        # Process and standardize opportunities using detected resolution
        standardized_tables = self._process_opportunities(
            params.opportunities, h3_resolution
        )

        # Combine all standardized tables using pivot
        unified_table = self._combine_opportunities(standardized_tables)
        logger.info("Unified opportunity table created: %s", unified_table)

        # Extract unique DESTINATION H3 IDs from opportunities
        destination_ids = self._extract_destination_ids(unified_table)
        if not destination_ids:
            raise ValueError("No destination IDs found in opportunity data")

        logger.info("Found %d unique destination IDs across ", len(destination_ids))

        # Filter OD matrix to only relevant destinations
        filtered_matrix = self._filter_od_matrix(
            od_table, destination_ids=destination_ids
        )

        # Compute closest-average accessibility
        result_table = self._compute_closest_average(
            filtered_matrix, unified_table, standardized_tables
        )
        logger.info("Closest Average table created: %s", result_table)

        # Export results
        output_path = Path(params.output_path)

        logger.info("Heatmap closest average analysis completed successfully")

        result_path = self._export_h3_results(result_table, output_path)

        # Return as list of (path, metadata) tuples for consistency with other tools
        metadata = DatasetMetadata(
            path=str(result_path),
            source_type="vector",
            format="geoparquet",
            geometry_type="Polygon",
            geometry_column="geometry",
        )
        return [(result_path, metadata)]

    def _process_opportunities(
        self: Self, opportunities: list[OpportunityClosestAverage], h3_resolution: int
    ) -> list[tuple[str, str]]:
        """
        Imports and standardizes all opportunity datasets.
        Returns a list of (standardized_table_name, opportunity_name)
        """
        opportunity_tables = []

        for idx, opp in enumerate(opportunities):
            # Use simple table name (internal), keep display name separate
            table_name = f"opp_{idx}"
            display_name = opp.name or Path(opp.input_path).stem

            try:
                # Import into DuckDB and get metadata
                meta, table_name = self.import_input(
                    opp.input_path, table_name=table_name
                )
                logger.info(
                    "Imported '%s' (geometry=%s)", opp.input_path, meta.geometry_type
                )

                # Standardize into canonical schema - these are DESTINATIONS
                std_table = self._prepare_opportunity_table(
                    table_name, meta, opp, h3_resolution
                )
                opportunity_tables.append((std_table, display_name))
                logger.info("Prepared standardized table: %s", std_table)

            except Exception as e:
                logger.error(
                    "Failed to import opportunity dataset '%s': %s", opp.input_path, e
                )
                raise

        return opportunity_tables

    def _prepare_opportunity_table(
        self: Self,
        table_name: str,
        meta: Metadata,
        opp: OpportunityClosestAverage,
        h3_resolution: int,
    ) -> str:
        """
        Converts an imported opportunity dataset into canonical schema.
        These are DESTINATIONS, so we use dest_id instead of orig_id.
        Schema: dest_id, max_cost, n_destinations
        """
        geom_col = meta.geometry_column or "geom"
        geom_type = (meta.geometry_type or "").lower()
        output_table = f"{table_name}_std"

        transform_to_4326 = geom_col
        try:
            if meta.crs and meta.crs.to_epsg() != 4326:
                source_crs = meta.crs.to_string()
                transform_to_4326 = (
                    f"ST_Transform({geom_col}, '{source_crs}', 'EPSG:4326')"
                )
        except Exception:
            pass

        if "point" in geom_type:
            query = f"""
            CREATE OR REPLACE TEMP TABLE {output_table} AS
            WITH features AS (
                SELECT
                    {transform_to_4326} AS geom
                FROM {table_name}
                WHERE {geom_col} IS NOT NULL
            ),
            exploded AS (
                SELECT (UNNEST(ST_Dump(geom))).geom AS simple_geom
                FROM features
            )
            SELECT
                h3_latlng_to_cell(ST_Y(simple_geom), ST_X(simple_geom), {h3_resolution}) AS dest_id,
                {opp.max_cost}::DOUBLE AS max_cost,
                {opp.n_destinations}::INT AS n_destinations
            FROM exploded
            WHERE simple_geom IS NOT NULL
            GROUP BY dest_id
            """
        elif "polygon" in geom_type or "multipolygon" in geom_type:
            query = f"""
            CREATE OR REPLACE TEMP TABLE {output_table} AS
            WITH polygons AS (
                SELECT UNNEST(ST_Dump(ST_Force2D({transform_to_4326}))) AS geom
                FROM {table_name}
                WHERE {geom_col} IS NOT NULL
            ),
            h3_cells AS (
                SELECT
                    UNNEST(h3_polygon_wkt_to_cells_experimental(ST_AsText(geom), {h3_resolution}, 'CONTAINMENT_OVERLAPPING')) AS dest_id
                FROM polygons
                WHERE geom IS NOT NULL
            )
            SELECT
                dest_id,
                {opp.max_cost}::DOUBLE AS max_cost,
                {opp.n_destinations}::INT AS n_destinations
            FROM h3_cells
            WHERE dest_id IS NOT NULL
            GROUP BY dest_id
            """
        else:
            raise ValueError(f"Unsupported geometry type: '{geom_type}'")

        self.con.execute(query)
        return output_table

    def _combine_opportunities(
        self: Self, standardized_tables: list[tuple[str, str]]
    ) -> str:
        """
        Combine standardized opportunity tables using a portable pivot (MAX(CASE ...)).
        Creates columns: {opportunity_name}_max_cost, {opportunity_name}_n_dest
        """
        if not standardized_tables:
            raise ValueError("No standardized opportunity tables to combine")

        union_parts: list[str] = []
        safe_names: list[str] = []
        for idx, (std_table, name) in enumerate(standardized_tables):
            safe_name = sanitize_sql_name(name, idx)

            safe_names.append(safe_name)
            union_parts.append(f"""
                SELECT
                    dest_id,
                    '{safe_name}' as opportunity_type,
                    max_cost,
                    n_destinations
                FROM {std_table}
                WHERE dest_id IS NOT NULL
            """)

        union_query = "\nUNION ALL\n".join(union_parts)

        unified_table = f"opportunity_closest_avg_unified_{uuid.uuid4().hex[:8]}"

        # Build portable pivot using MAX(CASE WHEN ...)
        max_cost_cols = ",\n            ".join(
            f"MAX(CASE WHEN opportunity_type = '{sn}' THEN max_cost END) AS {sn}_max_cost"
            for sn in safe_names
        )
        n_dest_cols = ",\n            ".join(
            f"MAX(CASE WHEN opportunity_type = '{sn}' THEN n_destinations END) AS {sn}_n_dest"
            for sn in safe_names
        )

        query = f"""
            CREATE OR REPLACE TEMP TABLE {unified_table} AS
            SELECT
                dest_id,
                {max_cost_cols},
                {n_dest_cols}
            FROM (
                {union_query}
            ) u
            GROUP BY dest_id
        """

        self.con.execute(query)
        logger.info(
            "Unified opportunity table '%s' created with %d layers",
            unified_table,
            len(standardized_tables),
        )

        schema = self.con.execute(f"DESCRIBE {unified_table}").fetchall()
        logger.info("Unified table schema: %s", [col[0] for col in schema])

        return unified_table

    def _compute_closest_average(
        self: Self,
        filtered_matrix: str,
        unified_table: str,
        standardized_tables: list[tuple[str, str]],
    ) -> str:
        """
        Compute closest-average accessibility using the pivoted opportunity table.
        Creates one column per opportunity type: {opportunity_name}_accessibility
        and an overall total_accessibility column.

        For each origin, computes average cost to the closest N destinations
        of each opportunity type within the max cost threshold.
        """

        result_table = "closest_avg_final"

        if not standardized_tables:
            raise ValueError("No standardized opportunity tables provided.")

        # Build individual opportunity calculations
        opportunity_calculations = []
        safe_names = []

        for idx, (_, opp_name) in enumerate(standardized_tables):
            safe_name = sanitize_sql_name(opp_name, idx)

            safe_names.append(safe_name)

            calculation = f"""
            -- Calculate closest average for {safe_name}
            ranked_{safe_name} AS (
                SELECT
                    m.orig_id,
                    m.dest_id,
                    m.cost,
                    o.{safe_name}_n_dest AS n_dest_for_dest,
                    ROW_NUMBER() OVER (
                        PARTITION BY m.orig_id
                        ORDER BY m.cost ASC
                    ) AS destination_rank
                FROM {filtered_matrix} m
                JOIN {unified_table} o ON m.dest_id = o.dest_id
                WHERE m.cost <= o.{safe_name}_max_cost
            ),
            closest_n_{safe_name} AS (
                SELECT
                    orig_id,
                    cost
                FROM ranked_{safe_name}
                WHERE destination_rank <= n_dest_for_dest
            ),
            aggregated_{safe_name} AS (
                SELECT
                    orig_id AS h3_index,
                    AVG(cost) AS {safe_name}_accessibility
                FROM closest_n_{safe_name}
                GROUP BY orig_id
            )
            """
            opportunity_calculations.append(calculation)

        # Build the final query
        if len(safe_names) == 1:
            safe_name = safe_names[0]
            query = f"""
            CREATE OR REPLACE TEMP TABLE {result_table} AS
            WITH {opportunity_calculations[0]}
            SELECT
                h3_index,
                {safe_name}_accessibility,
                {safe_name}_accessibility AS total_accessibility
            FROM aggregated_{safe_name}
            """
        else:
            ctes = ",\n".join(opportunity_calculations)

            select_parts = ["t0.h3_index"]
            join_parts = []

            for i, safe_name in enumerate(safe_names):
                select_parts.append(f"t{i}.{safe_name}_accessibility")
                if i > 0:
                    join_parts.append(
                        f"FULL JOIN aggregated_{safe_name} t{i} USING (h3_index)"
                    )

            # Build total_accessibility as mean of available accessibilities
            total_expr = " + ".join(
                [f"t{i}.{name}_accessibility" for i, name in enumerate(safe_names)]
            )
            count_expr = " + ".join(
                [
                    f"(t{i}.{name}_accessibility IS NOT NULL)::INT"
                    for i, name in enumerate(safe_names)
                ]
            )
            total_accessibility = (
                f"({total_expr}) / NULLIF({count_expr}, 0) AS total_accessibility"
            )

            query = f"""
            CREATE OR REPLACE TEMP TABLE {result_table} AS
            WITH
            {ctes}
            SELECT
                {', '.join(select_parts)},
                {total_accessibility}
            FROM aggregated_{safe_names[0]} t0
            {' '.join(join_parts)}
            """

        self.con.execute(query)

        # Log the final schema
        schema = self.con.execute(f"DESCRIBE {result_table}").fetchall()
        logger.info("Final result schema: %s", [col[0] for col in schema])

        return result_table
