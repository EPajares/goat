"""Process service for OGC API Processes.

Implements analytical processes using DuckDB:
- feature-count: Count features in a collection
- area-statistics: Calculate area-based statistics
- unique-values: Get unique values with counts
- class-breaks: Calculate classification breaks
"""

import logging
from typing import Any
from uuid import UUID

from geoapi.cql_evaluator import cql2_to_duckdb_sql, parse_cql2_filter
from geoapi.ducklake import ducklake_manager
from geoapi.ducklake_pool import execute_query_with_retry
from geoapi.models import (
    AreaStatisticsInput,
    AreaStatisticsOutput,
    ClassBreaksInput,
    ClassBreaksOutput,
    FeatureCountInput,
    FeatureCountOutput,
    InputDescription,
    JobControlOptions,
    Link,
    OutputDescription,
    ProcessDescription,
    ProcessSummary,
    TransmissionMode,
    UniqueValue,
    UniqueValuesInput,
    UniqueValuesOutput,
)
from geoapi.services.layer_service import layer_service

logger = logging.getLogger(__name__)


# === Process Definitions ===

PROCESSES: dict[str, ProcessDescription] = {
    "feature-count": ProcessDescription(
        id="feature-count",
        title="Feature Count",
        description="Count the number of features in a collection, optionally filtered by CQL2 expression.",
        version="1.0.0",
        jobControlOptions=[JobControlOptions.sync_execute],
        outputTransmission=[TransmissionMode.value],
        inputs={
            "collection": InputDescription(
                title="Collection ID",
                description="The UUID of the collection/layer to count features from.",
                schema={"type": "string", "format": "uuid"},
            ),
            "filter": InputDescription(
                title="CQL2 Filter",
                description="Optional CQL2 filter expression in JSON format.",
                schema={"type": "string"},
                minOccurs=0,
            ),
        },
        outputs={
            "count": OutputDescription(
                title="Feature Count",
                description="The number of features matching the criteria.",
                schema={"type": "integer", "minimum": 0},
            ),
        },
    ),
    "area-statistics": ProcessDescription(
        id="area-statistics",
        title="Area Statistics",
        description="Calculate area-based statistics for polygon features.",
        version="1.0.0",
        jobControlOptions=[JobControlOptions.sync_execute],
        outputTransmission=[TransmissionMode.value],
        inputs={
            "collection": InputDescription(
                title="Collection ID",
                description="The UUID of the collection/layer with polygon geometries.",
                schema={"type": "string", "format": "uuid"},
            ),
            "operation": InputDescription(
                title="Operation",
                description="Statistical operation to perform (sum, mean, min, max).",
                schema={"type": "string", "enum": ["sum", "mean", "min", "max"]},
            ),
            "filter": InputDescription(
                title="CQL2 Filter",
                description="Optional CQL2 filter expression.",
                schema={"type": "string"},
                minOccurs=0,
            ),
        },
        outputs={
            "statistics": OutputDescription(
                title="Area Statistics",
                description="Calculated area statistics.",
                schema={
                    "type": "object",
                    "properties": {
                        "total_area": {"type": "number"},
                        "feature_count": {"type": "integer"},
                        "result": {"type": "number"},
                        "unit": {"type": "string"},
                    },
                },
            ),
        },
    ),
    "unique-values": ProcessDescription(
        id="unique-values",
        title="Unique Values",
        description="Get unique values of an attribute with their occurrence counts.",
        version="1.0.0",
        jobControlOptions=[JobControlOptions.sync_execute],
        outputTransmission=[TransmissionMode.value],
        inputs={
            "collection": InputDescription(
                title="Collection ID",
                description="The UUID of the collection/layer.",
                schema={"type": "string", "format": "uuid"},
            ),
            "attribute": InputDescription(
                title="Attribute Name",
                description="The attribute/column to analyze.",
                schema={"type": "string"},
            ),
            "order": InputDescription(
                title="Sort Order",
                description="Order results by count (ascendent or descendent).",
                schema={
                    "type": "string",
                    "enum": ["ascendent", "descendent"],
                    "default": "descendent",
                },
                minOccurs=0,
            ),
            "filter": InputDescription(
                title="CQL2 Filter",
                description="Optional CQL2 filter expression.",
                schema={"type": "string"},
                minOccurs=0,
            ),
            "limit": InputDescription(
                title="Limit",
                description="Maximum number of unique values to return.",
                schema={
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100,
                },
                minOccurs=0,
            ),
            "offset": InputDescription(
                title="Offset",
                description="Offset for pagination.",
                schema={"type": "integer", "minimum": 0, "default": 0},
                minOccurs=0,
            ),
        },
        outputs={
            "values": OutputDescription(
                title="Unique Values",
                description="List of unique values with counts.",
                schema={
                    "type": "object",
                    "properties": {
                        "attribute": {"type": "string"},
                        "total": {"type": "integer"},
                        "values": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "value": {},
                                    "count": {"type": "integer"},
                                },
                            },
                        },
                    },
                },
            ),
        },
    ),
    "class-breaks": ProcessDescription(
        id="class-breaks",
        title="Class Breaks",
        description="Calculate classification breaks for a numeric attribute using various methods.",
        version="1.0.0",
        jobControlOptions=[JobControlOptions.sync_execute],
        outputTransmission=[TransmissionMode.value],
        inputs={
            "collection": InputDescription(
                title="Collection ID",
                description="The UUID of the collection/layer.",
                schema={"type": "string", "format": "uuid"},
            ),
            "attribute": InputDescription(
                title="Attribute Name",
                description="The numeric attribute/column to classify.",
                schema={"type": "string"},
            ),
            "method": InputDescription(
                title="Classification Method",
                description="Method for calculating breaks.",
                schema={
                    "type": "string",
                    "enum": [
                        "quantile",
                        "equal_interval",
                        "standard_deviation",
                        "heads_and_tails",
                    ],
                    "default": "quantile",
                },
                minOccurs=0,
            ),
            "breaks": InputDescription(
                title="Number of Classes",
                description="Number of classification breaks.",
                schema={"type": "integer", "minimum": 2, "maximum": 20, "default": 5},
                minOccurs=0,
            ),
            "filter": InputDescription(
                title="CQL2 Filter",
                description="Optional CQL2 filter expression.",
                schema={"type": "string"},
                minOccurs=0,
            ),
            "strip_zeros": InputDescription(
                title="Strip Zeros",
                description="Exclude zero values from classification.",
                schema={"type": "boolean", "default": False},
                minOccurs=0,
            ),
        },
        outputs={
            "breaks": OutputDescription(
                title="Class Breaks",
                description="Classification break values and statistics.",
                schema={
                    "type": "object",
                    "properties": {
                        "attribute": {"type": "string"},
                        "method": {"type": "string"},
                        "breaks": {"type": "array", "items": {"type": "number"}},
                        "min": {"type": "number"},
                        "max": {"type": "number"},
                        "mean": {"type": "number"},
                        "std_dev": {"type": "number"},
                    },
                },
            ),
        },
    ),
}


class ProcessService:
    """Service for executing analytical processes."""

    def get_process_list(self, base_url: str) -> list[ProcessSummary]:
        """Get list of available processes."""
        summaries = []
        for proc_id, proc in PROCESSES.items():
            summary = ProcessSummary(
                id=proc.id,
                title=proc.title,
                description=proc.description,
                version=proc.version,
                jobControlOptions=proc.jobControlOptions,
                outputTransmission=proc.outputTransmission,
                links=[
                    Link(
                        href=f"{base_url}/processes/{proc_id}",
                        rel="self",
                        type="application/json",
                        title=f"Process: {proc.title}",
                    ),
                ],
            )
            summaries.append(summary)
        return summaries

    def get_process(self, process_id: str, base_url: str) -> ProcessDescription | None:
        """Get process description by ID."""
        proc = PROCESSES.get(process_id)
        if not proc:
            return None

        # Add links
        proc.links = [
            Link(
                href=f"{base_url}/processes/{process_id}",
                rel="self",
                type="application/json",
            ),
            Link(
                href=f"{base_url}/processes/{process_id}/execution",
                rel="http://www.opengis.net/def/rel/ogc/1.0/execute",
                type="application/json",
                title="Execute process",
            ),
        ]
        return proc

    async def execute_process(
        self, process_id: str, inputs: dict[str, Any], base_url: str
    ) -> dict[str, Any]:
        """Execute a process with given inputs.

        Args:
            process_id: ID of the process to execute
            inputs: Input values
            base_url: Base URL for building links

        Returns:
            Process output as dict
        """
        if process_id == "feature-count":
            return await self._execute_feature_count(inputs)
        elif process_id == "area-statistics":
            return await self._execute_area_statistics(inputs)
        elif process_id == "unique-values":
            return await self._execute_unique_values(inputs)
        elif process_id == "class-breaks":
            return await self._execute_class_breaks(inputs)
        else:
            raise ValueError(f"Unknown process: {process_id}")

    async def _get_layer_info(self, collection_id: str) -> tuple[str, list[dict], str]:
        """Get layer table name, columns, and geometry column.

        Returns:
            Tuple of (table_name, columns, geometry_column)
        """
        try:
            layer_uuid = UUID(collection_id)
        except ValueError:
            raise ValueError(f"Invalid collection ID: {collection_id}")

        # Get layer metadata from PostgreSQL
        metadata = await layer_service.get_metadata_by_id(layer_uuid)
        if not metadata:
            raise ValueError(f"Collection not found: {collection_id}")

        return metadata.table_name, metadata.columns, metadata.geometry_column

    def _build_where_clause(
        self,
        cql_filter: str | None,
        columns: list[dict],
        geometry_column: str,
    ) -> tuple[str, list[Any]]:
        """Build WHERE clause from CQL filter.

        Returns:
            Tuple of (where_sql, params)
        """
        if not cql_filter:
            return "TRUE", []

        try:
            column_names = [col["name"] for col in columns]
            ast = parse_cql2_filter(cql_filter, "cql2-json")
            cql_sql, cql_params = cql2_to_duckdb_sql(ast, column_names, geometry_column)
            return cql_sql, cql_params
        except Exception as e:
            logger.warning(f"CQL2 parse error: {e}")
            raise ValueError(f"Invalid CQL2 filter: {e}")

    async def _execute_feature_count(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute feature-count process."""
        inp = FeatureCountInput(**inputs)

        # Get layer info
        table_name, columns, geom_col = await self._get_layer_info(inp.collection)

        # Build WHERE clause
        where_sql, params = self._build_where_clause(inp.filter, columns, geom_col)

        # Execute count query
        query = f"SELECT COUNT(*) FROM lake.{table_name} WHERE {where_sql}"
        logger.debug("Feature count query: %s with params: %s", query, params)

        try:
            result = execute_query_with_retry(
                ducklake_manager, query, params if params else None, fetch_all=False
            )
            count = result[0] if result else 0
        except Exception as e:
            logger.error("Feature count query failed: %s", e)
            raise RuntimeError(f"Query execution failed: {e}")

        return FeatureCountOutput(count=count).model_dump()

    async def _execute_area_statistics(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute area-statistics process."""
        inp = AreaStatisticsInput(**inputs)

        # Get layer info
        table_name, columns, geom_col = await self._get_layer_info(inp.collection)

        # Build WHERE clause
        where_sql, params = self._build_where_clause(inp.filter, columns, geom_col)

        # Calculate area statistics using DuckDB spatial functions
        # Transform to a projected CRS (Web Mercator) for area calculation
        area_expr = f"ST_Area(ST_Transform(\"{geom_col}\", 'EPSG:4326', 'EPSG:3857'))"

        # Build aggregation based on operation
        if inp.operation.value == "sum":
            agg_expr = f"SUM({area_expr})"
        elif inp.operation.value == "mean":
            agg_expr = f"AVG({area_expr})"
        elif inp.operation.value == "min":
            agg_expr = f"MIN({area_expr})"
        elif inp.operation.value == "max":
            agg_expr = f"MAX({area_expr})"
        else:
            agg_expr = f"SUM({area_expr})"

        query = f"""
            SELECT
                {agg_expr} AS result,
                SUM({area_expr}) AS total_area,
                COUNT(*) AS feature_count
            FROM lake.{table_name}
            WHERE {where_sql}
        """
        logger.debug("Area statistics query: %s with params: %s", query, params)

        try:
            result = execute_query_with_retry(
                ducklake_manager, query, params if params else None, fetch_all=False
            )

            if result:
                return AreaStatisticsOutput(
                    result=result[0],
                    total_area=result[1],
                    feature_count=result[2],
                    unit="m²",
                ).model_dump()
            else:
                return AreaStatisticsOutput(
                    result=None,
                    total_area=None,
                    feature_count=0,
                ).model_dump()
        except Exception as e:
            logger.error("Area statistics query failed: %s", e)
            raise RuntimeError(f"Query execution failed: {e}")

    async def _execute_unique_values(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute unique-values process."""
        inp = UniqueValuesInput(**inputs)

        # Get layer info
        table_name, columns, geom_col = await self._get_layer_info(inp.collection)

        # Validate attribute exists
        column_names = [col["name"] for col in columns]
        if inp.attribute not in column_names:
            raise ValueError(f"Attribute not found: {inp.attribute}")

        # Build WHERE clause
        where_sql, params = self._build_where_clause(inp.filter, columns, geom_col)

        # Add null check
        attr_col = f'"{inp.attribute}"'
        where_sql = f"({where_sql}) AND {attr_col} IS NOT NULL"

        # Map order
        order_dir = "DESC" if inp.order.value == "descendent" else "ASC"

        # Get total count of unique values
        count_query = f"""
            SELECT COUNT(DISTINCT {attr_col})
            FROM lake.{table_name}
            WHERE {where_sql}
        """

        # Get unique values with counts
        data_query = f"""
            SELECT {attr_col} AS value, COUNT(*) AS cnt
            FROM lake.{table_name}
            WHERE {where_sql}
            GROUP BY {attr_col}
            ORDER BY cnt {order_dir}, {attr_col}
            LIMIT {inp.limit} OFFSET {inp.offset}
        """

        logger.debug("Unique values query: %s with params: %s", data_query, params)

        try:
            # Get total
            total_result = execute_query_with_retry(
                ducklake_manager,
                count_query,
                params if params else None,
                fetch_all=False,
            )
            total = total_result[0] if total_result else 0

            # Get values
            result = execute_query_with_retry(
                ducklake_manager, data_query, params if params else None, fetch_all=True
            )

            values = [UniqueValue(value=row[0], count=row[1]) for row in result]

            return UniqueValuesOutput(
                attribute=inp.attribute,
                total=total,
                values=values,
            ).model_dump()
        except Exception as e:
            logger.error("Unique values query failed: %s", e)
            raise RuntimeError(f"Query execution failed: {e}")

    async def _execute_class_breaks(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute class-breaks process."""
        inp = ClassBreaksInput(**inputs)

        # Get layer info
        table_name, columns, geom_col = await self._get_layer_info(inp.collection)

        # Validate attribute exists
        column_names = [col["name"] for col in columns]
        if inp.attribute not in column_names:
            raise ValueError(f"Attribute not found: {inp.attribute}")

        # Validate attribute is numeric
        attr_col_info = next(
            (col for col in columns if col["name"] == inp.attribute), None
        )
        if attr_col_info:
            json_type = attr_col_info.get("json_type", "")
            if json_type not in ("number", "integer"):
                raise ValueError(
                    f"Attribute '{inp.attribute}' is not numeric (type: {json_type})"
                )

        # Build WHERE clause
        where_sql, params = self._build_where_clause(inp.filter, columns, geom_col)

        # Add null check and optional zero stripping
        attr_col = f'"{inp.attribute}"'
        where_sql = f"({where_sql}) AND {attr_col} IS NOT NULL"
        if inp.strip_zeros:
            where_sql = f"{where_sql} AND {attr_col} != 0"

        # Get basic statistics first
        stats_query = f"""
            SELECT
                MIN({attr_col}) AS min_val,
                MAX({attr_col}) AS max_val,
                AVG({attr_col}) AS mean_val,
                STDDEV({attr_col}) AS std_dev
            FROM lake.{table_name}
            WHERE {where_sql}
        """

        logger.debug("Class breaks stats query: %s", stats_query)

        try:
            stats_result = execute_query_with_retry(
                ducklake_manager,
                stats_query,
                params if params else None,
                fetch_all=False,
            )

            if not stats_result or stats_result[0] is None:
                return ClassBreaksOutput(
                    attribute=inp.attribute,
                    method=inp.method.value,
                    breaks=[],
                    min=None,
                    max=None,
                    mean=None,
                    std_dev=None,
                ).model_dump()

            min_val, max_val, mean_val, std_dev = stats_result

            # Calculate breaks based on method
            # Use connection with retry for methods that need DB access
            with ducklake_manager.connection() as con:
                if inp.method.value == "quantile":
                    breaks = await self._calculate_quantile_breaks(
                        con, table_name, attr_col, where_sql, params, inp.breaks
                    )
                elif inp.method.value == "equal_interval":
                    breaks = self._calculate_equal_interval_breaks(
                        min_val, max_val, inp.breaks
                    )
                elif inp.method.value == "standard_deviation":
                    breaks = self._calculate_std_dev_breaks(
                        min_val, max_val, mean_val, std_dev, inp.breaks
                    )
                elif inp.method.value == "heads_and_tails":
                    breaks = await self._calculate_heads_tails_breaks(
                        con,
                        table_name,
                        attr_col,
                        where_sql,
                        params,
                        inp.breaks,
                        mean_val,
                    )
                else:
                    breaks = []

            return ClassBreaksOutput(
                attribute=inp.attribute,
                method=inp.method.value,
                breaks=breaks,
                min=float(min_val) if min_val is not None else None,
                max=float(max_val) if max_val is not None else None,
                mean=float(mean_val) if mean_val is not None else None,
                std_dev=float(std_dev) if std_dev is not None else None,
            ).model_dump()
        except Exception as e:
            logger.error("Class breaks query failed: %s", e)
            raise RuntimeError(f"Query execution failed: {e}")

    async def _calculate_quantile_breaks(
        self,
        con: Any,
        table_name: str,
        attr_col: str,
        where_sql: str,
        params: list[Any],
        num_breaks: int,
    ) -> list[float]:
        """Calculate quantile breaks using PERCENTILE_CONT."""
        # Generate percentile values (e.g., for 5 breaks: 0.2, 0.4, 0.6, 0.8, 1.0)
        percentiles = [i / num_breaks for i in range(1, num_breaks + 1)]

        # Build query with multiple PERCENTILE_CONT calls
        percentile_exprs = ", ".join(
            f"PERCENTILE_CONT({p}) WITHIN GROUP (ORDER BY {attr_col})"
            for p in percentiles
        )
        query = f"""
            SELECT {percentile_exprs}
            FROM lake.{table_name}
            WHERE {where_sql}
        """

        if params:
            result = con.execute(query, params).fetchone()
        else:
            result = con.execute(query).fetchone()

        if result:
            return [float(v) for v in result if v is not None]
        return []

    def _calculate_equal_interval_breaks(
        self, min_val: float, max_val: float, num_breaks: int
    ) -> list[float]:
        """Calculate equal interval breaks."""
        if min_val == max_val:
            return [float(min_val)]

        interval = (max_val - min_val) / num_breaks
        breaks = [min_val + interval * i for i in range(1, num_breaks + 1)]
        return [float(b) for b in breaks]

    def _calculate_std_dev_breaks(
        self,
        min_val: float,
        max_val: float,
        mean_val: float,
        std_dev: float,
        num_breaks: int,
    ) -> list[float]:
        """Calculate standard deviation breaks."""
        if std_dev is None or std_dev == 0:
            return self._calculate_equal_interval_breaks(min_val, max_val, num_breaks)

        # Generate breaks at standard deviation intervals around mean
        breaks = []
        half_breaks = num_breaks // 2

        for i in range(-half_breaks, half_breaks + 1):
            if i == 0:
                continue
            break_val = mean_val + (i * std_dev)
            if min_val <= break_val <= max_val:
                breaks.append(break_val)

        # Always include max
        if not breaks or breaks[-1] < max_val:
            breaks.append(max_val)

        return sorted([float(b) for b in breaks])

    async def _calculate_heads_tails_breaks(
        self,
        con: Any,
        table_name: str,
        attr_col: str,
        where_sql: str,
        params: list[Any],
        num_breaks: int,
        initial_mean: float,
    ) -> list[float]:
        """Calculate heads and tails breaks.

        Heads/tails algorithm iteratively splits data at the mean,
        taking the "head" (above mean) for the next iteration.
        """
        breaks = []
        current_mean = initial_mean
        current_where = where_sql

        for _ in range(num_breaks - 1):
            breaks.append(float(current_mean))

            # Get mean of values above current mean
            query = f"""
                SELECT AVG({attr_col})
                FROM lake.{table_name}
                WHERE {current_where} AND {attr_col} > ?
            """
            query_params = params + [current_mean] if params else [current_mean]

            result = con.execute(query, query_params).fetchone()

            if result and result[0] is not None:
                current_mean = result[0]
            else:
                break

        return sorted(breaks)


# Singleton instance
process_service = ProcessService()
