import logging
from pathlib import Path
from typing import List, Optional, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.geoprocessing import BufferParams
from goatlib.models.io import DatasetMetadata
from goatlib.utils.helper import UNIT_TO_METERS

logger = logging.getLogger(__name__)


class BufferTool(AnalysisTool):
    """
    BufferTool: Buffers geometries by fixed or per-feature distances using DuckDB Spatial.
    """

    def _run_implementation(
        self: Self, params: BufferParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform buffer operation on a vector dataset."""

        # --- Import directly into DuckDB
        meta, table_name = self.import_input(params.input_path)
        geom_col = meta.geometry_column
        crs = meta.crs

        if not geom_col:
            raise ValueError(
                f"Could not detect geometry column for {params.input_path}."
            )

        # Fallback to output_crs (default EPSG:4326) if CRS not detected
        # This happens when exporting from DuckLake which doesn't preserve GeoParquet metadata
        if crs:
            crs_str = crs.to_string()
        else:
            crs_str = params.output_crs or "EPSG:4326"
            logger.warning(
                "Could not detect CRS for %s, using fallback: %s",
                params.input_path,
                crs_str,
            )

        # --- Define output path
        if not params.output_path:
            params.output_path = str(
                Path(params.input_path).parent
                / f"{Path(params.input_path).stem}_buffer.parquet"
            )
        output_path = Path(params.output_path)
        logger.info(
            "Starting buffer: %s | table='%s' | geometry='%s' | CRS=%s",
            params.input_path,
            table_name,
            geom_col,
            crs_str,
        )

        # --- Execute buffer operation
        self._execute_buffer(params, table_name, geom_col, crs_str, output_path)

        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            format="geoparquet",
            crs=crs_str or params.output_crs,
            geometry_type="Polygon",
        )

        logger.info("Buffer completed successfully → %s", output_path)
        return [(output_path, metadata)]

    def _execute_buffer(
        self: Self,
        params: BufferParams,
        table_name: str,
        geom_col: str,
        input_crs_str: Optional[str],
        output_path: Path,
    ) -> None:
        """Execute the buffer operation in DuckDB."""
        con = self.con

        work_view = "v_work"
        con.execute(
            f"""
            CREATE OR REPLACE VIEW {work_view} AS
            SELECT * EXCLUDE ({geom_col}),
                {geom_col} AS geom
            FROM {table_name}
            """
        )

        opts = (
            f"quad_segs => {params.num_triangles}, "
            f"endcap_style => '{params.cap_style}', "
            f"join_style => '{params.join_style}', "
            f"mitre_limit => {params.mitre_limit}"
        )

        # --- Always project to EPSG:3857 for planar buffering
        projected_geom_expr = (
            f"ST_Transform(geom, '{input_crs_str}', 'EPSG:3857')"
            if input_crs_str
            else "geom"
        )

        # --- Convert distance units
        distances_m = [
            d * UNIT_TO_METERS[params.units] for d in (params.distances or [])
        ]

        # --- Buffer execution (simplified for clarity)
        buffer_tables = []
        for i, dist in enumerate(distances_m):
            tmp = f"buf_{i}"
            con.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE {tmp} AS
                SELECT * EXCLUDE (geom),
                    ST_Buffer({projected_geom_expr}, {dist}, {opts}) AS geometry
                FROM {work_view}
                """
            )
            buffer_tables.append(tmp)

        con.execute(
            "CREATE OR REPLACE TEMP TABLE buffers AS "
            + " UNION ALL ".join(f"SELECT * FROM {t}" for t in buffer_tables)
        )

        # --- Optional dissolve
        source = "buffers"
        if params.dissolve:
            con.execute(
                """
                CREATE OR REPLACE TEMP TABLE dissolved AS
                SELECT ST_Union_Agg(geometry) AS geometry
                FROM buffers
                """
            )
            source = "dissolved"

        # --- Reproject back to input CRS
        if input_crs_str:
            con.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE final_buffers AS
                SELECT * EXCLUDE (geometry),
                    ST_Transform(geometry, 'EPSG:3857', '{input_crs_str}') AS geometry
                FROM {source}
                """
            )
            source = "final_buffers"

        con.execute(
            f"COPY {source} TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        logger.info("GeoParquet written to %s", output_path)
