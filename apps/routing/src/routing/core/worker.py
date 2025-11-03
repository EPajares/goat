import asyncio
from typing import Any

import routing._dotenv  # noqa: E402, F401, I001
import sentry_sdk
from celery import Celery, signals
from redis import Redis
from routing.core.config import settings
from routing.crud.crud_catchment_area import CRUDCatchmentArea  # type: ignore
from routing.db.session import async_session

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL)
redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)
crud_catchment_area = CRUDCatchmentArea(async_session(), redis)


@signals.celeryd_init.connect  # type: ignore
def init_sentry(**_kwargs: dict[str, Any]) -> None:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "prod" else 0.1,
    )


@celery_app.task  # type: ignore
def run_catchment_area(params: Any) -> str:
    loop = asyncio.get_event_loop()
    coroutine = crud_catchment_area.run(params)
    loop.run_until_complete(coroutine)
    return "OK"
