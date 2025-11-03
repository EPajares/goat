import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

import core._dotenv  # noqa: E402, F401, I001
from core.core.config import settings
from core.db.session import session_manager
from core.endpoints.deps import (
    close_http_client,
    close_qgis_application,
    initialize_qgis_application,
)
from core.endpoints.v2.api import router as api_router_v2

if settings.SENTRY_DSN and settings.ENVIRONMENT:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "prod" else 0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Starting up...")
    session_manager.init(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    qgis_application = initialize_qgis_application()
    yield
    print("Shutting down...")
    await session_manager.close()
    await close_http_client()
    close_qgis_application(qgis_application)


app = FastAPI(
    title=settings.PROJECT_NAME,
    redoc_url="/api/redoc",
    openapi_url=f"{settings.API_V2_STR}/openapi.json",
    lifespan=lifespan,
)


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )

static_path = Path(__file__).resolve().parent.parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/api/docs", include_in_schema=False)
async def swagger_ui_html() -> HTMLResponse:
    return get_swagger_ui_html(
        swagger_favicon_url="/static/api_favicon.png",
        openapi_url=f"{settings.API_V2_STR}/openapi.json",
        title=settings.PROJECT_NAME,
        swagger_ui_parameters={"persistAuthorization": True},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/healthz", description="Health Check", tags=["Health Check"])
def ping() -> dict[str, str]:
    """Health check."""
    return {"ping": "pong!"}


app.include_router(api_router_v2, prefix=settings.API_V2_STR)


@app.exception_handler(IntegrityError)
async def item_already_exists_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "message": "object with a unique field already exists.",
            "detail": str(exc.__dict__.get("orig")),
        },
    )


# Create data folder in case it does not exist
if not os.path.exists(settings.DATA_DIR):
    os.makedirs(settings.DATA_DIR)
