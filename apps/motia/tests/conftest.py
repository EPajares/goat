# Standard library imports
import sys

sys.path.insert(0, "/app/apps/core/src")

import uuid
from uuid import uuid4

# Import Env variables from Core
import core._dotenv  # noqa: E402, F401, I001

import pytest
import pytest_asyncio
from sqlalchemy import text
from jose import jwt

# Reuse Core's test infrastructure
from core.core.config import settings
from core.endpoints.deps import session_manager
from core.storage.ducklake import ducklake_manager
from core.services.layer_import import layer_importer
from core.crud.base import CRUDBase
from core.db.models import User
from core.db.models.folder import Folder

# ============================================================================
# Test Settings - Unique schema per test run to avoid conflicts
# ============================================================================

# Generate unique schema name for this test run (avoids conflicts with coworkers)
TEST_RUN_ID = uuid.uuid4().hex[:8]
TEST_CUSTOMER_SCHEMA = f"test_motia_{TEST_RUN_ID}"
TEST_ACCOUNTS_SCHEMA = f"test_accounts_{TEST_RUN_ID}"
TEST_DUCKLAKE_CATALOG = f"test_ducklake_{TEST_RUN_ID}"


def set_test_mode():
    """Configure settings for test mode with unique schemas."""
    settings.RUN_AS_BACKGROUND_TASK = False  # Run sync for tests
    settings.CUSTOMER_SCHEMA = TEST_CUSTOMER_SCHEMA  # Unique per test run
    settings.ACCOUNTS_SCHEMA = TEST_ACCOUNTS_SCHEMA  # Unique accounts schema
    settings.DUCKLAKE_CATALOG_SCHEMA = TEST_DUCKLAKE_CATALOG  # Unique DuckLake catalog
    settings.TEST_MODE = True


set_test_mode()

print(
    f"[TEST] Using schemas: CUSTOMER={TEST_CUSTOMER_SCHEMA}, ACCOUNTS={TEST_ACCOUNTS_SCHEMA}, DUCKLAKE={TEST_DUCKLAKE_CATALOG}"
)


# ============================================================================
# Core Fixtures (Session-scoped - run once)
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db_setup(event_loop):
    """Initialize database schema (once per session)."""
    print(
        f"[TEST] Initializing database with schemas: customer={TEST_CUSTOMER_SCHEMA}, accounts={TEST_ACCOUNTS_SCHEMA}"
    )

    session_manager.init(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    session_manager._engine.update_execution_options(
        schema_translate_map={
            "customer": settings.CUSTOMER_SCHEMA,
            "accounts": settings.ACCOUNTS_SCHEMA,
        }
    )

    async with session_manager.connect() as connection:
        # Drop test schemas if they exist (cleanup from previous failed run)
        for schema in [
            TEST_CUSTOMER_SCHEMA,
            TEST_ACCOUNTS_SCHEMA,
            TEST_DUCKLAKE_CATALOG,
        ]:
            await connection.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))

        # Create fresh test schemas
        for schema in [TEST_CUSTOMER_SCHEMA, TEST_ACCOUNTS_SCHEMA]:
            await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

        # Create all tables in our test schemas
        await session_manager.create_all(connection)
        await connection.commit()

    # Initialize DuckLake (creates its catalog schema)
    print(f"[TEST] Initializing DuckLake with catalog: {TEST_DUCKLAKE_CATALOG}")
    ducklake_manager.init(settings)

    yield

    # Cleanup: drop all test schemas entirely
    print(
        f"[TEST] Cleaning up schemas: {TEST_CUSTOMER_SCHEMA}, {TEST_ACCOUNTS_SCHEMA}, {TEST_DUCKLAKE_CATALOG}"
    )
    ducklake_manager.close()

    async with session_manager.connect() as connection:
        for schema in [
            TEST_CUSTOMER_SCHEMA,
            TEST_ACCOUNTS_SCHEMA,
            TEST_DUCKLAKE_CATALOG,
        ]:
            await connection.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        await connection.commit()

    await session_manager.close()


@pytest_asyncio.fixture
async def db_session(db_setup):
    """Get a database session for a test."""
    async with session_manager.session() as session:
        yield session


# ============================================================================
# User & Folder Fixtures (Required for layers)
# ============================================================================


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create test user (required for layer ownership)."""
    # Extract user_id from sample JWT (same as Core)
    scheme, _, token = settings.SAMPLE_AUTHORIZATION.partition(" ")
    user_id = jwt.get_unverified_claims(token)["sub"]

    user = User(
        id=user_id,
        firstname="Test",
        lastname="User",
        avatar=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create user schema in DuckLake
    ducklake_manager.create_user_schema(user_id)

    yield user

    # Cleanup
    ducklake_manager.delete_user_schema(user_id)
    await CRUDBase(User).delete(db_session, id=user_id)


@pytest_asyncio.fixture
async def test_folder(db_session, test_user):
    """Create test folder (required for layers)."""
    folder = Folder(
        id=uuid4(),
        user_id=test_user.id,
        name="test_folder",
    )
    db_session.add(folder)
    await db_session.commit()
    await db_session.refresh(folder)

    yield folder

    await CRUDBase(Folder).delete(db_session, id=folder.id)


# ============================================================================
# Layer Fixtures (Using goatlib test data via layer_importer directly)
# ============================================================================

GOATLIB_TEST_DATA = "/app/packages/python/goatlib/tests/data/vector"


@pytest_asyncio.fixture
async def polygon_layer(test_user):
    """Create polygon layer from goatlib test data using LayerImporter directly."""
    layer_id = uuid4()

    # Use layer_importer directly (sync, no CRUD overhead)
    result = layer_importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=f"{GOATLIB_TEST_DATA}/overlay_polygons.parquet",
        target_crs="EPSG:4326",
    )

    yield {
        "layer_id": layer_id,
        "user_id": test_user.id,
        "table_name": result.table_name,
        "feature_count": result.feature_count,
    }

    # Cleanup: delete layer from DuckLake
    #ducklake_manager.delete_layer_table(test_user.id, layer_id)


@pytest_asyncio.fixture
async def boundary_layer(test_user):
    """Create boundary layer for clip operations using LayerImporter directly."""
    layer_id = uuid4()

    # Use layer_importer directly (sync, no CRUD overhead)
    result = layer_importer.import_file(
        user_id=test_user.id,
        layer_id=layer_id,
        file_path=f"{GOATLIB_TEST_DATA}/overlay_boundary.parquet",
        target_crs="EPSG:4326",
    )

    yield {
        "layer_id": layer_id,
        "user_id": test_user.id,
        "table_name": result.table_name,
        "feature_count": result.feature_count,
    }

    # Cleanup: delete layer from DuckLake
    #ducklake_manager.delete_layer_table(test_user.id, layer_id)
