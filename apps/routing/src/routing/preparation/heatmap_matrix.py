from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple

import psycopg
from routing.core.config import settings
from routing.preparation.heatmap_matrix_process import HeatmapMatrixProcess
from routing.schemas.catchment_area import (
    CatchmentAreaRoutingTypeActiveMobility,
    CatchmentAreaRoutingTypeCar,
)
from routing.utils import print_info

"""
    Instructions for use:
    1. Set ROUTING_TYPE to the desired routing type / mode.
    2. Set NUM_THREADS to the desired number of threads.
    3. Set REPLACE_EXISTING_TABLE to True if you want to drop the existing table and create a new one.
    4. Set TRAVELTIME_MATRIX_REGIONS to al list of the desired regions to compute the heatmap matrix for.
    5. Set HEATMAP_MATRIX_DATE_SUFFIX in src/core/config.py to the date of computation.
    6. Ensure you're connecting to the correct database.
    7. Run the preparation script via the pre-defined launch config.

    Note: Each process currently takes a long time to process its first H3_6 cell, subsequent cells are much faster.
"""


class HeatmapMatrixPreparation:
    def __init__(self) -> None:
        # User configurable
        self.ROUTING_TYPE: (
            CatchmentAreaRoutingTypeActiveMobility | CatchmentAreaRoutingTypeCar
        ) = CatchmentAreaRoutingTypeActiveMobility.walking
        self.NUM_THREADS: int = 4
        self.REPLACE_EXISTING_TABLE: bool = False

        # Current heamtap matrix regions deployed in GOAT
        self.TRAVELTIME_MATRIX_REGIONS: List[str] = [
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'AT' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'CH' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'NL' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'HU' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'LI' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'LV' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'BG' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE cntr_code = 'DE' AND levl_code = 0",
            "SELECT ST_Union(geom) AS geom FROM public.nuts WHERE nuts_name = 'Haut-Rhin'",
        ]

    def get_cells_to_process(
        self, db_cursor: psycopg.Cursor, region_geofence: str
    ) -> List[str]:
        """Produce a grid of H3_6 cells to prepare the heatmap matrix in batches."""

        print_info("Producing H3_6 grid of traveltime matrix region.")

        # Produce and fetch a list of H3_6 cells representing the geofence region
        sql_fetch_region_h3_grid = f"""
            WITH region AS (
                {region_geofence}
            )
            SELECT grid.*
            FROM region,
            LATERAL basic.fill_polygon_h3(geom, 6) grid;
        """
        db_cursor.execute(sql_fetch_region_h3_grid)
        result = db_cursor.fetchall()

        cells_to_process: List[str] = []
        for h3_index in result:
            cells_to_process.append(h3_index[0])

        print_info(f"Number of H3_6 cells to process: {len(cells_to_process)}")

        return cells_to_process

    def split_cells_into_chunks(
        self, cells_to_process: List[str], region_geofence: str
    ) -> List[Tuple[int, List[str], str]]:
        """Split cells to process into NUM_THREADS chunks."""

        # Calculate chunk size and remainder
        chunk_size = len(cells_to_process) // self.NUM_THREADS
        remainder = len(cells_to_process) % self.NUM_THREADS

        # Split cells to process into thunks of size chunk_size + remainder
        chunks: List[Tuple[int, List[str], str]] = []
        start = 0
        for i in range(self.NUM_THREADS):
            end = (
                start + chunk_size + (1 if i < remainder else 0)
            )  # Use 1 if i < remainder else 0 for boolean to int conversion
            chunks.append((i, cells_to_process[start:end], region_geofence))
            start = end

        return chunks

    def initialize_traveltime_matrix_table(
        self, db_cursor: psycopg.Cursor, db_connection: psycopg.Connection
    ) -> None:
        """Create table to store traveltime matrix."""

        traveltime_matrix_table = f"basic.traveltime_matrix_{self.ROUTING_TYPE.value}_{settings.HEATMAP_MATRIX_DATE_SUFFIX}"

        # Drop table if it already exists
        sql_drop_table = f"""
            DROP TABLE IF EXISTS {traveltime_matrix_table};
        """
        db_cursor.execute(sql_drop_table)

        # Create table
        sql_create_table = f"""
            CREATE TABLE {traveltime_matrix_table} (
                orig_id h3index,
                dest_id h3index[],
                traveltime smallint,
                h3_3 int,
                PRIMARY KEY (orig_id, traveltime, h3_3)
            );
        """
        db_cursor.execute(sql_create_table)

        # Distribute table using CITUS
        sql_distribute_table = f"""
            SELECT create_distributed_table(
                '{traveltime_matrix_table}',
                'h3_3'
            );
        """
        db_cursor.execute(sql_distribute_table)

        # Commit changes
        db_connection.commit()

        print_info(f"Initialized traveltime matrix table: {traveltime_matrix_table}")

    def process_chunk(self, chunk: Tuple[int, List[str], str]) -> None:
        HeatmapMatrixProcess(
            thread_id=chunk[0],
            chunk=chunk[1],
            region_geofence=chunk[2],
            routing_type=self.ROUTING_TYPE,
        ).run()

    def run(self) -> None:
        # Connect to database
        db_connection: psycopg.Connection = psycopg.connect(
            settings.POSTGRES_DATABASE_URI
        )
        db_cursor: psycopg.Cursor = db_connection.cursor()

        # Initialize traveltime matrix table
        if self.REPLACE_EXISTING_TABLE:
            self.initialize_traveltime_matrix_table(db_cursor, db_connection)

        for index in range(len(self.TRAVELTIME_MATRIX_REGIONS)):
            print_info(
                f"Processing region {index + 1} of {len(self.TRAVELTIME_MATRIX_REGIONS)}"
            )

            # Get full list of parent H3_6 cells within our region of interest
            cells_to_process: List[str] = self.get_cells_to_process(
                db_cursor=db_cursor,
                region_geofence=self.TRAVELTIME_MATRIX_REGIONS[index],
            )

            # Split cells to process into NUM_THREADS chunks to be processed in parallel
            chunks: List[Tuple[int, List[str], str]] = self.split_cells_into_chunks(
                cells_to_process=cells_to_process,
                region_geofence=self.TRAVELTIME_MATRIX_REGIONS[index],
            )

            try:
                # Spawn NUM_THREADS processes to compute matrix in parallel
                with ProcessPoolExecutor(max_workers=self.NUM_THREADS) as process_pool:
                    # process_pool.map expects a callable that takes a single argument,
                    # and chunks is already a list of tuples, so it works directly.
                    process_pool.map(self.process_chunk, chunks)
            except Exception as e:
                print(e)
                break

            # Await user confirmation before proceeding to next region
            print_info(
                f"Region {index + 1} of {len(self.TRAVELTIME_MATRIX_REGIONS)} processed."
            )
            print("\n")

        # Close database connection
        db_connection.close()


if __name__ == "__main__":
    HeatmapMatrixPreparation().run()
