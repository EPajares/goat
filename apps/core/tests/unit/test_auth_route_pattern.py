import pytest
from core.deps.auth import route_pattern
from fastapi import APIRouter, FastAPI, Request
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_route_pattern_includes_router_prefixes() -> None:
    """starlette 1.x keeps included routers nested: scope["route"].path no
    longer carries the include_router prefixes. The authz resource lookup
    matches on the FULL pattern, so route_pattern must rebuild it."""
    captured: dict[str, str] = {}

    sub = APIRouter()

    @sub.get("/profile")
    def profile(request: Request) -> dict:
        captured["pattern"] = route_pattern(request)
        return {}

    @sub.get("/{organization_id}/members/{user_id}")
    def member(request: Request, organization_id: str, user_id: str) -> dict:
        captured["pattern"] = route_pattern(request)
        return {}

    api = APIRouter()
    api.include_router(sub, prefix="/users")
    app = FastAPI()
    app.include_router(api, prefix="/api/v2")
    client = TestClient(app)

    client.get("/api/v2/users/profile")
    assert captured["pattern"] == "/api/v2/users/profile"

    client.get("/api/v2/users/9c7f24ca-0000-0000-0000-000000000001/members/42")
    assert captured["pattern"] == "/api/v2/users/{organization_id}/members/{user_id}"
