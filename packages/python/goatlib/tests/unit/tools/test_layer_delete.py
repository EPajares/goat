"""Unit tests for LayerDelete tool.

Tests the layer deletion functionality including:
- Parameter validation
- Ownership verification
- DuckLake table deletion
- PostgreSQL metadata deletion
- PMTiles deletion
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

from goatlib.tools.layer_delete import (
    LayerDeleteOutput,
    LayerDeleteParams,
    LayerDeleteRunner,
)


class TestLayerDeleteParams:
    """Test parameter validation."""

    def test_valid_params(self):
        """Valid params with layer_id."""
        params = LayerDeleteParams(
            user_id="00000000-0000-0000-0000-000000000001",
            layer_id="00000000-0000-0000-0000-000000000002",
        )
        assert params.layer_id == "00000000-0000-0000-0000-000000000002"
        assert params.user_id == "00000000-0000-0000-0000-000000000001"

    def test_layer_id_required(self):
        """layer_id is required."""
        with pytest.raises(ValueError):
            LayerDeleteParams(
                user_id="00000000-0000-0000-0000-000000000001",
            )

    def test_user_id_required(self):
        """user_id is required."""
        with pytest.raises(ValueError):
            LayerDeleteParams(
                layer_id="00000000-0000-0000-0000-000000000002",
            )

    def test_optional_fields(self):
        """Optional fields from ToolInputBase."""
        params = LayerDeleteParams(
            user_id="00000000-0000-0000-0000-000000000001",
            layer_id="00000000-0000-0000-0000-000000000002",
            triggered_by_email="test@example.com",
        )
        assert params.triggered_by_email == "test@example.com"


class TestLayerDeleteOutput:
    """Test output schema."""

    def test_successful_output(self):
        """Test successful deletion output."""
        output = LayerDeleteOutput(
            layer_id="00000000-0000-0000-0000-000000000002",
            user_id="00000000-0000-0000-0000-000000000001",
            folder_id="00000000-0000-0000-0000-000000000003",
            name="",
            deleted=True,
            ducklake_deleted=True,
            metadata_deleted=True,
        )
        assert output.deleted is True
        assert output.ducklake_deleted is True
        assert output.metadata_deleted is True
        assert output.error is None

    def test_partial_deletion_output(self):
        """Test partial deletion (metadata only, no DuckLake table)."""
        output = LayerDeleteOutput(
            layer_id="00000000-0000-0000-0000-000000000002",
            user_id="00000000-0000-0000-0000-000000000001",
            folder_id="",
            name="",
            deleted=True,
            ducklake_deleted=False,
            metadata_deleted=True,
        )
        assert output.deleted is True
        assert output.ducklake_deleted is False

    def test_error_output(self):
        """Test error output."""
        output = LayerDeleteOutput(
            layer_id="00000000-0000-0000-0000-000000000002",
            user_id="00000000-0000-0000-0000-000000000001",
            folder_id="",
            name="",
            deleted=False,
            error="Permission denied",
        )
        assert output.deleted is False
        assert output.error == "Permission denied"


class TestLayerDeleteRunner:
    """Test the runner logic with mocks."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.customer_schema = "customer"
        settings.tiles_data_dir = "/app/data/tiles"
        settings.postgres_server = "localhost"
        settings.postgres_port = 5432
        settings.postgres_user = "test"
        settings.postgres_password = "test"
        settings.postgres_db = "test"
        settings.ducklake_postgres_uri = "postgresql://localhost/test"
        settings.ducklake_catalog_schema = "ducklake"
        settings.ducklake_data_dir = "/tmp/ducklake"
        return settings

    @pytest.fixture
    def runner(self, mock_settings):
        """Create runner with mocked settings."""
        runner = LayerDeleteRunner()
        runner.settings = mock_settings
        runner._duckdb_con = MagicMock()
        return runner

    def test_delete_ducklake_table_exists(self, runner):
        """Test DuckLake table deletion when table exists."""
        # Mock table exists check
        runner._duckdb_con.execute.return_value.fetchone.return_value = (1,)

        result = runner._delete_ducklake_table(
            layer_id="00000000-0000-0000-0000-000000000002",
            owner_id="00000000-0000-0000-0000-000000000001",
        )

        assert result is True
        # Verify DROP TABLE was called
        calls = [str(c) for c in runner._duckdb_con.execute.call_args_list]
        assert any("DROP TABLE" in str(c) for c in calls)

    def test_delete_ducklake_table_not_exists(self, runner):
        """Test DuckLake table deletion when table doesn't exist."""
        # Mock table doesn't exist
        runner._duckdb_con.execute.return_value.fetchone.return_value = (0,)

        result = runner._delete_ducklake_table(
            layer_id="00000000-0000-0000-0000-000000000002",
            owner_id="00000000-0000-0000-0000-000000000001",
        )

        assert result is False

    def test_delete_ducklake_table_error(self, runner):
        """Test DuckLake table deletion with error."""
        runner._duckdb_con.execute.side_effect = Exception("DuckDB error")

        result = runner._delete_ducklake_table(
            layer_id="00000000-0000-0000-0000-000000000002",
            owner_id="00000000-0000-0000-0000-000000000001",
        )

        assert result is False

    def test_table_path_construction(self, runner):
        """Test correct table path is constructed."""
        runner._duckdb_con.execute.return_value.fetchone.return_value = (1,)

        runner._delete_ducklake_table(
            layer_id="00000000-0000-0000-0000-000000000002",
            owner_id="00000000-0000-0000-0000-000000000001",
        )

        # Check the SQL contains correct schema/table names
        calls = runner._duckdb_con.execute.call_args_list
        # First call is table existence check
        first_call_sql = str(calls[0])
        assert "user_00000000000000000000000000000001" in first_call_sql
        assert "t_00000000000000000000000000000002" in first_call_sql


class TestLayerDeleteOwnership:
    """Test ownership verification logic."""

    @pytest.fixture
    def runner(self):
        """Create runner with mocked components."""
        runner = LayerDeleteRunner()
        runner.settings = MagicMock()
        runner.settings.customer_schema = "customer"
        return runner

    @pytest.mark.asyncio
    async def test_verify_ownership_layer_not_found(self, runner):
        """Test deletion when layer doesn't exist."""
        mock_pool = AsyncMock()
        mock_pool.fetchrow.return_value = None
        mock_pool.close = AsyncMock()

        with patch.object(runner, "get_postgres_pool", return_value=mock_pool):
            deleted, owner_id = await runner._verify_ownership_and_delete(
                layer_id="00000000-0000-0000-0000-000000000002",
                user_id="00000000-0000-0000-0000-000000000001",
            )

        assert deleted is False
        assert owner_id is None

    @pytest.mark.asyncio
    async def test_verify_ownership_not_owner(self, runner):
        """Test deletion denied when user doesn't own layer."""
        mock_pool = AsyncMock()
        mock_pool.fetchrow.return_value = {
            "id": "00000000-0000-0000-0000-000000000002",
            "user_id": "00000000-0000-0000-0000-000000000099",  # Different owner
        }
        mock_pool.close = AsyncMock()

        with patch.object(runner, "get_postgres_pool", return_value=mock_pool):
            with pytest.raises(PermissionError) as exc_info:
                await runner._verify_ownership_and_delete(
                    layer_id="00000000-0000-0000-0000-000000000002",
                    user_id="00000000-0000-0000-0000-000000000001",
                )

        assert "cannot delete layer" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_ownership_success(self, runner):
        """Test successful ownership verification and deletion."""
        import uuid

        mock_pool = AsyncMock()
        mock_pool.fetchrow.return_value = {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
            "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        }
        mock_pool.execute = AsyncMock()
        mock_pool.close = AsyncMock()

        with patch.object(runner, "get_postgres_pool", return_value=mock_pool):
            deleted, owner_id = await runner._verify_ownership_and_delete(
                layer_id="00000000-0000-0000-0000-000000000002",
                user_id="00000000-0000-0000-0000-000000000001",
            )

        assert deleted is True
        assert owner_id == "00000000-0000-0000-0000-000000000001"
        # Verify DELETE was called
        mock_pool.execute.assert_called_once()


class TestLayerDeletePMTiles:
    """Test PMTiles deletion."""

    @pytest.fixture
    def runner(self):
        """Create runner with mocked settings."""
        runner = LayerDeleteRunner()
        runner.settings = MagicMock()
        runner.settings.tiles_data_dir = "/app/data/tiles"
        return runner

    def test_delete_pmtiles_success(self, runner):
        """Test PMTiles deletion success."""
        with patch("goatlib.io.pmtiles.PMTilesGenerator") as MockGen:
            mock_generator = MockGen.return_value
            mock_generator.delete_pmtiles.return_value = True

            result = runner._delete_pmtiles(
                layer_id="00000000-0000-0000-0000-000000000002",
                owner_id="00000000-0000-0000-0000-000000000001",
            )

        assert result is True

    def test_delete_pmtiles_not_exists(self, runner):
        """Test PMTiles deletion when file doesn't exist."""
        with patch("goatlib.io.pmtiles.PMTilesGenerator") as MockGen:
            mock_generator = MockGen.return_value
            mock_generator.delete_pmtiles.return_value = False

            result = runner._delete_pmtiles(
                layer_id="00000000-0000-0000-0000-000000000002",
                owner_id="00000000-0000-0000-0000-000000000001",
            )

        assert result is False

    def test_delete_pmtiles_error(self, runner):
        """Test PMTiles deletion with error."""
        with patch("goatlib.io.pmtiles.PMTilesGenerator") as MockGen:
            MockGen.side_effect = Exception("PMTiles error")

            result = runner._delete_pmtiles(
                layer_id="00000000-0000-0000-0000-000000000002",
                owner_id="00000000-0000-0000-0000-000000000001",
            )

        assert result is False


class TestLayerDeleteRun:
    """Test the main run method."""

    @pytest.fixture
    def runner(self):
        """Create runner with mocked components."""
        runner = LayerDeleteRunner()
        runner.settings = MagicMock()
        runner.settings.customer_schema = "customer"
        runner.settings.tiles_data_dir = "/app/data/tiles"
        runner._duckdb_con = MagicMock()
        runner.cleanup = MagicMock()
        return runner

    def test_run_full_deletion(self, runner):
        """Test full deletion flow."""
        # Mock DuckLake deletion
        runner._delete_ducklake_table = MagicMock(return_value=True)

        # Mock PMTiles deletion
        runner._delete_pmtiles = MagicMock(return_value=True)

        # Mock ownership verification to return success tuple
        with patch.object(
            runner,
            "_verify_ownership_and_delete",
            new_callable=AsyncMock,
            return_value=(True, "00000000-0000-0000-0000-000000000001")
        ):
            params = LayerDeleteParams(
                user_id="00000000-0000-0000-0000-000000000001",
                layer_id="00000000-0000-0000-0000-000000000002",
            )

            result = runner.run(params)

        assert result["deleted"] is True
        assert result["ducklake_deleted"] is True
        assert result["metadata_deleted"] is True
        assert result["error"] is None

    def test_run_permission_denied(self, runner):
        """Test deletion with permission denied."""
        # Mock ownership verification to raise PermissionError
        with patch.object(
            runner,
            "_verify_ownership_and_delete",
            new_callable=AsyncMock,
            side_effect=PermissionError("User cannot delete this layer")
        ):
            params = LayerDeleteParams(
                user_id="00000000-0000-0000-0000-000000000001",
                layer_id="00000000-0000-0000-0000-000000000002",
            )

            result = runner.run(params)

        assert result["deleted"] is False
        assert "cannot delete" in result["error"]

    def test_run_no_settings(self, runner):
        """Test run without settings raises error."""
        runner.settings = None

        params = LayerDeleteParams(
            user_id="00000000-0000-0000-0000-000000000001",
            layer_id="00000000-0000-0000-0000-000000000002",
        )

        with pytest.raises(RuntimeError, match="Settings not initialized"):
            runner.run(params)
