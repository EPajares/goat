import logging
from pathlib import Path
from typing import Any, List, Optional, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.geoprocessing import UnionParams
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class UnionTool(AnalysisTool):
    """
    UnionTool: Combines layers with topological splitting at intersections
    (equivalent to QGIS union/vereinigen).
    Creates separate features for overlapping and non-overlapping parts.
    """

    def _run_implementation(
        self: Self, params: UnionParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform union operation on vector datasets."""

        # Import input dataset
        input_meta, input_table = self.import_input(params.input_path, "input")

        # Import overlay dataset if provided, otherwise perform self-union
        overlay_meta = None
        overlay_table = None
        if params.overlay_path:
            overlay_meta, overlay_table = self.import_input(
                params.overlay_path, "overlay"
            )

        # Validate geometry columns
        input_geom = input_meta.geometry_column
        if not input_geom:
            raise ValueError(
                f"Could not detect geometry column for input: {params.input_path}"
            )

        overlay_geom = None
        if overlay_meta:
            overlay_geom = overlay_meta.geometry_column
            if not overlay_geom:
                raise ValueError(
                    f"Could not detect geometry column for overlay: {params.overlay_path}"
                )

        # Validate geometry types
        self.validate_geometry_types(
            input_table, input_geom, params.accepted_input_geometry_types, "input"
        )
        if overlay_meta and overlay_table and overlay_geom:
            self.validate_geometry_types(
                overlay_table,
                overlay_geom,
                params.accepted_overlay_geometry_types,
                "overlay",
            )

        # Get CRS from input metadata, fallback to output_crs or EPSG:4326
        input_crs = input_meta.crs
        if input_crs:
            input_crs_str = input_crs.to_string()
        else:
            input_crs_str = params.output_crs or "EPSG:4326"
            logger.warning(
                "Could not detect CRS for %s, using fallback: %s",
                params.input_path,
                input_crs_str,
            )

        overlay_crs_str = None
        if overlay_meta:
            overlay_crs = overlay_meta.crs
            if overlay_crs:
                overlay_crs_str = overlay_crs.to_string()
            else:
                overlay_crs_str = params.output_crs or "EPSG:4326"
                logger.warning(
                    "Could not detect CRS for %s, using fallback: %s",
                    params.overlay_path,
                    overlay_crs_str,
                )

            # Validate CRS compatibility
            if input_crs_str != overlay_crs_str:
                logger.info(
                    "CRS mismatch detected. Input: %s, Overlay: %s",
                    input_crs_str,
                    overlay_crs_str,
                )
                logger.info("Transforming overlay layer to match input CRS")

        # Define output path
        if not params.output_path:
            suffix = "_self_union" if not params.overlay_path else "_union"
            params.output_path = str(
                Path(params.input_path).parent
                / f"{Path(params.input_path).stem}{suffix}.parquet"
            )
        output_path = Path(params.output_path)

        logger.info(
            "Starting union: input='%s' | overlay='%s' | input_geom='%s' | overlay_geom='%s'",
            params.input_path,
            params.overlay_path or "None (self-union)",
            input_geom,
            overlay_geom or "N/A",
        )

        # Execute union operation
        self._execute_union(
            params,
            input_table,
            overlay_table,
            input_meta,
            overlay_meta,
            input_geom,
            overlay_geom,
            input_crs_str,
            overlay_crs_str,
            output_path,
        )

        # Determine output geometry type (same as input)
        output_geometry_type = input_meta.geometry_type

        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            format="geoparquet",
            crs=params.output_crs or input_crs_str,
            geometry_type=output_geometry_type,
        )

        logger.info("Union completed successfully → %s", output_path)
        return [(output_path, metadata)]

    def _execute_union(
        self: Self,
        params: UnionParams,
        input_table: str,
        overlay_table: Optional[str],
        input_meta: Any,
        overlay_meta: Optional[Any],
        input_geom: str,
        overlay_geom: Optional[str],
        input_crs: Optional[str],
        overlay_crs: Optional[str],
        output_path: Path,
    ) -> None:
        """Execute the union operation in DuckDB."""
        con = self.con

        if overlay_table is None:
            # Self-union: split overlapping features within the same layer
            self._execute_self_union(
                params, input_table, input_geom, input_crs, output_path
            )
        else:
            # Two-layer union: combine features from both layers
            self._execute_two_layer_union(
                params,
                input_table,
                overlay_table,
                input_meta,
                overlay_meta,
                input_geom,
                overlay_geom,
                input_crs,
                overlay_crs,
                output_path,
            )

    def _execute_self_union(
        self: Self,
        params: UnionParams,
        input_table: str,
        input_geom: str,
        input_crs: Optional[str],
        output_path: Path,
    ) -> None:
        """Execute self-union operation to split overlapping features within the layer."""
        logger.info("Performing self-union (dissolve) operation")

        # Self-union dissolves all geometries into a single unified geometry
        # Then explode it back into individual features using UNNEST(ST_Dump(...))
        self.con.execute(f"""
            CREATE OR REPLACE VIEW unioned AS
            SELECT 
                ROW_NUMBER() OVER () AS fid,
                geom_part.geom AS {input_geom}
            FROM (
                SELECT UNNEST(ST_Dump(ST_Union_Agg({input_geom}))) as geom_part
                FROM {input_table}
                WHERE ST_IsValid({input_geom})
            )
        """)

        # Handle output CRS transformation if needed
        output_view = "unioned"
        if params.output_crs and input_crs and params.output_crs != input_crs:
            self.con.execute(f"""
                CREATE OR REPLACE VIEW unioned_transformed AS
                SELECT fid,
                    ST_Transform({input_geom}, '{input_crs}', '{params.output_crs}') AS {input_geom}
                FROM unioned
            """)
            output_view = "unioned_transformed"

        # Export to file
        self.con.execute(
            f"COPY {output_view} TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        logger.info("Self-union data written to %s", output_path)

    def _execute_two_layer_union(
        self: Self,
        params: UnionParams,
        input_table: str,
        overlay_table: str,
        input_meta: Any,
        overlay_meta: Any,
        input_geom: str,
        overlay_geom: str,
        input_crs: Optional[str],
        overlay_crs: Optional[str],
        output_path: Path,
    ) -> None:
        """Execute two-layer union operation using QGIS-style algorithm.

        Splits features from each layer at their overlap with features from the other layer.
        Overlapping areas appear multiple times (once per participating feature from each layer).
        """
        logger.info("Performing QGIS-style two-layer union with bbox spatial filtering")

        # For WGS84 datasets, assume both are in EPSG:4326 (no CRS conversion needed)
        logger.info(
            "Assuming both datasets are in EPSG:4326 (WGS84) - no CRS conversion required"
        )

        # Determine allowed output geometry types to filter degenerate geometries
        allowed_types = self.get_allowed_output_geometry_types(input_table, input_geom)
        logger.info(
            f"Filtering output to geometry types: {allowed_types or 'all types'}"
        )

        # Build geometry type filter clause
        geom_type_filter = (
            f"AND ST_GeometryType({input_geom}) IN {allowed_types}"
            if allowed_types
            else ""
        )

        # Build field selections
        input_fields = self._build_field_selection(
            self.con, input_table, input_geom, "i", ""
        )
        overlay_fields = self._build_field_selection(
            self.con,
            overlay_table,
            overlay_geom,
            "o",
            params.overlay_fields_prefix or "",
        )
        null_overlay_fields = self._get_null_overlay_fields(
            self.con, overlay_table, overlay_geom, params.overlay_fields_prefix or ""
        )
        null_input_fields = self._get_null_input_fields(
            self.con, input_table, input_geom
        )

        # Create unified geometries for difference operations
        logger.info("Creating unified geometries for difference operations")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE unified_overlay AS
            SELECT ST_Union_Agg({overlay_geom}) as geom
            FROM {overlay_table}
            WHERE ST_IsValid({overlay_geom})
        """)

        self.con.execute(f"""
            CREATE OR REPLACE TABLE unified_input AS
            SELECT ST_Union_Agg({input_geom}) as geom
            FROM {input_table}
            WHERE ST_IsValid({input_geom})
        """)

        # Part 1: Overlapping features with attributes from BOTH layers
        logger.info("Creating overlapping features with attributes from both layers")
        self.con.execute(f"""
            CREATE OR REPLACE VIEW overlapping_features AS
            SELECT
                {input_fields},
                {overlay_fields},
                ST_Intersection(i.{input_geom}, o.{overlay_geom}) AS {input_geom}
            FROM {input_table} i
            INNER JOIN {overlay_table} o ON ST_Intersects(i.{input_geom}, o.{overlay_geom})
            WHERE ST_IsValid(i.{input_geom})
                AND ST_IsValid(o.{overlay_geom})
                AND NOT ST_IsEmpty(ST_Intersection(i.{input_geom}, o.{overlay_geom}))
                {geom_type_filter.replace(input_geom, f"ST_Intersection(i.{input_geom}, o.{overlay_geom})")}
        """)

        # Part 2: Input-only features (subtract overlay from each input feature)
        logger.info("Creating input-only features")
        self.con.execute(f"""
            CREATE OR REPLACE VIEW input_only AS
            SELECT
                {input_fields},
                {null_overlay_fields},
                ST_Difference(i.{input_geom}, u.geom) AS {input_geom}
            FROM {input_table} i
            CROSS JOIN unified_overlay u
            WHERE ST_IsValid(i.{input_geom})
                AND NOT ST_IsEmpty(ST_Difference(i.{input_geom}, u.geom))
                {geom_type_filter.replace(input_geom, f"ST_Difference(i.{input_geom}, u.geom)")}
        """)

        # Part 3: Overlay-only features (subtract input from each overlay feature)
        logger.info("Creating overlay-only features")
        self.con.execute(f"""
            CREATE OR REPLACE VIEW overlay_only AS
            SELECT
                {null_input_fields},
                {overlay_fields},
                ST_Difference(o.{overlay_geom}, u.geom) AS {input_geom}
            FROM {overlay_table} o
            CROSS JOIN unified_input u
            WHERE ST_IsValid(o.{overlay_geom})
                AND NOT ST_IsEmpty(ST_Difference(o.{overlay_geom}, u.geom))
                {geom_type_filter.replace(input_geom, f"ST_Difference(o.{overlay_geom}, u.geom)")}
        """)

        # Combine all parts
        logger.info("Combining all union parts")
        self.con.execute("""
            CREATE OR REPLACE VIEW unioned AS
            SELECT * FROM overlapping_features
            UNION ALL
            SELECT * FROM input_only
            UNION ALL
            SELECT * FROM overlay_only
        """)

        # Handle output CRS transformation if needed
        output_view = "unioned"
        if params.output_crs and input_crs and params.output_crs != input_crs:
            self.con.execute(f"""
                CREATE OR REPLACE VIEW unioned_transformed AS
                SELECT * EXCLUDE ({input_geom}),
                    ST_Transform({input_geom}, '{input_crs}', '{params.output_crs}') AS {input_geom}
                FROM unioned
            """)
            output_view = "unioned_transformed"

        # Export to file
        self.con.execute(
            f"COPY {output_view} TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        logger.info("Two-layer union data written to %s", output_path)

    def get_allowed_output_geometry_types(
        self: Self,
        view_name: str,
        geom_column: str,
    ) -> str | None:
        """
        Determines allowed output geometry types based on input geometry type.
        Returns a SQL IN clause string or None if all types allowed.

        This is used to filter out degenerate geometries after operations like union.
        """
        # Detect geometry type from first feature
        input_geom_type = self.con.execute(f"""
            SELECT ST_GeometryType({geom_column}) 
            FROM {view_name} 
            LIMIT 1
        """).fetchone()[0]

        # Determine allowed output geometry types based on input type
        # Accept both single and multi versions of the same geometry family
        input_geom_upper = input_geom_type.upper()
        if "POLYGON" in input_geom_upper:  # Matches POLYGON or MULTIPOLYGON
            return "('POLYGON', 'MULTIPOLYGON')"
        elif "LINESTRING" in input_geom_upper:  # Matches LINESTRING or MULTILINESTRING
            return "('LINESTRING', 'MULTILINESTRING')"
        elif "POINT" in input_geom_upper:  # Matches POINT or MULTIPOINT
            return "('POINT', 'MULTIPOINT')"
        else:
            # Fallback: allow any geometry type
            return None

    def _build_field_selection(
        self, con, table_name: str, geom_column: str, alias: str, prefix: str
    ) -> str:
        """Build field selection SQL for a table, excluding geometry column."""
        result = con.execute(f"DESCRIBE {table_name}").fetchall()
        all_columns = [row[0] for row in result]
        data_columns = [col for col in all_columns if col != geom_column]

        field_exprs = []
        for col in data_columns:
            if prefix:
                field_exprs.append(f"{alias}.{col} AS {prefix}{col}")
            else:
                field_exprs.append(f"{alias}.{col}")

        return (
            ", ".join(field_exprs)
            if field_exprs
            else f"{alias}.__dummy__ AS __no_fields__"
        )

    def _get_null_overlay_fields(
        self, con, overlay_table: str, overlay_geom: str, prefix: str
    ) -> str:
        """Generate NULL values for overlay fields when they don't exist."""
        result = con.execute(f"DESCRIBE {overlay_table}").fetchall()
        overlay_columns = [row[0] for row in result if row[0] != overlay_geom]

        null_exprs = []
        for col in overlay_columns:
            field_name = f"{prefix}{col}" if prefix else col
            null_exprs.append(f"NULL AS {field_name}")

        return ", ".join(null_exprs) if null_exprs else "NULL AS __no_overlay_fields__"

    def _get_null_input_fields(self, con, input_table: str, input_geom: str) -> str:
        """Generate NULL values for input fields when they don't exist."""
        result = con.execute(f"DESCRIBE {input_table}").fetchall()
        input_columns = [row[0] for row in result if row[0] != input_geom]

        null_exprs = []
        for col in input_columns:
            null_exprs.append(f"NULL AS {col}")

        return ", ".join(null_exprs) if null_exprs else "NULL AS __no_input_fields__"
