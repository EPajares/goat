#!/usr/bin/env python3
"""Test script for LayerDelete process via OGC API.

This script tests the LayerDelete process by:
1. Creating a test folder and user in the database (fixtures)
2. Uploading a test file to S3
3. Calling LayerImport to create a layer
4. Calling LayerDelete to delete the layer
5. Verifying the layer no longer exists
6. Cleaning up test data

Usage:
    python scripts/test_layer_delete.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from uuid import uuid4

import requests

# Add paths for importing lib modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import lib.paths  # noqa: F401 - sets up full sys.path

from lib.s3 import get_s3_service
from lib.config import get_settings

# Configuration
API_BASE_URL = "http://localhost:8200"
TEST_DATA_DIR = Path(__file__).parent.parent / "tests" / "data" / "layer"

# Test user ID (use real one from your test setup)
TEST_USER_ID = "744e4fd1-685c-495c-8b02-efebce875359"

# Will be set by fixture
TEST_FOLDER_ID = None


async def create_test_user(user_id: str) -> bool:
    """Create a test user in the accounts.user table if it doesn't exist."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()

    engine = create_async_engine(settings.ASYNC_POSTGRES_DATABASE_URI)
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
            SELECT id FROM accounts."user" WHERE id = :id
        """),
            {"id": user_id},
        )
        existing = result.fetchone()

        if existing:
            print(f"Test user already exists: {user_id}")
            await engine.dispose()
            return False

        await conn.execute(
            text("""
            INSERT INTO accounts."user" (id, email, firstname, lastname) 
            VALUES (:id, :email, 'Test', 'User')
        """),
            {"id": user_id, "email": f"test-{user_id[:8]}@test.local"},
        )
    await engine.dispose()

    print(f"Created test user in accounts.user: {user_id}")
    return True


async def delete_test_user(user_id: str):
    """Delete the test user from the accounts.user table."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()

    engine = create_async_engine(settings.ASYNC_POSTGRES_DATABASE_URI)
    async with engine.begin() as conn:
        await conn.execute(
            text("""
            DELETE FROM accounts."user" WHERE id = :id
        """),
            {"id": user_id},
        )
    await engine.dispose()

    print(f"Deleted test user: {user_id}")


async def create_test_folder(user_id: str) -> str:
    """Create a test folder in the database."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    folder_id = uuid4()

    engine = create_async_engine(settings.ASYNC_POSTGRES_DATABASE_URI)
    async with engine.begin() as conn:
        await conn.execute(
            text("""
            INSERT INTO customer.folder (id, user_id, name, created_at, updated_at) 
            VALUES (:id, :user_id, :name, NOW(), NOW())
        """),
            {"id": str(folder_id), "user_id": user_id, "name": "Test Delete"},
        )
    await engine.dispose()

    print(f"Created test folder: {folder_id}")
    return str(folder_id)


async def delete_test_folder(folder_id: str):
    """Delete the test folder from the database."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()

    engine = create_async_engine(settings.ASYNC_POSTGRES_DATABASE_URI)
    async with engine.begin() as conn:
        # Delete any layers in this folder first
        await conn.execute(
            text("""
            DELETE FROM customer.layer WHERE folder_id = :folder_id
        """),
            {"folder_id": folder_id},
        )
        # Delete the folder
        await conn.execute(
            text("""
            DELETE FROM customer.folder WHERE id = :id
        """),
            {"id": folder_id},
        )
    await engine.dispose()

    print(f"Deleted test folder: {folder_id}")


async def check_layer_exists(layer_id: str) -> bool:
    """Check if a layer exists in the database."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()

    engine = create_async_engine(settings.ASYNC_POSTGRES_DATABASE_URI)
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
            SELECT id FROM customer.layer WHERE id = :id
        """),
            {"id": layer_id},
        )
        row = result.fetchone()
    await engine.dispose()

    return row is not None


def check_ducklake_table_exists(user_id: str, layer_id: str) -> bool:
    """Check if a DuckLake table exists for the layer."""
    from lib.ducklake import get_ducklake_manager

    ducklake_manager = get_ducklake_manager()
    schema_name = f"user_{user_id.replace('-', '')}"
    table_name = f"t_{layer_id.replace('-', '')}"

    try:
        with ducklake_manager.connection() as con:
            result = con.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_catalog = 'lake'
                    AND table_schema = '{schema_name}'
                    AND table_name = '{table_name}'
            """).fetchone()
            return result and result[0] > 0
    except Exception as e:
        print(f"Error checking DuckLake table: {e}")
        return False


def upload_test_file_to_s3(file_path: Path, user_id: str) -> str:
    """Upload a test file to S3 and return the s3_key."""
    settings = get_settings()
    s3 = get_s3_service()

    s3_key = f"user_{user_id.replace('-', '')}/uploads/{file_path.name}"

    print(f"Uploading {file_path.name} to S3...")

    content_type = (
        "application/geo+json"
        if file_path.suffix == ".geojson"
        else "application/octet-stream"
    )

    with open(file_path, "rb") as f:
        s3.upload_file(
            file_content=f,
            bucket_name=settings.S3_BUCKET_NAME,
            s3_key=s3_key,
            content_type=content_type,
        )

    print(f"  Upload complete: {s3_key}")
    return s3_key


def poll_job_status(job_id: str, max_attempts: int = 15, delay: float = 2.0) -> bool:
    """Poll job status until completion."""
    print(f"Polling job status: {job_id}")

    for attempt in range(max_attempts):
        response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"  Attempt {attempt + 1}: status={status}")

            if status in ("successful", "failed", "dismissed"):
                print(f"  Final status: {status}")
                if "message" in data:
                    print(f"  Message: {data['message']}")
                return status == "successful"
        else:
            print(f"  Attempt {attempt + 1}: HTTP {response.status_code}")

        time.sleep(delay)

    print("  Timeout waiting for job completion")
    return False


def create_layer_via_import(layer_id: str, s3_key: str) -> bool:
    """Create a layer by calling LayerImport process."""
    print(f"\n=== Creating layer via LayerImport ===")
    print(f"Layer ID: {layer_id}")

    payload = {
        "inputs": {
            "user_id": TEST_USER_ID,
            "layer_id": layer_id,
            "folder_id": TEST_FOLDER_ID,
            "name": "Layer to Delete",
            "description": "This layer will be deleted by test",
            "s3_key": s3_key,
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-User-Id": TEST_USER_ID,
    }

    response = requests.post(
        f"{API_BASE_URL}/processes/LayerImport/execution",
        json=payload,
        headers=headers,
    )

    print(f"Status: {response.status_code}")

    if response.status_code in (200, 201, 202):
        data = response.json()
        job_id = data.get("jobID")
        if job_id:
            print(f"Import job created: {job_id}")
            return poll_job_status(job_id)
    else:
        print(f"Error: {response.text[:500]}")

    return False


def test_layer_delete(layer_id: str) -> bool:
    """Test deleting a layer via LayerDelete process."""
    print(f"\n=== Testing LayerDelete ===")
    print(f"Layer ID to delete: {layer_id}")

    payload = {
        "inputs": {
            "user_id": TEST_USER_ID,
            "layer_id": layer_id,
        }
    }

    print(f"Request payload:")
    print(json.dumps(payload, indent=2))

    headers = {
        "Content-Type": "application/json",
        "X-User-Id": TEST_USER_ID,
    }

    response = requests.post(
        f"{API_BASE_URL}/processes/LayerDelete/execution",
        json=payload,
        headers=headers,
    )

    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text[:500]}")

    if response.status_code in (200, 201, 202):
        data = response.json()
        job_id = data.get("jobID")
        if job_id:
            print(f"\nDelete job created: {job_id}")
            return poll_job_status(job_id)

    return False


def test_process_description():
    """Test LayerDelete process description."""
    print("\n=== Testing /processes/LayerDelete ===")

    response = requests.get(f"{API_BASE_URL}/processes/LayerDelete")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Process ID: {data.get('id')}")
        print(f"Title: {data.get('title')}")
        print(f"Inputs: {list(data.get('inputs', {}).keys())}")
        print(f"Outputs: {list(data.get('outputs', {}).keys())}")
        return True
    return False


async def main():
    """Main test function with fixture setup/teardown."""
    global TEST_FOLDER_ID

    print("=" * 60)
    print("LayerDelete API Test Script")
    print("=" * 60)

    # Generate IDs
    layer_id = str(uuid4())

    # Setup: Create test user and folder
    print("\n=== Setting up test fixtures ===")
    user_created = await create_test_user(TEST_USER_ID)
    TEST_FOLDER_ID = await create_test_folder(TEST_USER_ID)

    # Test file path
    test_file = TEST_DATA_DIR / "points.geojson"

    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        print("Creating a simple test file...")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10.0, 50.0]},
                    "properties": {"name": "Test Point", "value": 42},
                }
            ],
        }
        with open(test_file, "w") as f:
            json.dump(geojson, f)

    try:
        # Test 1: Process description
        test_process_description()

        # Test 2: Upload file to S3
        print("\n=== Uploading test file to S3 ===")
        s3_key = upload_test_file_to_s3(test_file, TEST_USER_ID)

        # Test 3: Create a layer via import
        import_success = create_layer_via_import(layer_id, s3_key)

        if not import_success:
            print("\n❌ LayerImport failed - cannot test delete")
            return

        # Verify layer was created
        print("\n=== Verifying layer exists ===")
        layer_exists = await check_layer_exists(layer_id)
        ducklake_exists = check_ducklake_table_exists(TEST_USER_ID, layer_id)

        print(f"Layer in PostgreSQL: {layer_exists}")
        print(f"Table in DuckLake: {ducklake_exists}")

        if not layer_exists:
            print("\n❌ Layer was not created - cannot test delete")
            return

        # Test 4: Delete the layer
        delete_success = test_layer_delete(layer_id)

        if not delete_success:
            print("\n❌ LayerDelete job failed")
            return

        # Test 5: Verify layer no longer exists
        print("\n=== Verifying layer was deleted ===")
        layer_exists_after = await check_layer_exists(layer_id)
        ducklake_exists_after = check_ducklake_table_exists(TEST_USER_ID, layer_id)

        print(f"Layer in PostgreSQL: {layer_exists_after}")
        print(f"Table in DuckLake: {ducklake_exists_after}")

        if not layer_exists_after and not ducklake_exists_after:
            print("\n✅ LayerDelete test PASSED!")
            print("  - Layer metadata deleted from PostgreSQL")
            print("  - Layer table deleted from DuckLake")
        elif not layer_exists_after:
            print("\n⚠️ LayerDelete partially succeeded")
            print("  - Layer metadata deleted from PostgreSQL")
            print("  - DuckLake table may still exist (or never existed)")
        else:
            print("\n❌ LayerDelete test FAILED")
            print("  - Layer still exists in database")

    finally:
        # Teardown: Delete test folder and user
        print("\n=== Cleaning up test fixtures ===")
        await delete_test_folder(TEST_FOLDER_ID)
        if user_created:
            await delete_test_user(TEST_USER_ID)

    print("\n" + "=" * 60)
    print("Tests complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
