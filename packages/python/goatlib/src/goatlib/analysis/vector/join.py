import logging
from pathlib import Path
from typing import List, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.vector import (
    JoinOperationType,
    JoinParams,
    JoinType,
    MultipleMatchingRecordsType,
    SpatialRelationshipType,
    StatisticOperation,
)
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class JoinTool(AnalysisTool):
    """
    JoinTool: Performs spatial and attribute-based joins using DuckDB Spatial.
    """

    def _run_implementation(
        self: Self, params: JoinParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform join operation on vector datasets."""

        # Import target and join datasets
        target_meta, target_table = self.import_input(params.target_path, "target")
        join_meta, join_table = self.import_input(params.join_path, "join_data")

        # Validate geometry columns for spatial joins
        if params.use_spatial_relationship:
            target_geom = target_meta.geometry_column
            join_geom = join_meta.geometry_column

            if not target_geom or not join_geom:
                raise ValueError(
                    "Spatial join requires geometry columns in both datasets. "
                    f"Target: {target_geom}, Join: {join_geom}"
                )

        # Define output path
        output_path = Path(params.output_path)

        logger.info(
            "Starting join: target='%s' | join='%s' | spatial=%s | attribute=%s",
            params.target_path,
            params.join_path,
            params.use_spatial_relationship,
            params.use_attribute_relationship,
        )

        # Execute join operation
        self._execute_join(
            params, target_table, join_table, target_meta, join_meta, output_path
        )

        # Determine output geometry type
        output_geometry_type = None
        if target_meta.geometry_column:
            output_geometry_type = target_meta.geometry_type

        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            format="geoparquet",
            crs=target_meta.crs,
            geometry_type=output_geometry_type,
        )

        logger.info("Join completed successfully → %s", output_path)
        return [(output_path, metadata)]

    def _execute_join(
        self: Self,
        params: JoinParams,
        target_table: str,
        join_table: str,
        target_meta: any,
        join_meta: any,
        output_path: Path,
    ) -> None:
        """Execute the join operation in DuckDB."""

        # Build join condition
        join_conditions = []

        # Add spatial conditions
        if params.use_spatial_relationship:
            spatial_condition = self._build_spatial_condition(
                params, target_meta.geometry_column, join_meta.geometry_column
            )
            join_conditions.append(spatial_condition)

        # Add attribute conditions
        if params.use_attribute_relationship:
            for attr_rel in params.attribute_relationships:
                attr_condition = (
                    f"target.{attr_rel.target_field} = join_data.{attr_rel.join_field}"
                )
                join_conditions.append(attr_condition)

        # Combine all conditions with AND
        full_join_condition = " AND ".join(join_conditions)

        # Determine join type (INNER vs LEFT)
        join_type_sql = (
            "LEFT JOIN" if params.join_type == JoinType.left else "INNER JOIN"
        )

        # Handle different join operations
        if params.join_operation == JoinOperationType.one_to_many:
            self._execute_one_to_many_join(
                params,
                target_table,
                join_table,
                full_join_condition,
                join_type_sql,
                output_path,
            )
        else:
            self._execute_one_to_one_join(
                params,
                target_table,
                join_table,
                full_join_condition,
                join_type_sql,
                output_path,
            )

    def _build_spatial_condition(
        self: Self, params: JoinParams, target_geom: str, join_geom: str
    ) -> str:
        """Build spatial relationship condition for SQL."""
        target_geom_ref = f"target.{target_geom}"
        join_geom_ref = f"join_data.{join_geom}"

        if params.spatial_relationship == SpatialRelationshipType.intersects:
            return f"ST_Intersects({target_geom_ref}, {join_geom_ref})"
        elif params.spatial_relationship == SpatialRelationshipType.within_distance:
            return (
                f"ST_Distance({target_geom_ref}, {join_geom_ref}) <= {params.distance}"
            )
        elif params.spatial_relationship == SpatialRelationshipType.identical_to:
            return f"ST_Equals({target_geom_ref}, {join_geom_ref})"
        elif params.spatial_relationship == SpatialRelationshipType.completely_contains:
            return f"ST_Contains({target_geom_ref}, {join_geom_ref})"
        elif params.spatial_relationship == SpatialRelationshipType.completely_within:
            return f"ST_Within({target_geom_ref}, {join_geom_ref})"
        else:
            raise ValueError(
                f"Unsupported spatial relationship: {params.spatial_relationship}"
            )

    def _execute_one_to_many_join(
        self: Self,
        params: JoinParams,
        target_table: str,
        join_table: str,
        join_condition: str,
        join_type_sql: str,
        output_path: Path,
    ) -> None:
        """Execute one-to-many join (preserves all matching records)."""
        con = self.con

        # Build select clause with prefixed join fields to avoid conflicts
        target_fields = self._get_table_fields(target_table, "target")
        join_fields = self._get_table_fields(join_table, "join_data", prefix="join_")

        select_fields = ", ".join(target_fields + join_fields)

        query = f"""
        COPY (
            SELECT {select_fields}
            FROM {target_table} target
            {join_type_sql} {join_table} join_data
            ON {join_condition}
        ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """

        logger.info("Executing one-to-many join")
        con.execute(query)

    def _execute_one_to_one_join(
        self: Self,
        params: JoinParams,
        target_table: str,
        join_table: str,
        join_condition: str,
        join_type_sql: str,
        output_path: Path,
    ) -> None:
        """Execute one-to-one join with multiple matching records handling."""

        if params.multiple_matching_records == MultipleMatchingRecordsType.first_record:
            self._execute_first_record_join(
                params,
                target_table,
                join_table,
                join_condition,
                join_type_sql,
                output_path,
            )
        elif (
            params.multiple_matching_records
            == MultipleMatchingRecordsType.calculate_statistics
        ):
            self._execute_statistical_join(
                params,
                target_table,
                join_table,
                join_condition,
                join_type_sql,
                output_path,
            )
        else:  # count_only
            self._execute_count_only_join(
                params,
                target_table,
                join_table,
                join_condition,
                join_type_sql,
                output_path,
            )

    def _execute_first_record_join(
        self: Self,
        params: JoinParams,
        target_table: str,
        join_table: str,
        join_condition: str,
        join_type_sql: str,
        output_path: Path,
    ) -> None:
        """Execute join keeping only first matching record per target feature."""
        con = self.con

        # Create ranked join results
        order_clause = ""
        if params.sort_configuration:
            order_direction = (
                "DESC"
                if params.sort_configuration.sort_order == "descending"
                else "ASC"
            )
            order_clause = f"ORDER BY join_data.{params.sort_configuration.field} {order_direction}"

        target_fields = self._get_table_fields(target_table, "target")
        join_fields = self._get_table_fields(join_table, "join_data", prefix="join_")

        # Get properly formatted field lists
        target_fields = self._get_table_fields(target_table, "target")
        join_fields = self._get_table_fields(join_table, "join_data", prefix="join_")
        all_select_fields = ", ".join(target_fields + join_fields)

        # Create window function to rank matches
        con.execute(f"""
        CREATE OR REPLACE TEMP TABLE ranked_joins AS
        WITH joined_data AS (
            SELECT {all_select_fields},
                   ROW_NUMBER() OVER (
                       PARTITION BY {self._get_target_key_fields(target_table)}
                       {order_clause}
                   ) as rn
            FROM {target_table} target
            {join_type_sql} {join_table} join_data
            ON {join_condition}
        )
        SELECT * EXCLUDE (rn)
        FROM joined_data
        WHERE rn = 1 OR rn IS NULL  -- Keep first match or unmatched targets (for LEFT JOIN)
        """)

        con.execute(
            f"COPY ranked_joins TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

    def _execute_statistical_join(
        self: Self,
        params: JoinParams,
        target_table: str,
        join_table: str,
        join_condition: str,
        join_type_sql: str,
        output_path: Path,
    ) -> None:
        """Execute join with statistical aggregation of multiple matches."""
        con = self.con

        # Build aggregation expressions
        agg_expressions = ["COUNT(*) as match_count"]

        for field_stat in params.field_statistics:
            field_name = field_stat.field
            for operation in field_stat.operations:
                agg_expr = self._build_aggregation_expression(operation, field_name)
                agg_expressions.append(f"{agg_expr} as {field_name}_{operation.value}")

        agg_clause = ", ".join(agg_expressions)

        query = f"""
        CREATE OR REPLACE TEMP TABLE aggregated_joins AS
        SELECT {', '.join([f'target.{f}' for f in self._get_raw_field_names(target_table)])},
               {agg_clause}
        FROM {target_table} target
        {join_type_sql} {join_table} join_data
        ON {join_condition}
        GROUP BY {', '.join([f'target.{f}' for f in self._get_raw_field_names(target_table)])}
        """

        con.execute(query)
        con.execute(
            f"COPY aggregated_joins TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

    def _execute_count_only_join(
        self: Self,
        params: JoinParams,
        target_table: str,
        join_table: str,
        join_condition: str,
        join_type_sql: str,
        output_path: Path,
    ) -> None:
        """Execute join with only count of matches."""
        con = self.con

        query = f"""
        CREATE OR REPLACE TEMP TABLE count_joins AS
        SELECT {', '.join([f'target.{f}' for f in self._get_raw_field_names(target_table)])},
               COUNT(join_data.*) as match_count
        FROM {target_table} target
        {join_type_sql} {join_table} join_data
        ON {join_condition}
        GROUP BY {', '.join([f'target.{f}' for f in self._get_raw_field_names(target_table)])}
        """

        con.execute(query)
        con.execute(
            f"COPY count_joins TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

    def _build_aggregation_expression(
        self: Self, operation: StatisticOperation, field_name: str
    ) -> str:
        """Build SQL aggregation expression for statistics."""
        field_ref = f"join_data.{field_name}"

        if operation == StatisticOperation.sum:
            return f"SUM({field_ref})"
        elif operation == StatisticOperation.min:
            return f"MIN({field_ref})"
        elif operation == StatisticOperation.max:
            return f"MAX({field_ref})"
        elif operation == StatisticOperation.mean:
            return f"AVG({field_ref})"
        elif operation == StatisticOperation.count:
            return f"COUNT({field_ref})"
        elif operation == StatisticOperation.standard_deviation:
            return f"STDDEV({field_ref})"
        else:
            raise ValueError(f"Unsupported statistical operation: {operation}")

    def _get_table_fields(
        self: Self, table_name: str, alias: str, prefix: str = ""
    ) -> List[str]:
        """Get formatted field list for SELECT clause."""
        con = self.con

        # Get column names
        result = con.execute(f"PRAGMA table_info({table_name})").fetchall()
        columns = [row[1] for row in result]  # Column name is at index 1

        formatted_fields = []
        for col in columns:
            if prefix:
                formatted_fields.append(f"{alias}.{col} as {prefix}{col}")
            else:
                formatted_fields.append(f"{alias}.{col}")

        return formatted_fields

    def _get_raw_field_names(self: Self, table_name: str) -> List[str]:
        """Get raw field names for GROUP BY clauses."""
        con = self.con
        result = con.execute(f"PRAGMA table_info({table_name})").fetchall()
        return [row[1] for row in result]  # Column name is at index 1

    def _get_target_key_fields(self: Self, table_name: str) -> str:
        """Get target key fields for partitioning in window functions."""
        # For now, use all fields. In a more sophisticated implementation,
        # we could detect primary key or use geometry column + a subset of fields
        fields = self._get_raw_field_names(table_name)
        return ", ".join([f"target.{f}" for f in fields])
