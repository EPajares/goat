"""Authentication utilities for GOAT services.

Provides shared JWT token validation and Keycloak authentication
used across core, geoapi, and processes services.
"""

import logging
from typing import Any, Protocol

import requests
from jose import JOSEError, jwt

logger = logging.getLogger(__name__)


class AuthSettings(Protocol):
    """Protocol for settings objects that configure authentication."""

    AUTH: bool
    KEYCLOAK_SERVER_URL: str
    REALM_NAME: str


class KeycloakAuth:
    """Keycloak authentication handler.

    Handles JWT token validation using Keycloak's public key.
    Supports both production (signature verification) and development
    (signature bypass) modes.

    Example:
        from goatlib.auth import KeycloakAuth

        auth = KeycloakAuth(
            keycloak_url="https://auth.example.com",
            realm="myrealm",
            verify_signature=True,
        )
        user_data = auth.decode_token(token)
    """

    def __init__(
        self: "KeycloakAuth",
        keycloak_url: str,
        realm: str,
        verify_signature: bool = True,
        timeout: int = 10,
    ) -> None:
        """Initialize Keycloak authentication.

        Args:
            keycloak_url: Base URL of Keycloak server
            realm: Keycloak realm name
            verify_signature: Whether to verify JWT signatures
            timeout: HTTP request timeout in seconds
        """
        self._verify_signature = verify_signature
        self._issuer_url = f"{keycloak_url}/realms/{realm}"
        self._public_key: str | None = None
        self._timeout = timeout

        # Fetch public key on initialization
        self._fetch_public_key()

    def _fetch_public_key(self: "KeycloakAuth") -> None:
        """Fetch Keycloak public key for JWT verification."""
        try:
            response = requests.get(self._issuer_url, timeout=self._timeout)
            response.raise_for_status()
            raw_key = response.json().get("public_key")
            if raw_key:
                self._public_key = (
                    f"-----BEGIN PUBLIC KEY-----\n{raw_key}\n-----END PUBLIC KEY-----"
                )
                logger.info("Successfully loaded Keycloak public key")
            else:
                logger.warning("No public key in Keycloak response")
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch Keycloak public key: {e}")
        except Exception as e:
            logger.warning(f"Error processing Keycloak response: {e}")

    def decode_token(self: "KeycloakAuth", token: str) -> dict[str, Any]:
        """Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload as dict

        Raises:
            JOSEError: If token is invalid or verification fails
        """
        return jwt.decode(
            token,
            key=self._public_key,
            options={
                "verify_signature": self._verify_signature,
                "verify_aud": False,
                "verify_iss": self._issuer_url if self._verify_signature else False,
            },
        )

    @property
    def issuer_url(self: "KeycloakAuth") -> str:
        """Get the Keycloak issuer URL."""
        return self._issuer_url

    @property
    def public_key(self: "KeycloakAuth") -> str | None:
        """Get the Keycloak public key (PEM format)."""
        return self._public_key

    @property
    def verify_signature(self: "KeycloakAuth") -> bool:
        """Check if signature verification is enabled."""
        return self._verify_signature


def create_keycloak_auth(settings: AuthSettings) -> KeycloakAuth:
    """Create a KeycloakAuth instance from settings.

    Convenience function that extracts settings from a Pydantic settings object.

    Args:
        settings: Settings object with AUTH, KEYCLOAK_SERVER_URL, REALM_NAME

    Returns:
        Configured KeycloakAuth instance
    """
    return KeycloakAuth(
        keycloak_url=settings.KEYCLOAK_SERVER_URL,
        realm=settings.REALM_NAME,
        verify_signature=settings.AUTH,
    )


# Re-export JOSEError for convenience
__all__ = [
    "KeycloakAuth",
    "AuthSettings",
    "create_keycloak_auth",
    "JOSEError",
]
