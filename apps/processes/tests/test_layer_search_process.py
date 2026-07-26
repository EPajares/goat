"""Tests for the layer-search process (service seams + router guards)."""

from typing import Any

import duckdb
import pytest
from fastapi.testclient import TestClient

import processes.routers.processes as processes_router
from processes.main import app
from processes.services.analytics_service import analytics_service


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_editor_mode_without_auth_is_401(client: TestClient) -> None:
    resp = client.post(
        "/processes/layer-search/execution",
        json={
            "inputs": {
                "query": "murr",
                "layers": [
                    {
                        "layer_id": "5ea130d0-df2f-4535-8796-8b866711a44a",
                        "columns": ["name"],
                    }
                ],
            }
        },
    )
    assert resp.status_code == 401


def test_public_mode_requires_project_id(client: TestClient) -> None:
    resp = client.post(
        "/processes/layer-search/execution",
        json={"inputs": {"query": "murr"}},
    )
    assert resp.status_code == 422


def test_query_too_short_is_422(client: TestClient) -> None:
    resp = client.post(
        "/processes/layer-search/execution",
        json={"inputs": {"query": "m", "project_id": "0" * 32}},
    )
    assert resp.status_code == 422


def test_public_mode_resolves_snapshot_and_searches(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from processes.services import analytics_service as analytics_service_module

    monkeypatch.setattr(
        analytics_service_module,
        "get_public_search_layers",
        lambda project_id: [
            {"layer_id": "aaaa", "columns": ["name"], "label_column": None, "limit": 5}
        ],
    )

    calls: list[dict[str, Any]] = []

    def fake_scan(self: Any, spec: dict, query: str, map_center: Any) -> dict:
        calls.append({"spec": spec, "query": query})
        return {
            "layer_id": spec["layer_id"],
            "results": [],
            "truncated": False,
            "timed_out": False,
            "error": None,
        }

    monkeypatch.setattr(type(analytics_service), "_scan_one_layer", fake_scan)
    resp = client.post(
        "/processes/layer-search/execution",
        json={
            "inputs": {
                "query": "murr",
                "project_id": "b2f29b0e-ca02-4784-8248-1428640a2535",
            }
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "groups": [
            {
                "layer_id": "aaaa",
                "results": [],
                "truncated": False,
                "timed_out": False,
                "error": None,
            }
        ]
    }
    assert calls[0]["query"] == "murr"


def test_unknown_column_maps_to_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from processes.services import analytics_service as analytics_service_module

    monkeypatch.setattr(
        analytics_service_module,
        "get_public_search_layers",
        lambda project_id: [
            {"layer_id": "aaaa", "columns": ["nope"], "label_column": None, "limit": 5}
        ],
    )

    def raise_value_error(self: Any, spec: dict, query: str, map_center: Any) -> dict:
        raise ValueError("Unknown search column")

    monkeypatch.setattr(type(analytics_service), "_scan_one_layer", raise_value_error)
    resp = client.post(
        "/processes/layer-search/execution",
        json={
            "inputs": {
                "query": "murr",
                "project_id": "b2f29b0e-ca02-4784-8248-1428640a2535",
            }
        },
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]["detail"]
    assert detail == "Unknown search column"
    # The column name must never reach an unauthenticated caller.
    assert "nope" not in detail


def test_db_outage_does_not_leak_password(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """duckdb.IOException from an unreachable Postgres can contain the full
    ATTACH connection string, including the password, in its message. This
    must never reach an unauthenticated caller.
    """
    from processes.services import analytics_service as analytics_service_module

    def _raise_with_password(project_id: str) -> list[dict[str, Any]]:
        raise duckdb.IOException(
            "IO Error: Unable to connect to Postgres at "
            "'host=db user=goat password=SECRETPW dbname=goat': "
            "connection refused"
        )

    monkeypatch.setattr(
        analytics_service_module,
        "get_public_search_layers",
        _raise_with_password,
    )

    resp = client.post(
        "/processes/layer-search/execution",
        json={
            "inputs": {
                "query": "murr",
                "project_id": "b2f29b0e-ca02-4784-8248-1428640a2535",
            }
        },
    )
    assert resp.status_code == 503
    assert "SECRETPW" not in resp.text


def test_project_id_and_layers_together_without_auth_is_401(client: TestClient) -> None:
    resp = client.post(
        "/processes/layer-search/execution",
        json={
            "inputs": {
                "query": "murr",
                "project_id": "b2f29b0e-ca02-4784-8248-1428640a2535",
                "layers": [{"layer_id": "aaaa", "columns": ["name"]}],
            }
        },
    )
    assert resp.status_code == 401


def test_whitespace_only_query_is_422(client: TestClient) -> None:
    resp = client.post(
        "/processes/layer-search/execution",
        json={"inputs": {"query": "   ", "project_id": "0" * 32}},
    )
    assert resp.status_code == 422


def test_inflight_cap_returns_429(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(processes_router, "_LAYER_SEARCH_MAX_INFLIGHT", 0)
    resp = client.post(
        "/processes/layer-search/execution",
        json={
            "inputs": {
                "query": "murr",
                "project_id": "b2f29b0e-ca02-4784-8248-1428640a2535",
            }
        },
    )
    assert resp.status_code == 429
    assert resp.headers["retry-after"] == "1"


def test_time_budget_marks_layer_timed_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(type(analytics_service), "SEARCH_TIME_BUDGET_SECONDS", -1.0)
    result = analytics_service.layer_search(
        query="murr",
        layers=[
            {"layer_id": "aaaa", "columns": ["name"], "label_column": None, "limit": 5}
        ],
    )
    assert result == {
        "groups": [
            {
                "layer_id": "aaaa",
                "results": [],
                "truncated": False,
                "timed_out": True,
                "error": None,
            }
        ]
    }


def test_per_group_error_is_generic_and_returns_200(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from processes.services import analytics_service as analytics_service_module

    monkeypatch.setattr(
        analytics_service_module,
        "get_public_search_layers",
        lambda project_id: [
            {"layer_id": "aaaa", "columns": ["name"], "label_column": None, "limit": 5}
        ],
    )

    def raise_generic(self: Any, spec: dict, query: str, map_center: Any) -> dict:
        raise Exception(
            "Catalog Error: Table with name t_deadbeefdeadbeefdeadbeefdeadbeef does not "
            "exist! Did you mean t_secretlayeruuidhere0000000000000?"
        )

    monkeypatch.setattr(type(analytics_service), "_scan_one_layer", raise_generic)
    resp = client.post(
        "/processes/layer-search/execution",
        json={
            "inputs": {
                "query": "murr",
                "project_id": "b2f29b0e-ca02-4784-8248-1428640a2535",
            }
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "groups": [
            {
                "layer_id": "aaaa",
                "results": [],
                "truncated": False,
                "timed_out": False,
                "error": "layer unavailable",
            }
        ]
    }
    assert "secretlayeruuidhere" not in resp.text
