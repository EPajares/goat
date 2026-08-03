from typing import Any
from unittest.mock import patch

import pytest
from core.deps import keycloak as keycloak_deps
from keycloak.exceptions import KeycloakAuthenticationError


class _FailingAdmin:
    def get_user(self, user_id: str) -> Any:
        raise KeycloakAuthenticationError(
            error_message=b"Client not enabled to retrieve service account",
            response_code=401,
        )


class _WorkingAdmin:
    def get_user(self, user_id: str) -> Any:
        return {"email": "user@example.com", "enabled": True}


@pytest.mark.unit
async def test_get_keycloak_user_returns_empty_when_unconfigured() -> None:
    async def admin() -> Any:
        return None

    with patch.object(keycloak_deps, "keycloak_admin", admin):
        assert await keycloak_deps.get_keycloak_user("some-id") == {}


@pytest.mark.unit
async def test_get_keycloak_user_degrades_on_keycloak_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def admin() -> Any:
        return _FailingAdmin()

    monkeypatch.setattr(keycloak_deps.settings, "AUTH", True)
    with patch.object(keycloak_deps, "keycloak_admin", admin):
        assert await keycloak_deps.get_keycloak_user("some-id") == {}


@pytest.mark.unit
async def test_keycloak_admin_is_cached_across_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(keycloak_deps.settings, "KEYCLOAK_CLIENT_ID", "test-client")
    monkeypatch.setattr(keycloak_deps.settings, "KEYCLOAK_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(keycloak_deps, "_admin", None)
    with patch.object(keycloak_deps, "KeycloakAdmin") as admin_cls:
        first = await keycloak_deps.keycloak_admin()
        second = await keycloak_deps.keycloak_admin()
    assert first is second
    assert admin_cls.call_count == 1


@pytest.mark.unit
async def test_get_keycloak_user_returns_user(monkeypatch: pytest.MonkeyPatch) -> None:
    async def admin() -> Any:
        return _WorkingAdmin()

    monkeypatch.setattr(keycloak_deps.settings, "AUTH", True)
    with patch.object(keycloak_deps, "keycloak_admin", admin):
        user = await keycloak_deps.get_keycloak_user("some-id")
        assert user["email"] == "user@example.com"


@pytest.mark.unit
async def test_get_keycloak_user_skips_lookup_when_auth_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(keycloak_deps.settings, "AUTH", False)
    called = False

    async def admin() -> Any:
        nonlocal called
        called = True
        return _WorkingAdmin()

    with patch.object(keycloak_deps, "keycloak_admin", admin):
        assert await keycloak_deps.get_keycloak_user("some-id") == {}
    assert called is False
