"""Join tool for Windmill.

Performs spatial and attribute-based joins between datasets using DuckDB Spatial.
"""

import logging
from enum import StrEnum
from pathlib import Path
from typing import Any, List, Literal, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from goatlib.analysis.data_management.join import JoinTool
from goatlib.analysis.schemas.base import FieldStatistic
from goatlib.analysis.schemas.data_management import (
    AttributeRelationship,
    JoinOperationType,
    JoinParams,
    JoinType,
    MultipleMatchingRecordsType,
    SortConfiguration,
    SpatialRelationshipType,
)
from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    SECTION_OUTPUT,
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ScenarioSelectorMixin, ToolInputBase

logger = logging.getLogger(__name__)


class JoinMethod(StrEnum):
    """Method for joining features."""

    spatial = "spatial"
    attribute = "attribute"
    spatial_and_attribute = "spatial_and_attribute"


# Enum labels for i18n (map enum values to translation keys)
JOIN_METHOD_LABELS: dict[str, str] = {
    "spatial": "enums.join_method.spatial",
    "attribute": "enums.join_method.attribute",
    "spatial_and_attribute": "enums.join_method.spatial_and_attribute",
}

SPATIAL_RELATIONSHIP_LABELS: dict[str, str] = {
    "intersects": "enums.spatial_relationship_type.intersects",
    "within_distance": "enums.spatial_relationship_type.within_distance",
    "identical_to": "enums.spatial_relationship_type.identical_to",
    "completely_contains": "enums.spatial_relationship_type.completely_contains",
    "completely_within": "enums.spatial_relationship_type.completely_within",
}

DISTANCE_UNITS_LABELS: dict[str, str] = {
    "meters": "enums.units.meters",
    "kilometers": "enums.units.kilometers",
    "feet": "enums.units.feet",
    "miles": "enums.units.miles",
    "nautical_miles": "enums.units.nautical_miles",
    "yards": "enums.units.yards",
}

JOIN_OPERATION_LABELS: dict[str, str] = {
    "one_to_one": "enums.join_operation_type.one_to_one",
    "one_to_many": "enums.join_operation_type.one_to_many",
}

MULTIPLE_MATCHING_RECORDS_LABELS: dict[str, str] = {
    "first_record": "enums.multiple_matching_records_type.first_record",
    "calculate_statistics": "enums.multiple_matching_records_type.calculate_statistics",
    "count_only": "enums.multiple_matching_records_type.count_only",
}

JOIN_TYPE_LABELS: dict[str, str] = {
    "inner": "enums.join_type.inner",
    "left": "enums.join_type.left",
}


class JoinToolParams(ScenarioSelectorMixin, ToolInputBase, BaseModel):
    """Parameters for join tool.

    Does NOT inherit from JoinParams to avoid validator conflicts.
    We build JoinParams in the runner instead.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            UISection(id="join_layer", order=2, icon="layers"),
            UISection(id="join_method", order=3, icon="route"),
            UISection(id="spatial_settings", order=4, icon="location"),
            UISection(id="attribute_settings", order=5, icon="list"),
            UISection(
                id="join_options",
                order=6,
                icon="settings",
                collapsible=True,
            ),
            UISection(
                id="statistics",
                order=7,
                icon="chart",
                collapsible=True,
            ),
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                depends_on={"target_layer_id": {"$ne": None}},
            ),
            SECTION_OUTPUT,
        )
    )

    # Layer ID inputs
    target_layer_id: str = Field(
        ...,
        description="The layer to which join layer fields will be appended",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            widget="layer-selector",
        ),
    )
    target_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the target layer",
        json_schema_extra=ui_field(section="input", field_order=2, hidden=True),
    )
    join_layer_id: str = Field(
        ...,
        description="The layer containing fields to append to the target layer",
        json_schema_extra=ui_field(
            section="join_layer",
            field_order=1,
            widget="layer-selector",
        ),
    )
    join_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the join layer",
        json_schema_extra=ui_field(section="join_layer", field_order=2, hidden=True),
    )

    # Join method dropdown
    join_method: JoinMethod = Field(
        JoinMethod.attribute,
        description="How to match features between the target and join layers",
        json_schema_extra=ui_field(
            section="join_method",
            field_order=1,
            enum_labels=JOIN_METHOD_LABELS,
        ),
    )

    # Spatial relationship settings
    spatial_relationship: Optional[SpatialRelationshipType] = Field(
        SpatialRelationshipType.intersects,
        description="The spatial relationship used to match features",
        json_schema_extra=ui_field(
            section="spatial_settings",
            field_order=1,
            enum_labels=SPATIAL_RELATIONSHIP_LABELS,
            visible_when={"join_method": {"$in": ["spatial", "spatial_and_attribute"]}},
        ),
    )
    distance: Optional[float] = Field(
        None,
        description="Search distance for the within_distance relationship",
        gt=0,
        json_schema_extra=ui_field(
            section="spatial_settings",
            field_order=2,
            visible_when={"spatial_relationship": "within_distance"},
        ),
    )
    distance_units: Literal[
        "meters", "kilometers", "feet", "miles", "nautical_miles", "yards"
    ] = Field(
        "meters",
        description="Units for the search distance",
        json_schema_extra=ui_field(
            section="spatial_settings",
            field_order=3,
            enum_labels=DISTANCE_UNITS_LABELS,
            visible_when={"spatial_relationship": "within_distance"},
        ),
    )

    # Attribute relationship settings - simple field selectors
    target_field: Optional[str] = Field(
        None,
        description="Field in target layer to match",
        json_schema_extra=ui_field(
            section="attribute_settings",
            field_order=1,
            widget="field-selector",
            widget_options={"source_layer": "target_layer_id"},
            visible_when={
                "join_method": {"$in": ["attribute", "spatial_and_attribute"]}
            },
        ),
    )
    join_field: Optional[str] = Field(
        None,
        description="Field in join layer to match",
        json_schema_extra=ui_field(
            section="attribute_settings",
            field_order=2,
            widget="field-selector",
            widget_options={"source_layer": "join_layer_id"},
            visible_when={
                "join_method": {"$in": ["attribute", "spatial_and_attribute"]}
            },
        ),
    )

    # Join operation settings
    join_operation: JoinOperationType = Field(
        JoinOperationType.one_to_one,
        description="How to handle multiple matching features",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=1,
            enum_labels=JOIN_OPERATION_LABELS,
        ),
    )
    multiple_matching_records: MultipleMatchingRecordsType = Field(
        MultipleMatchingRecordsType.first_record,
        description="How to handle multiple matching records in one-to-one joins",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=2,
            enum_labels=MULTIPLE_MATCHING_RECORDS_LABELS,
            visible_when={"join_operation": "one_to_one"},
        ),
    )
    join_type: JoinType = Field(
        JoinType.left,
        description="Whether to keep all target features or only matching ones",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=3,
            enum_labels=JOIN_TYPE_LABELS,
        ),
    )

    # Sorting configuration
    sort_configuration: Optional[SortConfiguration] = Field(
        None,
        description="Sort order for selecting the first matching record",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=4,
            widget="sort-selector",
            widget_options={"source_layer": "join_layer_id"},
            visible_when={"multiple_matching_records": "first_record"},
        ),
    )

    # Statistics configuration
    field_statistics: Optional[List[FieldStatistic]] = Field(
        None,
        description="Statistics to calculate for matching records",
        json_schema_extra=ui_field(
            section="statistics",
            field_order=1,
            widget="field-statistics-selector",
            widget_options={"source_layer": "join_layer_id"},
            visible_when={"multiple_matching_records": "calculate_statistics"},
        ),
    )

    @model_validator(mode="after")
    def validate_join_config(self: Self) -> Self:
        """Validate join configuration."""
        use_spatial = self.join_method in (
            JoinMethod.spatial,
            JoinMethod.spatial_and_attribute,
        )
        use_attribute = self.join_method in (
            JoinMethod.attribute,
            JoinMethod.spatial_and_attribute,
        )

        # Spatial relationship validation
        if use_spatial:
            if self.spatial_relationship is None:
                raise ValueError("spatial_relationship is required for spatial joins")
            if self.spatial_relationship == SpatialRelationshipType.within_distance:
                if self.distance is None:
                    raise ValueError(
                        "distance is required for within_distance relationship"
                    )

        # Attribute relationship validation
        if use_attribute:
            if not self.target_field or not self.join_field:
                raise ValueError(
                    "target_field and join_field are required for attribute joins"
                )

        return self


class JoinToolRunner(BaseToolRunner[JoinToolParams]):
    """Join tool runner for Windmill."""

    tool_class = JoinTool
    output_geometry_type = None  # Same as target layer
    default_output_name = "Join"

    def process(
        self: Self, params: JoinToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run join analysis."""
        target_path = self.export_layer_to_parquet(
            layer_id=params.target_layer_id,
            user_id=params.user_id,
            cql_filter=params.target_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        join_path = self.export_layer_to_parquet(
            layer_id=params.join_layer_id,
            user_id=params.user_id,
            cql_filter=params.join_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        output_path = temp_dir / "output.parquet"

        # Derive boolean flags from join_method
        use_spatial = params.join_method in (
            JoinMethod.spatial,
            JoinMethod.spatial_and_attribute,
        )
        use_attribute = params.join_method in (
            JoinMethod.attribute,
            JoinMethod.spatial_and_attribute,
        )

        # Build attribute_relationships from simple field selectors
        attribute_relationships = None
        if use_attribute and params.target_field and params.join_field:
            attribute_relationships = [
                AttributeRelationship(
                    target_field=params.target_field,
                    join_field=params.join_field,
                )
            ]

        # Build JoinParams for the analysis tool
        analysis_params = JoinParams(
            target_path=str(target_path),
            join_path=str(join_path),
            output_path=str(output_path),
            use_spatial_relationship=use_spatial,
            use_attribute_relationship=use_attribute,
            spatial_relationship=params.spatial_relationship if use_spatial else None,
            distance=params.distance,
            distance_units=params.distance_units,
            attribute_relationships=attribute_relationships,
            join_operation=params.join_operation,
            multiple_matching_records=params.multiple_matching_records,
            join_type=params.join_type,
            sort_configuration=params.sort_configuration,
            field_statistics=params.field_statistics,
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: JoinToolParams) -> dict:
    """Windmill entry point for join tool."""
    runner = JoinToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
