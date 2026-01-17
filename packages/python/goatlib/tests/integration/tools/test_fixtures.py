"""Tests to verify the integration test fixtures work correctly.

These tests validate that the database fixtures are properly set up
before running more complex tool integration tests.

Run with:
    pytest tests/integration/tools/test_fixtures.py -v
"""

import uuid

import pytest

from .conftest import (
    TEST_ACCOUNTS_SCHEMA,
    TEST_CUSTOMER_SCHEMA,
    TEST_FOLDER_ID,
    TEST_PROJECT_ID,
    TEST_USER_ID,
    get_full_table_path,
    get_pg_connection,
    get_table_name,
    get_user_schema_name,
)

pytestmark = pytest.mark.integration


class TestSchemaHelpers:
    """Test schema/table name helper functions."""

    def test_get_user_schema_name(self):
        """Test user schema name generation."""
        user_id = "12345678-1234-1234-1234-123456789abc"
        schema = get_user_schema_name(user_id)
        assert schema == "user_12345678123412341234123456789abc"

    def test_get_table_name(self):
        """Test table name generation."""
        layer_id = "abcdef12-3456-7890-abcd-ef1234567890"
        table = get_table_name(layer_id)
        assert table == "t_abcdef1234567890abcdef1234567890"

    def test_get_full_table_path(self):
        """Test full table path generation."""
        user_id = "00000000-0000-0000-0000-000000000001"
        layer_id = "00000000-0000-0000-0000-000000000002"
        path = get_full_table_path(user_id, layer_id)
        assert (
            path
            == "lake.user_00000000000000000000000000000001.t_00000000000000000000000000000002"
        )


@pytest.mark.asyncio(loop_scope="session")
class TestPostgresFixtures:
    """Test PostgreSQL fixtures."""

    async def test_test_schemas_created(self, tool_settings, test_schemas):
        """Verify test schemas are created."""
        conn = await get_pg_connection(tool_settings)
        try:
            # Check customer schema exists
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = $1
                )
                """,
                TEST_CUSTOMER_SCHEMA,
            )
            assert result is True, f"Schema {TEST_CUSTOMER_SCHEMA} should exist"

            # Check accounts schema exists
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = $1
                )
                """,
                TEST_ACCOUNTS_SCHEMA,
            )
            assert result is True, f"Schema {TEST_ACCOUNTS_SCHEMA} should exist"
        finally:
            await conn.close()

    async def test_test_user_created(self, tool_settings, test_user):
        """Verify test user is created."""
        conn = await get_pg_connection(tool_settings)
        try:
            user = await conn.fetchrow(
                f"SELECT * FROM {TEST_ACCOUNTS_SCHEMA}.user WHERE id = $1",
                uuid.UUID(TEST_USER_ID),
            )
            assert user is not None, "Test user should exist"
            assert user["firstname"] == "Test"
            assert user["lastname"] == "User"
        finally:
            await conn.close()

    async def test_test_folder_created(self, tool_settings, test_folder):
        """Verify test folder is created."""
        conn = await get_pg_connection(tool_settings)
        try:
            folder = await conn.fetchrow(
                f"SELECT * FROM {TEST_CUSTOMER_SCHEMA}.folder WHERE id = $1",
                uuid.UUID(TEST_FOLDER_ID),
            )
            assert folder is not None, "Test folder should exist"
            assert folder["name"] == "Test Folder"
            assert str(folder["user_id"]) == TEST_USER_ID
        finally:
            await conn.close()

    async def test_test_project_created(self, tool_settings, test_project):
        """Verify test project is created."""
        conn = await get_pg_connection(tool_settings)
        try:
            project = await conn.fetchrow(
                f"SELECT * FROM {TEST_CUSTOMER_SCHEMA}.project WHERE id = $1",
                uuid.UUID(TEST_PROJECT_ID),
            )
            assert project is not None, "Test project should exist"
            assert project["name"] == "Test Project"
            assert str(project["user_id"]) == TEST_USER_ID
            assert str(project["folder_id"]) == TEST_FOLDER_ID
        finally:
            await conn.close()


class TestDuckLakeFixtures:
    """Test DuckLake fixtures."""

    def test_ducklake_connection(self, ducklake_connection):
        """Verify DuckLake connection is working."""
        # Check that lake catalog is attached
        result = ducklake_connection.execute(
            "SELECT * FROM duckdb_databases() WHERE database_name = 'lake'"
        ).fetchone()
        assert result is not None, "DuckLake should be attached as 'lake'"

    def test_create_test_layer_in_ducklake(
        self, create_test_layer_in_ducklake, ducklake_connection, test_user
    ):
        """Test creating a layer in DuckLake."""
        layer_id = str(uuid.uuid4())

        # Create test layer
        create_test_layer_in_ducklake(
            layer_id=layer_id,
            data=[
                {"id": 1, "name": "Test Point", "geometry": "POINT(11.5 48.1)"},
            ],
            geometry_type="POINT",
        )

        # Verify layer exists
        table_path = get_full_table_path(test_user["id"], layer_id)
        count = ducklake_connection.execute(
            f"SELECT COUNT(*) FROM {table_path}"
        ).fetchone()[0]
        assert count == 1, "Layer should have 1 feature"

        # Verify geometry
        geom_type = ducklake_connection.execute(
            f"SELECT ST_GeometryType(geometry) FROM {table_path}"
        ).fetchone()[0]
        assert "POINT" in geom_type.upper()


@pytest.mark.asyncio(loop_scope="session")
class TestLayerMetadataFixtures:
    """Test layer metadata fixtures."""

    async def test_create_test_layer_metadata(
        self, create_test_layer_metadata, tool_settings
    ):
        """Test creating layer metadata in PostgreSQL."""
        layer_id = str(uuid.uuid4())

        # Create layer metadata
        await create_test_layer_metadata(
            layer_id=layer_id,
            name="Test Layer Metadata",
            geometry_type="point",
        )

        # Verify metadata exists
        conn = await get_pg_connection(tool_settings)
        try:
            layer = await conn.fetchrow(
                f"SELECT * FROM {TEST_CUSTOMER_SCHEMA}.layer WHERE id = $1",
                uuid.UUID(layer_id),
            )
            assert layer is not None, "Layer metadata should exist"
            assert layer["name"] == "Test Layer Metadata"
            assert layer["feature_layer_geometry_type"] == "point"
            assert str(layer["user_id"]) == TEST_USER_ID
            assert str(layer["folder_id"]) == TEST_FOLDER_ID
        finally:
            await conn.close()
