"""
---------------------------------------------------------------------------------
This code is based on or incorporates material from the project:
https://github.com/developmentseed/tipg

The original code/repository is licensed under MIT License.
---------------------------------------------------------------------------------
"""
import os  # noqa: I001
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

import sentry_sdk

# Monkey patch filter query here because it needs to be patched before used by import down
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware
from tipg import __version__ as tipg_version
from tipg import collections, dependencies
from tipg.database import close_db_connection, connect_to_db

from tipg.filter.filters import Operator
from tipg.middleware import CacheControlMiddleware
from tipg.settings import (
    APISettings,
    CustomSQLSettings,
    DatabaseSettings,
    MVTSettings,
)

import geoapi._dotenv  # noqa: E402, F401, I001

from .exts import (
    ExtCollection,
    filter_query,
)

dependencies.filter_query = filter_query  # type: ignore
collections.Collection = ExtCollection  # type: ignore
from .catalog import LayerCatalog, postgres_settings  # noqa: E402, I001
from tipg.factory import Endpoints # noqa: E402

from .exts import (  # noqa: E402
    Operator as OperatorPatch,
)



mvt_settings = MVTSettings()
mvt_settings.max_features_per_tile = 20000
settings = APISettings()
db_settings = DatabaseSettings()
custom_sql_settings = CustomSQLSettings()

if os.getenv("SENTRY_DSN") and os.getenv("ENVIRONMENT"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("ENVIRONMENT"),
        traces_sample_rate=1.0 if os.getenv("ENVIRONMENT") == "prod" else 0.1,
    )

# Monkey patch the function that need modification
Operator.OPERATORS = OperatorPatch.OPERATORS


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI Lifespan."""
    # Create Connection Pool
    await connect_to_db(
        app,
        settings=postgres_settings,
        schemas=db_settings.schemas,
        user_sql_files=custom_sql_settings.sql_files,
    )
    # Init Layer Catalog
    layer_catalog = LayerCatalog(app=app)
    await layer_catalog.start()
    yield
    await layer_catalog.stop()
    await close_db_connection(app)


# Create FastAPI app
app = FastAPI(
    title=settings.name,
    version=tipg_version,
    openapi_url="/api",
    docs_url="/api.html",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

# Create Endpoints
ogc_api = Endpoints(
    title=settings.name,
    with_tiles_viewer=settings.add_tiles_viewer,
)
# Remove the list all collections endpoint
# ogc_api.router.routes = ogc_api.router.routes[1:]
ogc_api.router.routes = [
    route
    for route in ogc_api.router.routes
    if route.name != "collections"  # type: ignore
]
app.include_router(ogc_api.router)
app.add_middleware(CacheControlMiddleware, cachecontrol=settings.cachecontrol)
app.add_middleware(CompressionMiddleware)


@app.get(
    "/healthz",
    description="Health Check.",
    summary="Health Check.",
    operation_id="healthCheck",
    tags=["Health Check"],
)
async def ping() -> Dict[str, str]:
    """Health check."""
    return {"ping": "pongpong!"}
