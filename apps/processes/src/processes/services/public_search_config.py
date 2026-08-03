"""Resolve a public dashboard's searchable-layers config from the published snapshot."""

import json
import logging
import threading
import time
import uuid
from typing import Any, TypedDict

import duckdb
from goatlib.storage import configure_baked_extensions

from processes.config import settings

logger = logging.getLogger(__name__)

CONFIG_TTL_SECONDS = 30.0
MAX_LAYER_ENTRIES = 20
MAX_COLUMNS = 3
CACHE_MAX = 512


class SearchLayerSpec(TypedDict):
    layer_id: str
    columns: list[str]
    label_column: str | None
    limit: int


def parse_search_config(config: dict[str, Any]) -> list[SearchLayerSpec]:
    """Extract searchable-layer specs from a project_public.config snapshot."""
    search = (
        config.get("project", {})
        .get("builder_config", {})
        .get("settings", {})
        .get("search")
        or {}
    )
    entries = search.get("layers") or []
    uuid_by_project_layer = {
        layer.get("id"): layer.get("layer_id") for layer in config.get("layers") or []
    }

    specs: list[SearchLayerSpec] = []
    for entry in entries[:MAX_LAYER_ENTRIES]:
        layer_uuid = uuid_by_project_layer.get(entry.get("layer_project_id"))
        columns = [c for c in (entry.get("columns") or []) if isinstance(c, str)]
        if not layer_uuid or not columns:
            continue
        limit = entry.get("limit")
        valid_limit = (
            isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= 10
        )
        specs.append(
            SearchLayerSpec(
                layer_id=str(layer_uuid),
                columns=columns[:MAX_COLUMNS],
                label_column=entry.get("label_column"),
                limit=int(limit) if valid_limit else 5,
            )
        )
    return specs


_lock = threading.Lock()
_fetch_lock = threading.Lock()
_cache: dict[str, tuple[float, list[SearchLayerSpec]]] = {}
_con: duckdb.DuckDBPyConnection | None = None


def _reset_connection() -> None:
    """Drop the cached connection, closing it so its fds aren't leaked.

    Called on every DuckDB error, so a flapping Postgres would otherwise leak
    one handle per failure.
    """
    global _con
    con, _con = _con, None
    if con is not None:
        try:
            con.close()
        except Exception:  # noqa: BLE001 - a dead connection is what we're discarding
            logger.debug("Discarding a DuckDB connection that failed to close")


def _get_connection() -> duckdb.DuckDBPyConnection:
    global _con
    if _con is None:
        con = duckdb.connect()
        if not configure_baked_extensions(con):
            con.execute("INSTALL postgres;")
        con.execute("LOAD postgres;")
        con.execute(
            f"ATTACH '{settings.POSTGRES_DATABASE_URI}' AS pubcfg (TYPE postgres, READ_ONLY)"
        )
        _con = con
    return _con


def _fetch_config(project_id: uuid.UUID) -> dict[str, Any] | None:
    con = _get_connection()
    # postgres_query takes a SQL literal; project_id is a validated UUID.
    row = con.execute(
        "SELECT * FROM postgres_query('pubcfg', "
        f"'SELECT config::text AS config FROM customer.project_public "
        f"WHERE project_id = ''{project_id}''')"
    ).fetchone()
    return json.loads(row[0]) if row else None


def _cache_get(key: str, now: float) -> list[SearchLayerSpec] | None:
    with _lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < CONFIG_TTL_SECONDS:
            return cached[1]
    return None


def _evict_for_insert(now: float) -> None:
    """Make room in `_cache` for a new key. Caller holds `_lock`."""
    expired = [k for k, (ts, _) in _cache.items() if now - ts >= CONFIG_TTL_SECONDS]
    for k in expired:
        del _cache[k]
    if len(_cache) >= CACHE_MAX:
        oldest_key = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest_key]


def _cache_put(
    key: str, now: float, specs: list[SearchLayerSpec]
) -> list[SearchLayerSpec]:
    with _lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < CONFIG_TTL_SECONDS:
            return cached[1]
        if key not in _cache and len(_cache) >= CACHE_MAX:
            _evict_for_insert(now)
        _cache[key] = (now, specs)
        return specs


def get_public_search_layers(project_id: str) -> list[SearchLayerSpec]:
    """Searchable-layer specs for a published project, TTL-cached per process.

    Cache reads take a short lock so one slow fetch never blocks lookups for
    other keys; the Postgres fetch itself is serialized on `_fetch_lock`
    since the underlying DuckDB connection is not thread-safe.
    """
    pid = uuid.UUID(project_id)
    key = str(pid)

    cached = _cache_get(key, time.monotonic())
    if cached is not None:
        return cached

    with _fetch_lock:
        try:
            config = _fetch_config(pid)
        except duckdb.Error:
            _reset_connection()  # reconnect on next call (e.g. stale PG connection)
            raise
        specs = parse_search_config(config) if config else []

    return _cache_put(key, time.monotonic(), specs)
