"""Dependencies for Processes API."""

import logging

from fastapi import HTTPException
from goatlib.utils.layer import (
    InvalidLayerIdError,
    LayerNotFoundError,
    layer_id_to_table_name,
)
from goatlib.utils.layer import (
    get_schema_for_layer as _goatlib_get_schema_for_layer,
)
from goatlib.utils.layer import (
    normalize_layer_id as _goatlib_normalize_layer_id,
)

from processes.ducklake import ducklake_manager

logger = logging.getLogger(__name__)


def normalize_layer_id(layer_id: str) -> str:
    """Normalize layer ID to standard UUID format with hyphens.

    Accepts:
    - 32-char hex: abc123def456...
    - UUID format: abc123de-f456-...

    Returns:
        Standard UUID format (lowercase, with hyphens)

    Raises:
        HTTPException: If layer ID is invalid
    """
    try:
        return _goatlib_normalize_layer_id(layer_id)
    except InvalidLayerIdError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid collection ID: {e.layer_id}. Expected UUID format.",
        )


# Alias for backward compatibility
_layer_id_to_table_name = layer_id_to_table_name


def get_schema_for_layer(layer_id: str) -> str:
    """Get schema name for a layer ID, with caching.

    Queries DuckDB's information_schema for the attached DuckLake catalog.

    Args:
        layer_id: Normalized layer ID (UUID format with hyphens)

    Returns:
        Schema name (e.g., 'user_abc123...')

    Raises:
        HTTPException: If layer not found
    """
    try:
        return _goatlib_get_schema_for_layer(layer_id, ducklake_manager)
    except LayerNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Layer not found: {layer_id}",
        )
