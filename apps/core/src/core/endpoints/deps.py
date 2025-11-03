from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Path, Request, status
from httpx import AsyncClient, Timeout
from jose import jwt
from pydantic import UUID4
from qgis.core import QgsApplication
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.crud.crud_scenario import scenario as crud_scenario
from core.db.models.scenario import Scenario
from core.db.session import session_manager

http_client: Optional[AsyncClient] = None


async def get_db() -> Generator:  # type: ignore
    async with session_manager.session() as session:
        yield session


def get_user_id(request: Request) -> UUID:
    """Get the user ID from the JWT token or use the pre-defined user_id if running without authentication."""
    # Check if the request has an Authorization header
    authorization = request.headers.get("Authorization")

    if authorization:
        # Split the Authorization header into the scheme and the token
        scheme, _, token = authorization.partition(" ")

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization Scheme")
        if not token:
            raise HTTPException(status_code=401, detail="Missing Authorization Token")

        # Decode the JWT token and extract the user_id
        result = jwt.get_unverified_claims(token)["sub"]
    else:
        # This is returned if there is no Authorization header and therefore no authentication.
        scheme, _, token = settings.SAMPLE_AUTHORIZATION.partition(" ")
        result = jwt.get_unverified_claims(token)["sub"]

    return UUID(result)


async def get_scenario(
    project_id: UUID4 = Path(
        ...,
        description="The ID of the project",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    scenario_id: UUID4 = Path(
        ...,
        description="The ID of the scenario",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    async_session: AsyncSession = Depends(get_db),
) -> Scenario:
    """Get a scenario by its ID and project ID."""

    scenario = await crud_scenario.get_by_multi_keys(
        async_session, keys={"project_id": project_id, "id": scenario_id}
    )
    if len(scenario) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found"
        )
    return scenario[0]


def get_http_client() -> AsyncClient:
    """Returns an asynchronous HTTP client, typically used for connecting to the GOAT Routing service."""

    global http_client
    if http_client is None:
        http_client = AsyncClient(
            timeout=Timeout(
                settings.ASYNC_CLIENT_DEFAULT_TIMEOUT,
                read=settings.ASYNC_CLIENT_READ_TIMEOUT,
            )
        )
    return http_client


async def close_http_client() -> None:
    """Clean-up network resources used by the HTTP client."""

    global http_client
    if http_client is not None:
        await http_client.aclose()
        http_client = None


def initialize_qgis_application() -> QgsApplication:
    """Initialize QGIS session and resources."""

    QgsApplication.setPrefixPath("/usr", True)
    application = QgsApplication([], False)
    application.initQgis()
    return application


def close_qgis_application(application: QgsApplication) -> None:
    """Terminate QGIS session and clean-up resources."""

    application.exitQgis()
    QgsApplication.exit()
