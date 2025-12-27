"""Tests for CQL2 evaluator."""

import pytest

from geoapi.cql_evaluator import (
    cql2_to_duckdb_sql,
    parse_cql2_filter,
)


class TestDuckDBCQLEvaluator:
    """Tests for DuckDBCQLEvaluator."""

    def test_simple_equality(self):
        """Test simple equality comparison."""
        cql = '{"op": "=", "args": [{"property": "name"}, "Berlin"]}'
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name", "value"])

        assert '"name" = ?' in sql
        assert params == ["Berlin"]

    def test_numeric_comparison(self):
        """Test numeric comparison operators."""
        cql = '{"op": ">", "args": [{"property": "value"}, 100]}'
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name", "value"])

        assert '"value" > ?' in sql
        assert params == [100]

    def test_and_operator(self):
        """Test AND logical operator."""
        cql = """{
            "op": "and",
            "args": [
                {"op": "=", "args": [{"property": "name"}, "Berlin"]},
                {"op": ">", "args": [{"property": "value"}, 50]}
            ]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name", "value"])

        assert "AND" in sql
        assert '"name" = ?' in sql
        assert '"value" > ?' in sql
        assert len(params) == 2

    def test_or_operator(self):
        """Test OR logical operator."""
        cql = """{
            "op": "or",
            "args": [
                {"op": "=", "args": [{"property": "name"}, "Berlin"]},
                {"op": "=", "args": [{"property": "name"}, "Munich"]}
            ]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name", "value"])

        assert "OR" in sql
        assert params == ["Berlin", "Munich"]

    def test_not_operator(self):
        """Test NOT logical operator."""
        cql = """{
            "op": "not",
            "args": [{"op": "=", "args": [{"property": "name"}, "Berlin"]}]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name"])

        assert "NOT" in sql
        assert params == ["Berlin"]

    def test_like_operator(self):
        """Test LIKE operator."""
        cql = '{"op": "like", "args": [{"property": "name"}, "Ber%"]}'
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name"])

        assert "LIKE" in sql
        assert params == ["Ber%"]

    def test_between_operator(self):
        """Test BETWEEN operator using >= and <= combination."""
        # pygeofilter CQL2-JSON doesn't support 'between' directly
        # Use combined >= and <= which is equivalent
        cql = """{
            "op": "and",
            "args": [
                {"op": ">=", "args": [{"property": "value"}, 10]},
                {"op": "<=", "args": [{"property": "value"}, 100]}
            ]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["value"])

        assert "AND" in sql
        assert '"value" >= ?' in sql
        assert '"value" <= ?' in sql
        assert 10 in params
        assert 100 in params

    def test_in_operator(self):
        """Test IN operator."""
        cql = '{"op": "in", "args": [{"property": "name"}, ["Berlin", "Munich", "Hamburg"]]}'
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name"])

        assert "IN" in sql
        assert len(params) == 3

    def test_is_null_operator(self):
        """Test IS NULL operator."""
        cql = '{"op": "isNull", "args": [{"property": "name"}]}'
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name"])

        assert "IS NULL" in sql

    def test_invalid_field_raises_error(self):
        """Test that invalid field names raise errors."""
        cql = '{"op": "=", "args": [{"property": "invalid_field"}, "value"]}'
        ast = parse_cql2_filter(cql, "cql2-json")

        with pytest.raises(ValueError) as exc_info:
            cql2_to_duckdb_sql(ast, ["name", "value"])

        assert "Unknown field" in str(exc_info.value)

    def test_spatial_intersects(self):
        """Test S_INTERSECTS spatial operator."""
        cql = """{
            "op": "s_intersects",
            "args": [
                {"property": "geom"},
                {"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]}
            ]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["geom", "name"])

        assert "ST_Intersects" in sql

    def test_nested_logical_operators(self):
        """Test nested logical operators."""
        cql = """{
            "op": "and",
            "args": [
                {"op": "=", "args": [{"property": "name"}, "Berlin"]},
                {
                    "op": "or",
                    "args": [
                        {"op": ">", "args": [{"property": "value"}, 100]},
                        {"op": "<", "args": [{"property": "value"}, 10]}
                    ]
                }
            ]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        sql, params = cql2_to_duckdb_sql(ast, ["name", "value"])

        assert "AND" in sql
        assert "OR" in sql
        assert len(params) == 3


class TestParseCQL2Filter:
    """Tests for parse_cql2_filter function."""

    def test_parse_cql2_json(self):
        """Test parsing CQL2 JSON."""
        cql = '{"op": "=", "args": [{"property": "name"}, "test"]}'
        ast = parse_cql2_filter(cql, "cql2-json")
        assert ast is not None

    def test_parse_cql2_text(self):
        """Test parsing CQL2 text."""
        cql = "name = 'test'"
        ast = parse_cql2_filter(cql, "cql2-text")
        assert ast is not None

    def test_parse_default_lang(self):
        """Test that default language is cql2-json."""
        cql = '{"op": "=", "args": [{"property": "name"}, "test"]}'
        ast = parse_cql2_filter(cql)
        assert ast is not None
