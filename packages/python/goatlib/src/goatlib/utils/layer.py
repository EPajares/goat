"""Layer ID utilities for GOAT services.

Provides shared layer ID normalization and schema lookup
used across geoapi and processes services.
"""

import logging
import re
from typing import Protocol

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class InvalidLayerIdError(ValueError):
    """Raised when a layer ID is invalid."""

    def __init__(
        self: "InvalidLayerIdError", layer_id: str, message: str | None = None
    ) -> None:
        self.layer_id = layer_id
        self.message = message or f"Invalid layer ID: {layer_id}. Expected UUID format."
        super().__init__(self.message)


class LayerNotFoundError(ValueError):
    """Raised when a layer is not found in the catalog."""

    def __init__(self: "LayerNotFoundError", layer_id: str) -> None:
        self.layer_id = layer_id
        super().__init__(f"Layer not found: {layer_id}")


class DuckDBConnection(Protocol):
    """Protocol for DuckDB connection objects."""

    def execute(
        self: "DuckDBConnection", query: str, parameters: list | None = None
    ) -> "DuckDBConnection": ...
    def fetchone(self: "DuckDBConnection") -> tuple | None: ...


class DuckLakeManagerProtocol(Protocol):
    """Protocol for DuckLake manager objects."""

    def connection(self: "DuckLakeManagerProtocol") -> DuckDBConnection: ...
    def reconnect(self: "DuckLakeManagerProtocol") -> None: ...


def normalize_layer_id(layer_id: str) -> str:
    """Normalize layer ID to standard UUID format with hyphens.

    Accepts:
    - 32-char hex: abc123def456...
    - UUID format: abc123de-f456-...

    Args:
        layer_id: Layer ID in any supported format

    Returns:
        Standard UUID format (lowercase, with hyphens)

    Raises:
        InvalidLayerIdError: If layer ID is not a valid UUID format
    """
    # Remove hyphens first to validate
    clean = layer_id.replace("-", "").lower()

    # Validate it's a valid hex string of correct length
    if len(clean) != 32 or not re.match(r"^[a-f0-9]+$", clean):
        raise InvalidLayerIdError(layer_id)

    # Return standard UUID format with hyphens
    return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"


def format_uuid(uuid_str: str) -> str:
    """Format a 32-char hex string as UUID with hyphens.

    Args:
        uuid_str: 32-character hex string or already-formatted UUID

    Returns:
        UUID string with hyphens
    """
    if len(uuid_str) == 32:
        return f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:]}"
    return uuid_str


def layer_id_to_table_name(layer_id: str) -> str:
    """Convert layer ID (with hyphens) to DuckLake table name (no hyphens).

    Args:
        layer_id: Normalized layer ID (UUID format with hyphens)

    Returns:
        Table name in format t_<uuid_without_hyphens>
    """
    return f"t_{layer_id.replace('-', '')}"


# Global schema cache - shared across service instances
# 1 hour TTL, max 10K entries
_schema_cache: TTLCache[str, str] = TTLCache(maxsize=10000, ttl=3600)


def _is_connection_error(error: Exception) -> bool:
    """Check if error is a recoverable connection error."""
    error_msg = str(error).lower()
    return any(
        s in error_msg for s in ["ssl", "eof", "connection", "closed", "unsuccessful"]
    )


def get_schema_for_layer(
    layer_id: str,
    ducklake_manager: DuckLakeManagerProtocol,
    max_retries: int = 1,
) -> str:
    """Get schema name for a layer ID, with caching.

    Queries DuckDB's information_schema for the attached DuckLake catalog.

    Args:
        layer_id: Normalized layer ID (UUID format with hyphens)
        ducklake_manager: DuckLake manager instance for database access
        max_retries: Number of retry attempts on connection error

    Returns:
        Schema name (e.g., 'user_abc123...')

    Raises:
        LayerNotFoundError: If layer not found in catalog
    """
    # Check cache first
    if layer_id in _schema_cache:
        return _schema_cache[layer_id]

    # Query DuckDB catalog for the 'lake' attached database
    table_name = layer_id_to_table_name(layer_id)
    query = (
        "SELECT table_schema FROM information_schema.tables "
        "WHERE table_catalog = 'lake' AND table_name = ?"
    )

    last_error = None
    result = None

    for attempt in range(max_retries + 1):
        try:
            with ducklake_manager.connection() as con:
                result = con.execute(query, [table_name]).fetchone()
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries and _is_connection_error(e):
                logger.warning("DuckLake connection error, reconnecting: %s", e)
                ducklake_manager.reconnect()
            else:
                raise

    if result is None and last_error is not None:
        raise last_error

    if not result:
        raise LayerNotFoundError(layer_id)

    schema_name = result[0]
    _schema_cache[layer_id] = schema_name
    logger.debug("Cached schema for layer %s: %s", layer_id, schema_name)

    return schema_name


def clear_schema_cache() -> None:
    """Clear the schema cache. Useful for testing."""
    _schema_cache.clear()


__all__ = [
    "InvalidLayerIdError",
    "LayerNotFoundError",
    "normalize_layer_id",
    "format_uuid",
    "layer_id_to_table_name",
    "get_schema_for_layer",
    "clear_schema_cache",
]
