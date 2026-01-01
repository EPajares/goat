"""Database operations for Windmill tool outputs.

This module handles all PostgreSQL operations for tool results:
- Creating layer metadata in customer.layer
- Linking layers to projects in customer.layer_project
- Updating project layer_order

These operations are shared across all tools (buffer, clip, join, etc.)
to avoid code duplication in Windmill scripts.
"""

import json
import logging
import uuid as uuid_module
from typing import Any, Self

import asyncpg

from goatlib.tools.style import get_default_style

logger = logging.getLogger(__name__)


def normalize_geometry_type(geom_type: str | None) -> str | None:
    """Normalize DuckDB geometry type to GOAT schema enum value.

    DuckDB ST_GeometryType returns uppercase like 'POINT', 'LINESTRING', 'POLYGON'.
    GOAT schema expects lowercase: 'point', 'line', 'polygon'.

    Args:
        geom_type: Geometry type from DuckDB (e.g., 'POINT', 'MULTIPOLYGON')

    Returns:
        Normalized type ('point', 'line', 'polygon') or None
    """
    if not geom_type:
        return None

    geom_upper = geom_type.upper()

    if "POINT" in geom_upper:
        return "point"
    elif "LINE" in geom_upper or "STRING" in geom_upper:
        return "line"
    elif "POLYGON" in geom_upper:
        return "polygon"

    return None


class ToolDatabaseService:
    """Handles all database operations for tool outputs.

    Usage:
        pool = await asyncpg.create_pool(...)
        db = ToolDatabaseService(pool)

        await db.create_layer(layer_id=..., user_id=..., ...)
        await db.add_to_project(layer_id=..., project_id=..., ...)
    """

    def __init__(self: Self, pool: asyncpg.Pool, schema: str = "customer") -> None:
        """Initialize database service.

        Args:
            pool: asyncpg connection pool
            schema: Database schema name (default: customer)
        """
        self.pool = pool
        self.schema = schema

    async def get_project_folder_id(self: Self, project_id: str) -> str | None:
        """Get the folder_id for a project.

        Args:
            project_id: Project UUID

        Returns:
            folder_id or None if project not found
        """
        row = await self.pool.fetchrow(
            f"SELECT folder_id FROM {self.schema}.project WHERE id = $1",
            uuid_module.UUID(project_id),
        )
        if row:
            return str(row["folder_id"])
        return None

    async def create_layer(
        self: Self,
        layer_id: str,
        user_id: str,
        folder_id: str,
        name: str,
        layer_type: str = "feature",
        feature_layer_type: str | None = "tool",
        geometry_type: str | None = None,
        extent_wkt: str | None = None,
        attribute_mapping: dict[str, Any] | None = None,
        feature_count: int = 0,
        size: int = 0,
        properties: dict[str, Any] | None = None,
        other_properties: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a layer record in customer.layer.

        Args:
            layer_id: UUID for the new layer
            user_id: Owner user UUID
            folder_id: Parent folder UUID
            name: Layer display name
            layer_type: "feature" or "table"
            feature_layer_type: "standard", "tool", "street_network", or None for tables
            geometry_type: "point", "line", "polygon", or None (will be normalized)
            extent_wkt: Spatial extent as WKT string
            attribute_mapping: Column name mapping dict
            feature_count: Number of features
            size: Size of the layer data in bytes
            properties: Layer properties (style, etc.)
            other_properties: Additional properties

        Returns:
            The properties dict used (either provided or generated default)
        """
        # Normalize geometry type (POINT -> point, LINESTRING -> line, etc.)
        normalized_geom = normalize_geometry_type(geometry_type)

        # Generate default style if no properties provided
        if properties is None and normalized_geom:
            properties = get_default_style(normalized_geom)

        # Convert dicts to JSON strings for JSONB columns
        attr_mapping_json = json.dumps(attribute_mapping) if attribute_mapping else None
        properties_json = json.dumps(properties) if properties else None
        other_props_json = json.dumps(other_properties) if other_properties else None

        await self.pool.execute(
            f"""
            INSERT INTO {self.schema}.layer (
                id, user_id, folder_id, name, type, feature_layer_type,
                feature_layer_geometry_type, extent, attribute_mapping,
                size, properties, other_properties, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7,
                CASE WHEN $8::text IS NOT NULL
                    THEN ST_Multi(ST_GeomFromText($8::text, 4326))
                    ELSE NULL
                END,
                $9::jsonb, $10, $11::jsonb, $12::jsonb,
                NOW(), NOW()
            )
            """,
            uuid_module.UUID(layer_id),
            uuid_module.UUID(user_id),
            uuid_module.UUID(folder_id),
            name,
            layer_type,
            feature_layer_type,
            normalized_geom,
            extent_wkt,
            attr_mapping_json,
            size,
            properties_json,
            other_props_json,
        )
        logger.info(
            f"Created layer: {layer_id} ({name}) in folder {folder_id} "
            f"with {feature_count} features, size={size} bytes"
        )
        return properties

    async def add_to_project(
        self: Self,
        layer_id: str,
        project_id: str,
        name: str,
        properties: dict[str, Any] | None = None,
        other_properties: dict[str, Any] | None = None,
    ) -> int:
        """Link a layer to a project.

        Creates a record in customer.layer_project and updates the
        project's layer_order to include the new layer at the top.

        Args:
            layer_id: Layer UUID to link
            project_id: Project UUID to link to
            name: Display name for the layer in this project
            properties: Layer properties for this project context
            other_properties: Additional properties

        Returns:
            layer_project_id: The ID of the created link record
        """
        properties_json = json.dumps(properties) if properties else None
        other_props_json = json.dumps(other_properties) if other_properties else None

        # Create the layer_project link
        # order=0 is required (non-nullable column)
        row = await self.pool.fetchrow(
            f"""
            INSERT INTO {self.schema}.layer_project (
                layer_id, project_id, name, "order", properties, other_properties,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, 0, $4::jsonb, $5::jsonb, NOW(), NOW())
            RETURNING id
            """,
            uuid_module.UUID(layer_id),
            uuid_module.UUID(project_id),
            name,
            properties_json,
            other_props_json,
        )
        layer_project_id = row["id"]

        # Update project.layer_order - prepend the new layer to the list
        await self.pool.execute(
            f"""
            UPDATE {self.schema}.project
            SET layer_order = array_prepend($1, COALESCE(layer_order, ARRAY[]::int[])),
                updated_at = NOW()
            WHERE id = $2
            """,
            layer_project_id,
            uuid_module.UUID(project_id),
        )

        logger.info(
            f"Added layer {layer_id} to project {project_id} "
            f"(layer_project_id={layer_project_id})"
        )
        return layer_project_id

    async def delete_layer(self: Self, layer_id: str) -> None:
        """Delete a layer record from customer.layer.

        Note: This only deletes the metadata. DuckLake data should be
        deleted separately via DuckLakeManager.

        Args:
            layer_id: UUID of the layer to delete
        """
        await self.pool.execute(
            f"DELETE FROM {self.schema}.layer WHERE id = $1",
            uuid_module.UUID(layer_id),
        )
        logger.info(f"Deleted layer: {layer_id}")

    async def update_layer_status(
        self: Self,
        layer_id: str,
        feature_count: int | None = None,
        extent_wkt: str | None = None,
    ) -> None:
        """Update layer metadata after processing.

        Useful for updating feature count and extent after data ingestion.

        Args:
            layer_id: Layer UUID
            feature_count: Updated feature count
            extent_wkt: Updated extent as WKT
        """
        updates = ["updated_at = NOW()"]
        params = [uuid_module.UUID(layer_id)]
        param_idx = 2

        if feature_count is not None:
            updates.append(f"total_count = ${param_idx}")
            params.append(feature_count)
            param_idx += 1

        if extent_wkt is not None:
            updates.append(f"extent = ST_Multi(ST_GeomFromText(${param_idx}, 4326))")
            params.append(extent_wkt)
            param_idx += 1

        await self.pool.execute(
            f"""
            UPDATE {self.schema}.layer
            SET {', '.join(updates)}
            WHERE id = $1
            """,
            *params,
        )
        logger.info(f"Updated layer status: {layer_id}")
