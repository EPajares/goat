"""Integration tests for LayerDelete tool.

Tests actual layer deletion with DuckLake and PostgreSQL:
- Delete DuckLake table
- Delete PostgreSQL metadata
- Delete PMTiles
- Verify ownership enforcement

Note: These tests require running Docker containers (PostgreSQL, MinIO).
"""

import asyncio
from pathlib import Path
from typing import Any

import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.layer_delete import LayerDeleteParams, LayerDeleteRunner

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def delete_runner(tool_settings: ToolSettings) -> LayerDeleteRunner:
    """Create LayerDeleteRunner instance."""
    runner = LayerDeleteRunner()
    runner.init(tool_settings)
    return runner


# ============================================================================
# DuckLake Deletion Tests
# ============================================================================

class TestLayerDeleteDuckLake:
    """Test DuckLake table deletion."""

    def test_deletes_ducklake_table(
        self,
        delete_runner: LayerDeleteRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        ducklake_connection,
        vector_data_dir: Path,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
    ):
        """Test that deletion removes the DuckLake table."""
        # Setup: Create a layer in DuckLake and metadata in PostgreSQL
        layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_points.parquet",
        )
        asyncio.get_event_loop().run_until_complete(
            create_test_layer_metadata(
                layer_id=layer_id,
                name="Test Layer",
                geometry_type="point",
            )
        )

        # Verify table exists before deletion
        user_schema = f"user_{test_user['id'].replace('-', '')}"
        table_name = f"t_{layer_id.replace('-', '')}"
        result = ducklake_connection.execute(f"""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_catalog = 'lake'
            AND table_schema = '{user_schema}'
            AND table_name = '{table_name}'
        """).fetchone()
        assert result[0] == 1, "Table should exist before deletion"

        # Run deletion
        params = LayerDeleteParams(
            user_id=test_user["id"],
            layer_id=layer_id,
        )
        result = delete_runner.run(params)

        # Verify
        assert result["deleted"] is True
        assert result["ducklake_deleted"] is True

        # Verify table no longer exists
        result = ducklake_connection.execute(f"""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_catalog = 'lake'
            AND table_schema = '{user_schema}'
            AND table_name = '{table_name}'
        """).fetchone()
        assert result[0] == 0, "Table should be deleted"

    def test_handles_missing_ducklake_table(
        self,
        delete_runner: LayerDeleteRunner,
        create_test_layer_metadata,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
    ):
        """Test deletion when DuckLake table doesn't exist (metadata only)."""
        import uuid

        # Create only metadata, no DuckLake table
        layer_id = str(uuid.uuid4())
        asyncio.get_event_loop().run_until_complete(
            create_test_layer_metadata(
                layer_id=layer_id,
                name="Metadata Only Layer",
                geometry_type="point",
            )
        )

        # Run deletion
        params = LayerDeleteParams(
            user_id=test_user["id"],
            layer_id=layer_id,
        )
        result = delete_runner.run(params)

        # Should still succeed for metadata deletion
        assert result["deleted"] is True
        assert result["metadata_deleted"] is True
        assert result["ducklake_deleted"] is False


# ============================================================================
# PostgreSQL Metadata Deletion Tests
# ============================================================================

class TestLayerDeleteMetadata:
    """Test PostgreSQL metadata deletion."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_deletes_postgresql_metadata(
        self,
        delete_runner: LayerDeleteRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        postgres_pool,
        vector_data_dir: Path,
        test_user: dict[str, Any],
        tool_settings: ToolSettings,
    ):
        """Test that deletion removes PostgreSQL layer record."""
        import uuid as uuid_module

        # Setup
        layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_points.parquet",
        )
        await create_test_layer_metadata(
            layer_id=layer_id,
            name="Test Layer",
            geometry_type="point",
        )

        # Verify metadata exists before deletion
        row = await postgres_pool.fetchrow(
            f"SELECT id FROM {tool_settings.customer_schema}.layer WHERE id = $1",
            uuid_module.UUID(layer_id),
        )
        assert row is not None, "Layer metadata should exist before deletion"

        # Run deletion (synchronously)
        params = LayerDeleteParams(
            user_id=test_user["id"],
            layer_id=layer_id,
        )
        result = await asyncio.to_thread(delete_runner.run, params)

        # Verify
        assert result["deleted"] is True
        assert result["metadata_deleted"] is True

        # Verify metadata no longer exists
        row = await postgres_pool.fetchrow(
            f"SELECT id FROM {tool_settings.customer_schema}.layer WHERE id = $1",
            uuid_module.UUID(layer_id),
        )
        assert row is None, "Layer metadata should be deleted"


# ============================================================================
# Ownership Enforcement Tests
# ============================================================================

class TestLayerDeleteOwnership:
    """Test ownership enforcement during deletion."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_rejects_deletion_by_non_owner(
        self,
        delete_runner: LayerDeleteRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        vector_data_dir: Path,
        test_user: dict[str, Any],
    ):
        """Test that non-owner cannot delete a layer."""
        import uuid

        # Setup: Create layer owned by test_user
        layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_points.parquet",
        )
        await create_test_layer_metadata(
            layer_id=layer_id,
            name="Test Layer",
            geometry_type="point",
        )

        # Try to delete with a different user ID
        other_user_id = str(uuid.uuid4())
        params = LayerDeleteParams(
            user_id=other_user_id,
            layer_id=layer_id,
        )
        result = await asyncio.to_thread(delete_runner.run, params)

        # Should fail with permission error
        assert result["deleted"] is False
        assert result["error"] is not None
        assert "cannot delete" in result["error"].lower()

    def test_allows_deletion_by_owner(
        self,
        delete_runner: LayerDeleteRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        vector_data_dir: Path,
        test_user: dict[str, Any],
    ):
        """Test that owner can delete their own layer."""
        # Setup
        layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_points.parquet",
        )
        asyncio.get_event_loop().run_until_complete(
            create_test_layer_metadata(
                layer_id=layer_id,
                name="Test Layer",
                geometry_type="point",
            )
        )

        # Delete with owner's user ID
        params = LayerDeleteParams(
            user_id=test_user["id"],
            layer_id=layer_id,
        )
        result = delete_runner.run(params)

        # Should succeed
        assert result["deleted"] is True
        assert result["error"] is None


# ============================================================================
# Non-Existent Layer Tests
# ============================================================================

class TestLayerDeleteNonExistent:
    """Test deletion of non-existent layers."""

    def test_handles_nonexistent_layer(
        self,
        delete_runner: LayerDeleteRunner,
        test_user: dict[str, Any],
    ):
        """Test deletion of a layer that doesn't exist."""
        import uuid

        # Try to delete non-existent layer
        params = LayerDeleteParams(
            user_id=test_user["id"],
            layer_id=str(uuid.uuid4()),
        )
        result = delete_runner.run(params)

        # Should report not deleted (not an error, just not found)
        assert result["deleted"] is False
        assert result["metadata_deleted"] is False
        assert result["ducklake_deleted"] is False
