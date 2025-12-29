"""
OGC Process Description Generator.

Generates OGC API Processes compliant process descriptions from ToolInfo.
Reads geometry constraints from goatlib params_class properties and exposes
them via metadata with role="constraint".
"""

from typing import Any, Dict, List, Optional

from lib.ogc_schemas import (
    InputDescription,
    JobControlOptions,
    Link,
    Metadata,
    OutputDescription,
    ProcessDescription,
    ProcessSummary,
    TransmissionMode,
)
from lib.tool_registry import ToolInfo, get_all_tools, get_tool


def _get_geometry_constraints(params_class: type) -> Dict[str, List[str]]:
    """Extract geometry type constraints from a params_class.

    Looks for properties like:
    - accepted_input_geometry_types
    - accepted_overlay_geometry_types
    - accepted_target_geometry_types
    - etc.

    Returns:
        Dict mapping field prefix to list of accepted geometry types.
        E.g., {"input": ["Polygon", "MultiPolygon"], "overlay": ["Polygon"]}
    """
    constraints = {}

    # Find all accepted_*_geometry_types attributes
    constraint_attrs = [
        attr_name
        for attr_name in dir(params_class)
        if attr_name.startswith("accepted_") and attr_name.endswith("_geometry_types")
    ]

    if not constraint_attrs:
        return constraints

    # Create a dummy instance to access property values
    # goatlib params use @property decorators that require an instance
    try:
        # Get required fields from Pydantic model
        model_fields = getattr(params_class, "model_fields", {})
        dummy_args = {}
        for field_name, field_info in model_fields.items():
            # Provide dummy values for required fields
            if field_info.is_required():
                annotation = field_info.annotation
                if annotation == str or (
                    hasattr(annotation, "__origin__") and annotation.__origin__ is str
                ):
                    dummy_args[field_name] = "/tmp/dummy"
                elif annotation == int:
                    dummy_args[field_name] = 0
                elif annotation == float:
                    dummy_args[field_name] = 0.0
                elif annotation == bool:
                    dummy_args[field_name] = False

        # Create instance with dummy values
        dummy_instance = params_class(**dummy_args)

        # Extract geometry constraints from instance properties
        for attr_name in constraint_attrs:
            try:
                value = getattr(dummy_instance, attr_name)
                if isinstance(value, (list, tuple)) and len(value) > 0:
                    prefix = attr_name.replace("accepted_", "").replace(
                        "_geometry_types", ""
                    )
                    # Convert enum values to strings (e.g., GeometryType.polygon -> "Polygon")
                    geometry_types = []
                    for geom in value:
                        if hasattr(geom, "value"):
                            # It's an enum, get the value and format it
                            geometry_types.append(geom.value.title())
                        elif hasattr(geom, "name"):
                            geometry_types.append(geom.name.title())
                        else:
                            geometry_types.append(str(geom).title())
                    constraints[prefix] = geometry_types
            except Exception:
                pass

    except Exception:
        # If we can't create a dummy instance, constraints will be empty
        pass

    return constraints


def _generate_input_description(
    field_name: str,
    field_info: Any,
    schema: Dict[str, Any],
    geometry_constraints: Dict[str, List[str]],
) -> InputDescription:
    """Generate OGC InputDescription for a single field.

    Args:
        field_name: Name of the field (e.g., "input_layer_id")
        field_info: Pydantic field info
        schema: JSON schema for the field
        geometry_constraints: Dict of geometry constraints by prefix

    Returns:
        InputDescription with metadata for geometry constraints if applicable
    """
    # Determine title from field name
    title = field_name.replace("_", " ").title()

    # Get description from field info or schema
    description = None
    if hasattr(field_info, "description") and field_info.description:
        description = field_info.description
    elif "description" in schema:
        description = schema["description"]

    # Determine if field is required
    is_required = (
        field_info.is_required() if hasattr(field_info, "is_required") else True
    )
    min_occurs = 1 if is_required else 0

    # Build field schema
    field_schema = schema.copy()
    field_schema.pop(
        "description", None
    )  # Remove description from schema, it's in InputDescription

    # Check for geometry constraints
    metadata: List[Metadata] = []
    keywords: List[str] = []

    # Check if this is a layer_id field that might have geometry constraints
    if field_name.endswith("_layer_id"):
        keywords.append("layer")
        prefix = field_name.replace("_layer_id", "")

        # Look for matching geometry constraint
        if prefix in geometry_constraints:
            metadata.append(
                Metadata(
                    title="Accepted Geometry Types",
                    role="constraint",
                    value=geometry_constraints[prefix],
                )
            )
            keywords.append("geometry")

    return InputDescription(
        title=title,
        description=description,
        schema=field_schema,
        minOccurs=min_occurs,
        maxOccurs=1,
        keywords=keywords,
        metadata=metadata,
    )


def generate_process_description(
    tool_info: ToolInfo,
    base_url: str = "",
) -> ProcessDescription:
    """Generate OGC ProcessDescription from ToolInfo.

    Args:
        tool_info: ToolInfo from tool registry
        base_url: Base URL for generating links

    Returns:
        ProcessDescription with inputs, outputs, and geometry constraints in metadata
    """
    # Get geometry constraints from the original params_class
    geometry_constraints = _get_geometry_constraints(tool_info.params_class)

    # Get JSON schema from layer_params_class
    layer_schema = tool_info.layer_params_class.model_json_schema()
    properties = layer_schema.get("properties", {})
    set(layer_schema.get("required", []))

    # Build inputs dict
    inputs: Dict[str, InputDescription] = {}

    for field_name, field_schema in properties.items():
        # Skip output_layer_id - it's an output, not an input
        if field_name == "output_layer_id":
            continue

        # Get field info from model
        field_info = tool_info.layer_params_class.model_fields.get(field_name)

        inputs[field_name] = _generate_input_description(
            field_name=field_name,
            field_info=field_info,
            schema=field_schema,
            geometry_constraints=geometry_constraints,
        )

    # Build outputs dict
    outputs: Dict[str, OutputDescription] = {
        "result": OutputDescription(
            title="Result Layer",
            description="UUID of the output layer containing the analysis results",
            schema={"type": "string", "format": "uuid"},
        ),
    }

    # Build links
    links: List[Link] = []
    if base_url:
        links = [
            Link(
                href=f"{base_url}/processes/{tool_info.name}",
                rel="self",
                type="application/json",
            ),
            Link(
                href=f"{base_url}/processes/{tool_info.name}/execution",
                rel="http://www.opengis.net/def/rel/ogc/1.0/execute",
                type="application/json",
                title="Execute process",
            ),
        ]

    return ProcessDescription(
        id=tool_info.name,
        title=tool_info.display_name,
        description=tool_info.description,
        version="1.0.0",
        jobControlOptions=[JobControlOptions.async_execute],
        outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
        links=links,
        inputs=inputs,
        outputs=outputs,
    )


def generate_process_summary(
    tool_info: ToolInfo,
    base_url: str = "",
) -> ProcessSummary:
    """Generate OGC ProcessSummary from ToolInfo.

    Args:
        tool_info: ToolInfo from tool registry
        base_url: Base URL for generating links

    Returns:
        ProcessSummary for process list
    """
    links: List[Link] = []
    if base_url:
        links = [
            Link(
                href=f"{base_url}/processes/{tool_info.name}",
                rel="self",
                type="application/json",
                title=f"Process: {tool_info.display_name}",
            ),
        ]

    return ProcessSummary(
        id=tool_info.name,
        title=tool_info.display_name,
        description=tool_info.description,
        version="1.0.0",
        jobControlOptions=[JobControlOptions.async_execute],
        outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
        links=links,
    )


def get_process_list(base_url: str = "") -> List[ProcessSummary]:
    """Get list of all processes as OGC ProcessSummary objects.

    Args:
        base_url: Base URL for generating links

    Returns:
        List of ProcessSummary for all registered tools
    """
    tools = get_all_tools()
    return [
        generate_process_summary(tool_info, base_url) for tool_info in tools.values()
    ]


def get_process(process_id: str, base_url: str = "") -> Optional[ProcessDescription]:
    """Get OGC ProcessDescription for a specific process.

    Args:
        process_id: Process/tool name
        base_url: Base URL for generating links

    Returns:
        ProcessDescription or None if not found
    """
    tool_info = get_tool(process_id)
    if not tool_info:
        return None
    return generate_process_description(tool_info, base_url)
