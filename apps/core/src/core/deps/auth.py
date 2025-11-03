from typing import Any, Dict

import requests
from core.core.config import settings
from core.endpoints.deps import get_db
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JOSEError, jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

auth_key = None
try:
    ISSUER_URL = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.REALM_NAME}"

    _auth_server_public_key = requests.get(ISSUER_URL).json().get("public_key")
    auth_key = (
        "-----BEGIN PUBLIC KEY-----\n"
        + _auth_server_public_key
        + "\n-----END PUBLIC KEY-----"
    )  # noqa: E501
except Exception:
    print("Error getting public key from Keycloak")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V2_STR}/auth/access-token",
)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes a JWT token.
    """
    user_token: Dict[str, Any] = jwt.decode(
        token,
        key=auth_key,
        options={
            "verify_signature": settings.AUTH,
            "verify_aud": False,
            "verify_iss": ISSUER_URL,
        },
    )

    return user_token


async def auth(token: str = Depends(oauth2_scheme)) -> str:
    try:
        decode_token(token)
    except JOSEError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return token


def user_token(token: str = Depends(auth)) -> Dict[str, Any]:
    payload = decode_token(token)
    return payload


def is_superuser(
    user_token: Dict[str, Any] = Depends(user_token), throw_error: bool = True
) -> bool:
    is_superuser = False
    if user_token["realm_access"] and user_token["realm_access"]["roles"]:
        is_superuser = "superuser" in user_token["realm_access"]["roles"]

    if not is_superuser and throw_error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    return is_superuser


def clean_path(path: str) -> str:
    return path.replace(settings.API_V2_STR + "/", "")


async def _validate_authorization(
    request: Request, user_token: Dict[str, Any], async_session: AsyncSession
) -> bool:
    if settings.AUTH is not False:
        try:
            user_id = user_token["sub"]
            path = request.scope.get("path")
            route = request.scope.get("route")
            method = request.scope.get("method")
            if path and route and method and user_id:
                cleaned_path = clean_path(
                    path
                )  # e.g /organizations/b65e040a-f8f0-453f-9888-baa2b9342cce
                cleaned_route_path = clean_path(
                    route.path
                )  # e.g /organizations/{organization_id}
                authz_query = text(
                    f"SELECT * FROM {settings.ACCOUNTS_SCHEMA}.authorization('{user_id}', '{cleaned_route_path}', '{cleaned_path}', '{method}');"
                )
                response = await async_session.execute(authz_query)
                state = response.scalars().all()
                if not state or not len(state) or state[0] is False:
                    raise ValueError("Unauthorized")
                return True
            else:
                raise ValueError("Missing path, route, or method in request scope")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return True


async def auth_z(
    request: Request,
    user_token: Dict[str, Any] = Depends(user_token),
    async_session: AsyncSession = Depends(get_db),
) -> bool:
    """
    Authorization function to check if the user has access to the requested resource.
    """
    try:
        await _validate_authorization(request, user_token, async_session)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return True


async def auth_z_lite(request: Request, async_session: AsyncSession) -> bool:
    """
    Authorization function to check if the user has access to the requested resource (without FastAPI dependencies).
    """

    try:
        token = request.headers.get("Authorization")
        if token:
            token = token.split(" ")[1]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization token",
            )
        user_token = decode_token(token)
        return await _validate_authorization(request, user_token, async_session)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
