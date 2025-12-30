import logging
from pathlib import Path
from typing import List, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.geoprocessing import ClipParams
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class ClipTool(AnalysisTool):
    """Tool for clipping features from input layer using overlay layer geometry.

    This tool implements the standard clip operation using DuckDB views with bbox optimization.
    Automatically handles bbox columns for spatial indexing - creates them if needed or uses
    existing ones. Follows GeoParquet spatial indexing specification.
    """

    def _run_implementation(
        self: Self, params: ClipParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform clip operation using views with bbox spatial optimization.

        Args:
            params: ClipParams object with input_path, overlay_path, and other options.

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

        # For WGS84 datasets, assume both are in EPSG:4326 (no CRS conversion needed)
        logger.info(
            "Assuming both datasets are in EPSG:4326 (WGS84) - no CRS conversion required"
        )

        # Define output path
        if not params.output_path:
            params.output_path = str(
                Path(params.input_path).parent
                / f"{Path(params.input_path).stem}_clip.parquet"
            )
        output_path = Path(params.output_path)

        # Perform clipping operation using views with bbox optimization
        # Both views now have bbox columns (either pre-existing or created by import_input)
        logger.info("Performing view-based clipping with bbox spatial filtering")

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

        # Then clip each input feature against the unified overlay
        logger.info(
            "Performing clipping against unified overlay geometry with bbox optimization"
        )

        # Build geometry type filter clause
        geom_type_filter = (
            f"AND ST_GeometryType(ST_Intersection(i.{input_geom}, u.unified_geom)) IN {allowed_types}"
            if allowed_types
            else ""
        )

        self.con.execute(f"""
            CREATE OR REPLACE VIEW clipped_result AS
            SELECT
                i.* EXCLUDE ({input_geom}, bbox),
                ST_Intersection(i.{input_geom}, u.unified_geom) AS {input_geom}
            FROM {input_view} i
            CROSS JOIN unified_overlay u
            WHERE ST_IsValid(i.{input_geom})
                AND ST_Intersects(i.{input_geom}, u.unified_geom)
                -- Bbox-based spatial filter for performance (GeoParquet spatial indexing)
                AND i.bbox.minx <= u.bbox.maxx
                AND i.bbox.maxx >= u.bbox.minx
                AND i.bbox.miny <= u.bbox.maxy
                AND i.bbox.maxy >= u.bbox.miny
                AND NOT ST_IsEmpty(ST_Intersection(i.{input_geom}, u.unified_geom))
                -- Filter out degenerate geometries - keep only same type as input (ArcGIS/QGIS behavior)
                {geom_type_filter}
        """)

        # Export view result to file
        self.con.execute(
            f"COPY clipped_result TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        logger.info("Clipped data written to %s", output_path)

        # Create metadata for output
        output_metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            geometry_column=input_geom,
            crs="EPSG:4326",
            schema="public",
            table_name=output_path.stem,
        )

        return [(output_path, output_metadata)]
