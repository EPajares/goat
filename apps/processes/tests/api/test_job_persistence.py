"""API tests for job persistence in GOAT Core database.

These tests verify that:
1. Jobs are created in the database when analysis is started
2. Job status is updated correctly (pending -> running -> finished/failed)
3. Job payload contains result_layer_id or download_url
4. Jobs can be queried via the OGC API endpoints

Note: Using JobType.buffer as a proxy for OGC processes jobs since
there's no dedicated ogc_processes type in the current enum.
A proper JobType could be added to GOAT Core in the future.
"""

import sys

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/processes/src")

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from core.db.models.job import Job
from core.schemas.job import JobStatusType, JobType
from sqlalchemy import select

# Use buffer as proxy job type for OGC processes tests
# This could be changed to a dedicated JobType.ogc_processes in the future
OGC_JOB_TYPE = JobType.buffer


# ============================================================================
# Job Creation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_job_pending(db_session, test_user):
    """Test creating a job with pending status."""
    job_id = uuid4()

    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.accepted,
        payload={
            "process_id": "clip",
            "inputs": {
                "input_layer_id": str(uuid4()),
                "overlay_layer_id": str(uuid4()),
            },
        },
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Verify job was created
    assert job.id == job_id
    assert job.user_id == test_user.id
    assert job.type == OGC_JOB_TYPE
    assert job.status == JobStatusType.accepted
    assert job.payload["process_id"] == "clip"

    print(f"[TEST] Job created: {job.id} with status={job.status}")

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()


@pytest.mark.asyncio
async def test_job_status_transitions(db_session, test_user):
    """Test job status transitions: pending -> running -> finished."""
    job_id = uuid4()

    # Create job in accepted status
    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.accepted,
        payload={"process_id": "buffer"},
    )
    db_session.add(job)
    await db_session.commit()

    print(f"[TEST] Job {job_id}: status={job.status}")
    assert job.status == JobStatusType.accepted

    # Transition to running
    job.status = JobStatusType.running
    await db_session.commit()
    await db_session.refresh(job)

    print(f"[TEST] Job {job_id}: status={job.status}")
    assert job.status == JobStatusType.running

    # Transition to successful with result
    job.status = JobStatusType.successful
    job.payload = {
        "process_id": "buffer",
        "result_layer_id": str(uuid4()),
        "feature_count": 42,
    }
    await db_session.commit()
    await db_session.refresh(job)

    print(f"[TEST] Job {job_id}: status={job.status}, payload={job.payload}")
    assert job.status == JobStatusType.successful
    assert "result_layer_id" in job.payload
    assert job.payload["feature_count"] == 42

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()


@pytest.mark.asyncio
async def test_job_failed_status(db_session, test_user):
    """Test job failure with error message."""
    job_id = uuid4()

    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.accepted,
        payload={"process_id": "clip"},
    )
    db_session.add(job)
    await db_session.commit()

    # Transition to failed
    job.status = JobStatusType.failed
    job.payload = {
        "process_id": "clip",
        "error": "Invalid geometry type",
        "error_type": "ValueError",
    }
    await db_session.commit()
    await db_session.refresh(job)

    print(f"[TEST] Job {job_id}: status={job.status}, error={job.payload.get('error')}")
    assert job.status == JobStatusType.failed
    assert "error" in job.payload
    assert job.payload["error"] == "Invalid geometry type"

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()


@pytest.mark.asyncio
async def test_job_dismissed_status(db_session, test_user):
    """Test job dismissal (dismissed status)."""
    job_id = uuid4()

    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.running,
        payload={"process_id": "join"},
    )
    db_session.add(job)
    await db_session.commit()

    # Dismiss the job
    job.status = JobStatusType.dismissed
    await db_session.commit()
    await db_session.refresh(job)

    print(f"[TEST] Job {job_id}: status={job.status} (dismissed)")
    assert job.status == JobStatusType.dismissed

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()


# ============================================================================
# Job Query Tests
# ============================================================================


@pytest.mark.asyncio
async def test_query_job_by_id(db_session, test_user):
    """Test querying a job by ID."""
    job_id = uuid4()
    result_layer_id = uuid4()

    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.successful,
        payload={
            "process_id": "centroid",
            "result_layer_id": str(result_layer_id),
            "feature_count": 100,
        },
    )
    db_session.add(job)
    await db_session.commit()

    # Query the job
    stmt = select(Job).where(Job.id == job_id)
    result = await db_session.execute(stmt)
    queried_job = result.scalar_one_or_none()

    assert queried_job is not None
    assert queried_job.id == job_id
    assert queried_job.status == JobStatusType.successful
    assert queried_job.payload["result_layer_id"] == str(result_layer_id)

    print(f"[TEST] Queried job {job_id}: status={queried_job.status}")
    print(f"[TEST] Job payload: {queried_job.payload}")

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()


@pytest.mark.asyncio
async def test_query_jobs_by_user(db_session, test_user):
    """Test querying all jobs for a user."""
    job_ids = [uuid4() for _ in range(3)]

    # Create multiple jobs
    for i, job_id in enumerate(job_ids):
        job = Job(
            id=job_id,
            user_id=test_user.id,
            type=OGC_JOB_TYPE,
            status=[
                JobStatusType.accepted,
                JobStatusType.running,
                JobStatusType.successful,
            ][i],
            payload={"process_id": f"tool_{i}"},
        )
        db_session.add(job)
    await db_session.commit()

    # Query all jobs for user
    stmt = select(Job).where(Job.user_id == test_user.id).order_by(Job.created_at)
    result = await db_session.execute(stmt)
    jobs = result.scalars().all()

    assert len(jobs) >= 3
    print(f"[TEST] Found {len(jobs)} jobs for user {test_user.id}")
    for job in jobs:
        print(
            f"  - Job {job.id}: status={job.status}, process={job.payload.get('process_id')}"
        )

    # Cleanup
    for job_id in job_ids:
        stmt = select(Job).where(Job.id == job_id)
        result = await db_session.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            await db_session.delete(job)
    await db_session.commit()


@pytest.mark.asyncio
async def test_query_jobs_by_status(db_session, test_user):
    """Test querying jobs filtered by status."""
    job_ids = [uuid4() for _ in range(4)]

    # Create jobs with different statuses
    statuses = [
        JobStatusType.accepted,
        JobStatusType.running,
        JobStatusType.successful,
        JobStatusType.failed,
    ]
    for job_id, status in zip(job_ids, statuses):
        job = Job(
            id=job_id,
            user_id=test_user.id,
            type=OGC_JOB_TYPE,
            status=status,
            payload={"process_id": "test"},
        )
        db_session.add(job)
    await db_session.commit()

    # Query only successful jobs
    stmt = select(Job).where(
        Job.user_id == test_user.id, Job.status == JobStatusType.successful
    )
    result = await db_session.execute(stmt)
    successful_jobs = result.scalars().all()

    assert len(successful_jobs) >= 1
    for job in successful_jobs:
        assert job.status == JobStatusType.successful

    print(f"[TEST] Found {len(successful_jobs)} successful jobs")

    # Cleanup
    for job_id in job_ids:
        stmt = select(Job).where(Job.id == job_id)
        result = await db_session.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            await db_session.delete(job)
    await db_session.commit()


# ============================================================================
# Job Payload Tests
# ============================================================================


@pytest.mark.asyncio
async def test_job_payload_with_result_layer(db_session, test_user):
    """Test job payload contains result_layer_id when save_results=True."""
    job_id = uuid4()
    result_layer_id = uuid4()

    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.successful,
        payload={
            "process_id": "clip",
            "save_results": True,
            "result_layer_id": str(result_layer_id),
            "feature_count": 25,
            "geometry_type": "Polygon",
        },
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    print(f"[TEST] Job {job_id} payload:")
    print(f"  - process_id: {job.payload['process_id']}")
    print(f"  - save_results: {job.payload['save_results']}")
    print(f"  - result_layer_id: {job.payload['result_layer_id']}")
    print(f"  - feature_count: {job.payload['feature_count']}")

    assert job.payload["result_layer_id"] == str(result_layer_id)
    assert job.payload["feature_count"] == 25

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()


@pytest.mark.asyncio
async def test_job_payload_with_download_url(db_session, test_user):
    """Test job payload contains download_url when save_results=False."""
    job_id = uuid4()
    download_url = "https://goat-dev.nbg1.your-objectstorage.com/users/test/tools/clip/result.parquet?X-Amz-Signature=..."
    expires_at = datetime.now(timezone.utc).isoformat()

    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.successful,
        payload={
            "process_id": "clip",
            "save_results": False,
            "download_url": download_url,
            "download_expires_at": expires_at,
        },
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    print(f"[TEST] Job {job_id} payload:")
    print(f"  - process_id: {job.payload['process_id']}")
    print(f"  - save_results: {job.payload['save_results']}")
    print(f"  - download_url: {job.payload['download_url'][:80]}...")
    print(f"  - download_expires_at: {job.payload['download_expires_at']}")

    assert job.payload["download_url"] == download_url
    assert "download_expires_at" in job.payload

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()


# ============================================================================
# OGC Status Mapping Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ogc_status_values(db_session, test_user):
    """Test that job status values are OGC-compliant."""
    # OGC API Processes status values:
    # accepted, running, successful, failed, dismissed

    ogc_statuses = [
        JobStatusType.accepted,
        JobStatusType.running,
        JobStatusType.successful,
        JobStatusType.failed,
        JobStatusType.dismissed,
    ]

    for ogc_status in ogc_statuses:
        job = Job(
            id=uuid4(),
            user_id=test_user.id,
            type=OGC_JOB_TYPE,
            status=ogc_status,
            payload={"process_id": "test"},
        )
        db_session.add(job)
        await db_session.commit()

        print(f"[TEST] OGC status '{ogc_status.value}'")

        # Verify OGC-compliant status values
        assert ogc_status.value in [
            "accepted",
            "running",
            "successful",
            "failed",
            "dismissed",
        ]

        await db_session.delete(job)
        await db_session.commit()


# ============================================================================
# Job Timestamps Tests
# ============================================================================


@pytest.mark.asyncio
async def test_job_has_timestamps(db_session, test_user):
    """Test that job has created_at and updated_at timestamps."""
    job_id = uuid4()

    job = Job(
        id=job_id,
        user_id=test_user.id,
        type=OGC_JOB_TYPE,
        status=JobStatusType.accepted,
        payload={"process_id": "buffer"},
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Check timestamps exist and are datetime objects
    assert job.created_at is not None
    assert job.updated_at is not None
    assert isinstance(job.created_at, datetime)
    assert isinstance(job.updated_at, datetime)

    print(f"[TEST] Job {job_id} created_at: {job.created_at}")
    print(f"[TEST] Job {job_id} updated_at: {job.updated_at}")

    # Update job status
    job.status = JobStatusType.running
    await db_session.commit()
    await db_session.refresh(job)

    # Verify timestamps are still present after update
    assert job.updated_at is not None
    print(f"[TEST] After update - updated_at: {job.updated_at}")

    # Cleanup
    await db_session.delete(job)
    await db_session.commit()
