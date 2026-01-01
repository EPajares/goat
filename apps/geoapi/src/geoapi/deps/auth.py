"""Authentication dependencies for GeoAPI.

Provides JWT token validation and user extraction from Keycloak tokens.
"""

import logging
from typing import Any
from uuid import UUID

import requests
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JOSEError, jwt

from geoapi.config import settings

logger = logging.getLogger(__name__)

# Keycloak public key for JWT verification
_auth_key: str | None = None

try:
    ISSUER_URL = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.REALM_NAME}"
    _auth_server_public_key = (
        requests.get(ISSUER_URL, timeout=10).json().get("public_key")
    )
    _auth_key = (
        "-----BEGIN PUBLIC KEY-----\n"
        + _auth_server_public_key
        + "\n-----END PUBLIC KEY-----"
    )
    logger.info("Successfully loaded Keycloak public key")
except Exception as e:
    logger.warning(f"Error getting public key from Keycloak: {e}")
    ISSUER_URL = ""

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    auto_error=False,  # Don't auto-error, we handle it manually
)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JOSEError: If token is invalid
    """
    return jwt.decode(
        token,
        key=_auth_key,
        options={
            "verify_signature": settings.AUTH,
            "verify_aud": False,
            "verify_iss": ISSUER_URL if settings.AUTH else False,
        },
    )


async def get_user_token(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """Get and validate user token from request.

    Args:
        request: FastAPI request
        token: OAuth2 token from header

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If auth is enabled and token is missing/invalid
    """
    # If auth is disabled, return a mock token
    if not settings.AUTH:
        return {
            "sub": "00000000-0000-0000-0000-000000000000",
            "preferred_username": "dev_user",
            "email": "dev@example.com",
        }

    # Try to get token from header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_token(token)
    except JOSEError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_id(
    user_token: dict[str, Any] = Depends(get_user_token),
) -> UUID:
    """Extract user ID from token.

    Args:
        user_token: Decoded JWT token

    Returns:
        User UUID from token's 'sub' claim

    Raises:
        HTTPException: If user ID is missing or invalid
    """
    try:
        user_id = user_token.get("sub")
        if not user_id:
            raise ValueError("Missing 'sub' claim in token")
        return UUID(user_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID in token: {e}",
        )


async def get_optional_user_id(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> UUID | None:
    """Get user ID if token is present, otherwise return None.

    Useful for endpoints that work with or without authentication.

    Args:
        request: FastAPI request
        token: OAuth2 token from header

    Returns:
        User UUID or None if no valid token
    """
    if not settings.AUTH:
        return UUID("00000000-0000-0000-0000-000000000000")

    # Try to get token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        return None

    try:
        user_token = decode_token(token)
        user_id = user_token.get("sub")
        return UUID(user_id) if user_id else None
    except (JOSEError, ValueError, TypeError):
        return None
