import logging
from typing import Any, Dict

from core.core.config import settings
from core.endpoints.deps import get_current_token_claims, get_db
from fastapi import Depends, HTTPException, Request, status
from goatlib.auth import JOSEError, KeycloakAuth
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Initialize Keycloak auth using goatlib
_keycloak_auth = KeycloakAuth(
    keycloak_url=settings.KEYCLOAK_SERVER_URL or "",
    realm=settings.REALM_NAME,
    verify_signature=settings.AUTH,
)

# Legacy alias for backward compatibility
auth_key = _keycloak_auth.public_key
ISSUER_URL = _keycloak_auth.issuer_url


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes a JWT token.
    """
    return _keycloak_auth.decode_token(token)


def auth(request: Request) -> str:
    """Raw bearer token for the request, for forwarding to other services.

    Signature-verified when AUTH is enabled; with AUTH disabled the provided
    bearer token (or the sample token) is used unverified, matching the other
    dev-mode dependencies.
    """
    authorization = request.headers.get("Authorization")
    if not settings.AUTH:
        # No verification in dev mode; downstream services running with
        # AUTH=False ignore the forwarded token.
        return authorization.partition(" ")[2] if authorization else ""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    token = authorization.partition(" ")[2]
    try:
        decode_token(token)
    except JOSEError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return token


def user_token(request: Request) -> Dict[str, Any]:
    """JWT claims for the request.

    Signature-verified when AUTH is enabled; with AUTH disabled the provided
    bearer token (or the sample token) is used unverified, matching the other
    dev-mode dependencies.
    """
    return get_current_token_claims(request)


def is_superuser(
    user_token: Dict[str, Any] = Depends(user_token), throw_error: bool = True
) -> bool:
    is_superuser = False
    if user_token.get("realm_access", {}).get("roles"):
        is_superuser = "superuser" in user_token["realm_access"]["roles"]

    if not is_superuser and throw_error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    return is_superuser


def clean_path(path: str) -> str:
    return path.replace(settings.API_V2_STR + "/", "")


def route_pattern(request: Request) -> str:
    """Full matched route pattern including all router prefixes.

    starlette 1.x keeps included routers nested, so ``scope["route"].path``
    only holds the sub-route's own path ("/profile" instead of
    "/api/v2/users/profile"), which breaks the authz resource lookup.

    The full pattern is the route's own path spliced onto the *literal* prefix
    segments of the concrete request path. Prefix segments are copied verbatim
    and the placeholder part comes from the route itself, so nothing here
    depends on user-controlled values: a param whose value happens to equal a
    static segment name ("…/project/project/layer") cannot rewrite the pattern.

    Raises:
        ValueError: if the route path cannot be aligned with the request path
            (e.g. a ``:path`` converter spanning several segments). Callers
            must treat that as authorization failure — never as a pass.
    """
    route = request.scope.get("route")
    route_path: str = getattr(route, "path", "") or ""
    path: str = request.scope["path"]

    suffix = route_path.strip("/").split("/") if route_path.strip("/") else []
    segments = path.strip("/").split("/") if path.strip("/") else []
    if len(suffix) > len(segments):
        raise ValueError(
            f"route path {route_path!r} does not fit request path {path!r}"
        )

    prefix = segments[: len(segments) - len(suffix)]
    return "/" + "/".join([*prefix, *suffix])


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
                    route_pattern(request)
                )  # e.g /organizations/{organization_id}
                # Bind all user-controlled values as parameters — never
                # f-string-interpolate them (SQL injection). The schema is a
                # trusted config identifier (cannot be a bind param). user_id is
                # cast to uuid to match the function signature.
                authz_query = text(
                    f"SELECT * FROM {settings.SCHEMA}.authorization("
                    "CAST(:user_id AS uuid), :requested_resource, "
                    ":requested_path, :requested_method)"
                )
                response = await async_session.execute(
                    authz_query,
                    {
                        "user_id": user_id,
                        "requested_resource": cleaned_route_path,
                        "requested_path": cleaned_path,
                        "requested_method": method,
                    },
                )
                state = response.scalars().all()
                if not state or not len(state) or state[0] is False:
                    raise ValueError("Unauthorized")
                return True
            else:
                raise ValueError("Missing path, route, or method in request scope")
        except HTTPException:
            raise
        except Exception:
            # Don't leak the internal error (e.g. DB messages) to the client.
            logger.warning("authorization check failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )

    return True


async def auth_z(
    request: Request,
    async_session: AsyncSession = Depends(get_db),
) -> bool:
    """
    Authorization function to check if the user has access to the requested resource.
    """
    try:
        if settings.AUTH is False:
            return True
        token = request.headers.get("Authorization")
        if token:
            token = token.split(" ")[1]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization token",
            )
        user_token = decode_token(token)
        await _validate_authorization(request, user_token, async_session)
    except HTTPException:
        raise
    except Exception:
        # Don't leak the internal error (token/decode/DB details) to the client.
        logger.warning("authorization failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    return True
