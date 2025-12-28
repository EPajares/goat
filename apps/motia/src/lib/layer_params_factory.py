"""
Dynamic factory for generating LayerParams from path-based Params classes.

This module automatically transforms *Params classes (which use file paths) into
*LayerParams classes (which use DuckLake layer IDs and filters).

Auto-detection rules (no hardcoded mappings):
- Any field ending with "_path" -> *_layer_id + *_filter (except output_* fields)
- Any field ending with "_paths" -> *_layer_ids (list)
- output_path -> output_layer_id (no filter, optional)
- Adds user_id field
- Keeps all other fields unchanged
"""

from typing import Any, Dict, List, Optional, Type, get_type_hints

from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo


def _get_field_description(field_info: FieldInfo, field_name: str) -> str:
    """Extract description from field info or generate default."""
    if field_info.description:
        return field_info.description
    return f"Field: {field_name}"


def _transform_path_description(description: str, is_layer_id: bool) -> str:
    """Transform a path-based description to layer-based."""
    if is_layer_id:
        # Replace path-related terms with layer-related terms
        desc = description.replace("Path to", "UUID of")
        desc = desc.replace("path", "layer ID")
        desc = desc.replace("file", "layer")
        desc = desc.replace("dataset", "layer")
        desc = desc.replace("GeoParquet", "DuckLake")
        return desc
    return description


def create_layer_params_class(
    params_class: Type[BaseModel],
    class_name: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Dynamically create a LayerParams class from a path-based Params class.

    Args:
        params_class: The original *Params class (e.g., ClipParams, BufferParams)
        class_name: Optional name for the new class. Defaults to replacing 'Params' with 'LayerParams'

    Returns:
        A new Pydantic model class with layer-based fields instead of path-based fields.

    Example:
        >>> ClipLayerParams = create_layer_params_class(ClipParams)
        >>> params = ClipLayerParams(
        ...     user_id="user-uuid",
        ...     input_layer_id="input-uuid",
        ...     overlay_layer_id="overlay-uuid",
        ... )
    """
    if class_name is None:
        original_name = params_class.__name__
        if original_name.endswith("Params"):
            class_name = original_name.replace("Params", "LayerParams")
        else:
            class_name = f"{original_name}Layer"

    # Get all fields from the original class
    field_definitions: Dict[str, Any] = {}

    # Add user_id as first field
    field_definitions["user_id"] = (
        str,
        Field(..., description="UUID of the user who owns the layers."),
    )

    # Get type hints and field info from original class
    try:
        type_hints = get_type_hints(params_class)
    except Exception:
        type_hints = {}

    model_fields = params_class.model_fields

    for field_name, field_info in model_fields.items():
        # Get the type from type hints or field info
        field_type = type_hints.get(field_name, field_info.annotation)

        # Auto-detect path fields by suffix - no hardcoded mappings needed
        if field_name.endswith("_paths"):
            # List of paths -> list of layer_ids
            layer_ids_name = field_name.replace("_paths", "_layer_ids")
            original_desc = _get_field_description(field_info, field_name)

            field_definitions[layer_ids_name] = (
                List[str],
                Field(
                    ...,
                    description=_transform_path_description(original_desc, True),
                ),
            )

        elif field_name.endswith("_path"):
            # Single path -> layer_id + optional filter
            layer_id_name = field_name.replace("_path", "_layer_id")
            original_desc = _get_field_description(field_info, field_name)
            is_required = field_info.is_required()
            is_output = field_name.startswith("output")

            # Output fields are always optional and have special description
            if is_output:
                field_definitions[layer_id_name] = (
                    Optional[str],
                    Field(
                        None,
                        description="UUID for the output layer. If provided, result is saved to DuckLake. "
                        "If None, result is returned as parquet bytes.",
                    ),
                )
            elif is_required:
                # Required path -> required layer_id
                field_definitions[layer_id_name] = (
                    str,
                    Field(
                        ...,
                        description=_transform_path_description(original_desc, True),
                    ),
                )
            else:
                # Optional path -> optional layer_id
                field_definitions[layer_id_name] = (
                    Optional[str],
                    Field(
                        None,
                        description=_transform_path_description(original_desc, True),
                    ),
                )

            # Add filter field for non-output paths
            if not is_output:
                filter_name = field_name.replace("_path", "_filter")
                base_name = layer_id_name.replace("_layer_id", "")
                field_definitions[filter_name] = (
                    Optional[str],
                    Field(
                        None,
                        description=f"SQL WHERE clause to filter {base_name} layer features.",
                    ),
                )

        else:
            # Keep non-path fields as-is
            default_value = field_info.default
            if default_value is None and not field_info.is_required():
                default_value = None

            # Recreate the field with its original configuration
            new_field = Field(
                default=default_value if default_value is not None else ...,
                description=field_info.description,
            )

            # Handle the default_factory case
            if field_info.default_factory is not None:
                new_field = Field(
                    default_factory=field_info.default_factory,
                    description=field_info.description,
                )

            field_definitions[field_name] = (field_type, new_field)

    # Ensure output_crs is present (add if missing)
    if "output_crs" not in field_definitions:
        field_definitions["output_crs"] = (
            Optional[str],
            Field(
                "EPSG:4326",
                description="Target coordinate reference system for the output geometry.",
            ),
        )

    # Create docstring for the new class
    original_doc = params_class.__doc__ or f"Parameters for {params_class.__name__}"
    layer_doc = original_doc.replace("file paths", "DuckLake layer IDs")
    layer_doc = layer_doc.replace("Path to", "UUID of")
    layer_doc = f"{layer_doc}\n\nThis is the DuckLake layer-based version, auto-generated from {params_class.__name__}."

    # Create the new model
    layer_params_class = create_model(
        class_name,
        __doc__=layer_doc,
        **field_definitions,
    )

    # Copy over any property methods (like accepted_input_geometry_types)
    for attr_name in dir(params_class):
        if not attr_name.startswith("_"):
            attr = getattr(params_class, attr_name, None)
            if isinstance(attr, property):
                # Copy the property to the new class
                setattr(layer_params_class, attr_name, attr)

    return layer_params_class


def get_tool_name_from_params(params_class: Type[BaseModel]) -> str:
    """
    Extract tool name from a Params class name.

    Examples:
        ClipParams -> clip
        BufferParams -> buffer
        IntersectionParams -> intersection
    """
    name = params_class.__name__
    if name.endswith("Params"):
        name = name[:-6]  # Remove "Params"
    # Convert CamelCase to snake_case
    import re

    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return name
