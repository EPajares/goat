import logging
from pathlib import Path
from typing import List, Optional, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.models.io import DatasetMetadata
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class RoutingParams(BaseModel):
    """
    Parameters for performing routing data extraction operations.
    """

    # Input and output configuration
    input_path: str | Path = Field(..., description="Path to the input dataset.")
    output_path: Optional[str | Path] = Field(
        None,
        description="Destination file path for routing output. If not provided, will auto-generate.",
    )

    # Custom SQL query for data extraction
    custom_sql: str = Field(
        ...,
        description="Custom SQL query to extract network data from the input table. "
        "Should select columns: edge_id, source, target, cost, geometry",
    )

    # Optional output CRS
    output_crs: Optional[str] = Field(
        "EPSG:4326",
        description="Target coordinate reference system for the output geometry.",
    )

    @model_validator(mode="after")
    def check_all_fields(self: Self) -> "RoutingParams":
        # 1. Validate input_path
        input_p = Path(self.input_path)
        if not input_p.exists():
            raise ValueError(f"Input file does not exist: {self.input_path}")
        if not input_p.is_file():
            raise ValueError(f"Input path is not a file: {self.input_path}")

        # 2. Validate output_path parent
        if self.output_path:
            parent_dir = Path(self.output_path).parent
            if not parent_dir.exists():
                raise ValueError(
                    f"Parent directory for output does not exist: {parent_dir}"
                )

        # 3. Validate custom_sql
        if not self.custom_sql or not self.custom_sql.strip():
            raise ValueError("The 'custom_sql' parameter cannot be empty.")

        return self


class RoutingTool(AnalysisTool):
    """
    RoutingTool: Network data extraction utilities for routing applications.
    """

    def _run_implementation(
        self: Self, params: RoutingParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform routing data extraction from SQL database."""

        # --- Import directly into DuckDB
        meta, table_name = self.import_input(params.input_path)
        geom_col = meta.geometry_column
        crs = meta.crs

        # For routing, we can work with text geometry as well
        # Set defaults if detection fails
        if not geom_col:
            logger.warning(
                f"Could not detect geometry column for {params.input_path}. Assuming 'geometry'."
            )
            geom_col = "geometry"

        if not crs:
            logger.warning(
                f"Could not detect CRS for {params.input_path}. Assuming 'EPSG:4326'."
            )
            crs_str = "EPSG:4326"
        else:
            crs_str = crs.to_string()

        # --- Define output path
        if not params.output_path:
            params.output_path = str(
                Path(params.input_path).parent
                / f"{Path(params.input_path).stem}_routing.parquet"
            )
        output_path = Path(params.output_path)
        logger.info(
            "Starting routing data extraction: %s | table='%s' | geometry='%s' | CRS=%s",
            params.input_path,
            table_name,
            geom_col,
            crs_str,
        )

        # --- Execute routing data extraction
        self._execute_routing_extraction(params, output_path, table_name)

        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            format="geoparquet",
            crs=crs_str or params.output_crs,
            geometry_type="LineString",
        )

        return [(output_path, metadata)]

    def _execute_routing_extraction(
        self: Self,
        params: RoutingParams,
        output_path: Path,
        table_name: str,
    ) -> None:
        """Execute SQL query for routing data extraction and save to disk."""

        # Get custom SQL query from params
        sql_query = params.custom_sql

        if not sql_query:
            raise ValueError(
                f"Custom SQL query is required. Please provide 'custom_sql' parameter "
                f"that selects network data from table '{table_name}'."
            )

        logger.info(f"Executing SQL query: {sql_query[:200]}...")

        try:
            con = self.con

            # Execute the custom SQL query directly and export to Parquet
            con.execute(
                f"""
                COPY (
                    {sql_query}
                ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
                """
            )

            logger.info(f"Network file created: {output_path}")

        except Exception as e:
            logger.error(f"Failed to execute routing extraction: {e}")
            raise


def extract_network(input_file: str, custom_sql: str, output_file: str = None) -> str:
    """
    Quick function to extract network data for testing.

    Args:
        input_file: Path to input file (GeoParquet, Shapefile, etc.)
        custom_sql: SQL query to extract network data
        output_file: Output path (optional, will auto-generate if not provided)

    Returns:
        Path to the created network file
    """
    # Create params with custom_sql
    params = RoutingParams(
        input_path=input_file, output_path=output_file, custom_sql=custom_sql
    )

    # Create and run the tool
    tool = RoutingTool()
    results = tool.run(params)

    return str(results[0][0])
