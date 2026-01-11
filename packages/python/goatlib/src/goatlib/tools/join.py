"""Join tool for Windmill.

Performs spatial and attribute-based joins between datasets using DuckDB Spatial.
Matches ArcGIS Join Features tool functionality.
"""

import logging
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
from goatlib.tools.schemas import (
    get_default_layer_name,
    ScenarioSelectorMixin,
    ToolInputBase,
)

logger = logging.getLogger(__name__)

# Result section for join tool (depends on target_layer_id)
SECTION_RESULT_JOIN = UISection(
    id="result",
    order=7,
    icon="save",
    label="Result Layer",
    label_de="Ergebnisebene",
    depends_on={"target_layer_id": {"$ne": None}},
)

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

JOIN_TYPE_LABELS: dict[str, str] = {
    "inner": "enums.join_type.inner",
    "left": "enums.join_type.left",
}


class JoinToolParams(ScenarioSelectorMixin, ToolInputBase, BaseModel):
    """Parameters for join tool.

    Matches ArcGIS Join Features tool with toggle-based spatial/attribute selection.
    Does NOT inherit from JoinParams to avoid validator conflicts.
    We build JoinParams in the runner instead.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            UISection(id="join_layer", order=2, icon="layers"),
            UISection(id="join_settings", order=3, icon="route"),
            UISection(id="spatial_settings", order=4, icon="location"),
            UISection(id="attribute_settings", order=5, icon="list"),
            UISection(
                id="join_options",
                order=6,
                icon="settings",
                collapsible=True,
            ),
            SECTION_RESULT_JOIN,
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                collapsible=True,
                collapsed=True,
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

    # ===== Join Method Toggles (ArcGIS pattern) =====
    use_spatial_relationship: bool = Field(
        False,
        description="Match features based on their spatial location. If both options are enabled, features must match both criteria.",
        json_schema_extra=ui_field(
            section="join_settings",
            field_order=1,
            widget="switch",
            # Only show spatial relationship option when at least one layer has geometry
            # The _any_layer_has_geometry value is computed by the frontend from selected layers
            visible_when={"_any_layer_has_geometry": True},
        ),
    )
    use_attribute_relationship: bool = Field(
        True,  # Default to attribute join
        description="Match features based on attribute values. If both options are enabled, features must match both criteria.",
        json_schema_extra=ui_field(
            section="join_settings",
            field_order=2,
            widget="switch",
        ),
    )

    # ===== Spatial Relationship Settings =====
    spatial_relationship: Optional[SpatialRelationshipType] = Field(
        SpatialRelationshipType.intersects,
        description="How spatial features are joined to each other",
        json_schema_extra=ui_field(
            section="spatial_settings",
            field_order=1,
            enum_labels=SPATIAL_RELATIONSHIP_LABELS,
            visible_when={"use_spatial_relationship": True},
        ),
    )
    distance: Optional[float] = Field(
        None,
        description="How close features in the join layer must be to features in the target layer",
        gt=0,
        json_schema_extra=ui_field(
            section="spatial_settings",
            field_order=2,
            visible_when={
                "$and": [
                    {"use_spatial_relationship": True},
                    {"spatial_relationship": "within_distance"},
                ]
            },
        ),
    )
    distance_units: Literal[
        "meters", "kilometers", "feet", "miles", "nautical_miles", "yards"
    ] = Field(
        "meters",
        description="Distance units",
        json_schema_extra=ui_field(
            section="spatial_settings",
            field_order=3,
            enum_labels=DISTANCE_UNITS_LABELS,
            visible_when={
                "$and": [
                    {"use_spatial_relationship": True},
                    {"spatial_relationship": "within_distance"},
                ]
            },
        ),
    )

    # ===== Attribute Relationship Settings =====
    # Support for multiple attribute field pairs (like ArcGIS)
    attribute_relationships: Optional[List[AttributeRelationship]] = Field(
        None,
        description="Attribute relationships. Target field and join field must contain matching values.",
        json_schema_extra=ui_field(
            section="attribute_settings",
            field_order=1,
            visible_when={"use_attribute_relationship": True},
            repeatable=True,
            min_items=1,
        ),
    )

    # ===== Join Operation Settings =====
    join_type: JoinType = Field(
        JoinType.inner,  # Default to inner join
        description="Determines which features appear in the output. Inner Join keeps only matching features. Left Join keeps all target features even without matches.",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=1,
            enum_labels=JOIN_TYPE_LABELS,
        ),
    )
    join_operation: JoinOperationType = Field(
        JoinOperationType.one_to_one,
        description="How to handle multiple matching features. One-to-One keeps one result per target feature. One-to-Many creates a row for each match.",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=2,
            enum_labels=JOIN_OPERATION_LABELS,
        ),
    )

    # ===== Statistics Configuration (for one-to-one joins) =====
    calculate_statistics: bool = Field(
        False,
        description="Calculate statistics for numeric fields when multiple records match",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=3,
            widget="switch",
            visible_when={"join_operation": "one_to_one"},
        ),
    )
    field_statistics: Optional[List[FieldStatistic]] = Field(
        None,
        description="Field statistics to calculate. Supported statistics: sum, min, max, mean, standard deviation.",
        json_schema_extra=ui_field(
            section="join_options",
            field_order=4,
            widget="field-statistics-selector",
            widget_options={"source_layer": "join_layer_id"},
            visible_when={
                "$and": [
                    {"join_operation": "one_to_one"},
                    {"calculate_statistics": True},
                ]
            },
        ),
    )

    @model_validator(mode="after")
    def validate_join_config(self: Self) -> Self:
        """Validate join configuration."""
        # Must use at least one relationship type
        if not self.use_spatial_relationship and not self.use_attribute_relationship:
            raise ValueError(
                "Either use_spatial_relationship or use_attribute_relationship must be enabled"
            )

        # Spatial relationship validation
        if self.use_spatial_relationship:
            if self.spatial_relationship is None:
                raise ValueError(
                    "spatial_relationship is required when use_spatial_relationship is enabled"
                )
            if self.spatial_relationship == SpatialRelationshipType.within_distance:
                if self.distance is None:
                    raise ValueError(
                        "distance is required for within_distance relationship"
                    )

        # Attribute relationship validation
        if self.use_attribute_relationship:
            if (
                not self.attribute_relationships
                or len(self.attribute_relationships) == 0
            ):
                raise ValueError(
                    "At least one attribute relationship is required when use_attribute_relationship is enabled"
                )

        # Statistics validation
        if self.calculate_statistics:
            if not self.field_statistics or len(self.field_statistics) == 0:
                raise ValueError(
                    "field_statistics is required when calculate_statistics is enabled"
                )

        return self

    # Override result_layer_name with tool-specific defaults
    result_layer_name: str | None = Field(
        default=get_default_layer_name("join", "en"),
        description="Name for the join result layer.",
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget_options={
                "default_en": get_default_layer_name("join", "en"),
                "default_de": get_default_layer_name("join", "de"),
            },
        ),
    )


class JoinToolRunner(BaseToolRunner[JoinToolParams]):
    """Join tool runner for Windmill."""

    tool_class = JoinTool
    output_geometry_type = None  # Same as target layer
    default_output_name = get_default_layer_name("join", "en")

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

        # Determine multiple_matching_records based on calculate_statistics toggle
        # If calculate_statistics is True, use statistics; otherwise use first_record (sorted by ID)
        multiple_matching_records = (
            MultipleMatchingRecordsType.calculate_statistics
            if params.calculate_statistics
            else MultipleMatchingRecordsType.first_record
        )

        # Build JoinParams for the analysis tool
        # Sort by ID when using first_record (no sort_configuration needed)
        analysis_params = JoinParams(
            target_path=str(target_path),
            join_path=str(join_path),
            output_path=str(output_path),
            use_spatial_relationship=params.use_spatial_relationship,
            use_attribute_relationship=params.use_attribute_relationship,
            spatial_relationship=params.spatial_relationship
            if params.use_spatial_relationship
            else None,
            distance=params.distance,
            distance_units=params.distance_units,
            attribute_relationships=params.attribute_relationships,
            join_operation=params.join_operation,
            multiple_matching_records=multiple_matching_records,
            join_type=params.join_type,
            sort_configuration=None,  # Sort by ID in backend
            field_statistics=params.field_statistics
            if params.calculate_statistics
            else None,
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
