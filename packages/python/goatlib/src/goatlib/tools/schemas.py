"""Common schemas for Windmill tool scripts.

These schemas define the standard input/output contracts for all tools,
ensuring consistency across buffer, clip, join, layer-import, etc.
"""

from typing import Any

from pydantic import BaseModel, Field

from goatlib.analysis.schemas.ui import ui_field
from goatlib.i18n import get_translator


def get_default_layer_name(layer_key: str, lang: str = "en") -> str:
    """Get default layer name for a tool from i18n translations.

    Args:
        layer_key: Key from default_layer_names in translation files
        lang: Language code ("en" or "de")

    Returns:
        Default layer name in the specified language, or the key if not found
    """
    translator = get_translator(lang)
    name = translator.get_default_layer_name(layer_key)
    return name if name else layer_key


class ToolInputBase(BaseModel):
    """Base inputs that ALL tools receive.

    Every Windmill tool script should accept these parameters.
    GeoAPI injects `user_id` automatically from the auth token.

    folder_id is optional - if not provided, it will be derived from project_id.
    For layer imports outside a project, folder_id must be provided.

    scenario_id applies to all input layers - scenario features will be merged
    with original layer data (new/modified added, deleted removed).
    """

    user_id: str = Field(
        ...,
        description="User UUID (injected by GeoAPI)",
        json_schema_extra=ui_field(section="output", field_order=99, hidden=True),
    )
    folder_id: str | None = Field(
        None,
        description="Destination folder UUID for output layer. If not provided, derived from project_id.",
        json_schema_extra=ui_field(section="output", field_order=98, hidden=True),
    )
    project_id: str | None = Field(
        None,
        description="If provided, add result layer to this project",
        json_schema_extra=ui_field(section="output", field_order=97, hidden=True),
    )
    scenario_id: str | None = Field(
        None,
        description="Scenario UUID. If provided, scenario features are merged with layer data for all input layers.",
        json_schema_extra=ui_field(section="output", field_order=96, hidden=True),
    )
    result_layer_name: str | None = Field(
        None,
        description="Custom name for result layer. Uses tool default if not specified.",
        json_schema_extra=ui_field(
            section="result",
            field_order=1,
            label_key="result_layer_name",
            widget="layer-name-input",
        ),
    )
    # Keep output_name as alias for backward compatibility
    output_name: str | None = Field(
        None,
        description="Deprecated: Use result_layer_name instead",
        json_schema_extra=ui_field(section="output", field_order=1, hidden=True),
    )


class LayerInputMixin(BaseModel):
    """Mixin for tools that take a single layer as input.

    Use with ToolInputBase:
        class BufferParams(ToolInputBase, LayerInputMixin):
            distance: float

    The filter is a CQL2-JSON object that will be applied when reading the layer.
    """

    input_layer_id: str = Field(
        ...,
        description="Source layer UUID from DuckLake",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            widget="layer-selector",
        ),
    )
    input_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the input layer",
        json_schema_extra=ui_field(section="input", field_order=2, hidden=True),
    )


class TwoLayerInputMixin(BaseModel):
    """Mixin for tools that take two layers as input (e.g., clip, join, intersect).

    Use with ToolInputBase:
        class ClipParams(ToolInputBase, TwoLayerInputMixin):
            pass

    Each layer can have its own CQL2-JSON filter.
    """

    input_layer_id: str = Field(
        ...,
        description="Primary input layer UUID",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            widget="layer-selector",
        ),
    )
    input_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the input layer",
        json_schema_extra=ui_field(section="input", field_order=2, hidden=True),
    )
    overlay_layer_id: str = Field(
        ...,
        description="Overlay/clip/join layer UUID",
        json_schema_extra=ui_field(
            section="overlay",
            field_order=1,
            widget="layer-selector",
        ),
    )
    overlay_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the overlay layer",
        json_schema_extra=ui_field(section="overlay", field_order=2, hidden=True),
    )


class ScenarioSelectorMixin(BaseModel):
    """Mixin to add a visible scenario selector to a tool.

    Include this mixin BEFORE ToolInputBase to override the hidden scenario_id field
    with a visible scenario selector widget.

    Example:
        class MyToolParams(ScenarioSelectorMixin, ToolInputBase, LayerInputMixin):
            # scenario_id will now have a visible selector widget
            pass

    The SECTION_SCENARIO should be added to the tool's model_config json_schema_extra.
    """

    scenario_id: str | None = Field(
        None,
        description="Scenario to apply. Scenario features will be merged with layer data.",
        json_schema_extra=ui_field(
            section="scenario",
            field_order=1,
            widget="scenario-selector",
        ),
    )


class ToolOutputBase(BaseModel):
    """Standard output that all tools return.

    This ensures consistent response format for the frontend/job results.
    """

    # Identity
    layer_id: str = Field(..., description="UUID of the created layer")
    name: str = Field(..., description="Layer display name")

    # Location
    folder_id: str = Field(..., description="Folder containing the layer")
    user_id: str = Field(..., description="Owner user UUID")

    # Project association (if requested)
    project_id: str | None = Field(None, description="Project UUID if added to project")
    layer_project_id: int | None = Field(
        None, description="layer_project link ID if added to project"
    )

    # Layer metadata
    type: str = Field("feature", description="Layer type: feature or table")
    feature_layer_type: str | None = Field(
        "tool",
        description="Feature layer type: standard, tool, street_network (None for tables)",
    )
    geometry_type: str | None = Field(
        None, description="Geometry type: point, line, polygon, or None for tables"
    )
    feature_count: int = Field(0, description="Number of features/rows")
    extent: Any | None = Field(None, description="Spatial extent (WKT or dict)")
    attribute_mapping: dict[str, str] = Field(
        default_factory=dict, description="Column name mapping"
    )

    # Storage reference
    table_name: str | None = Field(None, description="DuckLake table name")
