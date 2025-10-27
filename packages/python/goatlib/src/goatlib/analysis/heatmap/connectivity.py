import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.heatmap.base import HeatmapToolBase
from goatlib.analysis.schemas.heatmap import HeatmapConnectivityParams
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class HeatmapConnectivityTool(HeatmapToolBase):
    """
    Computes connectivity heatmap - total area reachable within max travel time.
    """

    def _run_implementation(
        self: Self, params: HeatmapConnectivityParams
    ) -> list[tuple[Path, DatasetMetadata]]:
        logger.info("Starting Heatmap Connectivity Analysis")

        # Prepare OD matrix
        od_table, h3_resolution = self._prepare_od_matrix(params.od_matrix_source)
        logger.info(
            "OD matrix ready: table=%s, h3_resolution=%s", od_table, h3_resolution
        )

        # Input reference layer
        meta, reference_table = self.import_input(
            params.reference_area_path, table_name="reference_area"
        )

        # Process reference area to H3 cells
        reference_table_h3 = self._process_table_to_h3(
            reference_table, meta, h3_resolution, "reference_area_h3"
        )

        # Extract unique origin IDs
        origins_table = self._extract_unique_h3_indices(
            reference_table_h3, "temp_origins"
        )

        # Compute H3 partitions for efficient filtering
        partitions_table = self._compute_h3_partitions(origins_table, "temp_partitions")

        # Filter OD matrix
        filtered_matrix = self._filter_od_matrix(
            od_table,
            origins_table,
            partitions_table,
            params.max_traveltime,
            "filtered_matrix",
        )

        # Compute connectivity scores
        connectivity_table = self._compute_connectivity_scores(
            filtered_matrix, h3_resolution, "connectivity_scores"
        )

        return self._export_h3_results(connectivity_table, params.output_path)

    def _compute_connectivity_scores(
        self: Self, filtered_matrix: str, target_table: str = "connectivity_scores"
    ) -> str:
        """Compute connectivity scores using built-in h3_cell_area function."""

        query = f"""
            CREATE OR REPLACE TEMP TABLE {target_table} AS
            SELECT
                dest_id as h3_index,
                COUNT(*) * h3_cell_area(dest_id, 'm^2') AS accessibility,
                COUNT(*) AS reachable_cells
            FROM {filtered_matrix}
            GROUP BY dest_id
        """
        self.con.execute(query)

        row_count = self.con.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[
            0
        ]
        logger.info("Computed connectivity scores for %d destinations", row_count)
        return target_table
