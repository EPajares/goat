"""Intersection tool for Windmill.

Computes the geometric intersection of features from input and overlay layers.
"""

import logging
from pathlib import Path
from typing import List, Optional, Self

from pydantic import ConfigDict, Field

from goatlib.analysis.geoprocessing.intersection import IntersectionTool
from goatlib.analysis.schemas.geoprocessing import IntersectionParams
from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    SECTION_OUTPUT,
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase, TwoLayerInputMixin

logger = logging.getLogger(__name__)


class IntersectionToolParams(ToolInputBase, TwoLayerInputMixin, IntersectionParams):
    """Parameters for intersection tool.

    Inherits intersection options from IntersectionParams, adds layer context from ToolInputBase.
    input_path/overlay_path/output_path are not used (we use layer IDs instead).
    """

    # Override model_config to make field_selection section collapsible
    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            UISection(id="overlay", order=2, icon="layers"),
            UISection(
                id="field_selection",
                order=3,
                icon="list",
                collapsible=True,
                collapsed=True,
            ),
            SECTION_OUTPUT,
        )
    )

    input_path: str | None = None  # type: ignore[assignment]
    overlay_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None

    # Override field selectors to use input_layer_id/overlay_layer_id instead of input_path/overlay_path
    input_fields: Optional[List[str]] = Field(
        None,
        description="List of field names from input layer to keep in output. If None, all fields are kept.",
        json_schema_extra=ui_field(
            section="field_selection",
            field_order=1,
            widget="field-selector",
            widget_options={"source_layer": "input_layer_id", "multi": True},
        ),
    )
    overlay_fields: Optional[List[str]] = Field(
        None,
        description="List of field names from overlay layer to keep in output. If None, all fields are kept.",
        json_schema_extra=ui_field(
            section="field_selection",
            field_order=2,
            widget="field-selector",
            widget_options={"source_layer": "overlay_layer_id", "multi": True},
        ),
    )


class IntersectionToolRunner(BaseToolRunner[IntersectionToolParams]):
    """Intersection tool runner for Windmill."""

    tool_class = IntersectionTool
    output_geometry_type = None  # Depends on input
    default_output_name = "Intersection"

    def process(
        self: Self, params: IntersectionToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run intersection analysis."""
        input_path = self.export_layer_to_parquet(
            layer_id=params.input_layer_id,
            user_id=params.user_id,
            cql_filter=params.input_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        overlay_path = self.export_layer_to_parquet(
            layer_id=params.overlay_layer_id,
            user_id=params.user_id,
            cql_filter=params.overlay_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        output_path = temp_dir / "output.parquet"

        analysis_params = IntersectionParams(
            **params.model_dump(
                exclude={
                    "input_path",
                    "overlay_path",
                    "output_path",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "scenario_id",
                    "output_name",
                    "input_layer_id",
                    "input_layer_filter",
                    "overlay_layer_id",
                    "overlay_layer_filter",
                }
            ),
            input_path=input_path,
            overlay_path=overlay_path,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: IntersectionToolParams) -> dict:
    """Windmill entry point for intersection tool."""
    runner = IntersectionToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
