"""GOAT GeoAPI - OGC Features, Tiles, and Processes API.

A clean FastAPI implementation for serving vector tiles, features,
and analytical processes from DuckLake/DuckDB storage.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from geoapi.config import settings
from geoapi.ducklake import ducklake_manager
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

    # Initialize DuckLake connection pool (creates all connections upfront)
    ducklake_manager.init(settings)

    # Initialize layer service (PostgreSQL pool for metadata)
    await layer_service.init()

    logger.info("GeoAPI started successfully")

    yield

    # Cleanup
    logger.info("Shutting down GeoAPI...")
    await layer_service.close()
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
