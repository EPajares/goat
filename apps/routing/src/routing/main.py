import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware

import routing._dotenv  # noqa: E402, F401, I001
from routing.core.config import settings
from routing.endpoints.v2.api import router as api_router_v2

if settings.SENTRY_DSN and settings.ENVIRONMENT:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "prod" else 0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Starting up...")
    logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    redoc_url="/api/redoc",
    openapi_url=f"{settings.API_V2_STR}/openapi.json",
    lifespan=lifespan,
)


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

app.include_router(api_router_v2, prefix=settings.API_V2_STR)
