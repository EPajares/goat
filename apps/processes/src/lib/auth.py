"""Authentication middleware for OGC API Processes.

Extracts user_id from JWT token in Authorization header.
Validates token signature against Keycloak's public key (same as Core).
"""

from typing import Any, Callable, Dict, Optional
from uuid import UUID

import requests
from jose import JOSEError, jwt
from lib.config import get_settings

# Global auth key (fetched from Keycloak at startup)
_auth_key: Optional[str] = None
_issuer_url: Optional[str] = None


def _init_auth_key() -> None:
    """Initialize auth key from Keycloak public key.

    Called lazily on first auth request.
    Skips fetching if AUTH=False (signature verification disabled).
    """
    global _auth_key, _issuer_url

    if _auth_key is not None:
        return

    settings = get_settings()
    _issuer_url = settings.KEYCLOAK_ISSUER

    # Skip fetching public key if signature verification is disabled
    if not settings.AUTH:
        _auth_key = ""  # Empty key, won't be used
        return

    try:
        response = requests.get(_issuer_url, timeout=10)
        response.raise_for_status()
        public_key = response.json().get("public_key")
        if public_key:
            _auth_key = (
                "-----BEGIN PUBLIC KEY-----\n"
                + public_key
                + "\n-----END PUBLIC KEY-----"
            )
    except Exception as e:
        print(f"Warning: Error getting public key from Keycloak: {e}")
        # Auth will still work if settings.AUTH is False


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token claims

    Raises:
        JOSEError: If token is invalid or signature verification fails
    """
    _init_auth_key()
    settings = get_settings()

    user_token: Dict[str, Any] = jwt.decode(
        token,
        key=_auth_key,
        options={
            "verify_signature": settings.AUTH,
            "verify_aud": False,
            "verify_iss": _issuer_url,
        },
    )

    return user_token


def get_access_token_from_request(req: Dict[str, Any]) -> str:
    """Extract access token from Authorization header.

    Args:
        req: Motia request dict with headers

    Returns:
        Access token string (without Bearer prefix)

    Raises:
        ValueError: If no token or invalid header format
    """
    headers = req.get("headers", {})
    authorization = headers.get("authorization")

    if not authorization:
        raise ValueError("Missing Authorization header")

    # Split the Authorization header into the scheme and the token
    parts = authorization.split(" ", 1)
    if len(parts) != 2:
        raise ValueError("Invalid Authorization header format")

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise ValueError("Invalid Authorization scheme, expected Bearer")

    if not token:
        raise ValueError("Missing Authorization token")

    return token


def get_user_id_from_request(req: Dict[str, Any]) -> UUID:
    """Extract user_id from JWT token in Authorization header.

    Args:
        req: Motia request dict with headers

    Returns:
        User UUID from JWT token

    Raises:
        ValueError: If no token or invalid token
    """
    token = get_access_token_from_request(req)

    try:
        # Decode and validate the JWT token
        claims = decode_token(token)
        user_id_str = claims.get("sub")
        if not user_id_str:
            raise ValueError("Missing 'sub' claim in token")
        return UUID(user_id_str)
    except JOSEError as e:
        raise ValueError(f"Invalid JWT token: {e}")
    except Exception as e:
        raise ValueError(f"Token validation failed: {e}")


async def auth_middleware(
    req: Dict[str, Any], ctx: Any, next_fn: Callable
) -> Dict[str, Any]:
    """Authentication middleware that extracts user_id from JWT token.

    Attaches user_id to request for use in handlers.

    Args:
        req: Motia request dict
        ctx: Motia context with logger
        next_fn: Next middleware/handler function

    Returns:
        Response dict from next handler, or 401 error
    """
    try:
        user_id = get_user_id_from_request(req)
        # Attach user_id to request for use in handlers
        req["user_id"] = user_id
        ctx.logger.debug("Authenticated user", {"user_id": str(user_id)})
        return await next_fn()
    except ValueError as e:
        ctx.logger.warn("Authentication failed", {"error": str(e)})
        return {
            "status": 401,
            "body": {
                "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": str(e),
            },
        }
