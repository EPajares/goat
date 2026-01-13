"""Authentication dependencies for GeoAPI.

Provides JWT token validation and user extraction from Keycloak tokens.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from goatlib.auth import JOSEError, KeycloakAuth

from geoapi.config import settings

logger = logging.getLogger(__name__)

# Initialize Keycloak auth using goatlib
_keycloak_auth = KeycloakAuth(
    keycloak_url=settings.KEYCLOAK_SERVER_URL,
    realm=settings.REALM_NAME,
    verify_signature=settings.AUTH,
)

# Legacy alias for backward compatibility
_auth_key = _keycloak_auth.public_key
ISSUER_URL = _keycloak_auth.issuer_url

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
    return _keycloak_auth.decode_token(token)


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
    # Try to get token from header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    # If auth is disabled but token is provided, decode it without verification
    # This allows using real user IDs while bypassing signature validation
    if not settings.AUTH:
        if token:
            try:
                # Decode without signature verification
                return decode_token(token)
            except JOSEError as e:
                logger.warning(f"Failed to decode token in AUTH=False mode: {e}")
        # Fall back to mock user only if no token provided
        return {
            "sub": "00000000-0000-0000-0000-000000000000",
            "preferred_username": "dev_user",
            "email": "dev@example.com",
        }

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
    # if not settings.AUTH:
    #     return UUID("00000000-0000-0000-0000-000000000000")

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
