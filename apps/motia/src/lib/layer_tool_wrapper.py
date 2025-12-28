"""
Generic wrapper for running path-based tools with DuckLake layers.

This module provides a wrapper that:
1. Exports layers from DuckLake (with optional filters)
2. Runs the original *Tool with file paths
3. Optionally imports results back to DuckLake or returns parquet bytes

This allows any *Params/*Tool pair to work with DuckLake layers without
needing a manually-created *LayerTool class.
"""

import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from pydantic import BaseModel

from goatlib.analysis.core.base import AnalysisTool

logger = logging.getLogger(__name__)


@dataclass
class LayerToolResult:
    """Result of a layer tool operation."""

    # Output identification
    output_layer_id: Optional[str] = None  # Set if saved to DuckLake
    output_path: Optional[str] = None  # Set if returned as file

    # Result metadata
    feature_count: int = 0
    geometry_type: Optional[str] = None

    # Raw parquet bytes (only if output_layer_id was None)
    parquet_bytes: Optional[bytes] = None

    # Extra metadata from the tool
    extra: Dict[str, Any] = field(default_factory=dict)


class GenericLayerTool:
    """Generic wrapper for running path-based tools with DuckLake layers.

    This class wraps any *Tool class to work with DuckLake layer IDs.
    It automatically handles:
    - Exporting layers from DuckLake with optional SQL filters
    - Running the underlying tool with temp file paths
    - Importing results back to DuckLake or returning parquet bytes

    Auto-detection rules (no hardcoded mappings):
    - *_layer_id -> *_path (e.g., input_layer_id -> input_path)
    - *_layer_ids -> *_paths (e.g., input_layer_ids -> input_paths)
    - *_filter fields are used for SQL WHERE clauses

    Usage:
        from goatlib.analysis.vector import ClipTool
        from goatlib.analysis.schemas.vector import ClipParams

        wrapper = GenericLayerTool(
            tool_class=ClipTool,
            params_class=ClipParams,
            ducklake_manager=manager,
        )

        result = wrapper.run(layer_params)
    """

    def __init__(
        self,
        tool_class: Type[AnalysisTool],
        params_class: Type[BaseModel],
        ducklake_manager,
    ):
        """Initialize the generic layer tool.

        Args:
            tool_class: The original *Tool class (e.g., ClipTool)
            params_class: The original *Params class (e.g., ClipParams)
            ducklake_manager: DuckLake manager for layer operations
        """
        self.tool_class = tool_class
        self.params_class = params_class
        self.ducklake_manager = ducklake_manager

    def _export_layer_to_temp(
        self,
        layer_id: str,
        user_id: str,
        sql_filter: Optional[str] = None,
        temp_dir: str = None,
    ) -> Path:
        """Export a DuckLake layer to a temporary parquet file.

        Args:
            layer_id: UUID of the layer
            user_id: UUID of the user who owns the layer
            sql_filter: Optional SQL WHERE clause
            temp_dir: Optional temp directory path

        Returns:
            Path to the temporary parquet file
        """
        layer_uuid = UUID(layer_id)
        user_uuid = UUID(user_id)

        # Build the export query
        table_name = self.ducklake_manager.get_user_layer_table_name(
            user_id=user_uuid,
            layer_id=layer_uuid,
        )

        # Create temp file
        temp_dir_path = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        temp_file = temp_dir_path / f"{layer_id}.parquet"

        # Build export SQL
        if sql_filter:
            export_sql = f"SELECT * FROM {table_name} WHERE {sql_filter}"
        else:
            export_sql = f"SELECT * FROM {table_name}"

        # Export using DuckDB's COPY
        copy_sql = f"COPY ({export_sql}) TO '{temp_file}' (FORMAT PARQUET)"
        self.ducklake_manager.execute(copy_sql)

        logger.debug(f"Exported layer {layer_id} to {temp_file}")
        return temp_file

    def _import_result_to_layer(
        self,
        result_path: Path,
        user_id: str,
        output_layer_id: str,
    ) -> Dict[str, Any]:
        """Import a parquet result file into DuckLake.

        Args:
            result_path: Path to the result parquet file
            user_id: UUID of the user
            output_layer_id: UUID for the output layer

        Returns:
            Dict with import metadata
        """
        layer_uuid = UUID(output_layer_id)
        user_uuid = UUID(user_id)

        # Create the layer table
        table_name = self.ducklake_manager.get_user_layer_table_name(
            user_id=user_uuid,
            layer_id=layer_uuid,
        )

        # Import the parquet file
        import_sql = f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_parquet('{result_path}')
        """
        self.ducklake_manager.execute(import_sql)

        # Get row count
        count_result = self.ducklake_manager.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        )
        feature_count = count_result.fetchone()[0]

        logger.debug(f"Imported {feature_count} features to layer {output_layer_id}")

        return {
            "feature_count": feature_count,
            "output_layer_id": output_layer_id,
        }

    def run(self, layer_params: BaseModel) -> LayerToolResult:
        """Run the tool with DuckLake layers.

        Args:
            layer_params: LayerParams object with layer IDs instead of paths

        Returns:
            LayerToolResult with output info
        """
        # Extract user_id (required for all layer operations)
        user_id = getattr(layer_params, "user_id", None)
        if not user_id:
            raise ValueError("user_id is required for layer operations")

        # Create temp directory for this operation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Build path-based params from layer params
            path_params_data = {}
            temp_files: Dict[str, Path] = {}

            # Get all fields from layer_params
            layer_data = layer_params.model_dump()

            for field_name, value in layer_data.items():
                if value is None:
                    continue

                # Skip user_id and filter fields (handled separately)
                if field_name == "user_id":
                    continue
                if field_name.endswith("_filter"):
                    continue

                # Handle layer_id -> path conversion (auto-detected, no mapping needed)
                if field_name.endswith("_layer_id"):
                    # Get corresponding filter if any
                    filter_field = field_name.replace("_layer_id", "_filter")
                    sql_filter = layer_data.get(filter_field)

                    # Auto-convert: foo_layer_id -> foo_path
                    path_field = field_name.replace("_layer_id", "_path")

                    # Handle output_layer_id specially (destination, not export)
                    if field_name == "output_layer_id":
                        # Generate temp output path
                        temp_output = Path(temp_dir) / f"output_{value}.parquet"
                        path_params_data["output_path"] = str(temp_output)
                        temp_files["output"] = temp_output
                    else:
                        # Export the layer to temp file
                        temp_file = self._export_layer_to_temp(
                            layer_id=value,
                            user_id=user_id,
                            sql_filter=sql_filter,
                            temp_dir=temp_dir,
                        )
                        path_params_data[path_field] = str(temp_file)
                        temp_files[field_name] = temp_file

                elif field_name.endswith("_layer_ids"):
                    # Handle list of layer IDs (e.g., input_layer_ids)
                    path_field = field_name.replace("_layer_ids", "_paths")
                    paths = []
                    for i, lid in enumerate(value):
                        temp_file = self._export_layer_to_temp(
                            layer_id=lid,
                            user_id=user_id,
                            temp_dir=temp_dir,
                        )
                        paths.append(str(temp_file))
                    path_params_data[path_field] = paths

                else:
                    # Copy other fields directly
                    path_params_data[field_name] = value

            # If no output_path was set, create one
            if "output_path" not in path_params_data:
                temp_output = Path(temp_dir) / "output.parquet"
                path_params_data["output_path"] = str(temp_output)
                temp_files["output"] = temp_output

            # Create the path-based params
            params = self.params_class(**path_params_data)

            # Run the underlying tool
            tool = self.tool_class()
            results = tool.run(params)

            # Process results
            output_layer_id = getattr(layer_params, "output_layer_id", None)
            result_path = temp_files.get("output")

            if results and len(results) > 0:
                # Get the first result (most tools produce one output)
                result_path_from_tool, metadata = results[0]
                result_path = result_path_from_tool

            if not result_path or not result_path.exists():
                raise RuntimeError("Tool did not produce output file")

            # Import to DuckLake or return parquet bytes
            if output_layer_id:
                import_result = self._import_result_to_layer(
                    result_path=result_path,
                    user_id=user_id,
                    output_layer_id=output_layer_id,
                )
                return LayerToolResult(
                    output_layer_id=output_layer_id,
                    feature_count=import_result.get("feature_count", 0),
                )
            else:
                # Return parquet bytes
                parquet_bytes = result_path.read_bytes()
                return LayerToolResult(
                    output_path=str(result_path),
                    parquet_bytes=parquet_bytes,
                    feature_count=0,  # Would need to count from parquet
                )


def create_layer_tool(
    tool_class: Type[AnalysisTool],
    params_class: Type[BaseModel],
    ducklake_manager,
) -> GenericLayerTool:
    """Factory function to create a GenericLayerTool.

    Args:
        tool_class: The original *Tool class
        params_class: The original *Params class
        ducklake_manager: DuckLake manager instance

    Returns:
        Configured GenericLayerTool instance
    """
    return GenericLayerTool(
        tool_class=tool_class,
        params_class=params_class,
        ducklake_manager=ducklake_manager,
    )
