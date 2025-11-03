import re

from qgis.core import QgsExpression

"""Minimal converter: QGIS expression → Postgres/PostGIS SQL."""

_NUMERIC_FUNCS = {"abs","sqrt","pow","exp","ln","log10","round","ceil","floor","pi","sin","cos","tan","asin","acos","atan","degrees","radians","rand"}
_STRING_FUNCS  = {"length","char_length","upper","lower","trim","ltrim","rtrim","substr","substring","left","right","replace","regexp_replace","regexp_substr","strpos","concat"}
_DATETIME_FUNCS= {"now","age","extract","date_part","make_date","make_time","make_timestamp","to_date","to_timestamp","to_char"}
_CAST_FUNCS    = {"to_int","to_real","to_string"}
_GENERIC_FUNCS = {"coalesce","nullif"}
_AGG_FUNCS     = {"sum","avg","min","max","count"}

_METRIC_UNARY  = {"area":"ST_Area","length":"ST_Length","perimeter":"ST_Perimeter"}
_METRIC_BUFFER = "buffer"
_GEOM_UNARY    = {"centroid":"ST_Centroid","convex_hull":"ST_ConvexHull","envelope":"ST_Envelope","make_valid":"ST_MakeValid","is_empty":"ST_IsEmpty","is_valid":"ST_IsValid","x":"ST_X","y":"ST_Y","xmin":"ST_XMin","xmax":"ST_XMax","ymin":"ST_YMin","ymax":"ST_YMax"}

_ALL_FUNCS = (_NUMERIC_FUNCS|_STRING_FUNCS|_DATETIME_FUNCS|_CAST_FUNCS|_GENERIC_FUNCS|_AGG_FUNCS|set(_METRIC_UNARY)|{_METRIC_BUFFER}|set(_GEOM_UNARY))
_BANNED_MULTI_GEOM = {"distance","intersects","touches","within","overlaps","crosses"}
_OP_MAP = {"!=":"<>"}

_SPECIAL = {
    "$geometry":"geom",
    "$area":"ST_Area(geom::geography)",
    "$length":"ST_Length(geom::geography)",
    "$perimeter":"ST_Perimeter(geom::geography)",
    "$x":"ST_X(geom)","$y":"ST_Y(geom)",
    "$xmin":"ST_XMin(geom)","$xmax":"ST_XMax(geom)",
    "$ymin":"ST_YMin(geom)","$ymax":"ST_YMax(geom)"
}

_FUNC_RE = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.IGNORECASE)

class QgsExpressionToSqlConverter:
    def __init__(self, input_expr: str) -> None:
        expr = QgsExpression(input_expr)
        if not expr.isValid():
            if expr.hasParserError():
                raise ValueError(f"Invalid expression: {expr.parserErrorString()}")
            raise ValueError("Invalid expression")
        self.raw = expr.expression()

    def extract_field_names(self) -> set[str]:
        """Return set of column names (assumed always double‑quoted)."""

        return set(re.findall(r'"([^"]+)"', self.raw))

    def replace_field_name(self, old: str, new: str) -> None:
        """Replace field name in expression with attribute-mapped name."""

        pattern = re.compile(rf'"{re.escape(old)}"')
        self.raw = pattern.sub(f'"{new}"', self.raw)


    # ------------------------------------------------------------------
    def translate(self) -> tuple[str, str]:
        """Convert QGIS expression to a PostgreSQL compliant SELECT and GROUP BY clause."""

        sql = self.raw
        self._validate(sql)
        sql = self._subst(sql, _SPECIAL)
        sql = self._rewrite_casts(sql)
        sql = self._rewrite_buffer(sql)
        sql = self._rewrite_metric(sql)
        sql = self._rename_unary_geom(sql)
        sql = re.sub(r"\brand\s*\(", "random(", sql, flags=re.IGNORECASE)
        for q, pg in _OP_MAP.items():
            sql = sql.replace(q, pg)
        sql, grp = self._rewrite_aggs(sql)
        return sql, ", ".join(sorted(grp))

    # ------------------------------------------------------------------
    def _validate(self, text: str) -> None:
        for fn in _FUNC_RE.findall(text):
            fn_lower = fn.lower()
            if fn_lower in _BANNED_MULTI_GEOM:
                raise ValueError(f"Function '{fn}' needs multiple geometries - not supported.")
            if fn_lower not in _ALL_FUNCS:
                raise ValueError(f"Function '{fn}' is not supported.")

    @staticmethod
    def _subst(txt: str, mapping: dict[str, str]) -> str:
        for k, v in mapping.items():
            txt = re.sub(re.escape(k), v, txt, flags=re.IGNORECASE)
        return txt

    @staticmethod
    def _rewrite_casts(txt: str) -> str:
        txt = re.sub(r"\bto_int\s*\(([^)]+)\)", r"CAST(\1 AS integer)", txt, flags=re.IGNORECASE)
        txt = re.sub(r"\bto_real\s*\(([^)]+)\)", r"CAST(\1 AS double precision)", txt, flags=re.IGNORECASE)
        txt = re.sub(r"\bto_string\s*\(([^)]+)\)", r"CAST(\1 AS text)", txt, flags=re.IGNORECASE)
        return txt

    @staticmethod
    def _rewrite_buffer(txt: str) -> str:
        pat = re.compile(r"\bbuffer\s*\(\s*([^,]+?),\s*([^)]+?)\)", re.IGNORECASE)
        return pat.sub(lambda m: f"ST_Buffer({m.group(1)}::geography, {m.group(2)})", txt)

    def _geom_like(self, arg: str) -> bool:
        a = arg.lower()
        hints = ["geom", "::geography", "st_", "buffer("] + list(_GEOM_UNARY) + list(_METRIC_UNARY) + [_METRIC_BUFFER]
        return any(h in a for h in hints)

    def _rewrite_metric(self, txt: str) -> str:
        nest = r"(?:[^()]+|\([^()]*\))+"
        for q, pg in _METRIC_UNARY.items():
            pat = re.compile(rf"\b{q}\s*\(\s*({nest})\s*\)", re.IGNORECASE)
            def rp(m: re.Match[str]) -> str:
                arg = m.group(1).strip()
                if self._geom_like(arg):
                    return f"{pg}({arg}::geography)"
                if q == "length":
                    return f"char_length({arg})"
                return m.group(0)
            txt = pat.sub(rp, txt)
        return txt

    def _rename_unary_geom(self, txt: str) -> str:
        nest = r"(?:[^()]+|\([^()]*\))+"
        for q, pg in _GEOM_UNARY.items():
            pat = re.compile(rf"\b{q}\s*\(\s*({nest})\s*\)", re.IGNORECASE)
            txt = pat.sub(lambda m: f"{pg}({m.group(1)})" if self._geom_like(m.group(1)) else m.group(0), txt)
        return txt

    def _rewrite_aggs(self, sql: str) -> tuple[str, set[str]]:
        grp = set()
        def rp(m: re.Match[str]) -> str:
            func, params = m.group(1), m.group(2)
            parts = [p.strip() for p in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", params) if p.strip()]
            exprs = []
            for p in parts:
                if p.lower().startswith("group_by"):
                    val = re.split(r":=|=", p, 1)[-1]
                    for c in [v.strip().strip('"') for v in val.split(',') if v.strip()]:
                        grp.add(f'"{c}"')
                else:
                    exprs.append(p)
            rebuilt = ", ".join(exprs) if exprs else params
            return f"{func}({rebuilt})"
        pattern = re.compile(rf"\b({'|'.join(_AGG_FUNCS)})\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
        return pattern.sub(rp, sql), grp

def build_sql(expr: str, alias: str | None = None) -> str:
    sql, grp = QgsExpressionToSqlConverter(expr).translate()
    if alias:
        sql += f" AS {alias}"
    out = f"SELECT {sql}"
    if grp:
        out += "\nGROUP BY " + ", ".join(sorted(grp))
    return out
