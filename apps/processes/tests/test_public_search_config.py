"""Tests for public search config parsing."""

import uuid

import duckdb
import pytest

from processes.services import public_search_config as psc
from processes.services.public_search_config import (
    get_public_search_layers,
    parse_search_config,
)


@pytest.fixture(autouse=True)
def _reset_module_state():
    psc._cache.clear()
    psc._con = None
    yield
    psc._cache.clear()
    psc._con = None


def _snapshot(search: dict | None, layers: list[dict]) -> dict:
    settings: dict = {"map_view": {}}
    if search is not None:
        settings["search"] = search
    return {
        "project": {"builder_config": {"settings": settings}},
        "layers": layers,
    }


def test_resolves_layer_project_ids_to_layer_uuids() -> None:
    config = _snapshot(
        {
            "places": True,
            "layers": [
                {"layer_project_id": 7, "columns": ["name"], "label_column": "name"},
            ],
        },
        [{"id": 7, "layer_id": "aaaa-bbbb"}],
    )
    specs = parse_search_config(config)
    assert len(specs) == 1
    assert specs[0]["layer_id"] == "aaaa-bbbb"
    assert specs[0]["columns"] == ["name"]
    assert specs[0]["label_column"] == "name"
    assert specs[0]["limit"] == 5


def test_skips_entries_missing_from_snapshot_layers() -> None:
    config = _snapshot(
        {"layers": [{"layer_project_id": 99, "columns": ["name"]}]},
        [{"id": 7, "layer_id": "aaaa-bbbb"}],
    )
    assert parse_search_config(config) == []


def test_no_search_settings_returns_empty() -> None:
    assert parse_search_config(_snapshot(None, [])) == []


def test_caps_columns_at_three_and_entries_at_twenty() -> None:
    layers = [{"id": i, "layer_id": f"uuid-{i}"} for i in range(30)]
    entries = [
        {"layer_project_id": i, "columns": ["a", "b", "c", "d"]} for i in range(30)
    ]
    specs = parse_search_config(_snapshot({"layers": entries}, layers))
    assert len(specs) == 20
    assert all(len(s["columns"]) == 3 for s in specs)


def _searchable_config() -> dict:
    return _snapshot(
        {"layers": [{"layer_project_id": 1, "columns": ["name"]}]},
        [{"id": 1, "layer_id": "u-1"}],
    )


def test_invalid_uuid_raises_without_fetching(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def _fake_fetch(project_id: uuid.UUID) -> dict | None:
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(psc, "_fetch_config", _fake_fetch)

    with pytest.raises(ValueError):
        get_public_search_layers("not-a-uuid")

    assert called is False


def test_second_call_within_ttl_does_not_refetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def _fake_fetch(project_id: uuid.UUID) -> dict | None:
        nonlocal calls
        calls += 1
        return _searchable_config()

    monkeypatch.setattr(psc, "_fetch_config", _fake_fetch)
    pid = str(uuid.uuid4())

    first = get_public_search_layers(pid)
    second = get_public_search_layers(pid)

    assert calls == 1
    assert (
        first
        == second
        == [{"layer_id": "u-1", "columns": ["name"], "label_column": None, "limit": 5}]
    )


def test_call_after_ttl_expiry_refetches(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def _fake_fetch(project_id: uuid.UUID) -> dict | None:
        nonlocal calls
        calls += 1
        return _searchable_config()

    monkeypatch.setattr(psc, "_fetch_config", _fake_fetch)
    pid = str(uuid.uuid4())

    get_public_search_layers(pid)
    assert calls == 1

    key = str(uuid.UUID(pid))
    stale_ts, specs = psc._cache[key]
    psc._cache[key] = (stale_ts - psc.CONFIG_TTL_SECONDS - 1.0, specs)

    get_public_search_layers(pid)
    assert calls == 2


def test_duckdb_error_resets_connection_and_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed = False

    class _FakeCon:
        def close(self) -> None:
            nonlocal closed
            closed = True

    psc._con = _FakeCon()  # type: ignore[assignment]

    def _raise_fetch(project_id: uuid.UUID) -> dict | None:
        raise duckdb.Error("boom")

    monkeypatch.setattr(psc, "_fetch_config", _raise_fetch)
    pid = str(uuid.uuid4())

    with pytest.raises(duckdb.Error):
        get_public_search_layers(pid)

    assert psc._con is None
    assert closed is True


def test_reset_connection_survives_a_close_failure() -> None:
    class _BrokenCon:
        def close(self) -> None:
            raise duckdb.Error("already dead")

    psc._con = _BrokenCon()  # type: ignore[assignment]
    psc._reset_connection()
    assert psc._con is None


def test_cache_cap_evicts_oldest_when_full(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_fetch(project_id: uuid.UUID) -> dict | None:
        return _snapshot({"layers": []}, [])

    monkeypatch.setattr(psc, "_fetch_config", _fake_fetch)

    for _ in range(psc.CACHE_MAX + 10):
        get_public_search_layers(str(uuid.uuid4()))

    assert len(psc._cache) <= psc.CACHE_MAX
