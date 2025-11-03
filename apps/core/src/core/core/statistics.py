from typing import Any, Dict

from core.db.models.layer import FeatureGeometryType
from core.schemas.error import (
    ColumnTypeError,
    GeometryTypeError,
)
from core.schemas.layer import OgrPostgresType
from core.schemas.project import IFeatureStandardProjectRead, IFeatureToolProjectRead
from core.schemas.toolbox_base import (
    ColumnStatisticsOperation,
)
from core.utils import search_value


class StatisticsBase:
    """Helper functions that support statistical operations for endpoints."""

    def convert_geom_measurement_field(self, field: str) -> str:
        if field.endswith("$intersected_area"):
            field = f"ST_AREA({field.replace('$intersected_area', 'geom')}::geography)"
        elif field.endswith("$length"):
            field = f"ST_LENGTH({field.replace('$length', 'geom')}::geography)"
        return field

    def get_statistics_sql(
        self,
        field: str | None,
        operation: ColumnStatisticsOperation,
    ) -> str:
        # Parse pseudo columns when a column name is supplied
        if field:
            field = self.convert_geom_measurement_field(field)

        if operation == ColumnStatisticsOperation.count:
            query = f"COUNT({field})" if field else "COUNT(*)"
        elif operation == ColumnStatisticsOperation.sum:
            query = f"SUM({field})"
        # elif operation == ColumnStatisticsOperation.mean:
        #     query = f"AVG({field})"
        # elif operation == ColumnStatisticsOperation.median:
        #     query = f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {field})"
        elif operation == ColumnStatisticsOperation.min:
            query = f"MIN({field})"
        elif operation == ColumnStatisticsOperation.max:
            query = f"MAX({field})"
        else:
            raise ValueError(f"Unsupported operation {operation}")

        return query

    async def check_column_statistics(
        self,
        layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead,
        column_name: str | None,
        operation: ColumnStatisticsOperation,
    ) -> Dict[str, Any]:
        """Check if the column statistics field is valid and return the mapped statistics field and the mapped statistics field type."""

        column_statistics_field = column_name
        column_statistics_operation = operation

        # Ensure a column name is supplied for all operations except "count"
        if (
            not column_statistics_field
            and column_statistics_operation != ColumnStatisticsOperation.count
        ):
            raise ValueError("Column name is required for all operations except count.")

        # Check if field is $intersected_area and geometry type is polygon
        if column_statistics_field == "$intersected_area":
            if layer_project.feature_layer_geometry_type != FeatureGeometryType.polygon:
                raise GeometryTypeError(
                    "The layer does not contain polygon geometries and therefore $intersected_area cannot be computed. Pick a layer with polygon geometries."
                )
            return {
                "mapped_statistics_field": "$intersected_area",
                "mapped_statistics_field_type": OgrPostgresType.Real.value,
            }

        # Get mapped column name of field if specified (some count operations do not require a field)
        mapped_statistics_field = None
        mapped_statistics_field_type = None
        if column_name:
            mapped_statistics_field = search_value(
                layer_project.attribute_mapping, column_statistics_field
            )
            mapped_statistics_field_type = mapped_statistics_field.split("_")[0]

        # Check if mapped statistics field is float, integer or biginteger if the operation is not count
        # Count operations do not always require a field and support non-numeric columns
        if column_statistics_operation != ColumnStatisticsOperation.count:
            await self.check_is_number(mapped_statistics_field_type)

        return {
            "mapped_statistics_field": mapped_statistics_field,
            "mapped_statistics_field_type": mapped_statistics_field_type,
        }

    async def check_is_number(self, data_type: str | None) -> None:
        """Check if the data type is a number."""
        if data_type not in [
            OgrPostgresType.Integer,
            OgrPostgresType.Real,
            OgrPostgresType.Integer64,
        ]:
            raise ColumnTypeError(
                f"Field has to be {OgrPostgresType.Integer}, {OgrPostgresType.Real}, {OgrPostgresType.Integer64}."
            )
