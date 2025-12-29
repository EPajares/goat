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

from goatlib.analysis.statistics import (
    calculate_area_statistics,
    calculate_class_breaks,
    calculate_feature_count,
    calculate_unique_values,
)
from goatlib.storage import cql2_to_duckdb_sql, parse_cql2_filter

from geoapi.ducklake import ducklake_manager
from geoapi.models import (
    AreaStatisticsInput,
    ClassBreaksInput,
    FeatureCountInput,
    InputDescription,
    JobControlOptions,
    Link,
    OutputDescription,
    ProcessDescription,
    ProcessSummary,
    TransmissionMode,
    UniqueValuesInput,
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

        try:
            with ducklake_manager.connection() as con:
                result = calculate_feature_count(
                    con,
                    f"lake.{table_name}",
                    where_sql,
                    params if params else None,
                )
            return result.model_dump()
        except Exception as e:
            logger.error("Feature count query failed: %s", e)
            raise RuntimeError(f"Query execution failed: {e}")

    async def _execute_area_statistics(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute area-statistics process."""
        inp = AreaStatisticsInput(**inputs)

        # Get layer info
        table_name, columns, geom_col = await self._get_layer_info(inp.collection)

        # Build WHERE clause
        where_sql, params = self._build_where_clause(inp.filter, columns, geom_col)

        try:
            with ducklake_manager.connection() as con:
                result = calculate_area_statistics(
                    con,
                    f"lake.{table_name}",
                    geom_col,
                    operation=inp.operation,
                    where_clause=where_sql,
                    params=params if params else None,
                )
            return result.model_dump()
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

        try:
            with ducklake_manager.connection() as con:
                result = calculate_unique_values(
                    con,
                    f"lake.{table_name}",
                    inp.attribute,
                    where_clause=where_sql,
                    params=params if params else None,
                    order=inp.order,
                    limit=inp.limit,
                    offset=inp.offset,
                )
            return result.model_dump()
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

        try:
            with ducklake_manager.connection() as con:
                result = calculate_class_breaks(
                    con,
                    f"lake.{table_name}",
                    inp.attribute,
                    method=inp.method,
                    num_breaks=inp.breaks,
                    where_clause=where_sql,
                    params=params if params else None,
                    strip_zeros=inp.strip_zeros,
                )
            return result.model_dump()
        except Exception as e:
            logger.error("Class breaks query failed: %s", e)
            raise RuntimeError(f"Query execution failed: {e}")


# Singleton instance
process_service = ProcessService()
