"""Tests for the single `datetime` temporal field-kind."""

from typing import get_args

import pytest
from goatlib.computed_columns import validate_display_config

from geoapi.models.write import ColumnCreate, FieldKind
from geoapi.routers.features_write import _duckdb_type_to_kind, _resolve_kind_to_sql
from geoapi.routers.metadata import _kind_from_json_type
from geoapi.services.layer_service import LayerService

# One row per registry-resolved field kind: (kind, geometry_type needed to
# resolve it). The single source of truth for this test module — adding a
# kind to the codebase without extending this table (or FLOW_KINDS) fails
# the completeness test below.
ALL_KINDS: list[tuple[str, str | None]] = [
    ("string", None),
    ("number", None),
    ("datetime", None),
    ("boolean", None),
    ("area", "polygon"),
    ("perimeter", "polygon"),
    ("length", "line"),
]

# Kinds with their own creation flow: not resolvable via _resolve_kind_to_sql
# and their display_config is validated against a derived kind instead.
FLOW_KINDS: set[str] = {"formula"}


class TestDuckDBFormat:
    """Temporal DuckDB types collapse to a single OGC `date-time` format."""

    def test_date_collapses_to_datetime(self):
        assert LayerService._duckdb_to_json_format("DATE") == "date-time"

    def test_timestamp_format(self):
        assert LayerService._duckdb_to_json_format("TIMESTAMP") == "date-time"
        assert (
            LayerService._duckdb_to_json_format("TIMESTAMP WITH TIME ZONE")
            == "date-time"
        )

    def test_time_is_excluded(self):
        # Time-of-day is not temporal -> no format (falls through to string).
        assert LayerService._duckdb_to_json_format("TIME") is None

    def test_non_temporal_has_no_format(self):
        assert LayerService._duckdb_to_json_format("VARCHAR") is None
        assert LayerService._duckdb_to_json_format("DOUBLE") is None

    def test_temporal_json_type_stays_string(self):
        assert LayerService._duckdb_to_json_type("DATE") == "string"
        assert LayerService._duckdb_to_json_type("TIMESTAMP") == "string"


class TestKindFromJsonType:
    """Kind inference maps the OGC `date-time` format to `datetime`."""

    def test_datetime_format_infers_datetime(self):
        assert _kind_from_json_type("string", "date-time") == "datetime"

    def test_number_without_format(self):
        assert _kind_from_json_type("number") == "number"

    def test_string_without_format(self):
        assert _kind_from_json_type("string") == "string"


class TestKindWhitelistsAgree:
    """The request model's FieldKind Literal, the resolver, and the
    display-config registry are maintained separately — a kind present in one
    but missing from another surfaces only as a runtime 422/500, which the
    function-level tests below cannot catch.
    """

    def test_table_covers_the_literal(self):
        assert {k for k, _ in ALL_KINDS} | FLOW_KINDS == set(get_args(FieldKind))

    @pytest.mark.parametrize(("kind", "geom"), ALL_KINDS)
    def test_kind_passes_every_gate(self, kind: str, geom: str | None):
        # 1. FastAPI body validation (the gate that rejected kind="boolean")
        ColumnCreate(name="col", kind=kind)  # type: ignore[arg-type]
        # 2. Kind -> DuckDB type resolution
        duckdb_type, _, _, _ = _resolve_kind_to_sql(kind, None, geom)
        assert duckdb_type
        # 3. Display-config validation (raises ValueError on unknown kind)
        validate_display_config(kind, None)

    def test_formula_kind_passes_its_gates(self):
        # Body validation accepts the kind + expression
        ColumnCreate(name="col", kind="formula", formula="1 + 1")
        # The registry resolver must refuse it with a clear message — formula
        # is handled by its own flow
        with pytest.raises(ValueError, match="formula flow"):
            _resolve_kind_to_sql("formula", None, None)


class TestFormulaTypeToKind:
    """A formula's inferred DuckDB type maps onto a public field kind."""

    @pytest.mark.parametrize(
        ("duckdb_type", "expected"),
        [
            ("BOOLEAN", "boolean"),
            ("TIMESTAMP WITH TIME ZONE", "datetime"),
            ("DATE", "datetime"),
            ("BIGINT", "number"),
            ("DOUBLE", "number"),
            ("DECIMAL(18,3)", "number"),
            ("VARCHAR", "string"),
        ],
    )
    def test_mapping(self, duckdb_type: str, expected: str):
        assert _duckdb_type_to_kind(duckdb_type) == expected


class TestResolveKindToSql:
    """`datetime` resolves to a physical TIMESTAMP WITH TIME ZONE, not computed."""

    def test_datetime_kind(self):
        duckdb_type, compute_sql, depends_on, computed = _resolve_kind_to_sql(
            "datetime", None, None
        )
        assert duckdb_type == "TIMESTAMP WITH TIME ZONE"
        assert compute_sql is None
        assert depends_on == []
        assert computed is False
