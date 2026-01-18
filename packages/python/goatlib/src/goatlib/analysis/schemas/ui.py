"""UI metadata helpers for tool schemas.

This module provides utilities to embed UI configuration metadata
in Pydantic models via `json_schema_extra`. The metadata is used by
the frontend to dynamically render tool forms.

Example usage:
    from goatlib.analysis.schemas.ui import ui_field, ui_sections

    class HeatmapGravityParams(BaseModel):
        model_config = ConfigDict(
            json_schema_extra=ui_sections(
                UISection(id="routing", order=1, icon="route"),
                UISection(id="opportunities", order=2, icon="location-marker"),
            )
        )

        routing_mode: RoutingMode = Field(
            ...,
            description="Transport mode",
            json_schema_extra=ui_field(
                section="routing",
                field_order=1,
            ),
        )

        opportunities: list[OpportunityGravity] = Field(
            ...,
            json_schema_extra=ui_field(
                section="opportunities",
                repeatable=True,
                min_items=1,
            ),
        )
"""

from dataclasses import dataclass
from typing import Any, Self


@dataclass(frozen=True)
class UISection:
    """Definition of a UI section for grouping fields.

    Attributes:
        id: Unique section identifier (e.g., "routing", "opportunities")
        order: Display order (lower numbers first)
        label_key: i18n key for section label (defaults to id)
        label: Direct label text (overrides label_key if provided)
        label_de: German translation of label
        icon: Icon name from @p4b/ui/components/Icon (optional)
        collapsible: Whether section can be collapsed (default: False)
        collapsed: Initial collapsed state (default: False)
        depends_on: Condition for section to be enabled, MongoDB-like syntax
            e.g., {"routing_mode": {"$ne": None}} - enabled when routing_mode is set
    """

    id: str
    order: int = 0
    label_key: str | None = None
    label: str | None = None
    label_de: str | None = None
    icon: str | None = None
    collapsible: bool = False
    collapsed: bool = False
    depends_on: dict[str, Any] | None = None

    def to_dict(self: Self) -> dict[str, Any]:
        """Convert to dictionary for JSON schema."""
        result: dict[str, Any] = {
            "id": self.id,
            "order": self.order,
        }
        # Use direct label if provided, otherwise use label_key
        if self.label:
            result["label"] = self.label
            if self.label_de:
                result["label_de"] = self.label_de
        else:
            result["label_key"] = self.label_key or self.id
        if self.icon:
            result["icon"] = self.icon
        if self.collapsible:
            result["collapsible"] = self.collapsible
            result["collapsed"] = self.collapsed
        if self.depends_on:
            result["depends_on"] = self.depends_on
        return result


# Common section definitions for reuse
SECTION_ROUTING = UISection(id="routing", order=1, icon="route")
SECTION_CONFIGURATION = UISection(
    id="configuration",
    order=2,
    icon="settings",
    depends_on={"routing_mode": {"$ne": None}},
)
SECTION_INPUT = UISection(id="input", order=1, icon="layers")
SECTION_OUTPUT = UISection(id="output", order=10, icon="table")
SECTION_OPTIONS = UISection(id="options", order=5, icon="settings", collapsible=True)
SECTION_OPPORTUNITIES = UISection(
    id="opportunities",
    order=3,
    icon="location-marker",
    depends_on={"routing_mode": {"$ne": None}},
)
SECTION_SCENARIO = UISection(
    id="scenario", order=4, icon="scenario", collapsible=True, collapsed=True
)
# Section for result layer naming (order=7, before scenario which is usually 8)
# Uses "save" icon and is only shown when form is ready to run
SECTION_RESULT = UISection(
    id="result",
    order=7,
    icon="save",
    label_key="result",
    depends_on={"input_layer_id": {"$ne": None}},
)
# Result section variant for routing-based tools (heatmaps)
SECTION_RESULT_ROUTING = UISection(
    id="result",
    order=7,
    icon="save",
    label_key="result",
    depends_on={"routing_mode": {"$ne": None}},
)
# Result section variant for aggregate tools
SECTION_RESULT_AGGREGATE = UISection(
    id="result",
    order=7,
    icon="save",
    label_key="result",
    depends_on={"source_layer_id": {"$ne": None}},
)
SECTION_STATISTICS = UISection(id="statistics", order=3, icon="chart")
SECTION_TIME = UISection(id="time", order=3, icon="clock")
SECTION_AREA = UISection(
    id="area", order=2, label_key="summary_areas", icon="aggregate"
)
# Tool-specific input section for aggregate tools
SECTION_INPUT_AGGREGATE = UISection(
    id="input", order=1, label_key="pick_source_layer", icon="layers"
)


def ui_sections(*sections: UISection) -> dict[str, Any]:
    """Create model_config json_schema_extra with UI sections.

    Use this in a model's ConfigDict to define the available sections.

    Example:
        class MyParams(BaseModel):
            model_config = ConfigDict(
                json_schema_extra=ui_sections(
                    UISection(id="input", order=1, icon="layers"),
                    UISection(id="options", order=2, icon="settings"),
                )
            )

    Args:
        *sections: UISection definitions

    Returns:
        Dict for json_schema_extra with x-ui-sections key
    """
    return {"x-ui-sections": [s.to_dict() for s in sections]}


@dataclass
class UIFieldConfig:
    """Configuration for a UI field.

    Use ui_field() helper to create this configuration as a dict.
    """

    section: str
    field_order: int = 0
    label_key: str | None = None
    label: str | None = None  # Direct label text (overrides label_key)
    label_de: str | None = None  # German translation of label
    description_key: str | None = None
    hidden: bool = False
    advanced: bool = False
    optional: bool = False  # Explicitly mark as optional (overrides conditional required)
    visible_when: dict[str, Any] | None = None
    hidden_when: dict[str, Any] | None = None
    mutually_exclusive_group: str | None = None
    priority: int = 0
    repeatable: bool = False
    min_items: int | None = None
    max_items: int | None = None
    widget: str | None = None
    widget_options: dict[str, Any] | None = None
    enum_icons: dict[str, str] | None = None
    enum_labels: dict[str, str] | None = None  # Maps enum values to i18n keys

    def to_dict(self: Self) -> dict[str, Any]:
        """Convert to dictionary for JSON schema x-ui field."""
        result: dict[str, Any] = {
            "section": self.section,
            "field_order": self.field_order,
        }

        # Use direct label if provided, otherwise use label_key
        if self.label:
            result["label"] = self.label
            if self.label_de:
                result["label_de"] = self.label_de
        elif self.label_key:
            result["label_key"] = self.label_key
        if self.description_key:
            result["description_key"] = self.description_key
        if self.hidden:
            result["hidden"] = True
        if self.advanced:
            result["advanced"] = True
        if self.optional:
            result["optional"] = True
        if self.visible_when:
            result["visible_when"] = self.visible_when
        if self.hidden_when:
            result["hidden_when"] = self.hidden_when
        if self.mutually_exclusive_group:
            result["mutually_exclusive_group"] = self.mutually_exclusive_group
            result["priority"] = self.priority
        if self.repeatable:
            result["repeatable"] = True
            if self.min_items is not None:
                result["min_items"] = self.min_items
            if self.max_items is not None:
                result["max_items"] = self.max_items
        if self.widget:
            result["widget"] = self.widget
        if self.widget_options:
            result["widget_options"] = self.widget_options
        if self.enum_icons:
            result["enum_icons"] = self.enum_icons
        if self.enum_labels:
            result["enum_labels"] = self.enum_labels

        return result


def ui_field(
    section: str,
    field_order: int = 0,
    label_key: str | None = None,
    label: str | None = None,
    label_de: str | None = None,
    description_key: str | None = None,
    hidden: bool = False,
    advanced: bool = False,
    optional: bool = False,
    visible_when: dict[str, Any] | None = None,
    hidden_when: dict[str, Any] | None = None,
    mutually_exclusive_group: str | None = None,
    priority: int = 0,
    repeatable: bool = False,
    min_items: int | None = None,
    max_items: int | None = None,
    widget: str | None = None,
    widget_options: dict[str, Any] | None = None,
    enum_icons: dict[str, str] | None = None,
    enum_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Generate json_schema_extra dict for UI field configuration.

    This helper creates the x-ui metadata that controls how a field
    is displayed and behaves in the frontend tool form.

    Args:
        section: Section ID this field belongs to (e.g., "routing")
        field_order: Display order within section (lower first, default 0)
        label_key: i18n key for field label (default: field name)
        description_key: i18n key for field description
        hidden: If True, field is never shown in UI (for internal fields)
        optional: If True, field is explicitly optional even with visible_when condition
        visible_when: Condition to show field, MongoDB-like syntax:
            {"routing_mode": "public_transport"} - equals
            {"max_cost": {"$gte": 30}} - greater than or equal
            {"field": {"$ne": None}} - not equal (is set)
            {"mode": {"$in": ["a", "b"]}} - one of values
        hidden_when: Condition to hide field (opposite of visible_when)
        mutually_exclusive_group: Group name for mutually exclusive fields
        priority: Priority within mutually exclusive group (lower = default)
        repeatable: If True, field is a repeatable list (add/remove items)
        min_items: Minimum items for repeatable fields
        max_items: Maximum items for repeatable fields
        widget: Custom widget type (e.g., "layer-selector", "color-picker")
        widget_options: Options passed to custom widget
        enum_icons: Mapping of enum values to icon names for enum fields

    Returns:
        Dict to use as json_schema_extra in Field()

    Examples:
        # Basic field in a section
        name: str = Field(
            ...,
            json_schema_extra=ui_field(section="input", field_order=1),
        )

        # Conditional visibility
        pt_modes: list[str] = Field(
            None,
            json_schema_extra=ui_field(
                section="routing",
                visible_when={"routing_mode": "public_transport"},
            ),
        )

        # Mutually exclusive options
        potential_field: str = Field(
            None,
            json_schema_extra=ui_field(
                section="opportunities",
                mutually_exclusive_group="potential_source",
                priority=1,  # Default option (lowest priority)
            ),
        )
        potential_constant: float = Field(
            None,
            json_schema_extra=ui_field(
                section="opportunities",
                mutually_exclusive_group="potential_source",
                priority=2,
            ),
        )

        # Repeatable list field
        opportunities: list[Opportunity] = Field(
            ...,
            json_schema_extra=ui_field(
                section="opportunities",
                repeatable=True,
                min_items=1,
                max_items=10,
            ),
        )

        # Layer selector widget
        input_layer_id: str = Field(
            ...,
            json_schema_extra=ui_field(
                section="input",
                widget="layer-selector",
                widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
            ),
        )
    """
    config = UIFieldConfig(
        section=section,
        field_order=field_order,
        label_key=label_key,
        label=label,
        label_de=label_de,
        description_key=description_key,
        hidden=hidden,
        advanced=advanced,
        optional=optional,
        visible_when=visible_when,
        hidden_when=hidden_when,
        mutually_exclusive_group=mutually_exclusive_group,
        priority=priority,
        repeatable=repeatable,
        min_items=min_items,
        max_items=max_items,
        widget=widget,
        widget_options=widget_options,
        enum_icons=enum_icons,
        enum_labels=enum_labels,
    )
    return {"x-ui": config.to_dict()}


def merge_ui_field(
    existing_extra: dict[str, Any] | None,
    **ui_kwargs: Any,
) -> dict[str, Any]:
    """Merge UI field config with existing json_schema_extra.

    Use this when a field already has json_schema_extra and you want
    to add UI configuration without overwriting other metadata.

    Args:
        existing_extra: Existing json_schema_extra dict (or None)
        **ui_kwargs: Arguments to pass to ui_field()

    Returns:
        Merged dict with both existing extras and x-ui config
    """
    ui_config = ui_field(**ui_kwargs)
    if existing_extra:
        return {**existing_extra, **ui_config}
    return ui_config


# Convenience functions for common widget types


def layer_selector_field(
    section: str,
    field_order: int = 0,
    geometry_types: list[str] | None = None,
    feature_layer_types: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create UI config for a layer selector field.

    Args:
        section: Section ID
        field_order: Display order
        geometry_types: Allowed geometry types (e.g., ["Polygon", "Point"])
        feature_layer_types: Allowed layer types (e.g., ["standard", "tool"])
        **kwargs: Additional ui_field arguments

    Returns:
        json_schema_extra dict for layer selector
    """
    widget_options: dict[str, Any] = {}
    if geometry_types:
        widget_options["geometry_types"] = geometry_types
    if feature_layer_types:
        widget_options["feature_layer_types"] = feature_layer_types

    return ui_field(
        section=section,
        field_order=field_order,
        widget="layer-selector",
        widget_options=widget_options if widget_options else None,
        **kwargs,
    )


def scenario_selector_field(
    section: str = "scenario",
    field_order: int = 0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create UI config for a scenario selector field.

    Args:
        section: Section ID (default: "scenario")
        field_order: Display order
        **kwargs: Additional ui_field arguments

    Returns:
        json_schema_extra dict for scenario selector
    """
    return ui_field(
        section=section,
        field_order=field_order,
        widget="scenario-selector",
        **kwargs,
    )
