"""Code generation utilities for Windmill scripts.

Converts Pydantic models to Windmill-compatible function signatures.
Windmill parses function signatures statically and only understands primitive types.
"""

from enum import Enum
from pathlib import Path
from typing import Literal, Union

import tomllib


def _get_goatlib_dependencies() -> list[str]:
    """Read dependencies from goatlib's pyproject.toml."""
    # Find pyproject.toml relative to this file
    codegen_path = Path(__file__).resolve()
    # Go up: codegen.py -> tools -> goatlib -> src -> goatlib -> pyproject.toml
    pyproject_path = codegen_path.parent.parent.parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        # Fallback to hardcoded if pyproject.toml not found
        return [
            "asyncpg>=0.29.0",
            "boto3>=1.35.0",
            "duckdb>=1.4.3",
            "pydantic>=2.11.5",
            "pydantic-settings>=2.9.1",
            "pygeofilter>=0.2.4",
            "pyproj>=3.6.0",
            "pytz>=2024.1",
            "wmill>=1.0.0",
        ]

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    return pyproject.get("project", {}).get("dependencies", [])


def _build_requirements_comment() -> str:
    """Build the requirements comment for Windmill scripts."""
    deps = _get_goatlib_dependencies()
    all_deps = sorted(set(deps))
    lines = ["# requirements:"] + [f"# {dep}" for dep in all_deps]
    return "\n".join(lines)


def _is_pydantic_model(annotation: type) -> bool:
    """Check if a type is a Pydantic BaseModel."""
    try:
        from pydantic import BaseModel

        return isinstance(annotation, type) and issubclass(annotation, BaseModel)
    except (TypeError, ImportError):
        return False


def _is_enum(annotation: type) -> bool:
    """Check if a type is an Enum."""
    try:
        return isinstance(annotation, type) and issubclass(annotation, Enum)
    except TypeError:
        return False


def python_type_to_str(annotation: type) -> str:
    """Convert a Python type annotation to a string for code generation.

    Windmill only understands primitive types, so we convert:
    - Pydantic models -> dict
    - Enums/StrEnums -> str
    - list[Model] -> list[dict]
    """
    import types
    from typing import get_args, get_origin

    if annotation is type(None):
        return "None"

    # Handle Pydantic models as dict
    if _is_pydantic_model(annotation):
        return "dict"

    # Handle Enums as str (their values are strings)
    if _is_enum(annotation):
        return "str"

    origin = get_origin(annotation)

    if origin is types.UnionType or origin is Union:
        args = get_args(annotation)
        # Handle Optional (Union with None)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return f"{python_type_to_str(non_none[0])} | None"
        return " | ".join(python_type_to_str(a) for a in args)

    if origin is list:
        args = get_args(annotation)
        if args:
            inner_type = python_type_to_str(args[0])
            return f"list[{inner_type}]"
        return "list"

    if origin is dict:
        return "dict"

    if origin is Literal:
        args = get_args(annotation)
        return f"Literal[{', '.join(repr(a) for a in args)}]"

    if hasattr(annotation, "__name__"):
        return annotation.__name__

    return str(annotation)


def _format_default_value(value: object) -> str:
    """Format a default value for code generation.

    Handles enums specially to use their .value instead of repr().
    Also handles lists that may contain enums.
    """
    if isinstance(value, Enum):
        # Use the enum's value (e.g., "gaussian" instead of <ImpedanceFunction.gaussian>)
        return repr(value.value)
    if isinstance(value, list):
        # Handle lists that may contain enums
        formatted_items = [_format_default_value(item) for item in value]
        return f"[{', '.join(formatted_items)}]"
    return repr(value)


def generate_windmill_script(
    module_path: str,
    params_class: type,
    excluded_fields: set[str] | None = None,
) -> str:
    """Generate a Windmill script from a Pydantic params class.

    Windmill parses function signatures to build the JSON Schema for inputs.
    It only understands primitive types (str, int, float, bool, list, Literal, etc),
    NOT Pydantic models. So we introspect the Pydantic model fields and generate
    a function with individual typed arguments.

    Args:
        module_path: Import path for the module (e.g., "goatlib.tools.buffer")
        params_class: Pydantic model class with tool parameters
        excluded_fields: Field names to skip (internal fields not exposed to users)

    Returns:
        Generated Python script content for Windmill
    """
    from pydantic_core import PydanticUndefined

    if excluded_fields is None:
        excluded_fields = {"input_path", "output_path", "overlay_path", "output_crs"}

    # Get fields from Pydantic model
    fields = params_class.model_fields

    # Track if we need Literal import
    needs_literal = False

    # Build function signature - required args first, then optional
    required_args = []
    optional_args = []

    for name, field_info in fields.items():
        # Skip internal fields that aren't user-facing
        if name in excluded_fields:
            continue

        # Get type annotation
        annotation = field_info.annotation
        type_str = python_type_to_str(annotation)

        if "Literal" in type_str:
            needs_literal = True

        # Check if required or has default
        if field_info.is_required():
            required_args.append(f"{name}: {type_str}")
        elif (
            field_info.default is not None
            and field_info.default is not PydanticUndefined
        ):
            default_val = _format_default_value(field_info.default)
            optional_args.append(f"{name}: {type_str} = {default_val}")
        else:
            optional_args.append(f"{name}: {type_str} = None")

    # Required args first, then optional
    all_args = required_args + optional_args
    args_str = ",\n    ".join(all_args)
    params_class_name = params_class.__name__

    # Build imports
    imports = ["import sys"]
    if needs_literal:
        imports.append("from typing import Literal")

    imports_str = "\n".join(imports)

    requirements = _build_requirements_comment()

    script = f'''{requirements}

{imports_str}
sys.path.insert(0, "/app/workspace/packages/python/goatlib/src")


def main(
    {args_str}
) -> dict:
    """Run tool."""
    from {module_path} import {params_class_name}, main as _main

    params = {params_class_name}(**{{k: v for k, v in locals().items() if v is not None}})
    return _main(params)
'''
    return script
