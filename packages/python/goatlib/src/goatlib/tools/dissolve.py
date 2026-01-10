"""Dissolve tool for Windmill.

Merges polygon features that share common attribute values,
optionally computing statistics on dissolved groups.
Equivalent to QGIS "Auflösen" or ArcGIS "Dissolve".
"""

import logging
from pathlib import Path
from typing import Any, List, Optional, Self

from pydantic import ConfigDict, Field

from goatlib.analysis.geoprocessing.dissolve import DissolveTool
from goatlib.analysis.schemas.base import FieldStatistic
from goatlib.analysis.schemas.geoprocessing import DissolveParams
from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    SECTION_OUTPUT,
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import LayerInputMixin, ScenarioSelectorMixin, ToolInputBase

logger = logging.getLogger(__name__)


class DissolveToolParams(
    ScenarioSelectorMixin, ToolInputBase, LayerInputMixin, DissolveParams
):
    """Parameters for dissolve tool.

    Inherits dissolve options from DissolveParams, adds layer context from ToolInputBase.
    input_path/output_path are not used (we use input_layer_id instead).
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            UISection(
                id="dissolve_settings",
                order=2,
                icon="aggregate",
                depends_on={"input_layer_id": {"$ne": None}},
            ),
            UISection(
                id="statistics",
                order=3,
                icon="chart",
                collapsible=True,
                collapsed=True,
                depends_on={"input_layer_id": {"$ne": None}},
            ),
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                depends_on={"input_layer_id": {"$ne": None}},
            ),
            SECTION_OUTPUT,
        )
    )

    # Override file paths as optional - we use layer IDs instead
    input_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None  # type: ignore[assignment]

    # Override dissolve_fields with proper UI metadata
    dissolve_fields: Optional[List[str]] = Field(
        None,
        description="Fields to group by when dissolving. Features with matching values will be merged. If empty, all features are merged into one.",
        json_schema_extra=ui_field(
            section="dissolve_settings",
            field_order=1,
            widget="field-selector",
            widget_options={
                "source_layer": "input_layer_id",
                "multiple": True,
                "max": 3,
            },
        ),
    )

    # Override field_statistics with proper UI metadata
    field_statistics: Optional[List[FieldStatistic]] = Field(
        None,
        description="Statistics to calculate for each dissolved group.",
        json_schema_extra=ui_field(
            section="statistics",
            field_order=1,
            widget="field-statistics-selector",
            widget_options={"source_layer": "input_layer_id"},
        ),
    )


class DissolveToolRunner(BaseToolRunner[DissolveToolParams]):
    """Dissolve tool runner for Windmill."""

    tool_class = DissolveTool
    output_geometry_type = None  # Dynamic based on input geometry
    default_output_name = "Dissolved"

    def get_layer_properties(
        self: Self,
        params: DissolveToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return style for dissolved output.

        If statistics were computed, use quantile breaks on the first statistic field.
        Otherwise, use a simple fill style.
        """
        # Determine if we have a numeric field to style by
        color_field = None
        if params.field_statistics:
            # Use the first statistic for styling
            first_stat = params.field_statistics[0]
            if first_stat.operation.value == "count":
                color_field = "count"
            else:
                color_field = f"{first_stat.operation.value}_{first_stat.field}"

        # Import here to avoid circular imports
        from goatlib.tools.style import get_heatmap_style

        # Use Teal for dissolve - represents aggregated data
        # If no statistics, this will still return a valid style with default color
        color_scale_breaks = None
        if color_field and table_info and table_info.get("table_name"):
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

        return get_heatmap_style(
            color_field_name=color_field or "count",
            color_scale_breaks=color_scale_breaks,
            color_range_name="Teal",
        )

    def process(
        self: Self, params: DissolveToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run dissolve analysis."""
        input_path = self.export_layer_to_parquet(
            layer_id=params.input_layer_id,
            user_id=params.user_id,
            cql_filter=params.input_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        output_path = temp_dir / "output.parquet"

        analysis_params = DissolveParams(
            **params.model_dump(
                exclude={
                    "input_path",
                    "output_path",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "scenario_id",
                    "output_name",
                    "input_layer_id",
                    "input_layer_filter",
                }
            ),
            input_path=str(input_path),
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: DissolveToolParams) -> dict:
    """Windmill entry point for dissolve tool.

    This function is called by Windmill with parameters from the job.
    Environment variables provide database connection settings.

    Args:
        params: Parameters matching DissolveToolParams schema

    Returns:
        Dict with output layer metadata
    """
    runner = DissolveToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
