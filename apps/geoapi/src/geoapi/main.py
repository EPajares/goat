"""GOAT GeoAPI - OGC Features, Tiles, and Processes API.

A clean FastAPI implementation for serving vector tiles, features,
and analytical processes from DuckLake/DuckDB storage.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse

from geoapi.config import settings
from geoapi.ducklake import ducklake_manager
from geoapi.ducklake_pool import ducklake_pool
from geoapi.models import HealthCheck
from geoapi.routers import (
    features_router,
    metadata_router,
    processes_router,
    tiles_router,
)
from geoapi.services.layer_service import layer_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeouts based on endpoint type."""

    async def dispatch(self, request: Request, call_next):
        """Process request with timeout based on path."""
        # Determine timeout based on endpoint
        path = request.url.path

        if "/tiles/" in path:
            timeout = settings.TILE_TIMEOUT
        elif "/items" in path or "/features" in path:
            timeout = settings.FEATURE_TIMEOUT
        elif "/processes/" in path:
            timeout = settings.PROCESS_TIMEOUT
        else:
            timeout = settings.REQUEST_TIMEOUT

        try:
            response = await asyncio.wait_for(call_next(request), timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.error(f"Request timeout ({timeout}s) exceeded for {path}")
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "message": f"Request exceeded {timeout} second timeout",
                    "path": path,
                },
            )


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

    Initializes DuckLake connection and layer service on startup,
    cleans up on shutdown.
    """
    logger.info("Starting GeoAPI...")

    # Initialize DuckLake connection pool for tiles (4 concurrent connections)
    ducklake_pool.init()

    # Initialize single DuckLake connection for features/other queries
    ducklake_manager.init(settings)

    # Initialize layer service (PostgreSQL pool for metadata)
    await layer_service.init()

    logger.info("GeoAPI started successfully")

    yield

    # Cleanup
    logger.info("Shutting down GeoAPI...")
    await layer_service.close()
    ducklake_pool.close()
    ducklake_manager.close()
    logger.info("GeoAPI shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="OGC Features, Tiles, and Processes API for GOAT layers, powered by DuckDB/DuckLake",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)


# Add timeout middleware (first, so it wraps all other middleware)
app.add_middleware(TimeoutMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Include routers
app.include_router(metadata_router)
app.include_router(features_router)
app.include_router(tiles_router)
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
