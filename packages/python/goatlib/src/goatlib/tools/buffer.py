"""Buffer tool for Windmill.

This is an example implementation showing how to create a Windmill tool
using the BaseToolRunner infrastructure.

The tool creates buffer zones around features from an input layer.
"""

import logging
from pathlib import Path
from typing import Any, Self

from pydantic import ConfigDict

from goatlib.analysis.geoprocessing.buffer import BufferTool
from goatlib.analysis.schemas.geoprocessing import BufferParams, DistanceType
from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    SECTION_OUTPUT,
    UISection,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import LayerInputMixin, ScenarioSelectorMixin, ToolInputBase

logger = logging.getLogger(__name__)


class BufferToolParams(
    ScenarioSelectorMixin, ToolInputBase, LayerInputMixin, BufferParams
):
    """Parameters for buffer tool.

    Inherits buffer options from BufferParams, adds layer context from ToolInputBase.
    input_path/output_path are not used (we use input_layer_id instead).
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            UISection(
                id="configuration",
                order=2,
                icon="settings",
                depends_on={"input_layer_id": {"$ne": None}},
            ),
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                collapsible=True,
                collapsed=True,
                depends_on={"input_layer_id": {"$ne": None}},
            ),
            SECTION_OUTPUT,
        )
    )

    # Override file paths as optional - we use layer IDs instead
    input_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None  # type: ignore[assignment]


class BufferToolRunner(BaseToolRunner[BufferToolParams]):
    """Buffer tool runner for Windmill."""

    tool_class = BufferTool
    output_geometry_type = "polygon"
    default_output_name = "Buffer"

    def get_layer_properties(
        self: Self,
        params: BufferToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return style for buffer with ordinal scale based on buffer_distance values.

        Creates an ordinal color map where each buffer distance gets a distinct color.
        Uses the shared get_ordinal_polygon_style utility with color interpolation.
        """
        from goatlib.tools.style import get_ordinal_polygon_style

        # Get buffer distances from params (only for constant distances)
        if params.distance_type == DistanceType.constant and params.distances:
            from goatlib.utils.helper import UNIT_TO_METERS

            unit_mult = UNIT_TO_METERS.get(params.units, 1.0)
            # Convert to integers (matching how they're stored in the parquet)
            distances = sorted([int(round(d * unit_mult)) for d in params.distances])
        else:
            # For field-based distances, use default style
            return None

        # Use shared ordinal style utility with OrRd (orange-red) palette
        return get_ordinal_polygon_style(
            color_field="buffer_distance",
            values=distances,
            palette="OrRd",
            opacity=0.7,
        )

    def process(
        self: Self, params: BufferToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run buffer analysis."""
        input_path = self.export_layer_to_parquet(
            layer_id=params.input_layer_id,
            user_id=params.user_id,
            cql_filter=params.input_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        output_path = temp_dir / "output.parquet"

        analysis_params = BufferParams(
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
            input_path=input_path,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: BufferToolParams) -> dict:
    """Windmill entry point for buffer tool.

    This function is called by Windmill with parameters from the job.
    Environment variables provide database connection settings.

    Args:
        params: Parameters matching BufferToolParams schema

    Returns:
        Dict with output layer metadata
    """
    runner = BufferToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
