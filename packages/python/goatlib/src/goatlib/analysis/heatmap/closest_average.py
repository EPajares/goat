import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.heatmap.base import HeatmapToolBase
from goatlib.analysis.schemas.heatmap import (
    HeatmapClosestAverageParams,
)
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class HeatmapClosestAverageTool(HeatmapToolBase):
    """
    Computes closest average heatmap - average value of the closest features within max travel time.
    """

    def _run_implementation(
        self: Self, params: HeatmapClosestAverageParams
    ) -> list[tuple[Path, DatasetMetadata]]:
        logger.info("Starting Heatmap Closest Average Analysis")

        # Register OD matrix and detect H3 resolution
        od_table, h3_resolution = self._prepare_od_matrix(params.od_matrix_source)
        logger.info(
            "OD matrix ready: table=%s, h3_resolution=%s", od_table, h3_resolution
        )

        # Process and standardize opportunities using detected resolution
        standardized_tables = self._process_opportunities(
            params.opportunities, h3_resolution
        )
