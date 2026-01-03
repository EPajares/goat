"""Heatmap Closest Average tool for Windmill.

Computes closest average heatmap - average value of the closest features within max cost.
"""

import logging
from pathlib import Path
from typing import Any, Self

from pydantic import Field

from goatlib.analysis.accessibility import HeatmapClosestAverageTool
from goatlib.analysis.schemas.heatmap import HeatmapClosestAverageParams
from goatlib.analysis.schemas.ui import ui_field
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase
from goatlib.tools.style import get_heatmap_style

logger = logging.getLogger(__name__)


class HeatmapClosestAverageToolParams(ToolInputBase, HeatmapClosestAverageParams):
    """Parameters for heatmap closest average tool.

    Inherits heatmap options from HeatmapClosestAverageParams, adds layer context from ToolInputBase.
    """

    # Override file paths as optional - they will be resolved internally
    od_matrix_path: str | None = Field(
        default=None,
        description="Path to OD matrix (auto-populated from routing_mode if not provided)",
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    output_path: str | None = None  # type: ignore[assignment]


class HeatmapClosestAverageToolRunner(BaseToolRunner[HeatmapClosestAverageToolParams]):
    """Heatmap Closest Average tool runner for Windmill."""

    tool_class = HeatmapClosestAverageTool
    output_geometry_type = "polygon"  # H3 cells
    default_output_name = "Heatmap_Closest_Average"

    def get_layer_properties(
        self: Self,
        params: HeatmapClosestAverageToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return heatmap style for closest average accessibility with quantile breaks."""
        color_field = "total_accessibility"

        # Compute quantile breaks from the DuckLake table (6 breaks for 7 colors)
        color_scale_breaks = None
        if table_info and table_info.get("table_name"):
            color_scale_breaks = self.compute_quantile_breaks(
                table_name=table_info["table_name"],
                column_name=color_field,
                num_breaks=6,
                strip_zeros=True,
            )
            if color_scale_breaks:
                logger.info(
                    "Computed quantile breaks for %s: %s",
                    color_field,
                    color_scale_breaks,
                )

        # Use Emrld (green) for closest average - represents access to opportunities
        return get_heatmap_style(
            color_field_name=color_field,
            color_scale_breaks=color_scale_breaks,
            color_range_name="Emrld",
        )

    def process(
        self: Self, params: HeatmapClosestAverageToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run heatmap closest average analysis."""
        output_path = temp_dir / "output.parquet"

        # Resolve opportunity layer IDs to parquet paths
        resolved_opportunities = self.resolve_layer_paths(
            params.opportunities, params.user_id, "input_path"
        )

        # Build analysis params
        analysis_params = HeatmapClosestAverageParams(
            **params.model_dump(
                exclude={
                    "output_path",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "output_name",
                    "opportunities",  # Use resolved opportunities
                }
            ),
            opportunities=resolved_opportunities,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: HeatmapClosestAverageToolParams) -> dict:
    """Windmill entry point for heatmap closest average tool."""
    runner = HeatmapClosestAverageToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
