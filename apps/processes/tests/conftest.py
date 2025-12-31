# Standard library imports
import sys
import uuid
from uuid import uuid4

# Add src to path before importing lib.paths
sys.path.insert(0, "/app/apps/processes/src")

import lib.paths  # type: ignore # noqa: F401, E402 - sets up sys.path

# Import Env variables from Core
import core._dotenv  # noqa: E402, F401, I001
import pytest
import pytest_asyncio

# Reuse Core's test infrastructure
from core.core.config import settings

# Import LayerImporter for fixtures
from lib.layer_service import LayerImporter  # noqa: E402

# Import lib settings for processes API (separate from core settings)
from lib.config import settings as lib_settings  # noqa: E402
from core.crud.base import CRUDBase
from core.db.models import User
from core.db.models.folder import Folder
from core.db.models.project import Project
from core.db.models.scenario import Scenario
from core.endpoints.deps import session_manager
from core.storage.ducklake import ducklake_manager
from jose import jwt
from sqlalchemy import text

# ============================================================================
# Test Settings - Unique schema per test run to avoid conflicts
# ============================================================================

# Generate unique schema name for this test run (avoids conflicts with coworkers)
TEST_RUN_ID = uuid.uuid4().hex[:8]
TEST_CUSTOMER_SCHEMA = f"test_processes_{TEST_RUN_ID}"
TEST_ACCOUNTS_SCHEMA = f"test_accounts_{TEST_RUN_ID}"
TEST_DUCKLAKE_CATALOG = f"test_ducklake_{TEST_RUN_ID}"


def set_test_mode():
    """Configure settings for test mode with unique schemas."""
    settings.RUN_AS_BACKGROUND_TASK = False  # Run sync for tests
    settings.CUSTOMER_SCHEMA = TEST_CUSTOMER_SCHEMA  # Unique per test run
    settings.ACCOUNTS_SCHEMA = TEST_ACCOUNTS_SCHEMA  # Unique accounts schema
    settings.DUCKLAKE_CATALOG_SCHEMA = TEST_DUCKLAKE_CATALOG  # Unique DuckLake catalog
    settings.TEST_MODE = True

    # Also set lib settings for Processes API
    lib_settings.DUCKLAKE_CATALOG_SCHEMA = TEST_DUCKLAKE_CATALOG


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


# Lazy layer importer - created after DuckLake is initialized
def get_layer_importer():
    """Get or create LayerImporter instance (lazy initialization)."""
    if not hasattr(get_layer_importer, "_instance"):
        get_layer_importer._instance = LayerImporter()
    return get_layer_importer._instance


@pytest_asyncio.fixture
async def polygon_layer(test_user):
    """Create polygon layer from goatlib test data using LayerImporter directly."""
    layer_id = uuid4()
    layer_importer = get_layer_importer()

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
    # ducklake_manager.delete_layer_table(test_user.id, layer_id)


@pytest_asyncio.fixture
async def boundary_layer(test_user):
    """Create boundary layer for clip operations using LayerImporter directly."""
    layer_id = uuid4()
    layer_importer = get_layer_importer()

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
    # ducklake_manager.delete_layer_table(test_user.id, layer_id)


# ============================================================================
# Project & Scenario Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_project(db_session, test_user, test_folder):
    """Create test project for analysis results."""
    project = Project(
        id=uuid4(),
        user_id=test_user.id,
        folder_id=test_folder.id,
        name="Test Analysis Project",
        description="Project for testing analysis tools",
        tags=["test", "analysis"],
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    yield project

    await CRUDBase(Project).delete(db_session, id=project.id)


@pytest_asyncio.fixture
async def test_scenario(db_session, test_user, test_project):
    """Create test scenario for analysis with layer edits."""
    scenario = Scenario(
        id=uuid4(),
        user_id=test_user.id,
        project_id=test_project.id,
        name="Test Scenario",
    )
    db_session.add(scenario)
    await db_session.commit()
    await db_session.refresh(scenario)

    yield scenario

    await CRUDBase(Scenario).delete(db_session, id=scenario.id)
