"""
Auto-discovery tool registry for goatlib analysis tools.

This module automatically discovers all *Params classes from goatlib and
dynamically generates *LayerParams versions using the layer_params_factory.

The convention for tools is:
- Params: Schema class ending with "Params" (e.g., ClipParams, BufferParams)
- Tool: Tool class ending with "Tool" (e.g., ClipTool, BufferTool)

The tool name is derived from the class name by removing "Params" suffix
and converting to snake_case (e.g., "ClipParams" -> "clip").

LayerParams classes are generated dynamically, transforming:
- input_path -> input_layer_id + input_filter
- overlay_path -> overlay_layer_id + overlay_filter
- output_path -> output_layer_id
- Adds user_id field

Usage:
    from lib.tool_registry import get_tool, get_all_tools, get_tool_schema

    # Get tool by name (auto-discovered)
    tool_info = get_tool("clip")
    params_class = tool_info.params_class  # Dynamically generated LayerParams
    tool_class = tool_info.tool_class      # Original Tool class

    # Get all available tools
    tools = get_all_tools()
"""

import inspect
import logging
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

# Add GOAT Core to path for imports
sys.path.insert(0, "/app/apps/core/src")

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about a registered analysis tool."""

    name: str  # Short name (e.g., "clip")
    display_name: str  # Human readable (e.g., "Clip")
    description: str  # Description from docstring
    params_class: Type[BaseModel]  # Original *Params class (path-based)
    layer_params_class: Type[BaseModel]  # Dynamically generated *LayerParams class
    tool_class: Type  # Tool execution class
    result_class: Optional[Type] = None  # Result dataclass (optional)
    category: str = "vector"  # Tool category
    job_control_options: List[str] = (
        None  # OGC jobControlOptions: sync-execute, async-execute
    )

    def __post_init__(self):
        # Default to async-execute for traditional tools
        if self.job_control_options is None:
            self.job_control_options = ["async-execute"]

    @property
    def supports_sync(self) -> bool:
        """Check if tool supports synchronous execution."""
        return "sync-execute" in self.job_control_options

    @property
    def supports_async(self) -> bool:
        """Check if tool supports asynchronous execution."""
        return "async-execute" in self.job_control_options


# Tool registry - populated by auto-discovery
_registry: Dict[str, ToolInfo] = {}
_initialized = False


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _extract_tool_name(class_name: str, suffix: str) -> str:
    """Extract tool name from class name by removing suffix.

    Examples:
        ClipParams -> clip
        BufferParams -> buffer
        OriginDestinationParams -> origin_destination
    """
    if class_name.endswith(suffix):
        name = class_name[: -len(suffix)]
        return _camel_to_snake(name)
    return _camel_to_snake(class_name)


def _get_description(cls: Type) -> str:
    """Extract description from class docstring."""
    if cls.__doc__:
        # Get first line or paragraph of docstring
        lines = cls.__doc__.strip().split("\n")
        first_para = []
        for line in lines:
            line = line.strip()
            if not line and first_para:
                break
            if line:
                first_para.append(line)
        return " ".join(first_para)
    return f"{cls.__name__} analysis tool"


def _is_params_class(name: str, cls: Type) -> bool:
    """Check if a class is a *Params class (not *LayerParams)."""
    return (
        name.endswith("Params")
        and not name.endswith("LayerParams")
        and issubclass(cls, BaseModel)
        and hasattr(cls, "model_fields")
    )


def _has_path_fields(cls: Type[BaseModel]) -> bool:
    """Check if a Params class has path-based fields that can be converted."""
    for field_name in cls.model_fields:
        if field_name.endswith("_path") or field_name.endswith("_paths"):
            return True
    return False


def _discover_tools() -> None:
    """Auto-discover all *Params/*Tool pairs from goatlib and generate LayerParams."""
    global _registry, _initialized

    if _initialized:
        return

    try:
        # Import goatlib modules
        from goatlib.analysis import data_management, geoprocessing, schemas

        # Import local layer_params_factory (not from goatlib)
        from lib.layer_params_factory import create_layer_params_class

        # Find all *Params classes in schemas (not *LayerParams)
        params_classes: Dict[str, Type[BaseModel]] = {}
        params_categories: Dict[str, str] = {}  # Track category for each params class

        # Check geoprocessing schemas
        if hasattr(schemas, "geoprocessing"):
            for name, obj in inspect.getmembers(schemas.geoprocessing, inspect.isclass):
                if _is_params_class(name, obj) and _has_path_fields(obj):
                    tool_name = _extract_tool_name(name, "Params")
                    params_classes[tool_name] = obj
                    params_categories[tool_name] = "geoprocessing"
                    logger.debug(f"Found geoprocessing Params: {name} -> {tool_name}")

        # Check data_management schemas
        if hasattr(schemas, "data_management"):
            for name, obj in inspect.getmembers(
                schemas.data_management, inspect.isclass
            ):
                if _is_params_class(name, obj) and _has_path_fields(obj):
                    tool_name = _extract_tool_name(name, "Params")
                    params_classes[tool_name] = obj
                    params_categories[tool_name] = "data_management"
                    logger.debug(f"Found data_management Params: {name} -> {tool_name}")

        # Fallback: Check vector schemas for backwards compatibility
        if hasattr(schemas, "vector") and not params_classes:
            for name, obj in inspect.getmembers(schemas.vector, inspect.isclass):
                if _is_params_class(name, obj) and _has_path_fields(obj):
                    tool_name = _extract_tool_name(name, "Params")
                    params_classes[tool_name] = obj
                    params_categories[tool_name] = (
                        "geoprocessing"  # Default to geoprocessing
                    )
                    logger.debug(f"Found vector Params (legacy): {name} -> {tool_name}")

        # Find matching *Tool classes in geoprocessing module (not *LayerTool)
        tool_classes: Dict[str, Type] = {}
        result_classes: Dict[str, Type] = {}

        for name, obj in inspect.getmembers(geoprocessing, inspect.isclass):
            if name.endswith("Tool") and not name.endswith("LayerTool"):
                tool_name = _extract_tool_name(name, "Tool")
                tool_classes[tool_name] = obj
                logger.debug(f"Found geoprocessing Tool: {name} -> {tool_name}")
            elif name.endswith("Result") and not name.endswith("LayerResult"):
                tool_name = _extract_tool_name(name, "Result")
                result_classes[tool_name] = obj
                logger.debug(f"Found geoprocessing Result: {name} -> {tool_name}")

        # Find matching *Tool classes in data_management module
        for name, obj in inspect.getmembers(data_management, inspect.isclass):
            if name.endswith("Tool") and not name.endswith("LayerTool"):
                tool_name = _extract_tool_name(name, "Tool")
                tool_classes[tool_name] = obj
                logger.debug(f"Found data_management Tool: {name} -> {tool_name}")
            elif name.endswith("Result") and not name.endswith("LayerResult"):
                tool_name = _extract_tool_name(name, "Result")
                result_classes[tool_name] = obj
                logger.debug(f"Found data_management Result: {name} -> {tool_name}")

        # Register tools that have both params and tool classes
        for tool_name, params_class in params_classes.items():
            if tool_name in tool_classes:
                tool_class = tool_classes[tool_name]
                result_class = result_classes.get(tool_name)
                category = params_categories.get(tool_name, "geoprocessing")

                # Dynamically generate LayerParams class
                try:
                    layer_params_class = create_layer_params_class(params_class)
                    logger.debug(
                        f"Generated {layer_params_class.__name__} from {params_class.__name__}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not generate LayerParams for {params_class.__name__}: {e}"
                    )
                    continue

                # Create ToolInfo
                display_name = tool_name.replace("_", " ").title()
                description = _get_description(params_class)

                _registry[tool_name] = ToolInfo(
                    name=tool_name,
                    display_name=display_name,
                    description=description,
                    params_class=params_class,
                    layer_params_class=layer_params_class,
                    tool_class=tool_class,
                    result_class=result_class,
                    category=category,
                )
                logger.info(f"Registered tool: {tool_name} (category: {category})")
            else:
                logger.warning(
                    f"Found {params_class.__name__} but no matching Tool class"
                )

        _initialized = True
        logger.info(f"Tool registry initialized with {len(_registry)} tools")

    except ImportError as e:
        logger.error(f"Could not initialize tool registry: {e}")
        _initialized = True


def get_tool(name: str) -> Optional[ToolInfo]:
    """Get tool info by name.

    Args:
        name: Tool name (e.g., "clip", "buffer")

    Returns:
        ToolInfo or None if not found
    """
    _discover_tools()
    return _registry.get(name.lower())


def get_all_tools() -> Dict[str, ToolInfo]:
    """Get all registered tools.

    Returns:
        Dict mapping tool names to ToolInfo
    """
    _discover_tools()
    return _registry.copy()


def get_tool_names() -> List[str]:
    """Get list of all registered tool names.

    Returns:
        List of tool names
    """
    _discover_tools()
    return list(_registry.keys())


def get_tool_schema(name: str) -> Optional[Dict[str, Any]]:
    """Get JSON schema for a tool's layer params.

    Args:
        name: Tool name

    Returns:
        JSON schema dict or None if tool not found
    """
    tool = get_tool(name)
    if tool:
        return tool.layer_params_class.model_json_schema()
    return None


def get_motia_input_schema(
    name: str, extra_fields: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """Get Motia input schema for a tool (params + job fields).

    Args:
        name: Tool name
        extra_fields: Additional fields (defaults to jobId, timestamp, tool_name)

    Returns:
        JSON schema dict for Motia step config
    """
    tool = get_tool(name)
    if not tool:
        return None

    schema = tool.layer_params_class.model_json_schema()

    # Add standard Motia fields
    default_extras = {
        "jobId": {"type": "string", "description": "Unique job identifier"},
        "timestamp": {"type": "string", "description": "Job creation timestamp"},
        "tool_name": {"type": "string", "description": "Name of the tool to execute"},
    }

    if extra_fields:
        for field_name, field_type in extra_fields.items():
            default_extras[field_name] = {"type": field_type}

    schema.setdefault("properties", {}).update(default_extras)
    schema.setdefault("required", []).extend(["jobId", "timestamp", "tool_name"])

    return schema


def get_combined_input_schema() -> Dict[str, Any]:
    """Get combined input schema for all tools (for generic API step).

    This creates a schema that accepts:
    - tool_name: which tool to run
    - Common fields across all tools
    - Tool-specific fields as optional (union of all)

    Returns:
        JSON schema dict
    """
    _discover_tools()

    # Get list of tool names for enum
    tool_names = list(_registry.keys()) if _registry else ["clip"]

    # Start with base schema
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "enum": tool_names,
                "description": "Name of the analysis tool to execute",
            },
            "jobId": {"type": "string", "description": "Unique job identifier"},
            "timestamp": {"type": "string", "description": "Job creation timestamp"},
            # Common layer operation fields
            "user_id": {"type": "string", "description": "UUID of the user"},
            "output_layer_id": {
                "type": "string",
                "description": "UUID for output layer (optional)",
            },
        },
        "required": ["tool_name", "jobId", "timestamp", "user_id"],
    }

    # Collect all unique properties from all tools (use layer_params_class)
    all_properties: Dict[str, Any] = {}
    for tool_info in _registry.values():
        tool_schema = tool_info.layer_params_class.model_json_schema()
        for prop_name, prop_schema in tool_schema.get("properties", {}).items():
            if prop_name not in schema["properties"]:
                # Make tool-specific fields optional in combined schema
                all_properties[prop_name] = prop_schema

    schema["properties"].update(all_properties)

    return schema


def get_tools_metadata(include_schema: bool = False) -> List[Dict[str, Any]]:
    """Get metadata for all tools (for API responses).

    Args:
        include_schema: If True, include JSON schema for each tool's params

    Returns:
        List of dicts with name, display_name, description, category, and optionally schema
    """
    _discover_tools()
    result = []
    for info in _registry.values():
        tool_data: Dict[str, Any] = {
            "name": info.name,
            "display_name": info.display_name,
            "description": info.description,
            "category": info.category,
            "job_control_options": info.job_control_options,
        }
        if include_schema:
            tool_data["schema"] = info.layer_params_class.model_json_schema()
        result.append(tool_data)
    return result


def _register_statistics_tools() -> None:
    """Register statistics tools from goatlib.

    Statistics tools support synchronous execution (sync-execute) because
    they return results quickly without requiring background job processing.
    """
    global _registry

    try:
        from goatlib.analysis.statistics import (
            AreaStatisticsInput,
            ClassBreaksInput,
            FeatureCountInput,
            UniqueValuesInput,
            calculate_area_statistics,
            calculate_class_breaks,
            calculate_feature_count,
            calculate_unique_values,
        )
        from pydantic import Field, create_model

        # Create layer params classes that add collection and user_id
        def create_statistics_layer_params(
            base_class: Type[BaseModel], class_name: str
        ) -> Type[BaseModel]:
            """Create a LayerParams class from a statistics input class."""
            # Get fields from base class
            base_fields = {
                name: (info.annotation, info)
                for name, info in base_class.model_fields.items()
            }

            # Add layer/user fields
            layer_fields = {
                "collection": (
                    str,
                    Field(description="Collection/layer ID to analyze"),
                ),
                "user_id": (str, Field(description="UUID of the user")),
            }

            # Combine fields
            all_fields = {**layer_fields, **base_fields}

            return create_model(class_name, **all_fields)

        # Statistics tools - all support sync execution
        statistics_tools = [
            {
                "name": "feature_count",
                "display_name": "Feature Count",
                "description": "Count features in a layer with optional filtering",
                "params_class": FeatureCountInput,
                "execute_fn": calculate_feature_count,
                "category": "statistics",
            },
            {
                "name": "unique_values",
                "display_name": "Unique Values",
                "description": "Get unique values of an attribute with occurrence counts",
                "params_class": UniqueValuesInput,
                "execute_fn": calculate_unique_values,
                "category": "statistics",
            },
            {
                "name": "class_breaks",
                "display_name": "Class Breaks",
                "description": "Calculate classification breaks for a numeric attribute using various methods (quantile, equal interval, standard deviation, heads and tails)",
                "params_class": ClassBreaksInput,
                "execute_fn": calculate_class_breaks,
                "category": "statistics",
            },
            {
                "name": "area_statistics",
                "display_name": "Area Statistics",
                "description": "Calculate area-based statistics (sum, mean, min, max) for polygon features",
                "params_class": AreaStatisticsInput,
                "execute_fn": calculate_area_statistics,
                "category": "statistics",
            },
        ]

        for tool_def in statistics_tools:
            # Create a simple wrapper class for consistency with tool_class interface
            execute_fn = tool_def["execute_fn"]

            class StatisticsToolWrapper:
                """Wrapper to provide consistent interface for statistics functions."""

                def __init__(self, fn):
                    self._fn = fn

                def __call__(self, *args, **kwargs):
                    return self._fn(*args, **kwargs)

            wrapper = StatisticsToolWrapper(execute_fn)
            wrapper.__name__ = f"{tool_def['name'].title().replace('_', '')}Tool"

            # Create layer params class with input_layer_id and user_id
            layer_params_class = create_statistics_layer_params(
                tool_def["params_class"],
                f"{tool_def['name'].title().replace('_', '')}LayerParams",
            )

            _registry[tool_def["name"]] = ToolInfo(
                name=tool_def["name"],
                display_name=tool_def["display_name"],
                description=tool_def["description"],
                params_class=tool_def["params_class"],
                layer_params_class=layer_params_class,  # Use generated layer params
                tool_class=wrapper,
                result_class=None,  # Result is returned directly
                category=tool_def["category"],
                job_control_options=["sync-execute"],  # Statistics are sync-only
            )
            logger.info(f"Registered statistics tool: {tool_def['name']}")

    except ImportError as e:
        logger.warning(f"Could not register statistics tools: {e}")


# Auto-register statistics tools when module loads
def _ensure_statistics_registered():
    """Ensure statistics tools are registered after discovery."""
    global _initialized
    if _initialized:
        _register_statistics_tools()


# Override _discover_tools to also register statistics
_original_discover_tools = _discover_tools


def _discover_tools_with_statistics() -> None:
    """Discover tools and register statistics."""
    _original_discover_tools()
    _register_statistics_tools()


# Replace the function
_discover_tools = _discover_tools_with_statistics
