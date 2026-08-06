"""Helpers for handling computed columns within feature_write_service.

`parse_computed_columns` turns the layer's `field_config` JSONB blob
into a list of specs (name + dependency-set + compute SQL fragment).
`select_recompute_specs` filters those specs against a set of changed
source columns. `fetch_field_config` reads the JSONB from PG.

This module knows nothing about HTTP. Task D1 wires these helpers into
INSERT/UPDATE statements on customer layer tables.
"""

import json
import logging
from typing import Any
from uuid import UUID

import asyncpg
from goatlib.computed_columns import COMPUTED_KIND_REGISTRY

logger = logging.getLogger(__name__)


class ComputedColumnSpec:
    """A computed column on a layer: name + dependency-set + compute SQL."""

    __slots__ = ("name", "depends_on", "compute_sql")

    def __init__(
        self,
        name: str,
        depends_on: tuple[str, ...],
        compute_sql: str,
    ) -> None:
        self.name = name
        self.depends_on = depends_on
        self.compute_sql = compute_sql


# Sentinel dependency meaning "recompute on any change to the row".
DEPENDS_ON_ANY = "*"


def parse_computed_columns(
    field_config: dict[str, Any] | None,
    geom_column: str = "geometry",
) -> list[ComputedColumnSpec]:
    """Convert a layer's `field_config` JSONB into a list of specs."""
    specs: list[ComputedColumnSpec] = []
    for name, entry in (field_config or {}).items():
        if not entry.get("is_computed"):
            continue
        kind_name = entry.get("kind")
        if kind_name == "formula":
            # Formula columns carry their own expression. The expression was
            # validated (function whitelist, column existence, no subqueries)
            # when it was stored; parenthesize so it splices safely into a
            # SET clause.
            formula_sql = entry.get("formula")
            if not formula_sql:
                continue
            specs.append(
                ComputedColumnSpec(
                    name=name,
                    depends_on=tuple(entry.get("depends_on") or (DEPENDS_ON_ANY,)),
                    compute_sql=f"({formula_sql})",
                )
            )
            continue
        kind = COMPUTED_KIND_REGISTRY.get(kind_name) if kind_name else None
        if kind is None:
            # Unknown kind (e.g. JSONB written by a newer release).
            # Skip — we can't safely generate SQL for it.
            continue
        specs.append(
            ComputedColumnSpec(
                name=name,
                depends_on=tuple(entry.get("depends_on", kind.depends_on)),
                compute_sql=kind.compute_sql(geom_column),
            )
        )
    return specs


def select_recompute_specs(
    specs: list[ComputedColumnSpec],
    changed_source_cols: set[str],
) -> list[ComputedColumnSpec]:
    """Return the subset whose dependencies overlap the changed cols."""
    if not changed_source_cols:
        return []
    return [
        s
        for s in specs
        if DEPENDS_ON_ANY in s.depends_on
        or changed_source_cols.intersection(s.depends_on)
    ]


async def fetch_field_config(
    conn: asyncpg.Connection,
    layer_id: UUID,
) -> dict[str, Any]:
    """Read `field_config` JSONB from `customer.layer` for one layer.

    Returns an empty dict if the layer is not found or has no
    field_config. The caller is expected to have already verified the
    layer exists via the normal route auth flow.
    """
    row = await conn.fetchrow(
        "SELECT field_config FROM customer.layer WHERE id = $1::uuid",
        str(layer_id),
    )
    if row is None or row["field_config"] is None:
        return {}
    raw = row["field_config"]
    # asyncpg returns JSONB as either a dict (if a codec is registered) or
    # a JSON string. Handle both.
    if isinstance(raw, str):
        raw = json.loads(raw)
    return dict(raw or {})


def _normalize_layer_uuid(layer_id: str) -> str:
    """Hex-only UUIDs (no dashes) are common in customer.layer; normalise."""
    if "-" not in layer_id and len(layer_id) == 32:
        return f"{layer_id[:8]}-{layer_id[8:12]}-{layer_id[12:16]}-{layer_id[16:20]}-{layer_id[20:]}"
    return layer_id


async def write_field_config(
    conn: asyncpg.Connection,
    layer_id: str,
    field_config: dict[str, Any],
) -> None:
    """Replace the entire `field_config` JSONB for one layer."""
    await conn.execute(
        "UPDATE customer.layer SET field_config = $2::jsonb WHERE id = $1::uuid",
        _normalize_layer_uuid(layer_id),
        json.dumps(field_config),
    )
