import logging
from pathlib import Path
from typing import List, Self, Tuple

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
      4. Export results to GeoPackage/Parquet.
    """

    def _run_implementation(
        self: Self, params: HeatmapGravityParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
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

        origin_ids = self._extract_origin_ids(unified_table)
        if not origin_ids:
            raise ValueError("No origin IDs found in opportunity data")

        h3_partitions = self._compute_h3_partitions(origin_ids)
        logger.info(
            "Found %d unique origin IDs across %d H3 partitions",
            len(origin_ids),
            len(h3_partitions),
        )

        filtered_matrix = self._filter_traveltime_matrix(
            od_table, origin_ids, h3_partitions
        )

        gravity_results = self._compute_gravity_accessibility(
            filtered_matrix,
            unified_table,
            standardized_tables,
            params.impedance,
            params.max_sensitivity,
        )
        self._export_results(gravity_results, params.output_path)

        logger.info("Heatmap gravity analysis completed successfully")

    def _prepare_od_matrix(self: Self, od_matrix_source: str) -> Tuple[str, int]:
        """
        Register OD matrix source as a DuckDB VIEW and detect H3 resolution.
        Returns (view_name, h3_resolution)
        """
        view_name = "od_matrix"

        try:
            # Create a VIEW - no data imported, just a query definition
            self.con.execute(f"""
                CREATE OR REPLACE TEMP VIEW {view_name} AS
                SELECT * FROM read_parquet('{od_matrix_source}')
            """)
        except Exception as e:
            raise ValueError(
                f"Failed to register OD matrix from '{od_matrix_source}': {e}"
            )

        # Validate required columns
        try:
            result = self.con.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{view_name}'
            """).fetchall()
        except Exception as e:
            raise ValueError(f"Failed to inspect OD matrix schema: {e}")

        actual_columns = {row[0] for row in result}
        required_columns = {"orig_id", "dest_id", "traveltime"}

        if not required_columns.issubset(actual_columns):
            raise ValueError(
                f"OD matrix must contain columns: {required_columns}. "
                f"Found: {actual_columns}"
            )

        # Detect H3 resolution from first valid row
        try:
            result = self.con.execute(f"""
                SELECT
                    h3_get_resolution(COALESCE(orig_id, dest_id)) AS res
                FROM {view_name}
                WHERE orig_id IS NOT NULL OR dest_id IS NOT NULL
                LIMIT 1
            """).fetchone()
        except Exception as e:
            raise ValueError(f"Failed to detect H3 resolution: {e}")

        if result and result[0] is not None:
            h3_resolution = int(result[0])
            logger.info(
                "Registered OD matrix view '%s' at H3 resolution %d",
                view_name,
                h3_resolution,
            )
            return view_name, h3_resolution

        raise ValueError(
            f"Could not detect H3 resolution from OD matrix '{view_name}'. "
            "No valid H3 indices found in orig_id or dest_id columns. "
            "Please ensure your OD matrix contains valid H3 indices."
        )

    def _process_opportunities(
        self: Self, opportunities: List[OpportunityGravity], h3_resolution: int
    ) -> List[Tuple[str, str]]:
        """
        Imports and standardizes all opportunity datasets into the canonical schema:
        orig_id, potential, max_traveltime, sensitivity
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

    def _combine_opportunities(
        self: Self, standardized_tables: List[Tuple[str, str]]
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
                    orig_id,
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

    def _get_potential_sql(
        self: Self, opp: OpportunityGravity, geom_col: str, geom_type: str
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
                return f"ST_Area({geom_col}, 'metre')"

            if expr in ("$perimeter", "perimeter"):
                if "polygon" not in geom_type_lower:
                    raise ValueError(
                        f"Invalid potential_expression='{expr}' for geometry type '{geom_type}'. "
                        "Perimeter is only valid for Polygon or MultiPolygon geometries."
                    )
                return f"ST_Perimeter({geom_col}, 'metre')"

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

    def _prepare_opportunity_table(
        self: Self,
        table_name: str,
        meta: Metadata,
        opp: OpportunityGravity,
        h3_resolution: int,
    ) -> str:
        """
        Converts an imported opportunity dataset into the canonical gravity schema:
        orig_id, potential, max_traveltime, sensitivity
        """
        geom_type = (meta.geometry_type or "").lower()
        geom_col = meta.geometry_column or "geom"
        output_table = f"{table_name}_std"
        potential_sql = self._get_potential_sql(opp, geom_col, geom_type)

        logger.info(
            "Standardizing opportunity '%s' (geom=%s, potential=%s)",
            table_name,
            geom_type,
            potential_sql,
        )

        # --- Handle geometry types ---
        if "point" in geom_type:
            query = f"""
                CREATE OR REPLACE TEMP TABLE {output_table} AS
                SELECT
                    h3_latlng_to_cell(ST_Y({geom_col}), ST_X({geom_col}), {h3_resolution}) AS orig_id,
                    {potential_sql}::DOUBLE AS potential,
                    {opp.max_traveltime}::DOUBLE AS max_traveltime,
                    {opp.sensitivity}::DOUBLE AS sensitivity
                FROM {table_name}
            """

        elif "polygon" in geom_type:
            query = f"""
                CREATE OR REPLACE TEMP TABLE {output_table} AS
                WITH polys AS (
                    SELECT
                        h3_polygon_to_cells({geom_col}, {h3_resolution}) AS h3_cells,
                        {potential_sql}::DOUBLE AS total_potential
                    FROM {table_name}
                ),
                exploded AS (
                    SELECT
                        UNNEST(h3_cells) AS orig_id,
                        total_potential / array_length(h3_cells) AS potential
                    FROM polys
                )
                SELECT
                    orig_id,
                    potential,
                    {opp.max_traveltime}::DOUBLE AS max_traveltime,
                    {opp.sensitivity}::DOUBLE AS sensitivity
                FROM exploded
            """

        elif "line" in geom_type:
            query = f"""
                CREATE OR REPLACE TEMP TABLE {output_table} AS
                WITH sampled AS (
                    SELECT ST_SamplePoints({geom_col}, 100) AS pts,
                           {potential_sql}::DOUBLE AS potential_value
                    FROM {table_name}
                ),
                unnested AS (
                    SELECT UNNEST(pts) AS geom, potential_value FROM sampled
                )
                SELECT
                    h3_latlng_to_cell(ST_Y(geom), ST_X(geom), {h3_resolution}) AS orig_id,
                    potential_value AS potential,
                    {opp.max_traveltime}::DOUBLE AS max_traveltime,
                    {opp.sensitivity}::DOUBLE AS sensitivity
                FROM unnested
            """

        else:
            raise ValueError(f"Unsupported geometry type: '{geom_type}'")

        self.con.execute(query)
        return output_table

    def _extract_origin_ids(self: Self, unified_table: str) -> List[int]:
        """Extract unique origin IDs from the unified opportunity table."""
        result = self.con.execute(f"""
                SELECT DISTINCT orig_id
                FROM {unified_table}
                WHERE orig_id IS NOT NULL
            """).fetchall()
        return [row[0] for row in result] if result else []

    def _compute_h3_partitions(self: Self, origin_ids: List[int]) -> List[int]:
        """Convert origin IDs to H3 partition keys using the existing UDF."""
        if not origin_ids:
            return []

        # Create a temporary table with origin IDs
        self.con.execute(
            """
            CREATE OR REPLACE TEMP TABLE temp_origin_ids AS
            SELECT UNNEST($1) AS orig_id
        """,
            [origin_ids],
        )

        # Use the existing UDF to compute H3 partition keys
        result = self.con.execute("""
            SELECT DISTINCT to_short_h3_3(orig_id) AS h3_partition
            FROM temp_origin_ids
            WHERE orig_id IS NOT NULL
        """).fetchall()

        return [row[0] for row in result] if result else []

    def _filter_traveltime_matrix(
        self: Self, od_view: str, origin_ids: List[int], h3_partitions: List[int]
    ) -> str:
        """Filter the travel time matrix using H3 partitioning for efficiency."""
        filtered_table = "filtered_matrix"

        if h3_partitions:
            # Use H3 partitioning for efficient filtering with the UDF
            h3_partitions_sql = ", ".join(map(str, h3_partitions))
            origin_ids_sql = ", ".join(map(str, origin_ids))

            query = f"""
                CREATE OR REPLACE TEMP TABLE {filtered_table} AS
                SELECT orig_id, dest_id, traveltime
                FROM {od_view}
                WHERE to_short_h3_3(orig_id) IN ({h3_partitions_sql})
                AND orig_id IN ({origin_ids_sql})
            """
        else:
            # Fallback: filter by origin IDs only
            origin_ids_sql = ", ".join(map(str, origin_ids))
            query = f"""
                CREATE OR REPLACE TEMP TABLE {filtered_table} AS
                SELECT orig_id, dest_id, traveltime
                FROM {od_view}
                WHERE orig_id IN ({origin_ids_sql})
            """

        self.con.execute(query)
        row_count = self.con.execute(
            f"SELECT COUNT(*) FROM {filtered_table}"
        ).fetchone()[0]
        logger.info("Filtered matrix created with %d rows", row_count)

        return filtered_table

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
        standardized_tables: List[Tuple[str, str]],
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
                m.dest_id,
                {individual_columns_sql},
                -- Total accessibility as sum of all individual accessibilities
                ({' + '.join(sum_expressions)}) AS total_accessibility
            FROM {filtered_matrix} AS m
            JOIN {opportunities_table} AS o ON m.orig_id = o.orig_id
            WHERE (
                {' OR '.join([f"m.traveltime <= o.{safe_name}_max_tt" for safe_name in safe_names])}
            )
            GROUP BY m.dest_id
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

    def _export_results(
        self: Self, gravity_table: str, output_path: str
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Export results to GeoParquet with H3 index ordering for optimal performance."""

        # Create output directory if it doesn't exist
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Ensure .parquet extension
        if output_path_obj.suffix.lower() != ".parquet":
            output_path_obj = output_path_obj.with_suffix(".parquet")

        # Convert H3 cells to geometry and export to GeoParquet, ordered by H3 index
        query = f"""
            COPY (
                SELECT
                    dest_id,
                    * EXCLUDE (dest_id),
                    ST_AsWKB(ST_GeomFromText(h3_cell_to_boundary_wkt(dest_id))) AS geometry
                FROM {gravity_table}
                ORDER BY dest_id  -- Order by H3 index for optimal spatial indexing
            ) TO '{output_path_obj}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """

        self.con.execute(query)

        logger.info("GeoParquet written to %s", output_path)
