"""LayerDelete Tool - Delete layers from DuckLake and PostgreSQL.

This tool handles deletion of layers, removing both:
1. DuckLake table data (for feature/table layers)
2. PostgreSQL metadata (layer record and project links)

Usage:
    from goatlib.tools.layer_delete import LayerDeleteParams, main

    result = main(LayerDeleteParams(
        user_id="...",
        layer_id="...",
    ))
"""

import asyncio
import logging
from typing import Self

from pydantic import ConfigDict, Field

from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    ui_field,
    ui_sections,
)
from goatlib.tools.base import SimpleToolRunner
from goatlib.tools.schemas import ToolInputBase, ToolOutputBase

logger = logging.getLogger(__name__)


class LayerDeleteParams(ToolInputBase):
    """Parameters for LayerDelete tool."""

    model_config = ConfigDict(json_schema_extra=ui_sections(SECTION_INPUT))

    layer_id: str = Field(
        ...,
        description="ID of the layer to delete",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            widget="layer-selector",
        ),
    )
    # user_id inherited from ToolInputBase
    # project_id, folder_id, output_name not used for delete


class LayerDeleteOutput(ToolOutputBase):
    """Output schema for LayerDelete tool."""

    layer_id: str
    deleted: bool = False
    ducklake_deleted: bool = False
    metadata_deleted: bool = False
    error: str | None = None


class LayerDeleteRunner(SimpleToolRunner):
    """Runner for LayerDelete tool.

    Extends SimpleToolRunner for shared infrastructure (DuckDB, settings, logging).
    """

    def _delete_ducklake_table(self: Self, user_id: str, layer_id: str) -> bool:
        """Delete DuckLake table for a layer.

        Args:
            user_id: User UUID
            layer_id: Layer UUID

        Returns:
            True if table was deleted, False if it didn't exist
        """
        user_schema = f"user_{user_id.replace('-', '')}"
        table_name = f"t_{layer_id.replace('-', '')}"
        full_table = f"lake.{user_schema}.{table_name}"

        try:
            # Check if table exists
            result = self.duckdb_con.execute(f"""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_catalog = 'lake'
                AND table_schema = '{user_schema}'
                AND table_name = '{table_name}'
            """).fetchone()

            if result and result[0] > 0:
                self.duckdb_con.execute(f"DROP TABLE IF EXISTS {full_table}")
                logger.info("Deleted DuckLake table: %s", full_table)
                return True
            else:
                logger.info("DuckLake table not found: %s", full_table)
                return False
        except Exception as e:
            logger.warning("Error deleting DuckLake table %s: %s", full_table, e)
            return False

    async def _delete_postgres_layer(self: Self, layer_id: str) -> bool:
        """Delete layer record from PostgreSQL.

        This cascades to delete layer_project links as well.

        Args:
            layer_id: Layer UUID

        Returns:
            True if deleted, False if not found
        """
        pool = await self.get_postgres_pool()

        try:
            import uuid as uuid_module

            # Check if layer exists
            row = await pool.fetchrow(
                f"SELECT id FROM {self.settings.customer_schema}.layer WHERE id = $1",
                uuid_module.UUID(layer_id),
            )

            if not row:
                logger.info("Layer not found in PostgreSQL: %s", layer_id)
                return False

            # Delete layer (cascade deletes layer_project links)
            await pool.execute(
                f"DELETE FROM {self.settings.customer_schema}.layer WHERE id = $1",
                uuid_module.UUID(layer_id),
            )
            logger.info("Deleted layer from PostgreSQL: %s", layer_id)
            return True
        finally:
            await pool.close()

    def run(self: Self, params: LayerDeleteParams) -> dict:
        """Run the layer deletion.

        Args:
            params: Delete parameters

        Returns:
            LayerDeleteOutput as dict
        """
        if self.settings is None:
            raise RuntimeError("Settings not initialized. Call init_from_env() first.")

        logger.info(
            "Starting layer deletion: user=%s, layer=%s",
            params.user_id,
            params.layer_id,
        )

        output = LayerDeleteOutput(
            layer_id=params.layer_id,
            name="",
            folder_id="",
            user_id=params.user_id,
        )

        try:
            # Step 1: Delete DuckLake table
            output.ducklake_deleted = self._delete_ducklake_table(
                user_id=params.user_id,
                layer_id=params.layer_id,
            )

            # Step 2: Delete PostgreSQL metadata
            output.metadata_deleted = asyncio.get_event_loop().run_until_complete(
                self._delete_postgres_layer(params.layer_id)
            )

            output.deleted = output.metadata_deleted
            logger.info(
                "Layer deletion complete: layer=%s, ducklake=%s, metadata=%s",
                params.layer_id,
                output.ducklake_deleted,
                output.metadata_deleted,
            )

        except Exception as e:
            output.error = str(e)
            logger.error("Layer deletion failed: %s", e)

        finally:
            self.cleanup()

        return output.model_dump()


def main(params: LayerDeleteParams) -> dict:
    """Windmill entry point for LayerDelete.

    Args:
        params: Validated LayerDeleteParams

    Returns:
        LayerDeleteOutput as dict
    """
    runner = LayerDeleteRunner()
    runner.init_from_env()
    return runner.run(params)
