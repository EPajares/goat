"""GOAT Processes API - OGC API Processes for GOAT analysis tools.

A dedicated FastAPI service for OGC API Processes, handling:
- Async tool execution via Windmill (buffer, clip, heatmap, etc.)
- Sync analytics queries (feature-count, class-breaks, etc.)
- Job management (status, results, cancellation)

Separated from GeoAPI to prevent long-running jobs from blocking tile requests.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from processes.config import settings
from processes.ducklake import ducklake_manager
from processes.models import HealthCheck
from processes.routers import processes_router
from processes.services.windmill_client import windmill_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Initialize Sentry if configured
if os.getenv("SENTRY_DSN") and os.getenv("ENVIRONMENT"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("ENVIRONMENT"),
        traces_sample_rate=1.0 if os.getenv("ENVIRONMENT") == "prod" else 0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Initializes DuckLake connection for analytics queries on startup,
    cleans up on shutdown.
    """
    logger.info("Starting Processes API...")

    # Initialize DuckLake connection for sync analytics queries
    ducklake_manager.init(settings)

    logger.info("Processes API started successfully")

    yield

    # Cleanup
    logger.info("Shutting down Processes API...")
    await windmill_client.close()
    ducklake_manager.close()
    logger.info("Processes API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="OGC API Processes for GOAT geospatial analysis tools",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Include routers
app.include_router(processes_router)


@app.get(
    "/healthz",
    summary="Health check",
    response_model=HealthCheck,
    tags=["Health"],
)
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    return HealthCheck(status="ok", ping="pong")
