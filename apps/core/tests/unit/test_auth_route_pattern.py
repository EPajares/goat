import pytest
from core.deps.auth import route_pattern
from fastapi import APIRouter, FastAPI, Request
from fastapi.testclient import TestClient

captured: dict[str, str] = {}


def _client() -> TestClient:
    sub = APIRouter()

    @sub.get("/summary")
    def summary(request: Request) -> dict:
        captured["pattern"] = route_pattern(request)
        return {}

    @sub.get("/{project_id}/layer")
    def layer(request: Request, project_id: str) -> dict:
        captured["pattern"] = route_pattern(request)
        return {}

    @sub.get("/{project_id}/layer/{layer_id}")
    def layer_detail(request: Request, project_id: str, layer_id: str) -> dict:
        captured["pattern"] = route_pattern(request)
        return {}

    api = APIRouter()
    api.include_router(sub, prefix="/project")
    app = FastAPI()
    app.include_router(api, prefix="/api/v2")
    return TestClient(app)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/api/v2/project/summary", "/api/v2/project/summary"),
        ("/api/v2/project/abc123/layer", "/api/v2/project/{project_id}/layer"),
        (
            "/api/v2/project/abc/layer/9",
            "/api/v2/project/{project_id}/layer/{layer_id}",
        ),
    ],
)
def test_route_pattern_includes_router_prefixes(url: str, expected: str) -> None:
    """starlette 1.x keeps included routers nested: scope["route"].path no
    longer carries the include_router prefixes. The authz resource lookup
    matches on the FULL pattern, so route_pattern must rebuild it."""
    _client().get(url)
    assert captured["pattern"] == expected


@pytest.mark.unit
@pytest.mark.parametrize("value", ["project", "layer", "api", "v2", "summary"])
def test_route_pattern_ignores_user_controlled_values(value: str) -> None:
    """A path-param value equal to a static segment must not rewrite the
    pattern. The pattern decides which authz resource is checked, so a
    user-influenced pattern would be an authorization bypass primitive."""
    _client().get(f"/api/v2/project/{value}/layer")
    assert captured["pattern"] == "/api/v2/project/{project_id}/layer"


@pytest.mark.unit
def test_route_pattern_raises_when_route_longer_than_path() -> None:
    """Unalignable input must raise so the caller denies: _validate_authorization
    turns any exception into 401, so failing loudly here fails closed."""

    class FakeRoute:
        path = "/a/b/c/d"

    request = Request({"type": "http", "path": "/x", "route": FakeRoute()})
    with pytest.raises(ValueError):
        route_pattern(request)
