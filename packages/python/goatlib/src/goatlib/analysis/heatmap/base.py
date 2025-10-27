import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.core.base import AnalysisTool
from goatlib.io.utils import Metadata

logger = logging.getLogger(__name__)


def to_short_h3(h3_index: int) -> int | None:
    if h3_index is None:
        return None
    mask = 0x000FFFF000000000
    return (h3_index & mask) >> 36


class HeatmapToolBase(AnalysisTool):
    """Base class for heatmap analysis tools."""

    def __init__(self: Self) -> None:
        super().__init__()
        self._setup_heatmap_extensions()
        # Additional initialization for heatmap tools can go here

    def _setup_heatmap_extensions(self: Self) -> None:
        """Install required extensions and register helper functions."""
        self.con.execute("INSTALL h3 FROM community; LOAD h3;")
        self.con.create_function("to_short_h3", to_short_h3)
        logger.debug("H3 extensions and helper UDFs loaded.")

    def _prepare_od_matrix(
        self: Self, od_matrix_source: str, od_matrix_view_name: str = "od_matrix"
    ) -> tuple[str, int]:
        """
        Register OD matrix source as a DuckDB VIEW and detect H3 resolution.
        Returns (view_name, h3_resolution)
        """
        view_name = od_matrix_view_name
        try:
            self.con.execute(f"""
                CREATE OR REPLACE TEMP VIEW {view_name} AS
                SELECT * FROM read_parquet('{od_matrix_source}')
            """)
        except Exception as e:
            raise ValueError(
                f"Failed to register OD matrix from '{od_matrix_source}': {e}"
            )

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

        # Detect H3 resolution
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

        raise ValueError("Could not detect H3 resolution from OD matrix")

    def _filter_od_matrix(
        self: Self, od_table: str, origin_ids: list[int], h3_partitions: list[int]
    ) -> str:
        """Efficiently filter the OD matrix by origin IDs and partitions."""
        filtered_table = "filtered_matrix"

        if not origin_ids:
            raise ValueError("No origin IDs provided for filtering.")

        origin_ids_sql = ", ".join(map(str, origin_ids))

        if h3_partitions:
            h3_sql = ", ".join(map(str, h3_partitions))
            query = f"""
                CREATE OR REPLACE TEMP TABLE {filtered_table} AS
                SELECT orig_id, dest_id, traveltime
                FROM {od_table}
                WHERE to_short_h3(orig_id) IN ({h3_sql})
                  AND orig_id IN ({origin_ids_sql})
            """
        else:
            query = f"""
                CREATE OR REPLACE TEMP TABLE {filtered_table} AS
                SELECT orig_id, dest_id, traveltime
                FROM {od_table}
                WHERE orig_id IN ({origin_ids_sql})
            """

        self.con.execute(query)
        count = self.con.execute(f"SELECT COUNT(*) FROM {filtered_table}").fetchone()[0]
        logger.info("Filtered OD matrix created with %d rows", count)
        return filtered_table

    def _extract_origin_ids(self: Self, table: str) -> list[int]:
        res = self.con.execute(
            f"SELECT DISTINCT orig_id FROM {table} WHERE orig_id IS NOT NULL"
        ).fetchall()
        return [r[0] for r in res] if res else []

    def _compute_h3_partitions(self: Self, origin_ids: list[int]) -> list[int]:
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
            SELECT DISTINCT to_short_h3(orig_id) AS h3_partition
            FROM temp_origin_ids
            WHERE orig_id IS NOT NULL
        """).fetchall()

        return [row[0] for row in result] if result else []

    def _process_table_to_h3(
        self: Self,
        input_table: str,
        meta: Metadata,
        h3_resolution: int,
        output_table: str,
    ) -> str:
        """Convert any geometry (including Multi*) to H3 cells at specified resolution."""

        geom_type = meta.geometry_type.lower()
        geom_col = meta.geometry_column
        if not geom_col or not geom_type:
            raise ValueError(
                "No geometry column or type found in input data. "
                "H3 conversion requires geometries. "
                "Please ensure your input data has proper geometry metadata."
            )

        if not hasattr(meta, "crs") or meta.crs is None:
            raise ValueError(
                "No CRS information found in input data. "
                "H3 conversion requires known coordinate reference system. "
                "Please ensure your input data has proper CRS metadata."
            )

        transform_to_4326 = geom_col
        try:
            if meta.crs.to_epsg() != 4326:
                source_crs = meta.crs.to_string()
                logger.info(f"Transforming geometry from {source_crs} to EPSG:4326")
                transform_to_4326 = (
                    f"ST_Transform({geom_col}, '{source_crs}', 'EPSG:4326')"
                )
            else:
                logger.debug("Geometry is already in EPSG:4326")
        except Exception as e:
            raise ValueError(
                f"Could not determine EPSG code from CRS: {e}. "
                "H3 conversion requires known coordinate reference system."
            )

        # Base CTE for dumping geometries
        # ST_Dump breaks Multi* geometries into simple components (e.g., MultiPoint -> individual Points)
        # ST_Force2D ensures the geometries are 2D (removing any Z dimension)
        # and returns a structure where we can unnest to get individual geometries
        dumped_geoms_cte = f"""
                    WITH dumped_geoms AS (
                        SELECT
                            (UNNEST(ST_Dump(ST_Force2D({transform_to_4326})))).geom AS simple_geom
                        FROM {input_table}
                        WHERE {geom_col} IS NOT NULL
                    )
                """

        if "point" in geom_type:
            query = f"""
                    CREATE OR REPLACE TEMP TABLE {output_table} AS
                    {dumped_geoms_cte},
                    h3_cells AS (
                        SELECT
                            h3_latlng_to_cell(ST_Y(simple_geom), ST_X(simple_geom), {h3_resolution}) AS h3_index
                        FROM dumped_geoms
                    )
                    SELECT DISTINCT h3_index FROM h3_cells
                """
        elif "polygon" in geom_type:
            query = f"""
                    CREATE OR REPLACE TEMP TABLE {output_table} AS
                    {dumped_geoms_cte},
                    exploded AS (
                        SELECT
                            UNNEST(h3_polygon_wkt_to_cells(ST_AsText(simple_geom), {h3_resolution})) AS h3_index
                        FROM dumped_geoms
                    )
                    SELECT DISTINCT h3_index FROM exploded
                """
        elif "line" in geom_type:
            query = f"""
                    CREATE OR REPLACE TEMP TABLE {output_table} AS
                    {dumped_geoms_cte},
                    sampled AS (
                        SELECT ST_SamplePoints(simple_geom, 100) AS pts
                        FROM dumped_geoms
                    ),
                    unnested AS (
                        SELECT UNNEST(pts) AS geom FROM sampled
                    ),
                    h3_cells AS (
                        SELECT
                            h3_latlng_to_cell(ST_Y(geom), ST_X(geom), {h3_resolution}) AS h3_index
                        FROM unnested
                    )
                    SELECT DISTINCT h3_index FROM h3_cells
                """
        else:
            raise ValueError(f"Unsupported geometry type: '{geom_type}'")

        self.con.execute(query)
        count = self.con.execute(f"SELECT COUNT(*) FROM {output_table}").fetchone()[0]
        logger.info("Converted %d geometries to H3 cells: %s", count, output_table)
        return output_table

    def _export_h3_results(
        self: Self,
        results_table: str,
        output_path: str,
        h3_column: str = "h3_index",
    ) -> None:
        """Export results"""
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if output_path_obj.suffix.lower() != ".parquet":
            output_path_obj = output_path_obj.with_suffix(".parquet")

        query = f"""
            COPY (
                SELECT
                    *,
                    ST_AsWKB(ST_GeomFromText(h3_cell_to_boundary_wkt({h3_column}))) AS geometry
                FROM {results_table}
                ORDER BY {h3_column}
            ) TO '{output_path_obj}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
        self.con.execute(query)
        logger.info("Results written to: %s", output_path)
        return None
