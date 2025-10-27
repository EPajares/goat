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

        # --- Combine all standardized tables into a single unified table ---
        unified_table = self._combine_opportunities(standardized_tables)
        logger.info("Unified opportunity table created: %s", unified_table)

        # --- Extract unique origin H3 IDs ---
        origin_ids = self._extract_origin_ids(unified_table)
        if not origin_ids:
            raise ValueError("No origin IDs found in opportunity data")

        # --- Partition origins for batch processing ---
        h3_partitions = self._compute_h3_partitions(origin_ids)
        logger.info(
            "Found %d unique origin IDs across %d H3 partitions",
            len(origin_ids),
            len(h3_partitions),
        )

        # --- Filter OD matrix to only relevant origins ---
        filtered_matrix = self._filter_od_matrix(od_table, origin_ids, h3_partitions)

        # --- Compute closest-average accessibility per opportunity type ---
        result_table = self._compute_closest_average(filtered_matrix, unified_table)
        logger.info("Closest Average table created: %s", result_table)

        # Export results
        output_path = Path(params.output_path)
        self._export_h3_results(result_table, output_path)

    def _process_opportunities(
        self: Self, opportunities: list[OpportunityClosestAverage], h3_resolution: int
    ) -> None:  # Returns None, populates self.standardized_opportunities_details
        """
        Imports and standardizes all opportunity datasets into the canonical schema:
        orig_id, max_traveltime, n_destinations
        Returns a list of (table_name, display_name).
        """
        opportunity_tables = []
        used_names = {}

        for idx, opp in enumerate(opportunities):
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

                # Standardize into gravity schema
                std_table = self._prepare_opportunity_table(
                    table_name, meta, opp, h3_resolution
                )
                opportunity_tables.append((std_table, table_name))
                logger.info("Prepared standardized table: %s", std_table)

            except Exception as e:
                logger.warning(
                    "Failed to import opportunity dataset '%s': %s", opp.input_path, e
                )

        return opportunity_tables

    def _prepare_opportunity_table(
        self: Self,
        table_name: str,
        meta: Metadata,
        opp: OpportunityClosestAverage,
        h3_resolution: int,
    ) -> str:
        """
        Converts an imported opportunity dataset into canonical schema:
        orig_id, max_traveltime, n_destinations
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
            SELECT
                h3_latlng_to_cell(ST_Y({transform_to_4326}), ST_X({transform_to_4326}), {h3_resolution}) AS orig_id,
                {opp.max_traveltime}::DOUBLE AS max_traveltime,
                {opp.n_destinations}::INT AS n_destinations
            FROM {table_name}
            WHERE {geom_col} IS NOT NULL
            """
        elif "polygon" in geom_type:
            query = f"""
            CREATE OR REPLACE TEMP TABLE {output_table} AS
            WITH polygons AS (
                SELECT UNNEST(ST_Dump(ST_Force2D({transform_to_4326}))) AS geom
                FROM {table_name}
                WHERE {geom_col} IS NOT NULL
            ),
            h3_cells AS (
                SELECT
                    UNNEST(h3_polygon_wkt_to_cells_experimental(ST_AsText(geom), {h3_resolution}, 'CONTAINMENT_OVERLAPPING')) AS orig_id
                FROM polygons
            )
            SELECT
                orig_id,
                {opp.max_traveltime}::DOUBLE AS max_traveltime,
                {opp.n_destinations}::INT AS n_destinations
            FROM h3_cells
            """
        else:
            raise ValueError(f"Unsupported geometry type: '{geom_type}'")

        self.con.execute(query)
        return output_table

    def _combine_opportunities(
        self: Self, standardized_tables: list[tuple[str, str]]
    ) -> str:
        """
        Combine standardized opportunities into a unified table for pivoted output.
        Each opportunity layer becomes one column in the final H3 table.
        """
        if not standardized_tables:
            raise ValueError("No standardized opportunity tables provided")

        union_queries = []
        for std_table, name in standardized_tables:
            safe_name = name.replace("-", "_").replace(" ", "_").lower()
            union_queries.append(f"""
                SELECT
                    orig_id,
                    '{safe_name}' AS opportunity_type,
                    max_traveltime,
                    n_destinations
                FROM {std_table}
            """)

        union_sql = "\nUNION ALL\n".join(union_queries)

        unified_table = "opportunity_closest_avg_unified"

        query = f"""
            CREATE OR REPLACE TEMP TABLE {unified_table} AS
            SELECT *
            FROM ({union_sql})
        """
        self.con.execute(query)
        return unified_table

    def _compute_closest_average(
        self: Self, filtered_matrix: str, unified_table: str
    ) -> str:
        """
        Compute closest-average accessibility per opportunity type.
        Each column contains average of up to n_destinations closest opportunities.
        """
        # Generate pivot query per opportunity type
        distinct_opps = self.con.execute(
            f"SELECT DISTINCT opportunity_type FROM {unified_table}"
        ).fetchall()
        opportunity_columns = []

        for (opp,) in distinct_opps:
            col_name = f"{opp}_avg_traveltime"
            opportunity_columns.append(f"""
                SELECT
                    m.dest_id AS h3_index,
                    AVG(CASE WHEN rn <= o.n_destinations THEN m.traveltime END) AS {col_name}
                FROM {filtered_matrix} m
                JOIN {unified_table} o ON m.orig_id = o.orig_id AND o.opportunity_type = '{opp}'
                CROSS JOIN (
                    SELECT ROW_NUMBER() OVER (PARTITION BY m.dest_id ORDER BY m.traveltime ASC) AS rn
                ) AS r
                GROUP BY m.dest_id
            """)

        # Combine pivoted results
        result_table = "closest_avg_scores"
        full_query = (
            "CREATE OR REPLACE TEMP TABLE "
            + result_table
            + " AS\n"
            + "SELECT * FROM (\n"
            + "\nUNION ALL\n".join(opportunity_columns)
            + "\n)"
        )
        self.con.execute(full_query)
        return result_table
