import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.heatmap.base import HeatmapToolBase
from goatlib.analysis.schemas.heatmap import (
    HeatmapClosestAverageParams,
    OpportunityClosestAverage,
)
from goatlib.io.utils import Metadata
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class HeatmapClosestAverageTool(HeatmapToolBase):
    """
    Computes closest average heatmap - average value of the closest features within max travel time.
    """

    def _run_implementation(
        self: Self, params: HeatmapClosestAverageParams
    ) -> list[tuple[Path, DatasetMetadata]]:
        logger.info("Starting Heatmap Closest Average Analysis")

        # Register OD matrix and detect H3 resolution
        od_table, h3_resolution = self._prepare_od_matrix(params.od_matrix_source)
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

        # Filter OD matrix to only relevant origins
        filtered_matrix = self._filter_od_matrix(od_table, origin_ids=destination_ids)

        # Compute closest-average accessibility
        result_table = self._compute_closest_average(
            filtered_matrix, unified_table, standardized_tables
        )
        logger.info("Closest Average table created: %s", result_table)

        # Export results
        output_path = Path(params.output_path)
        return self._export_h3_results(result_table, output_path)

    def _process_opportunities(
        self: Self, opportunities: list[OpportunityClosestAverage], h3_resolution: int
    ) -> list[tuple[str, str]]:
        """
        Imports and standardizes all opportunity datasets.
        Returns a list of (standardized_table_name, opportunity_name)
        """
        opportunity_tables = []
        used_names = {}

        for opp in opportunities:
            # Determine table name and ensure uniqueness
            table_name = opp.name or Path(opp.input_path).stem
            if table_name in used_names:
                used_names[table_name] += 1
                table_name = f"{table_name}_{used_names[table_name]}"
            else:
                used_names[table_name] = 0

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
                # Use the original opportunity name for column naming
                display_name = opp.name or Path(opp.input_path).stem
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
        Schema: dest_id, max_traveltime, n_destinations
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
                {opp.max_traveltime}::DOUBLE AS max_traveltime,
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
                {opp.max_traveltime}::DOUBLE AS max_traveltime,
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
        Combine standardized opportunity tables using PIVOT to create columns for each opportunity type.
        Creates columns: {opportunity_name}_max_tt, {opportunity_name}_n_dest
        """
        if not standardized_tables:
            raise ValueError("No standardized opportunity tables to combine")

        # Create union of all standardized tables with opportunity type
        union_parts = []
        for std_table, name in standardized_tables:
            safe_name = name.replace("-", "_").replace(" ", "_").lower()
            union_parts.append(f"""
                SELECT
                    dest_id,
                    '{safe_name}' as opportunity_type,
                    max_traveltime,
                    n_destinations
                FROM {std_table}
                WHERE dest_id IS NOT NULL
            """)

        union_query = "\nUNION ALL\n".join(union_parts)

        unified_table = "opportunity_closest_avg_unified"

        # Use PIVOT to create columns for each opportunity type
        query = f"""
            CREATE OR REPLACE TEMP TABLE {unified_table} AS
            PIVOT (
                {union_query}
            )
            ON opportunity_type
            USING
                FIRST(max_traveltime) AS max_tt,
                FIRST(n_destinations) AS n_dest
        """

        self.con.execute(query)
        logger.info(
            "Unified opportunity table '%s' created with %d layers",
            unified_table,
            len(standardized_tables),
        )

        # Log the schema to verify pivot worked correctly
        schema = self.con.execute(f"DESCRIBE {unified_table}").fetchall()
        logger.info("Unified table schema: %s", [col[0] for col in schema])

        return unified_table

    def _find_reachable_origins(
        self: Self, od_table: str, destination_ids: list[int]
    ) -> list[int]:
        """Find all origins that can reach at least one of the given destinations."""
        if not destination_ids:
            return []

        dest_ids_sql = ", ".join(map(str, destination_ids))

        query = f"""
            SELECT DISTINCT orig_id
            FROM {od_table}
            WHERE dest_id IN ({dest_ids_sql})
            AND orig_id IS NOT NULL
        """

        result = self.con.execute(query).fetchall()
        return [row[0] for row in result] if result else []

    def _compute_closest_average(
        self: Self,
        filtered_matrix: str,
        unified_table: str,
        standardized_tables: list[tuple[str, str]],
    ) -> str:
        """
        Compute closest-average accessibility using the pivoted opportunity table.
        Creates one column per opportunity type: {opportunity_name}_accessibility

        For each origin, compute average travel time to the closest N destinations
        of each opportunity type within the max travel time.
        """
        result_table = "closest_avg_final"

        # Build individual opportunity calculations
        opportunity_calculations = []
        safe_names = []

        for _, opp_name in standardized_tables:
            safe_name = opp_name.replace("-", "_").replace(" ", "_").lower()
            safe_names.append(safe_name)

            # Calculate closest average for this opportunity type
            calculation = f"""
            -- Calculate closest average for {safe_name}
            ranked_{safe_name} AS (
                SELECT
                    m.orig_id,
                    m.dest_id,
                    m.traveltime,
                    ROW_NUMBER() OVER (
                        PARTITION BY m.orig_id
                        ORDER BY m.traveltime ASC
                    ) AS destination_rank
                FROM {filtered_matrix} m
                JOIN {unified_table} o ON m.dest_id = o.dest_id
                WHERE m.traveltime <= o.{safe_name}_max_tt
            ),
            closest_n_{safe_name} AS (
                SELECT
                    orig_id,
                    traveltime
                FROM ranked_{safe_name}
                WHERE destination_rank <= (SELECT {safe_name}_n_dest FROM {unified_table} WHERE dest_id = ranked_{safe_name}.dest_id LIMIT 1)
            ),
            aggregated_{safe_name} AS (
                SELECT
                    orig_id AS h3_index,
                    AVG(traveltime) AS {safe_name}_accessibility
                FROM closest_n_{safe_name}
                GROUP BY orig_id
            )
            """
            opportunity_calculations.append(calculation)

        # Build the main query that combines all opportunity types
        if len(safe_names) == 1:
            # Single opportunity type - simpler query
            safe_name = safe_names[0]
            query = f"""
            CREATE OR REPLACE TEMP TABLE {result_table} AS
            WITH {opportunity_calculations[0]}
            SELECT * FROM aggregated_{safe_name}
            """
        else:
            # Multiple opportunity types - combine with FULL JOIN
            ctes = ",\n".join(opportunity_calculations)

            # Build the select and join parts
            select_parts = ["t0.h3_index"]
            join_parts = []

            for i, safe_name in enumerate(safe_names):
                select_parts.append(f"t{i}.{safe_name}_accessibility")
                if i > 0:
                    join_parts.append(
                        f"FULL JOIN aggregated_{safe_name} t{i} USING (h3_index)"
                    )

            query = f"""
            CREATE OR REPLACE TEMP TABLE {result_table} AS
            WITH
            {ctes}
            SELECT
                {', '.join(select_parts)}
            FROM aggregated_{safe_names[0]} t0
            {' '.join(join_parts)}
            """

        self.con.execute(query)

        # Log the final schema
        schema = self.con.execute(f"DESCRIBE {result_table}").fetchall()
        logger.info("Final result schema: %s", [col[0] for col in schema])

        return result_table
