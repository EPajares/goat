"""
OGC Job List Endpoint.

Returns list of jobs from GOAT Core jobs table.
GET /jobs

Follows OGC API - Processes - Part 1: Core standard.
"""

import os
import sys
from typing import Any, Dict

sys.path.insert(0, "/app/apps/processes/src")
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path

config = {
    "name": "OGCJobList",
    "type": "api",
    "description": "List jobs (OGC API Processes)",
    "path": "/jobs",
    "method": "GET",
    "emits": [],
    "flows": ["analysis-flow"],
}


async def handler(req: Dict[str, Any], context):
    """
    List jobs from GOAT Core.

    Returns OGC JobList format.

    Query parameters (OGC standard):
    - type: Filter by process ID (tool name)
    - status: Filter by job status (accepted, running, successful, failed, dismissed)
    - limit: Maximum number of jobs to return (default 10, max 100)
    - offset: Number of jobs to skip for pagination

    Query parameters (GOAT extensions):
    - user_id: Filter by user UUID
    """
    # Build base URL from request headers
    default_host = os.environ.get("PROCESSES_HOST", "localhost")
    default_port = os.environ.get("PROCESSES_PORT", "8200")
    default_host_port = f"{default_host}:{default_port}"
    proto = req.get("headers", {}).get("x-forwarded-proto", "http")
    host = req.get("headers", {}).get("host", default_host_port)
    base_url = f"{proto}://{host}"

    # Get query parameters
    query_params = req.get("queryParams", {})
    process_type = query_params.get("type")
    status_filter = query_params.get("status")
    user_id = query_params.get("user_id")

    # Handle limit
    try:
        limit = min(int(query_params.get("limit", 10)), 100)
    except (ValueError, TypeError):
        limit = 10

    # Handle offset
    try:
        offset = int(query_params.get("offset", 0))
    except (ValueError, TypeError):
        offset = 0

    context.logger.info("OGC Job list requested", {
        "type": process_type,
        "status": status_filter,
        "limit": limit,
        "offset": offset,
    })

    try:
        # Import components
        import core._dotenv  # noqa

        from core.core.config import settings
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        # Create async engine and session
        engine = create_async_engine(settings.ASYNC_SQLALCHEMY_DATABASE_URI, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # Map OGC status to GOAT Core status for filtering
        ogc_to_core_status = {
            "accepted": "pending",
            "running": "running",
            "successful": "finished",
            "failed": "failed",
            "dismissed": "killed",
        }

        # Map GOAT Core status to OGC status for response
        core_to_ogc_status = {
            "pending": "accepted",
            "running": "running",
            "finished": "successful",
            "failed": "failed",
            "timeout": "failed",
            "killed": "dismissed",
        }

        async with async_session() as session:
            # Build SQL query with filters
            # Note: Using status_simple column (TEXT) not status (JSONB)
            where_clauses = []
            params = {"limit": limit, "offset": offset}

            if process_type:
                where_clauses.append("type = :process_type")
                params["process_type"] = process_type

            if status_filter:
                core_status = ogc_to_core_status.get(status_filter)
                if core_status:
                    where_clauses.append("status_simple = :status")
                    params["status"] = core_status

            if user_id:
                where_clauses.append("user_id = :user_id::uuid")
                params["user_id"] = user_id

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            # Get total count
            count_query = text(f"SELECT COUNT(*) FROM customer.job {where_sql}")
            count_result = await session.execute(count_query, params)
            total_count = count_result.scalar() or 0

            # Get jobs
            query = text(f"""
                SELECT id, user_id, type, status_simple, payload, created_at, updated_at
                FROM customer.job
                {where_sql}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await session.execute(query, params)
            rows = result.fetchall()

            # Build job list
            job_list = []
            for row in rows:
                job_id, row_user_id, job_type, status_simple, payload, created_at, updated_at = row
                ogc_status = core_to_ogc_status.get(status_simple, "failed")

                job_info = {
                    "processID": job_type,
                    "type": "process",
                    "jobID": str(job_id),
                    "status": ogc_status,
                    "created": created_at.isoformat() if created_at else None,
                    "updated": updated_at.isoformat() if updated_at else None,
                    "links": [
                        {
                            "href": f"{base_url}/jobs/{job_id}",
                            "rel": "self",
                            "type": "application/json",
                        },
                    ],
                }

                # Add results link if successful
                if ogc_status == "successful":
                    job_info["links"].append(
                        {
                            "href": f"{base_url}/jobs/{job_id}/results",
                            "rel": "http://www.opengis.net/def/rel/ogc/1.0/results",
                            "type": "application/json",
                        }
                    )

                # Add message if there's an error
                if payload and payload.get("error_message"):
                    job_info["message"] = payload["error_message"]

                job_list.append(job_info)

            # Build pagination links
            links = [
                {
                    "href": f"{base_url}/jobs?limit={limit}&offset={offset}",
                    "rel": "self",
                    "type": "application/json",
                }
            ]

            if offset + limit < total_count:
                links.append(
                    {
                        "href": f"{base_url}/jobs?limit={limit}&offset={offset + limit}",
                        "rel": "next",
                        "type": "application/json",
                    }
                )

            if offset > 0:
                prev_offset = max(0, offset - limit)
                links.append(
                    {
                        "href": f"{base_url}/jobs?limit={limit}&offset={prev_offset}",
                        "rel": "prev",
                        "type": "application/json",
                    }
                )

            response = {
                "jobs": job_list,
                "links": links,
                "numberMatched": total_count,
                "numberReturned": len(job_list),
            }

        await engine.dispose()

        return {"status": 200, "body": response}

    except Exception as e:
        context.logger.error(f"Failed to list jobs: {e}")
        return {
            "status": 500,
            "body": {
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/ServerError",
                "title": "Internal server error",
                "status": 500,
                "detail": str(e),
            },
        }
