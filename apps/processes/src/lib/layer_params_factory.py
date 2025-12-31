"""
Dynamic factory for generating LayerParams from path-based Params classes.

This module automatically transforms *Params classes (which use file paths) into
*LayerParams classes (which use DuckLake layer IDs and filters).

Auto-detection rules (no hardcoded mappings):
- Any field ending with "_path" -> *_layer_id + *_filter (except output_* fields)
- Any field ending with "_paths" -> *_layer_ids (list)
- output_path -> output_layer_id (no filter, optional)
- Nested models (List[SomeModel]) with *_path fields are also transformed
- Adds user_id field
- Keeps all other fields unchanged
"""

import logging
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)

# Cache for transformed nested models to avoid recreating them
_nested_model_cache: Dict[Type[BaseModel], Type[BaseModel]] = {}


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


def _has_path_fields(model_class: Type[BaseModel]) -> bool:
    """Check if a model has any *_path or *_paths fields."""
    if not hasattr(model_class, "model_fields"):
        return False
    for field_name in model_class.model_fields:
        if field_name.endswith("_path") or field_name.endswith("_paths"):
            return True
    return False


def _transform_nested_model(
    nested_class: Type[BaseModel],
) -> Type[BaseModel]:
    """
    Transform a nested model's path fields to layer fields.

    For example, OpportunityGravity with input_path becomes
    OpportunityGravityLayer with input_layer_id and input_filter.
    """
    if nested_class in _nested_model_cache:
        return _nested_model_cache[nested_class]

    if not _has_path_fields(nested_class):
        return nested_class

    class_name = f"{nested_class.__name__}Layer"
    field_definitions: Dict[str, Any] = {}

    try:
        type_hints = get_type_hints(nested_class)
    except Exception:
        type_hints = {}

    model_fields = nested_class.model_fields

    for field_name, field_info in model_fields.items():
        field_type = type_hints.get(field_name, field_info.annotation)

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

            if is_output:
                field_definitions[layer_id_name] = (
                    Optional[str],
                    Field(None, description="UUID for the output layer."),
                )
            elif is_required:
                field_definitions[layer_id_name] = (
                    str,
                    Field(
                        ...,
                        description=_transform_path_description(original_desc, True),
                    ),
                )
            else:
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
            is_required = field_info.is_required()
            default_value = field_info.default

            if field_info.default_factory is not None:
                new_field = Field(
                    default_factory=field_info.default_factory,
                    description=field_info.description,
                )
            elif is_required:
                new_field = Field(..., description=field_info.description)
            else:
                new_field = Field(
                    default=default_value, description=field_info.description
                )

            field_definitions[field_name] = (field_type, new_field)

    # Create the transformed nested model
    layer_nested_class = create_model(
        class_name,
        __doc__=f"Layer-based version of {nested_class.__name__}",
        **field_definitions,
    )

    _nested_model_cache[nested_class] = layer_nested_class
    return layer_nested_class


def _get_nested_model_type(field_type: Any) -> Optional[Type[BaseModel]]:
    """
    Extract nested BaseModel type from List[SomeModel] or Optional[List[SomeModel]].
    Returns None if not a nested model type.
    """
    origin = get_origin(field_type)

    # Handle Optional[List[...]] or Union[List[...], None]
    if origin is Union:
        args = get_args(field_type)
        for arg in args:
            if arg is not type(None):
                result = _get_nested_model_type(arg)
                if result:
                    return result
        return None

    # Handle List[SomeModel]
    if origin is list:
        args = get_args(field_type)
        if args and len(args) == 1:
            inner_type = args[0]
            if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                return inner_type

    return None


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

    # ========================================================================
    # Common fields added to ALL LayerParams (required for GOAT integration)
    # ========================================================================

    # Required: user context
    field_definitions["user_id"] = (
        str,
        Field(..., description="UUID of the user who owns the layers."),
    )

    # Optional: project context (for saving results, layer styling, etc.)
    field_definitions["project_id"] = (
        Optional[str],
        Field(
            None,
            description="UUID of the project. Required if save_results=True to associate output layer with project.",
        ),
    )

    # Optional: scenario context (for analyzing changes/edits to layers)
    field_definitions["scenario_id"] = (
        Optional[str],
        Field(
            None,
            description="UUID of the scenario. If provided, layer edits from this scenario are applied before analysis.",
        ),
    )

    # Optional: whether to persist results to GOAT
    field_definitions["save_results"] = (
        Optional[bool],
        Field(
            True,
            description="Whether to save results to GOAT. If False, returns a pre-signed URL to download results.",
        ),
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

        # Check if this is a nested model with path fields (e.g., List[OpportunityGravity])
        nested_model = _get_nested_model_type(field_type)
        if nested_model and _has_path_fields(nested_model):
            # Transform the nested model and use it
            transformed_nested = _transform_nested_model(nested_model)
            is_required = field_info.is_required()

            # Rebuild the type with transformed nested model
            origin = get_origin(field_type)
            if origin is Union:
                # Handle Optional[List[...]]
                new_type = Optional[List[transformed_nested]]
            else:
                # Handle List[...]
                new_type = List[transformed_nested]

            if is_required:
                field_definitions[field_name] = (
                    new_type,
                    Field(..., description=field_info.description),
                )
            else:
                field_definitions[field_name] = (
                    new_type,
                    Field(default_factory=list, description=field_info.description),
                )
            logger.debug(
                f"Transformed nested model field: {field_name} -> List[{transformed_nested.__name__}]"
            )
            continue

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
            # Keep non-path fields as-is, preserving their required/optional status
            is_required = field_info.is_required()
            default_value = field_info.default

            # Handle the default_factory case
            if field_info.default_factory is not None:
                new_field = Field(
                    default_factory=field_info.default_factory,
                    description=field_info.description,
                )
            elif is_required:
                # Field is required (no default)
                new_field = Field(
                    ...,
                    description=field_info.description,
                )
            else:
                # Field is optional with a default value (which could be None)
                new_field = Field(
                    default=default_value,
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
