import logging
from pathlib import Path
from typing import List, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.geoprocessing import DifferenceParams
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class DifferenceTool(AnalysisTool):
    """Tool for computing the difference between input and overlay geometries.

    This tool implements the QGIS 'Difference' operation using DuckDB views with bbox optimization.
    Automatically handles bbox columns for spatial indexing - creates them if needed or uses
    existing ones. Follows GeoParquet spatial indexing specification.
    """

    def _run_implementation(
        self: Self, params: DifferenceParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform difference operation using views with bbox spatial optimization.

        Args:
            params: DifferenceParams object with input_path, overlay_path, and other options.

        Returns:
            List containing tuple of (output_path, metadata).
        """

        # Import input and overlay datasets with automatic bbox handling
        input_meta, input_view = self.import_input(params.input_path, "input_data")
        overlay_meta, overlay_view = self.import_input(
            params.overlay_path, "overlay_data"
        )

        # Validate geometry columns
        input_geom = input_meta.geometry_column
        overlay_geom = overlay_meta.geometry_column

        if not input_geom:
            raise ValueError(
                f"Could not detect geometry column for input: {params.input_path}"
            )

        if not overlay_geom:
            raise ValueError(
                f"Could not detect geometry column for overlay: {params.overlay_path}"
            )

        # Validate geometry types
        self.validate_geometry_types(
            input_view, input_geom, params.accepted_input_geometry_types, "input"
        )
        self.validate_geometry_types(
            overlay_view,
            overlay_geom,
            params.accepted_overlay_geometry_types,
            "overlay",
        )

        # Get CRS from input metadata, fallback to output_crs or EPSG:4326
        crs = input_meta.crs
        if crs:
            crs_str = crs.to_string()
        else:
            crs_str = params.output_crs or "EPSG:4326"
            logger.warning(
                "Could not detect CRS for %s, using fallback: %s",
                params.input_path,
                crs_str,
            )

        # Define output path
        if not params.output_path:
            params.output_path = str(
                Path(params.input_path).parent
                / f"{Path(params.input_path).stem}_difference.parquet"
            )
        output_path = Path(params.output_path)

        # Perform difference operation using views with bbox optimization
        # Both views now have bbox columns (either pre-existing or created by import_input)
        logger.info("Performing view-based difference with bbox spatial filtering")

        # Detect input geometry type to filter output appropriately
        input_geom_type = self.con.execute(f"""
            SELECT ST_GeometryType({input_geom}) 
            FROM {input_view} 
            LIMIT 1
        """).fetchone()[0]

        # Determine allowed output geometry types based on input type
        # Accept both single and multi versions of the same geometry family
        input_geom_upper = input_geom_type.upper()
        if "POLYGON" in input_geom_upper:  # Matches POLYGON or MULTIPOLYGON
            allowed_types = "('POLYGON', 'MULTIPOLYGON')"
        elif "LINESTRING" in input_geom_upper:  # Matches LINESTRING or MULTILINESTRING
            allowed_types = "('LINESTRING', 'MULTILINESTRING')"
        elif "POINT" in input_geom_upper:  # Matches POINT or MULTIPOINT
            allowed_types = "('POINT', 'MULTIPOINT')"
        else:
            # Fallback: allow any geometry type
            allowed_types = None

        logger.info(
            f"Input geometry type: {input_geom_type}, filtering output to: {allowed_types}"
        )

        # First, create a unified overlay geometry from all overlay features
        logger.info("Creating unified overlay geometry from all overlay features")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE unified_overlay AS
            WITH unified AS (
                SELECT ST_Union_Agg({overlay_geom}) as geom
                FROM {overlay_view}
                WHERE ST_IsValid({overlay_geom})
            )
            SELECT
                geom as unified_geom,
                {{
                    'minx': ST_XMin(geom),
                    'maxx': ST_XMax(geom),
                    'miny': ST_YMin(geom),
                    'maxy': ST_YMax(geom)
                }} AS bbox
            FROM unified
        """)

        # Then compute difference for each input feature against the unified overlay
        logger.info(
            "Computing difference against unified overlay geometry with bbox optimization"
        )

        # Build geometry type filter clause
        geom_type_filter = ""
        if allowed_types:
            geom_type_filter = f"""
                AND (
                    u.unified_geom IS NULL 
                    OR ST_GeometryType(ST_Difference(i.{input_geom}, u.unified_geom)) IN {allowed_types}
                )
            """

        self.con.execute(f"""
            CREATE OR REPLACE VIEW difference_result AS
            SELECT
                i.* EXCLUDE ({input_geom}, bbox),
                CASE
                    WHEN u.unified_geom IS NOT NULL 
                        AND ST_Intersects(i.{input_geom}, u.unified_geom)
                        -- Bbox-based spatial filter for performance (GeoParquet spatial indexing)
                        AND i.bbox.minx <= u.bbox.maxx
                        AND i.bbox.maxx >= u.bbox.minx
                        AND i.bbox.miny <= u.bbox.maxy
                        AND i.bbox.maxy >= u.bbox.miny
                    THEN
                        ST_Difference(i.{input_geom}, u.unified_geom)
                    ELSE
                        i.{input_geom}
                END AS {input_geom}
            FROM {input_view} i
            LEFT JOIN unified_overlay u ON TRUE
            WHERE ST_IsValid(i.{input_geom})
                AND (
                    u.unified_geom IS NULL
                    OR NOT ST_IsEmpty(
                        CASE
                            WHEN ST_Intersects(i.{input_geom}, u.unified_geom)
                            THEN ST_Difference(i.{input_geom}, u.unified_geom)
                            ELSE i.{input_geom}
                        END
                    )
                )
                -- Filter out degenerate geometries - keep only same type as input (ArcGIS/QGIS behavior)
                {geom_type_filter}
        """)

        # Export view result to file
        self.con.execute(
            f"COPY difference_result TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        logger.info("Difference data written to %s", output_path)

        # Create metadata for output
        output_metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            geometry_column=input_geom,
            crs=crs_str,
            schema="public",
            table_name=output_path.stem,
        )

        return [(output_path, output_metadata)]
