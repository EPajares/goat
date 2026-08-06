import logging
from typing import Any

from core.core.config import settings
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from keycloak.exceptions import KeycloakError, KeycloakGetError

logger = logging.getLogger(__name__)

_admin: KeycloakAdmin | None = None


async def keycloak_admin() -> KeycloakAdmin | None:
    """Admin client for the configured realm, authenticated as a service account
    via the client-credentials grant (least-privilege; no master-realm admin).

    Returns ``None`` when the service-account client isn't configured, so callers
    degrade gracefully (skip Keycloak enrichment / writes) instead of crashing.

    The client is created once and reused — python-keycloak obtains its token
    lazily and refreshes it when expired, so rebuilding per request would cost
    an extra token grant on every call.
    """
    global _admin
    if not (settings.KEYCLOAK_CLIENT_ID and settings.KEYCLOAK_CLIENT_SECRET):
        return None
    if _admin is None:
        connection = KeycloakOpenIDConnection(
            server_url=settings.KEYCLOAK_SERVER_URL,
            realm_name=settings.REALM_NAME,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
            verify=True,
        )
        _admin = KeycloakAdmin(connection=connection)
    return _admin


async def get_keycloak_user(user_id: str) -> dict[str, Any]:
    """User representation from Keycloak, or ``{}`` when the admin client is
    unconfigured or the lookup fails.

    Enrichment reads must never break the caller: Keycloak being unreachable,
    the client lacking service-account access, or the user missing from the
    realm all degrade to "no extra data". Writes (update/delete) intentionally
    do NOT go through this — a failed write must surface, not desync silently.
    """
    if not settings.AUTH:
        return {}
    admin = await keycloak_admin()
    if admin is None:
        return {}
    try:
        return admin.get_user(user_id) or {}
    except KeycloakGetError as e:
        if e.response_code == 404:
            logger.warning("keycloak user %s not found in realm", user_id)
        else:
            logger.warning("keycloak user lookup failed for %s", user_id, exc_info=True)
        return {}
    except KeycloakError:
        logger.warning("keycloak user lookup failed for %s", user_id, exc_info=True)
        return {}
