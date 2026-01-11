"""LayerDeleteMulti Tool - Delete multiple layers from DuckLake.

This tool handles bulk deletion of layers, removing DuckLake table data.
Unlike layer_delete, this does NOT delete PostgreSQL metadata (that should
already be handled by the caller via CASCADE delete).

Usage:
    from goatlib.tools.layer_delete_multi import LayerDeleteMultiParams, main

    result = main(LayerDeleteMultiParams(
        user_id="...",
        layer_ids=["layer-uuid-1", "layer-uuid-2"],
    ))
"""

import logging
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    ui_field,
    ui_sections,
)
from goatlib.tools.base import SimpleToolRunner
from goatlib.tools.schemas import ToolInputBase

logger = logging.getLogger(__name__)


class LayerDeleteMultiParams(ToolInputBase):
    """Parameters for LayerDeleteMulti tool."""

    model_config = ConfigDict(json_schema_extra=ui_sections(SECTION_INPUT))

    layer_ids: list[str] = Field(
        ...,
        description="List of layer IDs to delete",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
        ),
    )
    # user_id inherited from ToolInputBase


class LayerDeleteResult(BaseModel):
    """Result for a single layer deletion."""

    layer_id: str
    deleted: bool = False
    error: str | None = None


class LayerDeleteMultiOutput(BaseModel):
    """Output schema for LayerDeleteMulti tool.

    Note: Does not inherit from ToolOutputBase since this tool
    doesn't create layers - it deletes them.
    """

    total: int = 0
    deleted_count: int = 0
    failed_count: int = 0
    results: list[LayerDeleteResult] = Field(default_factory=list)
    error: str | None = None


class LayerDeleteMultiRunner(SimpleToolRunner):
    """Runner for LayerDeleteMulti tool.

    Extends SimpleToolRunner for shared infrastructure (DuckDB, settings, logging).
    """

    def _delete_ducklake_table(self: Self, layer_id: str, owner_id: str) -> bool:
        """Delete DuckLake table for a layer.

        Args:
            layer_id: Layer UUID
            owner_id: Layer owner's UUID

        Returns:
            True if table was deleted, False if it didn't exist or error
        """
        user_schema = f"user_{owner_id.replace('-', '')}"
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

    def run(self: Self, params: LayerDeleteMultiParams) -> dict:
        """Run the multi-layer deletion.

        Args:
            params: Delete parameters with list of layer IDs

        Returns:
            LayerDeleteMultiOutput as dict
        """
        if self.settings is None:
            raise RuntimeError("Settings not initialized. Call init_from_env() first.")

        logger.info(
            "Starting multi-layer deletion: user=%s, layers=%d",
            params.user_id,
            len(params.layer_ids),
        )

        output = LayerDeleteMultiOutput(
            total=len(params.layer_ids),
        )

        try:
            for layer_id in params.layer_ids:
                result = LayerDeleteResult(
                    layer_id=layer_id,
                )

                try:
                    # Delete DuckLake table
                    # Note: PostgreSQL metadata is already deleted via CASCADE
                    # when the folder was deleted, so we just need user_id for
                    # the DuckLake schema path
                    deleted = self._delete_ducklake_table(
                        layer_id=layer_id,
                        owner_id=params.user_id,
                    )
                    result.deleted = deleted
                    if deleted:
                        output.deleted_count += 1
                    else:
                        # Table didn't exist, but that's not an error
                        # (might be external layer or already deleted)
                        output.deleted_count += 1

                except Exception as e:
                    result.error = str(e)
                    output.failed_count += 1
                    logger.warning("Failed to delete layer %s: %s", layer_id, e)

                output.results.append(result)

            logger.info(
                "Multi-layer deletion complete: total=%d, deleted=%d, failed=%d",
                output.total,
                output.deleted_count,
                output.failed_count,
            )

        except Exception as e:
            output.error = str(e)
            logger.error("Multi-layer deletion failed: %s", e)
            raise

        finally:
            self.cleanup()

        return output.model_dump()


def main(params: LayerDeleteMultiParams) -> dict:
    """Windmill entry point for LayerDeleteMulti.

    Args:
        params: Validated LayerDeleteMultiParams

    Returns:
        LayerDeleteMultiOutput as dict
    """
    runner = LayerDeleteMultiRunner()
    runner.init_from_env()
    return runner.run(params)
