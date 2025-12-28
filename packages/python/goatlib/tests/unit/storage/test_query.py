"""Tests for CQL2 evaluator and query builder."""

import pytest
from goatlib.storage import (
    QueryFilters,
    build_bbox_filter,
    build_filters,
    build_id_filter,
    build_order_clause,
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

    def test_geometry_column_alias_geom_to_geometry(self):
        """Test that 'geom' is aliased to the actual geometry column 'geometry'."""
        cql = """{
            "op": "s_intersects",
            "args": [
                {"property": "geom"},
                {"type": "Point", "coordinates": [0, 0]}
            ]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        # The actual geometry column is "geometry", but the CQL filter uses "geom"
        sql, params = cql2_to_duckdb_sql(
            ast, ["name", "geometry"], geometry_column="geometry"
        )

        # Should use the actual geometry column name "geometry", not "geom"
        assert '"geometry"' in sql
        assert '"geom"' not in sql

    def test_geometry_column_alias_geometry_to_geom(self):
        """Test that 'geometry' is aliased to the actual geometry column 'geom'."""
        cql = """{
            "op": "s_intersects",
            "args": [
                {"property": "geometry"},
                {"type": "Point", "coordinates": [0, 0]}
            ]
        }"""
        ast = parse_cql2_filter(cql, "cql2-json")
        # The actual geometry column is "geom", but the CQL filter uses "geometry"
        sql, params = cql2_to_duckdb_sql(ast, ["name", "geom"], geometry_column="geom")

        # Should use the actual geometry column name "geom", not "geometry"
        assert '"geom"' in sql


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


class TestQueryFilters:
    """Tests for QueryFilters dataclass."""

    def test_add_clause(self):
        """Test adding a clause."""
        filters = QueryFilters()
        filters.add('"name" = ?', "Berlin")

        assert len(filters.clauses) == 1
        assert filters.params == ["Berlin"]

    def test_add_multiple_clauses(self):
        """Test adding multiple clauses."""
        filters = QueryFilters()
        filters.add('"name" = ?', "Berlin")
        filters.add('"value" > ?', 100)

        assert len(filters.clauses) == 2
        assert filters.params == ["Berlin", 100]

    def test_extend(self):
        """Test extending with another QueryFilters."""
        filters1 = QueryFilters()
        filters1.add('"name" = ?', "Berlin")

        filters2 = QueryFilters()
        filters2.add('"value" > ?', 100)

        filters1.extend(filters2)

        assert len(filters1.clauses) == 2
        assert filters1.params == ["Berlin", 100]

    def test_to_where_sql_empty(self):
        """Test to_where_sql with no clauses."""
        filters = QueryFilters()
        assert filters.to_where_sql() == ""

    def test_to_where_sql_with_clauses(self):
        """Test to_where_sql with clauses."""
        filters = QueryFilters()
        filters.add('"name" = ?', "Berlin")
        filters.add('"value" > ?', 100)

        result = filters.to_where_sql()
        assert result == ' AND "name" = ? AND "value" > ?'

    def test_to_full_where_empty(self):
        """Test to_full_where with no clauses."""
        filters = QueryFilters()
        assert filters.to_full_where() == "TRUE"

    def test_to_full_where_with_clauses(self):
        """Test to_full_where with clauses."""
        filters = QueryFilters()
        filters.add('"name" = ?', "Berlin")
        filters.add('"value" > ?', 100)

        result = filters.to_full_where()
        assert result == '"name" = ? AND "value" > ?'

    def test_method_chaining(self):
        """Test method chaining."""
        filters = QueryFilters()
        filters.add('"a" = ?', 1).add('"b" = ?', 2)

        assert len(filters.clauses) == 2
        assert filters.params == [1, 2]


class TestBuildBboxFilter:
    """Tests for build_bbox_filter function."""

    def test_build_bbox_filter(self):
        """Test building bbox filter."""
        filters = build_bbox_filter([0, 0, 10, 10], "geometry")

        assert len(filters.clauses) == 1
        assert "ST_Intersects" in filters.clauses[0]
        assert "ST_GeomFromText" in filters.clauses[0]
        assert len(filters.params) == 1
        assert "POLYGON" in filters.params[0]


class TestBuildIdFilter:
    """Tests for build_id_filter function."""

    def test_build_id_filter(self):
        """Test building ID filter."""
        filters = build_id_filter(["a", "b", "c"])

        assert len(filters.clauses) == 1
        assert "IN" in filters.clauses[0]
        assert filters.params == ["a", "b", "c"]

    def test_build_id_filter_empty(self):
        """Test building ID filter with empty list."""
        filters = build_id_filter([])

        assert len(filters.clauses) == 0
        assert filters.params == []


class TestBuildFilters:
    """Tests for build_filters function."""

    def test_build_filters_with_bbox(self):
        """Test building filters with bbox."""
        filters = build_filters(bbox=[0, 0, 10, 10], geometry_column="geom")

        assert len(filters.clauses) == 1
        assert "ST_Intersects" in filters.clauses[0]

    def test_build_filters_with_ids(self):
        """Test building filters with IDs."""
        filters = build_filters(ids=["a", "b"])

        assert len(filters.clauses) == 1
        assert "IN" in filters.clauses[0]

    def test_build_filters_combined(self):
        """Test building combined filters."""
        filters = build_filters(
            bbox=[0, 0, 10, 10],
            ids=["a", "b"],
            geometry_column="geom",
        )

        assert len(filters.clauses) == 2

    def test_build_filters_no_geometry(self):
        """Test building filters without geometry."""
        filters = build_filters(
            bbox=[0, 0, 10, 10],
            has_geometry=False,
        )

        # bbox should be skipped when has_geometry=False
        assert len(filters.clauses) == 0


class TestBuildOrderClause:
    """Tests for build_order_clause function."""

    def test_order_asc(self):
        """Test ascending order."""
        result = build_order_clause("name")
        assert result == 'ORDER BY "name" ASC'

    def test_order_asc_explicit(self):
        """Test explicit ascending order."""
        result = build_order_clause("+name")
        assert result == 'ORDER BY "name" ASC'

    def test_order_desc(self):
        """Test descending order."""
        result = build_order_clause("-name")
        assert result == 'ORDER BY "name" DESC'

    def test_order_none(self):
        """Test no order."""
        result = build_order_clause(None)
        assert result == ""

    def test_order_empty(self):
        """Test empty string."""
        result = build_order_clause("")
        assert result == ""
