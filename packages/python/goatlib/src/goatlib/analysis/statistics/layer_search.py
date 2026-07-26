"""Feature text search over a layer's attribute columns."""

import logging

import duckdb

from goatlib.analysis.schemas.statistics import LayerSearchGroup, LayerSearchItem

logger = logging.getLogger(__name__)


def _qi(name: str) -> str:
    """Quote a SQL identifier, doubling any embedded double quotes."""
    return '"' + name.replace('"', '""') + '"'


def search_layer_features(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    query: str,
    columns: list[str],
    layer_id: str,
    label_column: str | None = None,
    geometry_column: str = "geometry",
    map_center: tuple[float, float] | None = None,
    limit: int = 5,
    candidate_cap: int = 50,
) -> LayerSearchGroup:
    """Search a layer's text columns for a substring, ranked prefix-first
    and (optionally) nearest-first relative to map_center.

    Raises:
        ValueError: If a requested column does not exist on the table.
    """
    desc = con.execute(f"DESCRIBE {table_name}").fetchall()
    existing = {row[0] for row in desc}
    # The message reaches unauthenticated public-dashboard callers, so it must
    # not name the column or the layer — that would turn a 400 into a schema
    # oracle. The details go to the logs instead.
    for col in [*columns, *([label_column] if label_column else [])]:
        if col not in existing:
            logger.warning("Unknown search column '%s' on layer %s", col, layer_id)
            raise ValueError("Unknown search column")
    if geometry_column not in existing:
        logger.warning(
            "Unknown geometry column '%s' on layer %s", geometry_column, layer_id
        )
        raise ValueError("Unknown geometry column")

    label_col = label_column or columns[0]
    g = _qi(geometry_column)
    escape_clause = r" ESCAPE '\'"
    like_clauses = " OR ".join(
        f"CAST({_qi(c)} AS VARCHAR) ILIKE ?{escape_clause}" for c in columns
    )
    prefix_clauses = " OR ".join(
        f"CAST({_qi(c)} AS VARCHAR) ILIKE ?{escape_clause}" for c in columns
    )
    col_selects = ", ".join(
        f"CAST({_qi(c)} AS VARCHAR) AS {_qi(f'_s_{c}')}" for c in columns
    )

    escaped_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    order_terms = [f"CASE WHEN {prefix_clauses} THEN 0 ELSE 1 END"]
    params: list = [f"%{escaped_query}%"] * len(columns) + [f"{escaped_query}%"] * len(
        columns
    )
    if map_center is not None:
        order_terms.append(f"ST_Distance(ST_Centroid({g}), ST_Point(?, ?)) NULLS LAST")
        params.extend([map_center[0], map_center[1]])

    sql = f"""
        SELECT rowid + 1 AS id,
               CAST({_qi(label_col)} AS VARCHAR) AS label,
               {col_selects},
               ST_X(ST_Centroid({g})) AS cx, ST_Y(ST_Centroid({g})) AS cy,
               ST_XMin({g}) AS bx0, ST_YMin({g}) AS by0,
               ST_XMax({g}) AS bx1, ST_YMax({g}) AS by1
        FROM {table_name}
        WHERE {like_clauses}
        ORDER BY {", ".join(order_terms)}
        LIMIT {int(candidate_cap) + 1}
    """
    rows = con.execute(sql, params).fetchall()
    truncated = len(rows) > limit
    rows = rows[:candidate_cap]

    q_lower = query.lower()
    items: list[LayerSearchItem] = []
    for row in rows[:limit]:
        rid, label = row[0], row[1]
        col_values = dict(zip(columns, row[2 : 2 + len(columns)]))
        matched_column, matched_value = "", ""
        for c in columns:
            val = col_values.get(c)
            if val is not None and q_lower in str(val).lower():
                matched_column, matched_value = c, str(val)
                break
        if not matched_value:
            for c in columns:
                val = col_values.get(c)
                if val is not None:
                    matched_column, matched_value = c, str(val)
                    break
        cx, cy, bx0, by0, bx1, by1 = row[2 + len(columns) : 8 + len(columns)]
        items.append(
            LayerSearchItem(
                id=rid,
                label=label,
                matched_column=matched_column,
                matched_value=matched_value,
                values={
                    c: (str(v) if v is not None else None)
                    for c, v in col_values.items()
                },
                centroid=[cx, cy] if cx is not None else [],
                bbox=[bx0, by0, bx1, by1] if bx0 is not None else None,
            )
        )

    return LayerSearchGroup(
        layer_id=layer_id,
        results=items,
        truncated=truncated,
        timed_out=False,
        error=None,
    )
