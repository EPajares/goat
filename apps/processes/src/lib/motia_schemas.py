"""
Schema utilities for converting goatlib Pydantic models to Motia/Zod schemas.

This module provides utilities to dynamically generate Motia-compatible schemas
from goatlib's Pydantic models, avoiding duplication and ensuring consistency.

For the tool registry and tool lookup, see tool_registry.py.

Usage:
    from lib.motia_schemas import pydantic_to_zod_schema, pydantic_to_json_schema

    # Get JSON schema for Python Motia steps
    schema = pydantic_to_json_schema(MyPydanticModel)

    # Get Zod-compatible schema string for TypeScript
    zod_schema = pydantic_to_zod_schema(MyPydanticModel)
"""

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


def pydantic_to_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """Convert a Pydantic model to JSON Schema.

    Args:
        model: Pydantic model class

    Returns:
        JSON Schema dict compatible with Zod and Motia
    """
    return model.model_json_schema()


def pydantic_to_zod_schema(model: Type[BaseModel]) -> str:
    """Convert a Pydantic model to a Zod-compatible schema string for TypeScript.

    This generates a string that can be used in TypeScript Motia steps to define
    the bodySchema using z.object().

    Args:
        model: Pydantic model class

    Returns:
        TypeScript code string defining the Zod schema
    """
    schema = model.model_json_schema()
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    zod_fields = []
    for field_name, field_schema in properties.items():
        zod_type = _json_type_to_zod(field_schema, field_name in required)
        description = field_schema.get("description", "")

        if description:
            zod_fields.append(f'    {field_name}: {zod_type}.describe("{description}")')
        else:
            zod_fields.append(f"    {field_name}: {zod_type}")

    return "z.object({\n" + ",\n".join(zod_fields) + "\n})"


def _json_type_to_zod(field_schema: Dict[str, Any], required: bool) -> str:
    """Convert a JSON Schema field to Zod type string."""
    field_type = field_schema.get("type")

    # Handle anyOf (Optional types)
    if "anyOf" in field_schema:
        types = [
            t.get("type") for t in field_schema["anyOf"] if t.get("type") != "null"
        ]
        if types:
            field_type = types[0]
        required = False  # anyOf with null means optional

    # Map JSON Schema types to Zod
    type_map = {
        "string": "z.string()",
        "integer": "z.number().int()",
        "number": "z.number()",
        "boolean": "z.boolean()",
        "array": "z.array(z.any())",
        "object": "z.object({})",
    }

    zod_type = type_map.get(field_type, "z.any()")

    # Check for UUID format
    if (
        field_schema.get("format") == "uuid"
        or "uuid" in field_schema.get("description", "").lower()
    ):
        zod_type = "z.string().uuid()"

    # Make optional if not required
    if not required:
        zod_type += ".optional()"

    return zod_type


def add_motia_fields(
    schema: Dict[str, Any],
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Add standard Motia job fields to a schema.

    Args:
        schema: Base JSON schema dict
        extra_fields: Additional fields to add

    Returns:
        Schema with Motia fields added
    """
    # Clone to avoid mutating original
    result = {
        "type": schema.get("type", "object"),
        "properties": dict(schema.get("properties", {})),
        "required": list(schema.get("required", [])),
    }

    # Add standard Motia fields
    motia_fields = {
        "jobId": {"type": "string", "description": "Unique job identifier"},
        "timestamp": {"type": "string", "description": "Job creation timestamp"},
    }

    if extra_fields:
        motia_fields.update(extra_fields)

    result["properties"].update(motia_fields)
    result["required"].extend(["jobId", "timestamp"])

    return result
