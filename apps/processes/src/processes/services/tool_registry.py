"""
Tool registry for goatlib Windmill tools.

This module uses goatlib.tools.*ToolParams classes as the single source of truth
for both OGC Processes API and Windmill script generation.

Includes support for:
- UI metadata extraction (x-ui-sections, x-ui field config)
- i18n translation resolution based on Accept-Language header

Usage:
    from processes.services.tool_registry import tool_registry

    # Get tool by name
    tool_info = tool_registry.get_tool("buffer")

    # Get all available tools
    tools = tool_registry.get_all_tools()

    # Get OGC process description with translations
    process_desc = tool_registry.get_process_description("buffer", base_url, language="de")
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Self

from pydantic import BaseModel

from processes.models.processes import (
    InputDescription,
    JobControlOptions,
    Link,
    Metadata,
    OutputDescription,
    ProcessDescription,
    ProcessList,
    ProcessSummary,
    TransmissionMode,
)

logger = logging.getLogger(__name__)

# Fields to exclude from OGC Process inputs (internal implementation details)
EXCLUDED_FIELDS = {
    "input_path",
    "output_path",
    "output_name",  # Hide for now, use automatic naming
    "overlay_path",
    "output_crs",
    "reference_area_path",  # heatmap_connectivity internal path
}

# Default language for translations
DEFAULT_LANGUAGE = "en"


@dataclass
class ToolInfo:
    """Information about a registered analysis tool."""

    name: str  # Short name (e.g., "buffer")
    display_name: str  # Human readable (e.g., "Buffer")
    description: str  # Tool description
    params_class: type[BaseModel]  # *ToolParams class from goatlib.tools
    windmill_path: str  # Windmill script path (e.g., "f/goat/buffer")
    category: str = "geoprocessing"
    job_control_options: list[str] = field(default_factory=lambda: ["async-execute"])
    keywords: list[str] = field(default_factory=list)
    toolbox_hidden: bool = False  # Hide from toolbox UI
    docs_path: str | None = (
        None  # Documentation path (e.g., "/toolbox/geoprocessing/buffer")
    )
    worker_tag: str = "tools"  # Windmill worker tag for job routing

    @property
    def supports_sync(self) -> bool:
        """Check if tool supports synchronous execution."""
        return "sync-execute" in self.job_control_options

    @property
    def supports_async(self) -> bool:
        """Check if tool supports asynchronous execution."""
        return "async-execute" in self.job_control_options


class ToolRegistry:
    """Registry for goatlib tools using *ToolParams as single source of truth.

    Supports UI metadata extraction and i18n translations.
    """

    def __init__(self: Self) -> None:
        self._registry: dict[str, ToolInfo] = {}
        self._initialized = False
        self._translator_cache: dict[str, Any] = {}

    def _get_translator(self: Self, language: str) -> Any:
        """Get cached translator for a language."""
        if language not in self._translator_cache:
            try:
                from goatlib.i18n import get_translator

                self._translator_cache[language] = get_translator(language)
            except ImportError:
                logger.warning("goatlib.i18n not available, translations disabled")
                self._translator_cache[language] = None
            except Exception:
                logger.exception(f"Failed to initialize translator for {language}")
                self._translator_cache[language] = None

        return self._translator_cache[language]

    def _get_description(
        self: Self,
        params_class: type[BaseModel],
    ) -> str:
        """Extract tool description from Pydantic class docstring or fallback."""
        if params_class.__doc__:
            # Take first line of docstring
            return params_class.__doc__.strip().split("\n")[0]
        return f"Run {params_class.__name__} analysis"

    def _init_tools(self: Self) -> None:
        """Initialize all goatlib tools from their *ToolParams classes.

        Uses lazy initialization - only called when registry is first accessed.
        """
        if self._initialized:
            return

        try:
            # Import tool registry from goatlib - single source of truth
            from goatlib.tools.registry import TOOL_REGISTRY

            for tool_def in TOOL_REGISTRY:
                try:
                    params_class = tool_def.get_params_class()
                    self._registry[tool_def.name] = ToolInfo(
                        name=tool_def.name,
                        display_name=tool_def.display_name,
                        description=self._get_description(params_class),
                        params_class=params_class,
                        windmill_path=tool_def.windmill_path,
                        category=tool_def.category,
                        job_control_options=[
                            "async-execute"
                        ],  # All tools support async
                        keywords=list(tool_def.keywords),
                        toolbox_hidden=tool_def.toolbox_hidden,
                        docs_path=tool_def.docs_path,
                        worker_tag=tool_def.worker_tag,
                    )
                except Exception as e:
                    logger.warning(f"Failed to register tool {tool_def.name}: {e}")

            logger.info(f"Initialized {len(self._registry)} tools from goatlib")

        except ImportError as e:
            logger.warning(f"goatlib not available, tools disabled: {e}")
        except Exception:
            logger.exception("Failed to initialize tools")

        self._initialized = True

    def get_tool(self: Self, name: str) -> ToolInfo | None:
        """Get tool info by name."""
        self._init_tools()
        return self._registry.get(name)

    def get_all_tools(self: Self) -> dict[str, ToolInfo]:
        """Get all registered tools."""
        self._init_tools()
        return self._registry

    def get_tool_names(self: Self) -> list[str]:
        """Get list of all tool names."""
        self._init_tools()
        return list(self._registry.keys())

    def get_full_json_schema(
        self: Self,
        tool_name: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> dict | None:
        """Get full JSON schema for a tool with translations applied.

        Returns the Pydantic-generated JSON schema with x-ui metadata,
        and translates labels/descriptions based on language.

        Args:
            tool_name: Tool name
            language: ISO 639-1 language code
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        # Get base schema from Pydantic
        schema = tool.params_class.model_json_schema()

        # Apply translations using goatlib.i18n (handles sections, fields, enum_labels)
        translator = self._get_translator(language)
        if translator:
            try:
                from goatlib.i18n import resolve_schema_translations

                schema = resolve_schema_translations(schema, language, translator)
            except ImportError:
                logger.debug("Translation resolution not available")

        return schema

    def _json_schema_for_field(
        self: Self,
        field_name: str,
        field_info: Any,
    ) -> dict[str, Any]:
        """Generate JSON schema for a single Pydantic field.

        Fallback when field not in full schema (shouldn't happen normally).
        """
        return self._type_to_json_schema(field_info.annotation, field_name)

    def _type_to_json_schema(
        self: Self,
        python_type: Any,
        field_name: str | None = None,
    ) -> dict[str, Any]:
        """Convert Python type to JSON schema type.

        Handles common types including Optional, List, Literal, UUID, etc.
        """
        import types
        from enum import Enum
        from typing import Literal, get_args, get_origin
        from uuid import UUID

        origin = get_origin(python_type)
        args = get_args(python_type)

        # Handle Optional (Union with None)
        if origin is types.UnionType or origin is type(None):
            # Filter out None to get the actual type
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                return self._type_to_json_schema(non_none_args[0], field_name)
            # Multiple types - return anyOf
            return {"anyOf": [self._type_to_json_schema(t) for t in non_none_args]}

        # Handle Literal
        if origin is Literal:
            return {"enum": list(args)}

        # Handle List/list
        if origin in (list, tuple):
            if args:
                return {
                    "type": "array",
                    "items": self._type_to_json_schema(args[0]),
                }
            return {"type": "array"}

        # Handle dict
        if origin is dict:
            return {"type": "object"}

        # Handle primitives
        if python_type is str:
            return {"type": "string"}
        if python_type is int:
            return {"type": "integer"}
        if python_type is float:
            return {"type": "number"}
        if python_type is bool:
            return {"type": "boolean"}
        if python_type is UUID:
            return {"type": "string", "format": "uuid"}

        # Handle Enum
        if isinstance(python_type, type) and issubclass(python_type, Enum):
            return {"enum": [e.value for e in python_type]}

        # Handle Pydantic models (nested)
        if hasattr(python_type, "model_json_schema"):
            return {"$ref": f"#/$defs/{python_type.__name__}"}

        # Fallback
        return {"type": "string"}

    def _extract_geometry_metadata(
        self: Self,
        x_ui: dict[str, Any],
    ) -> list[Metadata]:
        """Extract geometry constraint metadata from x-ui widget options.

        Converts widget_options geometry constraints to OGC metadata format.
        """
        metadata = []
        widget_options = x_ui.get("widget_options", {})

        if "geometry_types" in widget_options:
            metadata.append(
                Metadata(
                    title="geometry_types",
                    role="constraint",
                    value=",".join(widget_options["geometry_types"]),
                )
            )

        if "multi_select" in widget_options:
            metadata.append(
                Metadata(
                    title="multi_select",
                    role="constraint",
                    value=str(widget_options["multi_select"]).lower(),
                )
            )

        return metadata

    def get_process_summary(
        self: Self,
        tool_name: str,
        base_url: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> ProcessSummary | None:
        """Get OGC process summary for a tool.

        Args:
            tool_name: Tool name
            base_url: Base URL for links
            language: Language code for translations
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        # Get translated title/description if available
        title = tool.display_name
        description = tool.description
        translator = self._get_translator(language)
        if translator:
            translated_title = translator.get_tool_title(tool.name)
            translated_desc = translator.get_tool_description(tool.name)
            if translated_title:
                title = translated_title
            if translated_desc:
                description = translated_desc

        return ProcessSummary(
            id=tool.name,
            title=title,
            description=description,
            version="1.0.0",
            keywords=tool.keywords,
            jobControlOptions=[
                JobControlOptions(opt) for opt in tool.job_control_options
            ],
            outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
            x_ui_toolbox_hidden=tool.toolbox_hidden,
            x_ui_category=tool.category,
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
        self: Self,
        tool_name: str,
        base_url: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> ProcessDescription | None:
        """Get full OGC process description for a tool.

        Uses Pydantic's model_fields to generate OGC-compliant input descriptions.
        Excludes internal fields (input_path, output_path, etc.) that are
        implementation details not exposed to users.

        Includes UI metadata (x-ui-sections, x-ui) and resolved translations.

        Args:
            tool_name: Tool name (e.g., "buffer")
            base_url: Base URL for links
            language: ISO 639-1 language code for translations
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        # Get full JSON schema with UI metadata and translations
        full_schema = self.get_full_json_schema(tool_name, language)

        # Get translator for field labels
        translator = self._get_translator(language)

        # Extract x-ui-sections from schema
        ui_sections = full_schema.get("x-ui-sections", []) if full_schema else []

        # Build inputs from params class model_fields
        inputs: dict[str, InputDescription] = {}

        for field_name, field_info in tool.params_class.model_fields.items():
            # Skip internal fields
            if field_name in EXCLUDED_FIELDS:
                continue

            # Get field schema from Pydantic-generated full schema (includes $ref, x-ui, etc.)
            # Need to check both field_name and alias (Pydantic uses alias as property key in JSON schema)
            schema_key = field_info.alias if field_info.alias else field_name
            field_schema = (
                full_schema.get("properties", {}).get(schema_key, {})
                if full_schema
                else {}
            )

            # Check if field is hidden via x-ui metadata
            x_ui = field_schema.get("x-ui", {})
            if x_ui.get("hidden", False):
                continue

            # Use field schema from full_schema directly (preserves $ref, nested types, x-ui)
            # Only fallback to manual conversion if not in full_schema
            if field_schema:
                json_schema = field_schema.copy()
            else:
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

            # Get translated title/description
            # First check if x-ui.label/description was set (from label_key resolution)
            title = (
                x_ui.get("label")
                or field_info.title
                or field_name.replace("_", " ").title()
            )
            description = (
                x_ui.get("description")
                or field_info.description
                or f"Parameter: {field_name}"
            )

            if translator:
                # If no x-ui.label, try translating field_name directly
                if not x_ui.get("label"):
                    translated_label = translator.get_field_label(field_name)
                    if translated_label:
                        title = translated_label
                # If no x-ui.description, try translating field_name directly
                if not x_ui.get("description"):
                    translated_desc = translator.get_field_description(field_name)
                    if translated_desc:
                        description = translated_desc

            inputs[field_name] = InputDescription(
                title=title,
                description=description,
                schema_=json_schema,
                minOccurs=1 if field_info.is_required() else 0,
                maxOccurs=1,
                # Mark layer fields so UI can render layer selector dropdown
                keywords=["layer"] if is_layer_field else [],
                # Add geometry constraints as metadata if present in widget_options
                metadata=self._extract_geometry_metadata(x_ui),
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

        # Get translated tool title/description
        title = tool.display_name
        description = tool.description
        if translator:
            translated_title = translator.get_tool_title(tool.name)
            translated_desc = translator.get_tool_description(tool.name)
            if translated_title:
                title = translated_title
            if translated_desc:
                description = translated_desc

        # Extract $defs from full schema for nested type resolution
        schema_defs = full_schema.get("$defs", {}) if full_schema else {}

        # Build links list
        links = [
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
        ]

        # Add documentation link if docs_path is available
        if tool.docs_path:
            links.append(
                Link(
                    href=tool.docs_path,
                    rel="describedby",
                    type="text/html",
                    title="Documentation",
                )
            )

        # Build process description with UI sections
        process_desc = ProcessDescription(
            id=tool.name,
            title=title,
            description=description,
            version="1.0.0",
            keywords=tool.keywords,
            jobControlOptions=[
                JobControlOptions(opt) for opt in tool.job_control_options
            ],
            outputTransmission=[TransmissionMode.value, TransmissionMode.reference],
            inputs=inputs,
            outputs=outputs,
            x_ui_sections=ui_sections,
            schema_defs=schema_defs,
            links=links,
        )

        return process_desc

    def get_process_list(
        self: Self,
        base_url: str,
        limit: int = 100,
        language: str = DEFAULT_LANGUAGE,
    ) -> ProcessList:
        """Get OGC process list with all tools.

        Args:
            base_url: Base URL for links
            limit: Maximum number of processes to return
            language: Language code for translations
        """
        self._init_tools()

        processes = []
        for tool_name in list(self._registry.keys())[:limit]:
            summary = self.get_process_summary(tool_name, base_url, language)
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
