"""Heatmap Gravity tool for Windmill.

Performs gravity-based spatial accessibility analysis.
"""

import logging
from pathlib import Path
from typing import Any, Self

from pydantic import ConfigDict, Field

from goatlib.analysis.accessibility import HeatmapGravityTool
from goatlib.analysis.schemas.heatmap import HeatmapGravityParams
from goatlib.analysis.schemas.ui import (
    SECTION_CONFIGURATION,
    SECTION_OPPORTUNITIES,
    SECTION_RESULT_ROUTING,
    SECTION_ROUTING,
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import (
    get_default_layer_name,
    ScenarioSelectorMixin,
    ToolInputBase,
)
from goatlib.tools.style import get_heatmap_style

logger = logging.getLogger(__name__)


class HeatmapGravityToolParams(
    ScenarioSelectorMixin, ToolInputBase, HeatmapGravityParams
):
    """Parameters for heatmap gravity tool.

    Inherits heatmap options from HeatmapGravityParams, adds layer context from ToolInputBase.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_ROUTING,
            SECTION_CONFIGURATION,
            SECTION_OPPORTUNITIES,
            SECTION_RESULT_ROUTING,
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                collapsible=True,
                collapsed=True,
            ),
        )
    )

    # Override file paths as optional - they will be resolved internally
    od_matrix_path: str | None = Field(
        default=None,
        description="Path to OD matrix (auto-populated from routing_mode if not provided)",
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    output_path: str | None = None  # type: ignore[assignment]

    # Override result_layer_name with tool-specific defaults
    result_layer_name: str | None = Field(
        default=get_default_layer_name("heatmap_gravity", "en"),
        description="Name for the heatmap gravity result layer.",
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget_options={
                "default_en": get_default_layer_name("heatmap_gravity", "en"),
                "default_de": get_default_layer_name("heatmap_gravity", "de"),
            },
        ),
    )


class HeatmapGravityToolRunner(BaseToolRunner[HeatmapGravityToolParams]):
    """Heatmap Gravity tool runner for Windmill."""

    tool_class = HeatmapGravityTool
    output_geometry_type = "polygon"  # H3 cells
    default_output_name = get_default_layer_name("heatmap_gravity", "en")

    def get_layer_properties(
        self: Self,
        params: HeatmapGravityToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return heatmap style for gravity accessibility with quantile breaks."""
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

        # Use Emrld (green) for gravity - represents access to opportunities
        return get_heatmap_style(
            color_field_name=color_field,
            color_scale_breaks=color_scale_breaks,
            color_range_name="Emrld",
        )

    def process(
        self: Self, params: HeatmapGravityToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run heatmap gravity analysis."""
        output_path = temp_dir / "output.parquet"

        # Resolve opportunity layer IDs to parquet paths
        resolved_opportunities = self.resolve_layer_paths(
            params.opportunities, params.user_id, "input_path"
        )

        # Build analysis params
        analysis_params = HeatmapGravityParams(
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


def main(params: HeatmapGravityToolParams) -> dict:
    """Windmill entry point for heatmap gravity tool."""
    runner = HeatmapGravityToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
