"""Tests for layer feature text search."""

import duckdb
import pytest
from goatlib.analysis.statistics import search_layer_features


@pytest.fixture
def con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(
        """
        CREATE TABLE pois (
            name VARCHAR, street VARCHAR, category VARCHAR, geometry GEOMETRY
        )
        """
    )
    con.execute(
        """
        INSERT INTO pois VALUES
        ('Murrbruecke', 'Hauptstrasse', 'bridge', ST_Point(9.58, 48.98)),
        ('Bahnhof Murrhardt', 'Bahnhofstrasse', 'station', ST_Point(9.57, 48.97)),
        ('Murr Apotheke', 'Murrhardter Strasse', 'pharmacy', ST_Point(11.0, 50.0)),
        ('Rathaus', 'Marktplatz', 'townhall', ST_Point(9.58, 48.98)),
        (NULL, 'Murrweg', 'path', ST_Point(9.60, 48.99))
        """
    )
    return con


def test_matches_substring_case_insensitive(con: duckdb.DuckDBPyConnection) -> None:
    group = search_layer_features(
        con, "pois", query="murr", columns=["name", "street"], layer_id="abc"
    )
    assert group.layer_id == "abc"
    labels = [r.label for r in group.results]
    assert "Murrbruecke" in labels
    assert "Bahnhof Murrhardt" in labels
    assert "Rathaus" not in labels


def test_prefix_matches_rank_before_substring(con: duckdb.DuckDBPyConnection) -> None:
    group = search_layer_features(
        con, "pois", query="murr", columns=["name"], layer_id="abc"
    )
    # 'Murrbruecke'/'Murr Apotheke' (prefix) before 'Bahnhof Murrhardt' (substring)
    labels = [r.label for r in group.results]
    assert labels.index("Bahnhof Murrhardt") > labels.index("Murrbruecke")


def test_proximity_orders_nearer_first_within_rank(
    con: duckdb.DuckDBPyConnection,
) -> None:
    group = search_layer_features(
        con,
        "pois",
        query="murr",
        columns=["name"],
        map_center=(9.58, 48.98),
        layer_id="abc",
    )
    labels = [r.label for r in group.results]
    # Both prefix matches; Murrbruecke at map center, Murr Apotheke far away
    assert labels.index("Murrbruecke") < labels.index("Murr Apotheke")


def test_matched_column_and_value(con: duckdb.DuckDBPyConnection) -> None:
    group = search_layer_features(
        con, "pois", query="murrweg", columns=["name", "street"], layer_id="abc"
    )
    assert len(group.results) == 1
    item = group.results[0]
    assert item.matched_column == "street"
    assert item.matched_value == "Murrweg"
    assert item.label is None  # name is NULL, label_column defaults to columns[0]


def test_label_column_override(con: duckdb.DuckDBPyConnection) -> None:
    group = search_layer_features(
        con,
        "pois",
        query="bridge",
        columns=["category"],
        label_column="name",
        layer_id="abc",
    )
    assert group.results[0].label == "Murrbruecke"


def test_limit_and_truncated_flag(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        "INSERT INTO pois SELECT 'Murr ' || i, 's', 'c', ST_Point(9.0, 48.0) FROM range(60) t(i)"
    )
    group = search_layer_features(
        con,
        "pois",
        query="murr",
        columns=["name"],
        limit=5,
        candidate_cap=50,
        layer_id="abc",
    )
    assert len(group.results) == 5
    assert group.truncated is True


def test_unknown_column_raises(con: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(ValueError) as excinfo:
        search_layer_features(
            con, "pois", query="murr", columns=["nope"], layer_id="abc"
        )
    # Generic on purpose: the message is echoed to unauthenticated callers.
    assert str(excinfo.value) == "Unknown search column"
    assert "nope" not in str(excinfo.value)


def test_unknown_geometry_column_raises(con: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(ValueError) as excinfo:
        search_layer_features(
            con,
            "pois",
            query="murr",
            columns=["name"],
            layer_id="abc",
            geometry_column="nope",
        )
    assert str(excinfo.value) == "Unknown geometry column"
    assert "nope" not in str(excinfo.value)


def test_geometry_and_ids(con: duckdb.DuckDBPyConnection) -> None:
    group = search_layer_features(
        con, "pois", query="rathaus", columns=["name"], layer_id="abc"
    )
    item = group.results[0]
    assert item.id >= 1  # rowid + 1
    assert item.centroid == pytest.approx([9.58, 48.98])
    assert item.bbox == pytest.approx([9.58, 48.98, 9.58, 48.98])


def test_truncated_means_more_matches_than_shown(
    con: duckdb.DuckDBPyConnection,
) -> None:
    con.execute("DELETE FROM pois")
    con.execute(
        "INSERT INTO pois SELECT 'Murr ' || i, 's', 'c', ST_Point(9.0, 48.0) FROM range(5) t(i)"
    )
    group = search_layer_features(
        con, "pois", query="murr", columns=["name"], limit=5, layer_id="abc"
    )
    assert len(group.results) == 5
    assert group.truncated is False

    con.execute("INSERT INTO pois VALUES ('Murr extra', 's', 'c', ST_Point(9.0, 48.0))")
    group = search_layer_features(
        con, "pois", query="murr", columns=["name"], limit=5, layer_id="abc"
    )
    assert len(group.results) == 5
    assert group.truncated is True


def test_like_metacharacters_literal(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("DELETE FROM pois")
    con.execute(
        """
        INSERT INTO pois VALUES
        ('AAA', 's', 'c', ST_Point(9.0, 48.0)),
        ('A_A', 's', 'c', ST_Point(9.0, 48.0))
        """
    )
    group = search_layer_features(
        con, "pois", query="A_A", columns=["name"], layer_id="abc"
    )
    assert len(group.results) == 1
    assert group.results[0].label == "A_A"


def test_unicode_case_folding_fallback(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("DELETE FROM pois")
    con.execute(
        """
        INSERT INTO pois VALUES
        ('İstanbul', 's', 'c', ST_Point(9.0, 48.0))
        """
    )
    group = search_layer_features(
        con, "pois", query="istanbul", columns=["name"], layer_id="abc"
    )
    assert len(group.results) == 1
    item = group.results[0]
    assert item.matched_value != ""
    assert item.matched_column == "name"
