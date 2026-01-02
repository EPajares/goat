"""Common schemas for Windmill tool scripts.

These schemas define the standard input/output contracts for all tools,
ensuring consistency across buffer, clip, join, layer-import, etc.
"""

from typing import Any

from pydantic import BaseModel, Field

from goatlib.analysis.schemas.ui import ui_field


class ToolInputBase(BaseModel):
    """Base inputs that ALL tools receive.

    Every Windmill tool script should accept these parameters.
    GeoAPI injects `user_id` automatically from the auth token.

    folder_id is optional - if not provided, it will be derived from project_id.
    For layer imports outside a project, folder_id must be provided.
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
    output_name: str | None = Field(
        None,
        description="Custom name for output layer (optional)",
        json_schema_extra=ui_field(section="output", field_order=1),
    )


class LayerInputMixin(BaseModel):
    """Mixin for tools that take a single layer as input.

    Use with ToolInputBase:
        class BufferParams(ToolInputBase, LayerInputMixin):
            distance: float
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


class TwoLayerInputMixin(BaseModel):
    """Mixin for tools that take two layers as input (e.g., clip, join, intersect).

    Use with ToolInputBase:
        class ClipParams(ToolInputBase, TwoLayerInputMixin):
            pass
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
    overlay_layer_id: str = Field(
        ...,
        description="Overlay/clip/join layer UUID",
        json_schema_extra=ui_field(
            section="overlay",
            field_order=1,
            widget="layer-selector",
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
    attribute_mapping: dict[str, str] | None = Field(
        None, description="Column name mapping"
    )

    # Storage reference
    table_name: str | None = Field(None, description="DuckLake table name")
