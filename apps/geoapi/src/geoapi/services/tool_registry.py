"""
Auto-discovery tool registry for goatlib analysis tools.

This module automatically discovers all *Params classes from goatlib and
creates OGC Process descriptions from them.

The convention for tools is:
- Params: Schema class ending with "Params" (e.g., ClipParams, BufferParams)
- Tool: Tool class ending with "Tool" (e.g., ClipTool, BufferTool)

The tool name is derived from the class name by removing "Params" suffix
and converting to snake_case (e.g., "ClipParams" -> "clip").

Usage:
    from geoapi.services.tool_registry import tool_registry

    # Get tool by name
    tool_info = tool_registry.get_tool("clip")

    # Get all available tools
    tools = tool_registry.get_all_tools()

    # Get OGC process description
    process_desc = tool_registry.get_process_description("clip", base_url)
"""

import inspect
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel

from geoapi.models.processes import (
    InputDescription,
    JobControlOptions,
    Link,
    OutputDescription,
    ProcessDescription,
    ProcessList,
    ProcessSummary,
    TransmissionMode,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about a registered analysis tool."""

    name: str  # Short name (e.g., "clip")
    display_name: str  # Human readable (e.g., "Clip")
    description: str  # Description from docstring
    params_class: Type[BaseModel]  # Original *Params class
    tool_class: Type  # Tool execution class
    result_class: Type | None = None  # Result dataclass (optional)
    category: str = "geoprocessing"  # Tool category
    job_control_options: list[str] = field(default_factory=lambda: ["async-execute"])
    keywords: list[str] = field(default_factory=list)

    @property
    def supports_sync(self) -> bool:
        """Check if tool supports synchronous execution."""
        return "sync-execute" in self.job_control_options

    @property
    def supports_async(self) -> bool:
        """Check if tool supports asynchronous execution."""
        return "async-execute" in self.job_control_options


class ToolRegistry:
    """Registry for auto-discovered goatlib analysis tools."""

    def __init__(self):
        self._registry: dict[str, ToolInfo] = {}
        self._initialized = False

    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    def _extract_tool_name(self, class_name: str, suffix: str) -> str:
        """Extract tool name from class name by removing suffix."""
        if class_name.endswith(suffix):
            name = class_name[: -len(suffix)]
            return self._camel_to_snake(name)
        return self._camel_to_snake(class_name)

    def _get_description(self, cls: Type) -> str:
        """Extract description from class docstring."""
        if cls.__doc__:
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

    def _is_params_class(self, name: str, cls: Type) -> bool:
        """Check if a class is a *Params class (not *LayerParams)."""
        return (
            name.endswith("Params")
            and not name.endswith("LayerParams")
            and issubclass(cls, BaseModel)
            and hasattr(cls, "model_fields")
        )

    def _has_path_fields(self, cls: Type[BaseModel]) -> bool:
        """Check if a Params class has path-based fields that can be converted."""
        for field_name in cls.model_fields:
            if field_name.endswith("_path") or field_name.endswith("_paths"):
                return True
        return False

    def _setup_goatlib_path(self) -> None:
        """Ensure goatlib is importable."""
        # Add goatlib path if not already in sys.path
        goatlib_path = Path("/app/packages/python/goatlib/src")
        if goatlib_path.exists() and str(goatlib_path) not in sys.path:
            sys.path.insert(0, str(goatlib_path))
            logger.info(f"Added goatlib path: {goatlib_path}")

    def _discover_tools(self) -> None:
        """Auto-discover all *Params/*Tool pairs from goatlib."""
        if self._initialized:
            return

        self._setup_goatlib_path()

        try:
            from goatlib.analysis import (
                accessibility,
                data_management,
                geoprocessing,
                schemas,
            )

            # Find all *Params classes in schemas
            params_classes: dict[str, Type[BaseModel]] = {}
            params_categories: dict[str, str] = {}

            # Check geoprocessing schemas
            if hasattr(schemas, "geoprocessing"):
                for name, obj in inspect.getmembers(
                    schemas.geoprocessing, inspect.isclass
                ):
                    if self._is_params_class(name, obj) and self._has_path_fields(obj):
                        tool_name = self._extract_tool_name(name, "Params")
                        params_classes[tool_name] = obj
                        params_categories[tool_name] = "geoprocessing"
                        logger.debug(
                            f"Found geoprocessing Params: {name} -> {tool_name}"
                        )

            # Check data_management schemas
            if hasattr(schemas, "data_management"):
                for name, obj in inspect.getmembers(
                    schemas.data_management, inspect.isclass
                ):
                    if self._is_params_class(name, obj) and self._has_path_fields(obj):
                        tool_name = self._extract_tool_name(name, "Params")
                        params_classes[tool_name] = obj
                        params_categories[tool_name] = "data_management"
                        logger.debug(
                            f"Found data_management Params: {name} -> {tool_name}"
                        )

            # Check heatmap/accessibility schemas
            if hasattr(schemas, "heatmap"):
                for name, obj in inspect.getmembers(schemas.heatmap, inspect.isclass):
                    if self._is_params_class(name, obj) and self._has_path_fields(obj):
                        tool_name = self._extract_tool_name(name, "Params")
                        params_classes[tool_name] = obj
                        params_categories[tool_name] = "accessibility"
                        logger.debug(f"Found heatmap Params: {name} -> {tool_name}")

            # Fallback: Check vector schemas
            if hasattr(schemas, "vector") and not params_classes:
                for name, obj in inspect.getmembers(schemas.vector, inspect.isclass):
                    if self._is_params_class(name, obj) and self._has_path_fields(obj):
                        tool_name = self._extract_tool_name(name, "Params")
                        params_classes[tool_name] = obj
                        params_categories[tool_name] = "geoprocessing"
                        logger.debug(
                            f"Found vector Params (legacy): {name} -> {tool_name}"
                        )

            # Find matching *Tool classes
            tool_classes: dict[str, Type] = {}
            result_classes: dict[str, Type] = {}

            for module in [geoprocessing, data_management, accessibility]:
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name.endswith("Tool") and not name.endswith("LayerTool"):
                        tool_name = self._extract_tool_name(name, "Tool")
                        tool_classes[tool_name] = obj
                        logger.debug(f"Found Tool: {name} -> {tool_name}")
                    elif name.endswith("Result") and not name.endswith("LayerResult"):
                        tool_name = self._extract_tool_name(name, "Result")
                        result_classes[tool_name] = obj

            # Register tools with both params and tool classes
            for tool_name, params_class in params_classes.items():
                if tool_name in tool_classes:
                    tool_class = tool_classes[tool_name]
                    result_class = result_classes.get(tool_name)
                    category = params_categories.get(tool_name, "geoprocessing")

                    display_name = tool_name.replace("_", " ").title()
                    description = self._get_description(params_class)

                    self._registry[tool_name] = ToolInfo(
                        name=tool_name,
                        display_name=display_name,
                        description=description,
                        params_class=params_class,
                        tool_class=tool_class,
                        result_class=result_class,
                        category=category,
                        keywords=[category],
                    )
                    logger.info(f"Registered tool: {tool_name} (category: {category})")
                else:
                    logger.warning(
                        f"Found {params_class.__name__} but no matching Tool class"
                    )

            self._initialized = True
            logger.info(f"Tool registry initialized with {len(self._registry)} tools")

        except ImportError as e:
            logger.error(f"Could not initialize tool registry: {e}")
            self._initialized = True

    def get_tool(self, name: str) -> ToolInfo | None:
        """Get tool info by name."""
        self._discover_tools()
        return self._registry.get(name.lower())

    def get_all_tools(self) -> dict[str, ToolInfo]:
        """Get all registered tools."""
        self._discover_tools()
        return self._registry.copy()

    def get_tool_names(self) -> list[str]:
        """Get list of all tool names."""
        self._discover_tools()
        return list(self._registry.keys())

    def _pydantic_field_to_json_schema(
        self,
        field_name: str,
        field_info: Any,
        field_type: Any,
    ) -> dict[str, Any]:
        """Convert a Pydantic field to JSON Schema."""
        schema: dict[str, Any] = {}

        # Get type name
        origin = getattr(field_type, "__origin__", None)

        if origin is list:
            schema["type"] = "array"
            args = getattr(field_type, "__args__", ())
            if args:
                schema["items"] = self._python_type_to_json_schema(args[0])
        elif origin is dict:
            schema["type"] = "object"
        elif field_type is str:
            schema["type"] = "string"
        elif field_type is int:
            schema["type"] = "integer"
        elif field_type is float:
            schema["type"] = "number"
        elif field_type is bool:
            schema["type"] = "boolean"
        elif hasattr(field_type, "__members__"):  # Enum
            schema["type"] = "string"
            schema["enum"] = list(field_type.__members__.keys())
        else:
            schema["type"] = "object"

        return schema

    def _python_type_to_json_schema(self, python_type: Any) -> dict[str, Any]:
        """Convert Python type to JSON Schema."""
        if python_type is str:
            return {"type": "string"}
        elif python_type is int:
            return {"type": "integer"}
        elif python_type is float:
            return {"type": "number"}
        elif python_type is bool:
            return {"type": "boolean"}
        elif hasattr(python_type, "__members__"):  # Enum
            return {"type": "string", "enum": list(python_type.__members__.keys())}
        else:
            return {"type": "object"}

    def get_process_summary(
        self, tool_name: str, base_url: str
    ) -> ProcessSummary | None:
        """Get OGC process summary for a tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        return ProcessSummary(
            id=tool.name,
            title=tool.display_name,
            description=tool.description,
            version="1.0.0",
            keywords=tool.keywords,
            jobControlOptions=[
                JobControlOptions(opt) for opt in tool.job_control_options
            ],
            outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
            links=[
                Link(
                    href=f"{base_url}/processes/{tool.name}",
                    rel="self",
                    type="application/json",
                    title="Process description",
                ),
            ],
        )

    def get_process_description(
        self, tool_name: str, base_url: str
    ) -> ProcessDescription | None:
        """Get full OGC process description for a tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        # Build inputs from params class
        inputs: dict[str, InputDescription] = {}
        params_class = tool.params_class

        # Add standard GOAT inputs
        inputs["user_id"] = InputDescription(
            title="User ID",
            description="UUID of the user who owns the layers",
            schema_={"type": "string", "format": "uuid"},
            minOccurs=1,
            maxOccurs=1,
        )
        inputs["project_id"] = InputDescription(
            title="Project ID",
            description="UUID of the project (required for saving results)",
            schema_={"type": "string", "format": "uuid"},
            minOccurs=0,
            maxOccurs=1,
        )

        # Parse params class fields
        for field_name, field_info in params_class.model_fields.items():
            # Transform path fields to layer_id fields
            if field_name.endswith("_path"):
                layer_field = field_name.replace("_path", "_layer_id")
                filter_field = field_name.replace("_path", "_filter")

                inputs[layer_field] = InputDescription(
                    title=field_name.replace("_", " ")
                    .title()
                    .replace("Path", "Layer ID"),
                    description=field_info.description
                    or f"UUID of the {field_name.replace('_path', '')} layer",
                    schema_={"type": "string", "format": "uuid"},
                    minOccurs=1 if field_info.is_required() else 0,
                    maxOccurs=1,
                    keywords=["layer"],
                )

                # Add filter for non-output paths
                if not field_name.startswith("output"):
                    inputs[filter_field] = InputDescription(
                        title=f"{field_name.replace('_', ' ').title().replace('Path', '')} Filter",
                        description="SQL WHERE clause to filter layer features",
                        schema_={"type": "string"},
                        minOccurs=0,
                        maxOccurs=1,
                    )
            elif field_name.endswith("_paths"):
                layer_field = field_name.replace("_paths", "_layer_ids")
                inputs[layer_field] = InputDescription(
                    title=field_name.replace("_", " ")
                    .title()
                    .replace("Paths", "Layer IDs"),
                    description=field_info.description or "List of layer UUIDs",
                    schema_={
                        "type": "array",
                        "items": {"type": "string", "format": "uuid"},
                    },
                    minOccurs=1 if field_info.is_required() else 0,
                    maxOccurs="unbounded",
                    keywords=["layer"],
                )
            else:
                # Regular field
                field_type = field_info.annotation
                json_schema = self._pydantic_field_to_json_schema(
                    field_name, field_info, field_type
                )

                inputs[field_name] = InputDescription(
                    title=field_name.replace("_", " ").title(),
                    description=field_info.description or f"Parameter: {field_name}",
                    schema_=json_schema,
                    minOccurs=1 if field_info.is_required() else 0,
                    maxOccurs=1,
                )

        # Define outputs
        outputs = {
            "result": OutputDescription(
                title="Result",
                description="Processing result as GeoJSON or reference to DuckLake layer",
                schema_={
                    "oneOf": [
                        {"type": "object", "format": "geojson-feature-collection"},
                        {"type": "string", "format": "uri"},
                    ]
                },
            ),
        }

        return ProcessDescription(
            id=tool.name,
            title=tool.display_name,
            description=tool.description,
            version="1.0.0",
            keywords=tool.keywords,
            jobControlOptions=[
                JobControlOptions(opt) for opt in tool.job_control_options
            ],
            outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
            inputs=inputs,
            outputs=outputs,
            links=[
                Link(
                    href=f"{base_url}/processes/{tool.name}",
                    rel="self",
                    type="application/json",
                    title="Process description",
                ),
                Link(
                    href=f"{base_url}/processes/{tool.name}/execution",
                    rel="http://www.opengis.net/def/rel/ogc/1.0/execute",
                    type="application/json",
                    title="Execute process",
                ),
                Link(
                    href=f"{base_url}/processes",
                    rel="up",
                    type="application/json",
                    title="Process list",
                ),
            ],
        )

    def get_process_list(self, base_url: str, limit: int = 100) -> ProcessList:
        """Get OGC process list with all tools."""
        self._discover_tools()

        processes = []
        for tool_name in list(self._registry.keys())[:limit]:
            summary = self.get_process_summary(tool_name, base_url)
            if summary:
                processes.append(summary)

        return ProcessList(
            processes=processes,
            links=[
                Link(
                    href=f"{base_url}/processes",
                    rel="self",
                    type="application/json",
                    title="Process list",
                ),
            ],
        )


# Global registry instance
tool_registry = ToolRegistry()
