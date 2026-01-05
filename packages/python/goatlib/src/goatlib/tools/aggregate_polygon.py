"""Aggregate Polygon tool for Windmill.

Aggregates polygon features onto polygons or H3 hexagonal grids,
computing statistics like count, sum, mean, min, or max.
Supports weighting by intersection area ratio.
"""

import logging
from pathlib import Path
from typing import Any, List, Optional, Self

from pydantic import Field, model_validator

from goatlib.analysis.geoanalysis.aggregate_polygon import AggregatePolygonTool
from goatlib.analysis.schemas.aggregate import (
    AggregatePolygonParams,
    AggregationAreaType,
    ColumnStatistic,
    validate_area_type_config,
)
from goatlib.analysis.schemas.ui import (
    SECTION_AREA,
    SECTION_INPUT_AGGREGATE,
    SECTION_STATISTICS,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase

logger = logging.getLogger(__name__)


class AggregatePolygonToolParams(ToolInputBase, AggregatePolygonParams):
    """Parameters for aggregate polygon tool.

    Inherits aggregate options from AggregatePolygonParams, adds layer context from ToolInputBase.
    source_path/area_layer_path/output_path are not used (we use layer IDs instead).
    """

    model_config = {
        "json_schema_extra": ui_sections(
            SECTION_INPUT_AGGREGATE,
            SECTION_AREA,
            SECTION_STATISTICS,
        )
    }

    # Override file paths as optional - we use layer IDs instead
    source_path: str | None = Field(
        None,
        description="Path to the polygon layer (auto-populated from source_layer_id).",
        json_schema_extra=ui_field(section="input", hidden=True),
    )
    area_layer_path: str | None = Field(
        None,
        description="Path to the area layer (auto-populated from area_layer_id).",
        json_schema_extra=ui_field(section="area", hidden=True),
    )
    output_path: str | None = Field(
        None,
        description="Output path (auto-generated).",
        json_schema_extra=ui_field(section="output", hidden=True),
    )

    # ---- Layer ID fields (UI uses these instead of paths) ----
    source_layer_id: str = Field(
        ...,
        description="Layer ID for the polygon layer to be aggregated.",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            label_key="select_source_layer",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
        ),
    )

    area_layer_id: Optional[str] = Field(
        None,
        description="Layer ID for the polygon layer used for aggregation. Required when area_type is 'polygon'.",
        json_schema_extra=ui_field(
            section="area",
            field_order=2,
            label_key="select_area_layer",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
            visible_when={"area_type": "polygon"},
        ),
    )

    # Override UI metadata for inherited fields
    area_type: AggregationAreaType = Field(
        ...,
        description="Type of area to aggregate polygons into: polygon layer or H3 hexagonal grid.",
        json_schema_extra=ui_field(
            section="area",
            field_order=1,
            label_key="select_area_type",
        ),
    )

    column_statistics: ColumnStatistic = Field(
        ...,
        description="Statistical operation to perform on the aggregated polygons.",
        json_schema_extra=ui_field(
            section="statistics",
            field_order=1,
            label_key="select_statistics_configuration",
        ),
    )

    weighted_by_intersecting_area: bool = Field(
        False,
        description="If true, statistics are weighted by the intersection area ratio between source and area polygons.",
        json_schema_extra=ui_field(
            section="statistics",
            field_order=3,
            label_key="weighted_by_intersecting_area",
        ),
    )

    # Override group_by_field to use source_layer_id instead of source_path
    group_by_field: Optional[List[str]] = Field(
        None,
        description="Optional field(s) in the source layer to group aggregated results by (max 3 fields).",
        json_schema_extra=ui_field(
            section="statistics",
            field_order=10,
            advanced=True,
            label_key="select_group_fields",
            widget="field-selector",
            widget_options={"source_layer": "source_layer_id", "multiple": True, "max": 3},
        ),
    )

    @model_validator(mode="after")
    def validate_area_configuration(self: Self) -> "AggregatePolygonToolParams":
        """Override parent validator to check area_layer_id instead of area_layer_path."""
        validate_area_type_config(
            area_type=self.area_type,
            area_layer=self.area_layer_id,
            h3_resolution=self.h3_resolution,
            area_layer_field_name="area_layer_id",
        )
        return self


class AggregatePolygonToolRunner(BaseToolRunner[AggregatePolygonToolParams]):
    """Aggregate Polygon tool runner for Windmill."""

    tool_class = AggregatePolygonTool
    output_geometry_type = "polygon"
    default_output_name = "Aggregated_Polygons"

    def get_layer_properties(
        self: Self,
        params: AggregatePolygonToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return style for aggregated output with quantile breaks."""
        # Determine the value field based on the statistics operation
        stat_op = params.column_statistics.operation
        stat_field = params.column_statistics.field

        if stat_op.value == "count":
            color_field = "count"
        else:
            # For sum/mean/min/max, the output column is named after the operation
            color_field = (
                f"{stat_op.value}_{stat_field}" if stat_field else stat_op.value
            )

        # Compute quantile breaks from the DuckLake table
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

        # Import here to avoid circular imports
        from goatlib.tools.style import get_heatmap_style

        # Use Orange for aggregation - represents count/sum data
        return get_heatmap_style(
            color_field_name=color_field,
            color_scale_breaks=color_scale_breaks,
            color_range_name="Oranges",
        )

    def process(
        self: Self, params: AggregatePolygonToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run aggregate polygon analysis."""
        output_path = temp_dir / "output.parquet"

        # Export source polygon layer
        source_path = str(
            self.export_layer_to_parquet(params.source_layer_id, params.user_id)
        )

        # Export area layer if polygon aggregation
        area_layer_path = None
        if params.area_type == AggregationAreaType.polygon and params.area_layer_id:
            area_layer_path = str(
                self.export_layer_to_parquet(params.area_layer_id, params.user_id)
            )

        # Build analysis params using model_dump pattern (like other tools)
        analysis_params = AggregatePolygonParams(
            **params.model_dump(
                exclude={
                    "source_path",
                    "area_layer_path",
                    "output_path",
                    "output_crs",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "output_name",
                    "source_layer_id",
                    "area_layer_id",
                    "accepted_source_geometry_types",
                    "accepted_area_geometry_types",
                }
            ),
            source_path=source_path,
            area_layer_path=area_layer_path,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: AggregatePolygonToolParams) -> dict:
    """Windmill entry point for aggregate polygon tool.

    This function is called by Windmill with parameters from the job.
    Environment variables provide database connection settings.

    Args:
        params: Parameters matching AggregatePolygonToolParams schema

    Returns:
        Dict with output layer metadata
    """
    runner = AggregatePolygonToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
