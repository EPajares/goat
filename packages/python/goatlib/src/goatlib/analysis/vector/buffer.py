import logging
from pathlib import Path
from typing import List, Optional, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.vector import BufferParams
from goatlib.io.formats import VECTOR_EXTS
from goatlib.io.ingest import convert_any
from goatlib.io.utils import (
    download_if_remote,
    get_parquet_metadata,
)
from goatlib.models.io import DatasetMetadata
from goatlib.utils.helper import UNIT_TO_METERS
from pyproj import CRS

logger = logging.getLogger(__name__)


class BufferTool(AnalysisTool):
    """
    BufferTool: Buffers geometries by fixed or per-feature distances using DuckDB Spatial.
    """

    def run(
        self: "BufferTool", params: BufferParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform buffer operation on a vector dataset."""
        input_path = Path(download_if_remote(params.input_path))
        if input_path.suffix.lower() not in VECTOR_EXTS:
            raise ValueError(f"Unsupported input format: {input_path.suffix}")

        # --- Convert non-Parquet sources
        if input_path.suffix.lower() != ".parquet":
            converted = convert_any(str(input_path), input_path.parent)
            if not converted or not isinstance(converted[0][0], Path):
                raise RuntimeError(f"Failed to convert input {input_path} to Parquet.")
            params.input_path = str(converted[0][0])
            input_path = Path(params.input_path)

        # --- Define output path
        if not params.output_path:
            params.output_path = str(
                input_path.parent / f"{input_path.stem}_buffer.parquet"
            )

        output_path = Path(params.output_path)

        # --- Extract metadata
        meta = get_parquet_metadata(self.con, str(input_path))
        geom_col = meta.get("geometry_column")
        input_crs = meta.get("crs")  # CRS in GeoParquet (projjson dict or str)

        if not geom_col:
            raise ValueError(f"Could not detect geometry column for {input_path}.")

        # --- Parse CRS properly
        crs_obj = None
        try:
            if input_crs:
                crs_obj = (
                    CRS.from_json(input_crs)
                    if isinstance(input_crs, str)
                    else CRS.from_json_dict(input_crs)
                )
        except Exception as e:
            logger.warning(f"Failed to parse CRS from GeoParquet metadata: {e}")

        auth_str = None
        if crs_obj and crs_obj.to_authority():
            auth_str = f"{crs_obj.to_authority()[0]}:{crs_obj.to_authority()[1]}"

        logger.info(
            "Starting buffer: %s | geometry='%s' | CRS=%s",
            input_path,
            geom_col,
            auth_str or "unknown",
        )

        # --- Execute buffer
        self._execute_buffer(params, geom_col, crs_obj, output_path)

        metadata = DatasetMetadata(
            source=str(input_path),
            output=str(output_path),
            crs=auth_str or params.output_crs,
            operation="buffer",
        )

        logger.info("Buffer completed successfully → %s", output_path)
        return [(output_path, metadata)]

    def _execute_buffer(
        self: "BufferTool",
        params: BufferParams,
        geom_col: str,
        input_crs: Optional[CRS],
        output_path: Path,
    ) -> None:
        """Execute the buffer operation in DuckDB, preserving attributes."""
        con = self.con
        input_path = Path(params.input_path)

        # --- Register input view
        con.execute(
            f"""
            CREATE OR REPLACE VIEW v_input AS
            SELECT * EXCLUDE ({geom_col}),
                {geom_col} AS geom
            FROM read_parquet('{input_path}')
            """
        )

        # --- Buffer options
        opts = (
            f"quad_segs => {params.num_triangles}, "
            f"endcap_style => '{params.cap_style}', "
            f"join_style => '{params.join_style}', "
            f"mitre_limit => {params.mitre_limit}"
        )

        # --- Determine CRS strings
        if input_crs and input_crs.to_authority():
            source_crs_str = (
                f"{input_crs.to_authority()[0]}:{input_crs.to_authority()[1]}"
            )
        else:
            source_crs_str = None
            logger.warning(
                "Input CRS unknown or non-standard; assuming planar coordinates."
            )

        # --- Always project to EPSG:3857 for planar buffering
        projected_geom_expr = (
            f"ST_Transform(geom, '{source_crs_str}', 'EPSG:3857')"
            if source_crs_str
            else "geom"
        )

        # --- Convert distance units
        if params.distances:
            distances_m = [d * UNIT_TO_METERS[params.units] for d in params.distances]
        else:
            distances_m = None

        # --- Buffer operation
        if params.field:
            # Per-feature distance from attribute
            con.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE buffers AS
                SELECT * EXCLUDE (geom),
                       ST_Buffer({projected_geom_expr}, {params.field}, {opts}) AS geometry
                FROM v_input
                """
            )
        else:
            # Fixed distances
            buffer_tables = []
            for i, dist in enumerate(distances_m):
                tmp = f"buf_{i}"
                con.execute(
                    f"""
                    CREATE OR REPLACE TEMP TABLE {tmp} AS
                    SELECT * EXCLUDE (geom),
                        ST_Buffer({projected_geom_expr}, {dist}, {opts}) AS geometry
                    FROM v_input
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
            logger.info("Dissolving buffered geometries...")
            con.execute(
                """
                CREATE OR REPLACE TEMP TABLE dissolved AS
                SELECT ST_Union_Agg(geometry) AS geometry
                FROM buffers
                """
            )
            source = "dissolved"

        # --- Transform back to original CRS
        if source_crs_str:
            con.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE final_buffers AS
                SELECT ST_Transform(geometry, 'EPSG:3857', '{source_crs_str}') AS geometry,
                       * EXCLUDE (geometry)
                FROM {source}
                """
            )
            source = "final_buffers"

        # --- Export to GeoParquet
        con.execute(
            f"COPY {source} TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        logger.info("GeoParquet written to %s", output_path)
