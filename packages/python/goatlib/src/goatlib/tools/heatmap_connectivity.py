"""Heatmap Connectivity tool for Windmill.

Computes connectivity heatmap - total area reachable within max cost.
"""

import logging
from pathlib import Path
from typing import Any, Self

from pydantic import ConfigDict, Field

from goatlib.analysis.accessibility import HeatmapConnectivityTool
from goatlib.analysis.schemas.heatmap import HeatmapConnectivityParams
from goatlib.analysis.schemas.ui import (
    SECTION_CONFIGURATION,
    SECTION_ROUTING,
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ScenarioSelectorMixin, ToolInputBase
from goatlib.tools.style import get_heatmap_style

logger = logging.getLogger(__name__)


class HeatmapConnectivityToolParams(
    ScenarioSelectorMixin, ToolInputBase, HeatmapConnectivityParams
):
    """Parameters for heatmap connectivity tool.

    Inherits heatmap options from HeatmapConnectivityParams, adds layer context from ToolInputBase.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_ROUTING,
            SECTION_CONFIGURATION,
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                depends_on={"reference_area_layer_id": {"$ne": None}},
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
    reference_area_path: str | None = None  # type: ignore[assignment]

    # Layer ID for the reference area (replaces reference_area_path for tools)
    reference_area_layer_id: str = Field(
        description="Layer ID for the reference area polygon",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=4,
            label_key="reference_area_path",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
        ),
    )
    reference_area_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the reference area layer",
        json_schema_extra=ui_field(section="configuration", field_order=5, hidden=True),
    )


class HeatmapConnectivityToolRunner(BaseToolRunner[HeatmapConnectivityToolParams]):
    """Heatmap Connectivity tool runner for Windmill."""

    tool_class = HeatmapConnectivityTool
    output_geometry_type = "polygon"  # H3 cells
    default_output_name = "Heatmap_Connectivity"

    def get_layer_properties(
        self: Self,
        params: HeatmapConnectivityToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return heatmap style for connectivity accessibility with quantile breaks."""
        # Connectivity outputs "accessibility" (not "total_accessibility")
        color_field = "accessibility"

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

        # Use Teal (blue) for connectivity - represents spatial coverage/area
        return get_heatmap_style(
            color_field_name=color_field,
            color_scale_breaks=color_scale_breaks,
            color_range_name="Teal",
        )

    def process(
        self: Self, params: HeatmapConnectivityToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run heatmap connectivity analysis."""
        output_path = temp_dir / "output.parquet"

        # Export reference area layer
        reference_area_path = str(
            self.export_layer_to_parquet(
                layer_id=params.reference_area_layer_id,
                user_id=params.user_id,
                cql_filter=params.reference_area_layer_filter,
                scenario_id=params.scenario_id,
                project_id=params.project_id,
            )
        )

        # Build analysis params
        analysis_params = HeatmapConnectivityParams(
            **params.model_dump(
                exclude={
                    "output_path",
                    "reference_area_path",
                    "reference_area_layer_id",
                    "reference_area_layer_filter",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "scenario_id",
                    "output_name",
                }
            ),
            reference_area_path=reference_area_path,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: HeatmapConnectivityToolParams) -> dict:
    """Windmill entry point for heatmap connectivity tool."""
    runner = HeatmapConnectivityToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
