import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.heatmap.base import HeatmapToolBase
from goatlib.analysis.schemas.heatmap import (
    HeatmapGravityParams,
    ImpedanceFunction,
    OpportunityGravity,
)
from goatlib.io.utils import Metadata
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class HeatmapGravityTool(HeatmapToolBase):
    """
    Performs gravity-based spatial accessibility analysis.

    Steps:
      1. Import and standardize all opportunity layers.
      2. Combine standardized layers into a unified opportunity table.
      3. Filter travel-time matrix and compute gravity accessibility.
      4. Export results
    """

    def _run_implementation(
        self: Self, params: HeatmapGravityParams
    ) -> list[tuple[Path, DatasetMetadata]]:
        logger.info("Starting Heatmap Gravity Analysis")

        # Register OD matrix and detect H3 resolution
        od_table, h3_resolution = self._prepare_od_matrix(params.od_matrix_source)
        logger.info(
            "OD matrix ready: table=%s, h3_resolution=%s", od_table, h3_resolution
        )

        # Process and standardize opportunities using detected resolution
        standardized_tables = self._process_opportunities(
            params.opportunities, h3_resolution
        )

        # Combine all standardized opportunity tables
        unified_table = self._combine_opportunities(standardized_tables)
        logger.info("Unified opportunity table created: %s", unified_table)

        destination_ids = self._extract_destination_ids(unified_table)
        if not destination_ids:
            raise ValueError("No destination IDs found in opportunity data")

        logger.info("Found %d unique destination IDs across ", len(destination_ids))

        filtered_matrix = self._filter_od_matrix(
            od_table, destination_ids=destination_ids
        )

        gravity_results = self._compute_gravity_accessibility(
            filtered_matrix,
            unified_table,
            standardized_tables,
            params.impedance,
            params.max_sensitivity,
        )
        self._export_h3_results(gravity_results, params.output_path)

        logger.info("Heatmap gravity analysis completed successfully")

    def _process_opportunities(
        self: Self, opportunities: list[OpportunityGravity], h3_resolution: int
    ) -> list[tuple[str, str]]:
        """
        Imports and standardizes all opportunity datasets into the canonical schema:
        dest_id, potential, max_traveltime, sensitivity
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
        opp: OpportunityGravity,
        h3_resolution: int,
    ) -> str:
        """
        Converts an imported opportunity dataset into the canonical gravity schema:
        dest_id, potential, max_traveltime, sensitivity.

        Handles Point, MultiPoint, Polygon, and MultiPolygon geometries.
        """

        geom_type = (meta.geometry_type or "").lower()
        geom_col = meta.geometry_column or "geom"
        output_table = f"{table_name}_std"

        # --- Transform to WGS84 if needed ---
        transform_to_4326 = geom_col
        try:
            if meta.crs and meta.crs.to_epsg() != 4326:
                source_crs = meta.crs.to_string()
                transform_to_4326 = (
                    f"ST_Transform({geom_col}, '{source_crs}', 'EPSG:4326')"
                )
        except Exception:
            pass

        potential_sql = self._get_potential_sql(opp, transform_to_4326, geom_type)

        # --- Branch by geometry type ---
        if "point" in geom_type:
            # Points / MultiPoints: dump if multipoint
            query = f"""
            CREATE OR REPLACE TEMP TABLE {output_table} AS
            WITH features AS (
                SELECT
                    {potential_sql}::DOUBLE AS total_potential,
                    {transform_to_4326} AS geom
                FROM {table_name}
                WHERE {geom_col} IS NOT NULL
            ),
            exploded AS (
                SELECT
                        total_potential,
                        ST_NumGeometries(geom) AS num_parts, -- Calculate the total number of parts ONCE
                        (UNNEST(ST_Dump(geom))).geom AS simple_geom -- Dump the geometry ONCE
                FROM features
            )
            SELECT
                h3_latlng_to_cell(ST_Y(simple_geom), ST_X(simple_geom), {h3_resolution}) AS dest_id,
                SUM(total_potential / num_parts) AS potential,
                {opp.max_traveltime}::DOUBLE AS max_traveltime,
                {opp.sensitivity}::DOUBLE AS sensitivity
            FROM exploded
            GROUP BY dest_id
            """
        elif "polygon" in geom_type:
            # Polygons / MultiPolygons: split into simple polygons and distribute potential
            query = f"""
            CREATE OR REPLACE TEMP TABLE {output_table} AS
            WITH features AS (
                SELECT
                    {potential_sql}::DOUBLE AS total_potential,
                    {transform_to_4326} AS geom
                FROM {table_name}
                WHERE {geom_col} IS NOT NULL
            ),
            polygons AS (
                SELECT
                    ROW_NUMBER() OVER () AS row_id,
                    total_potential,
                    (UNNEST(ST_Dump(ST_Force2D(geom))).geom) AS simple_geom
                FROM features
            ),
            h3_cells_raw AS (
                SELECT
                    row_id,
                    total_potential,
                    UNNEST(h3_polygon_wkt_to_cells_experimental(ST_AsText(simple_geom), {h3_resolution}, 'CONTAINMENT_OVERLAPPING')) AS dest_id
                FROM polygons
            ),
            h3_cells_unique AS (
                SELECT DISTINCT row_id, total_potential, dest_id
                FROM h3_cells_raw
            ),
            h3_counts AS (
                SELECT
                    row_id,
                    COUNT(*) AS num_cells,
                    total_potential
                FROM h3_cells_unique
                GROUP BY row_id, total_potential
            )
            SELECT
                u.dest_id,
                SUM(u.total_potential / hc.num_cells) AS potential,
                {opp.max_traveltime}::DOUBLE AS max_traveltime,
                {opp.sensitivity}::DOUBLE AS sensitivity
            FROM h3_cells_unique u
            JOIN h3_counts hc ON u.row_id = hc.row_id
            GROUP BY u.dest_id
            """

        else:
            raise ValueError(f"Unsupported geometry type: '{geom_type}'")

        self.con.execute(query)
        return output_table

    def _get_potential_sql(
        self: Self, opp: OpportunityGravity, wgs84_geom_sql: str, geom_type: str
    ) -> str:
        """
        Determines the SQL expression for potential.

        Priority:
        1. potential_expression
        2. potential_constant
        3. potential_field
        4. defaults to 1.0

        Special rule:
        - 'area' and 'perimeter' expressions are only valid for Polygon/MultiPolygon geometries.
        """
        geom_type_lower = (geom_type or "").lower()

        # --- Handle potential_expression first ---
        if opp.potential_expression:
            expr = opp.potential_expression.lower().strip()

            if expr in ("$area", "area"):
                if "polygon" not in geom_type_lower:
                    raise ValueError(
                        f"Invalid potential_expression='{expr}' for geometry type '{geom_type}'. "
                        "Area is only valid for Polygon or MultiPolygon geometries."
                    )
                return f"ST_Area_Spheroid({wgs84_geom_sql})"

            if expr in ("$perimeter", "perimeter"):
                if "polygon" not in geom_type_lower:
                    raise ValueError(
                        f"Invalid potential_expression='{expr}' for geometry type '{geom_type}'. "
                        "Perimeter is only valid for Polygon or MultiPolygon geometries."
                    )
                return f"ST_Perimeter_Spheroid({wgs84_geom_sql})"

            # Custom user expression (use as-is)
            return expr

        # --- Constant potential ---
        if opp.potential_constant is not None:
            return str(float(opp.potential_constant))

        # --- Field-based potential ---
        if opp.potential_field:
            return f'"{opp.potential_field}"'

        # --- Default constant ---
        return "1.0"

    def _combine_opportunities(
        self: Self, standardized_tables: list[tuple[str, str]]
    ) -> str:
        """
        Combine opportunities.
        """
        if not standardized_tables:
            raise ValueError("No standardized opportunity tables provided")

        # Create a union of all standardized tables with opportunity type
        union_parts = []
        for std_table, name in standardized_tables:
            safe_name = name.replace("-", "_").replace(" ", "_").lower()
            union_parts.append(f"""
                SELECT
                    dest_id,
                    '{safe_name}' as opportunity_type,
                    potential,
                    max_traveltime,
                    sensitivity
                FROM {std_table}
            """)

        union_query = "\nUNION ALL\n".join(union_parts)

        unified_table = "opportunity_potentials_unified"

        # Use PIVOT to create columns for each opportunity type
        query = f"""
            CREATE OR REPLACE TEMP TABLE {unified_table} AS
            PIVOT (
                {union_query}
            )
            ON opportunity_type
            USING
                FIRST(potential) AS potential,
                FIRST(max_traveltime) AS max_tt,
                FIRST(sensitivity) AS sens
        """

        self.con.execute(query)
        logger.info(
            "Unified opportunity table '%s' created with %d layers",
            unified_table,
            len(standardized_tables),
        )

        return unified_table

    def _impedance_sql(
        self: Self, which: ImpedanceFunction, max_sens: float, opportunity_name: str
    ) -> str:
        """
        Returns the correct SQL formula for the impedance function.
        Updated to use pivoted column names.
        """
        # Reference the pivoted column names
        potential_col = f"o.{opportunity_name}_potential"
        max_tt_col = f"o.{opportunity_name}_max_tt"
        sens_col = f"o.{opportunity_name}_sens"

        if which == ImpedanceFunction.gaussian:
            return f"""
                SUM(
                    EXP(
                        ((((m.traveltime / {max_tt_col}) * (m.traveltime / {max_tt_col})) * -1)
                        / ({sens_col} / {max_sens}))
                    ) * {potential_col}
                )
            """
        elif which == ImpedanceFunction.linear:
            return f"SUM( (1 - (m.traveltime / {max_tt_col})) * {potential_col} )"
        elif which == ImpedanceFunction.exponential:
            return f"""
                SUM(
                    EXP(
                        ((({sens_col} / {max_sens}) * -1) * (m.traveltime / {max_tt_col}))
                    ) * {potential_col}
                )
            """
        elif which == ImpedanceFunction.power:
            return f"""
                SUM(
                    POW(
                        (m.traveltime / {max_tt_col}),
                        (({sens_col} / {max_sens}) * -1)
                    ) * {potential_col}
                )
            """
        else:
            raise ValueError(f"Unknown impedance function: {which}")

    def _compute_gravity_accessibility(
        self: Self,
        filtered_matrix: str,
        opportunities_table: str,
        standardized_tables: list[tuple[str, str]],
        impedance_func: ImpedanceFunction,
        max_sensitivity: float,
    ) -> str:
        """Compute gravity-based accessibility scores per destination with individual opportunity columns."""
        gravity_table = "gravity_scores"

        # Build individual opportunity accessibility columns
        opportunity_columns = []
        sum_expressions = []
        safe_names = []

        for std_table, opp_name in standardized_tables:
            safe_name = opp_name.replace("-", "_").replace(" ", "_").lower()
            safe_names.append(safe_name)
            impedance_sql = self._impedance_sql(
                impedance_func, max_sensitivity, safe_name
            )

            opportunity_columns.append(f"""
                {impedance_sql} AS {safe_name}_accessibility
            """)
            sum_expressions.append(f"{safe_name}_accessibility")

        # Build the main query with individual opportunity accessibilities
        individual_columns_sql = ",\n            ".join(opportunity_columns)

        query = f"""
            CREATE OR REPLACE TEMP TABLE {gravity_table} AS
            SELECT
                m.orig_id AS h3_index,
                {individual_columns_sql},
                -- Total accessibility as sum of all individual accessibilities
                ({' + '.join(sum_expressions)}) AS total_accessibility
            FROM {filtered_matrix} AS m
            JOIN {opportunities_table} AS o ON m.dest_id = o.dest_id
            WHERE (
                {' OR '.join([f"m.traveltime <= o.{safe_name}_max_tt" for safe_name in safe_names])}
            )
            GROUP BY m.orig_id
            HAVING total_accessibility IS NOT NULL
        """

        self.con.execute(query)
        row_count = self.con.execute(
            f"SELECT COUNT(*) FROM {gravity_table}"
        ).fetchone()[0]
        logger.info(
            "Computed gravity scores for %d destinations with %d opportunity columns",
            row_count,
            len(standardized_tables),
        )

        return gravity_table
