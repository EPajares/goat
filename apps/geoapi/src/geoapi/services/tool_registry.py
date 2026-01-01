"""
Tool registry for goatlib Windmill tools.

This module uses goatlib.tools.*ToolParams classes as the single source of truth
for both OGC Processes API and Windmill script generation.

Usage:
    from geoapi.services.tool_registry import tool_registry

    # Get tool by name
    tool_info = tool_registry.get_tool("buffer")

    # Get all available tools
    tools = tool_registry.get_all_tools()

    # Get OGC process description
    process_desc = tool_registry.get_process_description("buffer", base_url)
"""

import logging
from dataclasses import dataclass, field
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

# Fields to exclude from OGC Process inputs (internal implementation details)
EXCLUDED_FIELDS = {"input_path", "output_path", "overlay_path", "output_crs"}


@dataclass
class ToolInfo:
    """Information about a registered analysis tool."""

    name: str  # Short name (e.g., "buffer")
    display_name: str  # Human readable (e.g., "Buffer")
    description: str  # Tool description
    params_class: Type[BaseModel]  # *ToolParams class from goatlib.tools
    windmill_path: str  # Windmill script path (e.g., "f/goat/buffer")
    category: str = "geoprocessing"
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
    """Registry for goatlib tools using *ToolParams as single source of truth."""

    def __init__(self):
        self._registry: dict[str, ToolInfo] = {}
        self._initialized = False

    def _get_description(self, cls: Type) -> str:
        """Extract first paragraph from class docstring."""
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
        return f"{cls.__name__} tool"

    def _init_tools(self) -> None:
        """Initialize tools from goatlib.tools.registry."""
        if self._initialized:
            return

        try:
            from goatlib.tools.registry import TOOL_REGISTRY

            for tool_def in TOOL_REGISTRY:
                params_class = tool_def.get_params_class()
                self._registry[tool_def.name] = ToolInfo(
                    name=tool_def.name,
                    display_name=tool_def.display_name,
                    description=self._get_description(params_class),
                    params_class=params_class,
                    windmill_path=tool_def.windmill_path,
                    category=tool_def.category,
                    keywords=list(tool_def.keywords),
                )

            self._initialized = True
            logger.info(f"Tool registry initialized with {len(self._registry)} tools")

        except ImportError as e:
            logger.error(f"Could not initialize tool registry: {e}")
            self._initialized = True

    def get_tool(self, name: str) -> ToolInfo | None:
        """Get tool info by name."""
        self._init_tools()
        return self._registry.get(name.lower())

    def get_all_tools(self) -> dict[str, ToolInfo]:
        """Get all registered tools."""
        self._init_tools()
        return self._registry.copy()

    def get_tool_names(self) -> list[str]:
        """Get list of all tool names."""
        self._init_tools()
        return list(self._registry.keys())

    def _json_schema_for_field(
        self, field_name: str, field_info: Any
    ) -> dict[str, Any]:
        """Convert Pydantic field to JSON Schema."""
        from typing import Union, get_args, get_origin

        from pydantic_core import PydanticUndefined

        annotation = field_info.annotation
        origin = get_origin(annotation)

        # Handle Optional types (Union with None)
        if origin is Union:
            args = get_args(annotation)
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                # It's Optional[X], recurse on X
                inner_schema = self._type_to_json_schema(non_none[0])
            else:
                # Multiple types - use anyOf
                inner_schema = {
                    "anyOf": [self._type_to_json_schema(a) for a in non_none]
                }
        else:
            inner_schema = self._type_to_json_schema(annotation)

        # Add default value if present
        if (
            field_info.default is not None
            and field_info.default is not PydanticUndefined
        ):
            inner_schema["default"] = field_info.default

        return inner_schema

    def _type_to_json_schema(self, python_type: Any) -> dict[str, Any]:
        """Convert Python type to JSON Schema."""
        from typing import Literal, get_args, get_origin

        origin = get_origin(python_type)

        if python_type is str:
            return {"type": "string"}
        elif python_type is int:
            return {"type": "integer"}
        elif python_type is float:
            return {"type": "number"}
        elif python_type is bool:
            return {"type": "boolean"}
        elif origin is list:
            args = get_args(python_type)
            if args:
                return {"type": "array", "items": self._type_to_json_schema(args[0])}
            return {"type": "array"}
        elif origin is Literal:
            args = get_args(python_type)
            return {"type": "string", "enum": list(args)}
        elif hasattr(python_type, "__members__"):  # Enum
            return {"type": "string", "enum": list(python_type.__members__.keys())}
        else:
            return {"type": "string"}

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
        """Get full OGC process description for a tool.

        Uses Pydantic's model_fields to generate OGC-compliant input descriptions.
        Excludes internal fields (input_path, output_path, etc.) that are
        implementation details not exposed to users.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        # Build inputs from params class model_fields
        inputs: dict[str, InputDescription] = {}

        for field_name, field_info in tool.params_class.model_fields.items():
            # Skip internal fields
            if field_name in EXCLUDED_FIELDS:
                continue

            # Get JSON schema for field
            json_schema = self._json_schema_for_field(field_name, field_info)

            # Detect layer fields - these get special UI treatment (dropdown selector)
            is_layer_field = field_name.endswith("_layer_id") or field_name.endswith(
                "_layer_ids"
            )

            # Add format hints for known field types
            if is_layer_field:
                json_schema["format"] = "uuid"
            elif field_name in ("user_id", "folder_id", "project_id"):
                json_schema["format"] = "uuid"

            inputs[field_name] = InputDescription(
                title=field_info.title or field_name.replace("_", " ").title(),
                description=field_info.description or f"Parameter: {field_name}",
                schema_=json_schema,
                minOccurs=1 if field_info.is_required() else 0,
                maxOccurs=1,
                # Mark layer fields so UI can render layer selector dropdown
                keywords=["layer"] if is_layer_field else [],
            )

        # Define outputs
        outputs = {
            "result": OutputDescription(
                title="Result",
                description="Processing result with layer metadata",
                schema_={
                    "type": "object",
                    "properties": {
                        "layer_id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "feature_count": {"type": "integer"},
                    },
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
        self._init_tools()

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
