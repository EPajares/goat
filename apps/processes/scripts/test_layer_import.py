#!/usr/bin/env python3
"""Test script for LayerImport process via OGC API.

This script tests the LayerImport process by:
1. Creating a test folder in the database (fixture)
2. Uploading a test file to S3
3. Calling the /processes/LayerImport/execution endpoint
4. Polling for job completion
5. Cleaning up test data

Usage:
    python scripts/test_layer_import.py
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
    """Create a test user in the accounts.user table if it doesn't exist.

    Note: User table is in 'accounts' schema, not 'customer' schema.
    The folder table has FK to accounts.user.id.

    Returns:
        True if user was created, False if already exists
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()

    engine = create_async_engine(settings.ASYNC_POSTGRES_DATABASE_URI)
    async with engine.begin() as conn:
        # Check if user already exists in accounts schema
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

        # Create user in accounts schema
        # Required columns: id, email (NOT NULL)
        # Optional columns: firstname, lastname, avatar, newsletter_subscribe, hubspot_id, organization_id
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
    """Create a test folder in the database.

    Returns:
        The folder ID
    """
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
            {"id": str(folder_id), "user_id": user_id, "name": "Test Imports"},
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


def upload_test_file_to_s3(file_path: Path, user_id: str) -> str:
    """Upload a test file to S3 and return the s3_key.

    Args:
        file_path: Local path to the file to upload
        user_id: User ID for organizing files in S3

    Returns:
        S3 key of the uploaded file
    """
    settings = get_settings()
    s3 = get_s3_service()

    # Build S3 key like the real upload flow does
    s3_key = f"user_{user_id.replace('-', '')}/uploads/{file_path.name}"

    print(f"Uploading {file_path.name} to S3...")
    print(f"  Bucket: {settings.S3_BUCKET_NAME}")
    print(f"  S3 Key: {s3_key}")

    # Determine content type
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

    print(f"  Upload complete!")
    return s3_key


def test_process_list():
    """Test that LayerImport is in the process list."""
    print("\n=== Testing /processes endpoint ===")

    response = requests.get(f"{API_BASE_URL}/processes")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        processes = data.get("processes", [])
        layer_processes = [p for p in processes if p["id"].startswith("Layer")]
        print(f"Layer processes found: {[p['id'] for p in layer_processes]}")
        return True
    return False


def test_process_description():
    """Test LayerImport process description."""
    print("\n=== Testing /processes/LayerImport ===")

    response = requests.get(f"{API_BASE_URL}/processes/LayerImport")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Process ID: {data.get('id')}")
        print(f"Title: {data.get('title')}")
        print(f"Inputs: {list(data.get('inputs', {}).keys())}")
        print(f"Outputs: {list(data.get('outputs', {}).keys())}")
        return True
    return False


def test_layer_import_execution():
    """Test executing LayerImport process with real S3 upload."""
    print("\n" + "=" * 60)
    print("Testing LayerImport with S3 upload")
    print("=" * 60)

    # Generate unique IDs
    layer_id = str(uuid4())

    # Test file path
    test_file = TEST_DATA_DIR / "points.geojson"

    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        return False

    print(f"\nTest file: {test_file}")
    print(f"Layer ID: {layer_id}")

    # Step 1: Upload file to S3
    try:
        s3_key = upload_test_file_to_s3(test_file, TEST_USER_ID)
    except Exception as e:
        print(f"ERROR: Failed to upload to S3: {e}")
        return False

    # Step 2: Execute LayerImport
    print(f"\n=== Executing LayerImport ===")

    payload = {
        "inputs": {
            "user_id": TEST_USER_ID,
            "layer_id": layer_id,
            "folder_id": TEST_FOLDER_ID,
            "name": "Test Points Layer",
            "description": "Imported via test script",
            "s3_key": s3_key,
        }
    }

    print(f"Request payload:")
    print(json.dumps(payload, indent=2))

    headers = {
        "Content-Type": "application/json",
        "X-User-Id": TEST_USER_ID,
    }

    response = requests.post(
        f"{API_BASE_URL}/processes/LayerImport/execution",
        json=payload,
        headers=headers,
    )

    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text[:500]}")

    if response.status_code in (200, 201, 202):
        data = response.json()
        job_id = data.get("jobID")
        if job_id:
            print(f"\nJob created: {job_id}")
            return poll_job_status(job_id)

    return False


def poll_job_status(job_id: str, max_attempts: int = 10, delay: float = 2.0):
    """Poll job status until completion."""
    print(f"\n=== Polling job status: {job_id} ===")

    for attempt in range(max_attempts):
        response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"Attempt {attempt + 1}: status={status}")

            if status in ("successful", "failed", "dismissed"):
                print(f"\nFinal status: {status}")
                if "message" in data:
                    print(f"Message: {data['message']}")
                return status == "successful"
        else:
            print(f"Attempt {attempt + 1}: HTTP {response.status_code}")

        time.sleep(delay)

    print("Timeout waiting for job completion")
    return False


def test_wfs_import():
    """Test importing from a public WFS service."""
    print("\n=== Testing WFS Import ===")

    layer_id = str(uuid4())

    # Public WFS service for testing
    wfs_url = "https://geodienste.hamburg.de/HH_WFS_Verwaltungsgrenzen"

    payload = {
        "inputs": {
            "user_id": TEST_USER_ID,  # Required for all layer processes
            "layer_id": layer_id,
            "folder_id": TEST_FOLDER_ID,
            "name": "Hamburg Boundaries (WFS)",
            "wfs_url": wfs_url,
            "wfs_layer_name": "landesgrenze",
        }
    }

    print(f"WFS URL: {wfs_url}")
    print(f"Layer ID: {layer_id}")

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
    print(f"Response: {response.text[:500]}")

    if response.status_code in (200, 201, 202):
        data = response.json()
        job_id = data.get("jobID")
        if job_id:
            print(f"Job created: {job_id}")
            return poll_job_status(job_id)

    return False


async def main():
    """Main test function with fixture setup/teardown."""
    global TEST_FOLDER_ID

    print("=" * 60)
    print("LayerImport API Test Script")
    print("=" * 60)

    # Setup: Create test user and folder
    print("\n=== Setting up test fixtures ===")
    user_created = await create_test_user(TEST_USER_ID)
    TEST_FOLDER_ID = await create_test_folder(TEST_USER_ID)

    try:
        # Test 1: Process list
        test_process_list()

        # Test 2: Process description
        test_process_description()

        # Test 3: Execute import
        print("\n" + "=" * 60)
        print("Testing LayerImport execution")
        print("=" * 60)
        success = test_layer_import_execution()

        if success:
            print("\n✅ LayerImport test PASSED!")
        else:
            print("\n❌ LayerImport test FAILED")

    finally:
        # Teardown: Delete test folder and user (in reverse order)
        print("\n=== Cleaning up test fixtures ===")
        await delete_test_folder(TEST_FOLDER_ID)
        if user_created:
            await delete_test_user(TEST_USER_ID)

    print("\n" + "=" * 60)
    print("Tests complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
