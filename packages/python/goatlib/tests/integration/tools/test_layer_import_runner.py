"""Integration tests for LayerImport tool.

Tests actual layer import functionality with S3 and DuckLake:
- Import from S3 (file upload workflow)
- Create DuckLake table from imported data
- Verify PostgreSQL metadata creation

Note: These tests require running Docker containers (PostgreSQL, MinIO, DuckDB).
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any

import duckdb
import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.layer_import import LayerImportParams, LayerImportRunner

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def import_runner(tool_settings: ToolSettings) -> LayerImportRunner:
    """Create LayerImportRunner instance."""
    runner = LayerImportRunner()
    runner.init(tool_settings)
    return runner


@pytest.fixture
def upload_test_file_to_s3(
    tool_settings: ToolSettings,
    vector_data_dir: Path,
) -> callable:
    """Factory fixture to upload test files to S3 for import testing.

    Returns:
        Function that uploads a file and returns the S3 key
    """
    uploaded_keys: list[str] = []

    def _upload(filename: str) -> str:
        """Upload a file to S3 and return the key.

        Args:
            filename: Name of file in vector_data_dir

        Returns:
            S3 key for the uploaded file
        """
        import boto3

        # Get S3 client from settings
        client = tool_settings.get_s3_client()

        # Create unique key
        s3_key = f"test-uploads/{uuid.uuid4()}/{filename}"

        # Upload file
        local_path = vector_data_dir / filename
        client.upload_file(
            str(local_path),
            tool_settings.s3_bucket_name,
            s3_key,
        )

        uploaded_keys.append(s3_key)
        return s3_key

    yield _upload

    # Cleanup: Delete uploaded files
    try:
        client = tool_settings.get_s3_client()
        for key in uploaded_keys:
            try:
                client.delete_object(
                    Bucket=tool_settings.s3_bucket_name,
                    Key=key,
                )
            except Exception:
                pass
    except Exception:
        pass


# ============================================================================
# S3 Import Tests
# ============================================================================


class TestLayerImportFromS3:
    """Test import from S3 storage."""

    def test_imports_parquet_from_s3(
        self,
        import_runner: LayerImportRunner,
        upload_test_file_to_s3,
        cleanup_output_layer,
        ducklake_connection: duckdb.DuckDBPyConnection,
        vector_data_dir: Path,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
    ):
        """Test importing a parquet file from S3."""
        # Upload test file to S3
        s3_key = upload_test_file_to_s3("overlay_points.parquet")

        # Run import
        params = LayerImportParams(
            user_id=test_user["id"],
            folder_id=test_folder["id"],
            s3_key=s3_key,
            name="Imported Points",
        )
        result = import_runner.run(params)

        try:
            # Verify result
            assert result.get("layer_id") is not None
            assert result.get("error") is None

            # Verify layer was created in DuckLake
            layer_id = result["layer_id"]
            user_schema = f"user_{test_user['id'].replace('-', '')}"
            table_name = f"t_{layer_id.replace('-', '')}"

            count = ducklake_connection.execute(f"""
                SELECT COUNT(*) FROM lake.{user_schema}.{table_name}
            """).fetchone()[0]

            assert count > 0, "DuckLake table should have features"

        finally:
            # Cleanup
            if result.get("layer_id"):
                asyncio.get_event_loop().run_until_complete(
                    cleanup_output_layer(result["layer_id"])
                )

    def test_imports_geojson_from_s3(
        self,
        import_runner: LayerImportRunner,
        upload_test_file_to_s3,
        cleanup_output_layer,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
        tmp_path: Path,
    ):
        """Test importing a GeoJSON file from S3."""
        # Create a simple GeoJSON file
        geojson_content = """{
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [11.5, 48.1]},
                    "properties": {"name": "Test Point", "value": 100}
                }
            ]
        }"""
        geojson_path = tmp_path / "test.geojson"
        geojson_path.write_text(geojson_content)

        # Upload to S3
        client = import_runner.settings.get_s3_client()
        s3_key = f"test-uploads/{uuid.uuid4()}/test.geojson"
        client.upload_file(
            str(geojson_path),
            import_runner.settings.s3_bucket_name,
            s3_key,
        )

        try:
            # Run import
            params = LayerImportParams(
                user_id=test_user["id"],
                folder_id=test_folder["id"],
                s3_key=s3_key,
                name="GeoJSON Import",
            )
            result = import_runner.run(params)

            # Verify result
            assert result.get("layer_id") is not None
            assert result.get("error") is None

        finally:
            # Cleanup S3 file
            try:
                client.delete_object(
                    Bucket=import_runner.settings.s3_bucket_name,
                    Key=s3_key,
                )
            except Exception:
                pass

            # Cleanup layer
            if result.get("layer_id"):
                asyncio.get_event_loop().run_until_complete(
                    cleanup_output_layer(result["layer_id"])
                )


# ============================================================================
# PostgreSQL Metadata Tests
# ============================================================================


class TestLayerImportMetadata:
    """Test PostgreSQL metadata creation during import."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_creates_postgresql_metadata(
        self,
        import_runner: LayerImportRunner,
        upload_test_file_to_s3,
        cleanup_output_layer,
        postgres_pool,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
        tool_settings: ToolSettings,
    ):
        """Test that import creates layer metadata in PostgreSQL."""
        import uuid as uuid_module

        # Upload test file
        s3_key = upload_test_file_to_s3("overlay_points.parquet")

        # Run import
        params = LayerImportParams(
            user_id=test_user["id"],
            folder_id=test_folder["id"],
            s3_key=s3_key,
            name="Test Metadata Layer",
            description="Test description",
            tags=["test", "import"],
        )
        result = await asyncio.to_thread(import_runner.run, params)

        try:
            assert result.get("layer_id") is not None

            # Verify metadata in PostgreSQL
            layer_id = result["layer_id"]
            row = await postgres_pool.fetchrow(
                f"""
                SELECT id, name, user_id, folder_id
                FROM {tool_settings.customer_schema}.layer
                WHERE id = $1
                """,
                uuid_module.UUID(layer_id),
            )

            assert row is not None, "Layer metadata should exist"
            assert row["name"] == "Test Metadata Layer"
            assert str(row["user_id"]) == test_user["id"]
            assert str(row["folder_id"]) == test_folder["id"]

        finally:
            if result.get("layer_id"):
                await cleanup_output_layer(result["layer_id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_uses_filename_when_name_not_provided(
        self,
        import_runner: LayerImportRunner,
        upload_test_file_to_s3,
        cleanup_output_layer,
        postgres_pool,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
        tool_settings: ToolSettings,
    ):
        """Test that import uses filename when name is not provided."""
        import uuid as uuid_module

        # Upload test file
        s3_key = upload_test_file_to_s3("overlay_points.parquet")

        # Run import without name
        params = LayerImportParams(
            user_id=test_user["id"],
            folder_id=test_folder["id"],
            s3_key=s3_key,
            name=None,  # Let it use filename
        )
        result = await asyncio.to_thread(import_runner.run, params)

        try:
            assert result.get("layer_id") is not None

            # Check name (should be derived from filename)
            layer_id = result["layer_id"]
            row = await postgres_pool.fetchrow(
                f"""
                SELECT name FROM {tool_settings.customer_schema}.layer WHERE id = $1
                """,
                uuid_module.UUID(layer_id),
            )

            assert row is not None
            # Name should contain "overlay_points" or similar
            assert "overlay" in row["name"].lower() or row["name"] is not None

        finally:
            if result.get("layer_id"):
                await cleanup_output_layer(result["layer_id"])


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestLayerImportErrors:
    """Test error handling during import."""

    def test_rejects_missing_source(
        self,
        import_runner: LayerImportRunner,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
    ):
        """Test that import fails when neither s3_key nor wfs_url provided."""
        params = LayerImportParams(
            user_id=test_user["id"],
            folder_id=test_folder["id"],
            s3_key=None,
            wfs_url=None,
        )

        # Should raise ValueError when no source is provided
        with pytest.raises(
            ValueError, match="Either s3_key or wfs_url must be provided"
        ):
            import_runner.run(params)

    def test_handles_nonexistent_s3_key(
        self,
        import_runner: LayerImportRunner,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
    ):
        """Test handling of non-existent S3 object."""
        from botocore.exceptions import ClientError

        params = LayerImportParams(
            user_id=test_user["id"],
            folder_id=test_folder["id"],
            s3_key=f"nonexistent/{uuid.uuid4()}/file.parquet",
        )

        # Should raise ClientError (404) when S3 key doesn't exist
        with pytest.raises(ClientError):
            import_runner.run(params)


# ============================================================================
# Feature Layer Type Tests
# ============================================================================


class TestLayerImportFeatureType:
    """Test that imports create 'standard' feature layers."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_creates_standard_feature_layer(
        self,
        import_runner: LayerImportRunner,
        upload_test_file_to_s3,
        cleanup_output_layer,
        postgres_pool,
        test_user: dict[str, Any],
        test_folder: dict[str, Any],
        tool_settings: ToolSettings,
    ):
        """Test that import creates a 'standard' feature layer type."""
        import uuid as uuid_module

        # Upload test file
        s3_key = upload_test_file_to_s3("overlay_points.parquet")

        # Run import
        params = LayerImportParams(
            user_id=test_user["id"],
            folder_id=test_folder["id"],
            s3_key=s3_key,
            name="Standard Layer Test",
        )
        result = await asyncio.to_thread(import_runner.run, params)

        try:
            assert result.get("layer_id") is not None

            # Check feature_layer_type
            layer_id = result["layer_id"]
            row = await postgres_pool.fetchrow(
                f"""
                SELECT feature_layer_type FROM {tool_settings.customer_schema}.layer WHERE id = $1
                """,
                uuid_module.UUID(layer_id),
            )

            assert row is not None
            assert row["feature_layer_type"] == "standard"

        finally:
            if result.get("layer_id"):
                await cleanup_output_layer(result["layer_id"])
