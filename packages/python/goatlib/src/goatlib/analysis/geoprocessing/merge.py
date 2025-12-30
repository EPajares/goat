import logging
from pathlib import Path
from typing import Dict, List, Optional, Self, Tuple

from goatlib.analysis.core.base import AnalysisTool
from goatlib.analysis.schemas.geoprocessing import MergeParams
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class MergeTool(AnalysisTool):
    """
    MergeTool: Combines multiple vector layers into a single layer using DuckDB Spatial.

    Features:
    - Merges 2+ layers of compatible geometry types
    - Automatic CRS harmonization (reproject all to target CRS)
    - Simple field handling (duplicate field names get suffixed with layer index)
    - Optional source tracking field (layer_source: 0, 1, 2, etc.)
    - Geometry type validation and promotion
    - Efficient DuckDB-based processing
    """

    def _run_implementation(
        self: Self, params: MergeParams
    ) -> List[Tuple[Path, DatasetMetadata]]:
        """Perform merge operation on multiple vector datasets."""

        if len(params.input_paths) < 2:
            raise ValueError("At least 2 input layers required for merge operation.")

        # --- Import all inputs and collect metadata
        layer_info = []
        for i, input_path in enumerate(params.input_paths):
            # Use unique table name for each input to avoid conflicts
            unique_table_name = f"v_input_{i}"
            meta, table_name = self.import_input(
                input_path, table_name=unique_table_name
            )
            layer_info.append(
                {
                    "index": i,
                    "path": Path(input_path),
                    "meta": meta,
                    "table": table_name,
                    "geom_col": meta.geometry_column,
                    "crs": meta.crs,
                    "geometry_type": meta.geometry_type,
                }
            )

            if not meta.geometry_column:
                raise ValueError(
                    f"Could not detect geometry column for layer {i}: {input_path}"
                )

        # --- Validate geometry compatibility
        if params.validate_geometry_types:
            self._validate_geometry_types(layer_info)

        # --- Determine target CRS
        target_crs = params.output_crs or (
            layer_info[0]["crs"].to_string() if layer_info[0]["crs"] else "EPSG:4326"
        )
        logger.info(f"Target CRS for merge: {target_crs}")

        # --- Determine output path
        if not params.output_path:
            params.output_path = str(
                Path(params.input_paths[0]).parent
                / f"{Path(params.input_paths[0]).stem}_merged.parquet"
            )
        output_path = Path(params.output_path)

        # --- Execute merge
        output_geom_type = self._execute_merge(
            params, layer_info, target_crs, output_path
        )

        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            format="geoparquet",
            crs=target_crs,
            geometry_type=output_geom_type,
        )

        logger.info(
            f"Merge completed: {len(params.input_paths)} layers → {output_path}"
        )
        return [(output_path, metadata)]

    def _validate_geometry_types(self, layer_info: List[Dict]) -> None:
        """
        Validate that all layers have compatible geometry types.

        Compatible types:
        - Point, MultiPoint → Point family
        - LineString, MultiLineString → LineString family
        - Polygon, MultiPolygon → Polygon family

        Raises ValueError if incompatible types found (e.g., Point + Polygon).
        """

        base_type = self._normalize_geometry_type(layer_info[0]["geometry_type"])

        for info in layer_info[1:]:
            geom_type = self._normalize_geometry_type(info["geometry_type"])
            if geom_type != base_type:
                raise ValueError(
                    f"Incompatible geometry types detected:\n"
                    f"  Layer 0 ({layer_info[0]['path'].name}): "
                    f"{layer_info[0]['geometry_type']} → {base_type} family\n"
                    f"  Layer {info['index']} ({info['path'].name}): "
                    f"{info['geometry_type']} → {geom_type} family\n"
                    f"Set validate_geometry_types=False to allow mixed geometries."
                )

        logger.info(f"✓ All layers have compatible geometry type: {base_type} family")

    def _normalize_geometry_type(self, geom_type: Optional[str]) -> str:
        """
        Normalize geometry type to base family type.

        Examples:
        - Point, MultiPoint → "Point"
        - LineString, MultiLineString → "LineString"
        - Polygon, MultiPolygon → "Polygon"
        """
        if not geom_type:
            return "Unknown"

        geom_lower = geom_type.lower()
        if "point" in geom_lower:
            return "Point"
        elif "line" in geom_lower:
            return "LineString"
        elif "polygon" in geom_lower:
            return "Polygon"
        return geom_type

    def _execute_merge(
        self,
        params: MergeParams,
        layer_info: List[Dict],
        target_crs: str,
        output_path: Path,
    ) -> str:
        """Execute the merge operation in DuckDB."""
        con = self.con

        # --- Step 1: Collect all columns from all layers and track which layer has which
        layer_columns: Dict[int, List[str]] = {}  # layer_idx -> list of columns
        all_columns: Dict[str, List[int]] = {}  # column_name -> list of layer indices

        for info in layer_info:
            layer_idx = info["index"]
            table_name = info["table"]
            geom_col = info["geom_col"]

            # Get column list from this layer (exclude geometry and bbox columns)
            cols_query = f"PRAGMA table_info({table_name})"
            columns = [
                row[1]
                for row in con.execute(cols_query).fetchall()
                if row[1] not in (geom_col, "bbox")
            ]

            layer_columns[layer_idx] = columns

            for col in columns:
                if col not in all_columns:
                    all_columns[col] = []
                all_columns[col].append(layer_idx)

        # --- Step 2: Resolve field conflicts (rename duplicates)
        # Fields appearing in multiple layers: field → field, field_1, field_2, etc.
        final_columns: List[str] = []  # Ordered list of all output columns
        column_mapping: Dict[int, Dict[str, str]] = {
            i: {} for i in range(len(layer_info))
        }

        for col, layer_indices in all_columns.items():
            if len(layer_indices) == 1:
                # Unique column - keep original name
                final_columns.append(col)
                column_mapping[layer_indices[0]][col] = col
            else:
                # Conflicting column - rename with suffix
                for i, layer_idx in enumerate(layer_indices):
                    if i == 0:
                        new_name = col  # First occurrence keeps original
                    else:
                        new_name = f"{col}_{i}"
                    final_columns.append(new_name)
                    column_mapping[layer_idx][col] = new_name

        if params.add_source_field:
            final_columns.append("layer_source")
        final_columns.append("geometry")

        logger.info(f"Output schema will have {len(final_columns)} columns")

        # --- Step 3: Create normalized SELECT for each layer with aligned columns
        normalized_selects = []

        for info in layer_info:
            layer_idx = info["index"]
            table_name = info["table"]
            geom_col = info["geom_col"]
            source_crs = info["crs"].to_string() if info["crs"] else None

            # Build SELECT parts for this layer
            select_parts = []

            # Add all non-geometry columns (with NULL for missing ones)
            for final_col in final_columns:
                if final_col == "layer_source":
                    continue  # Handle separately
                if final_col == "geometry":
                    continue  # Handle separately

                # Find original column name for this final column in this layer
                original_col = None
                for orig, mapped in column_mapping[layer_idx].items():
                    if mapped == final_col:
                        original_col = orig
                        break

                if original_col:
                    select_parts.append(f'"{original_col}" AS "{final_col}"')
                else:
                    select_parts.append(f'NULL AS "{final_col}"')

            # Add layer_source if requested
            if params.add_source_field:
                select_parts.append(f"{layer_idx} AS layer_source")

            # Add geometry with optional transform and promotion
            geom_transform = (
                f"ST_Transform({geom_col}, '{source_crs}', '{target_crs}')"
                if source_crs and source_crs != target_crs
                else geom_col
            )
            if params.promote_to_multi:
                geom_transform = f"ST_Multi({geom_transform})"
            select_parts.append(f"{geom_transform} AS geometry")

            select_query = f"SELECT {', '.join(select_parts)} FROM {table_name}"
            normalized_selects.append(select_query)

        # --- Step 4: Union all normalized selects
        union_query = " UNION ALL ".join(normalized_selects)

        con.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE merged AS
            {union_query}
            """
        )

        merged_count = con.execute("SELECT COUNT(*) FROM merged").fetchone()[0]
        logger.info(f"Merged table has {merged_count} rows")

        # --- Step 5: Export to output
        con.execute(
            f"COPY merged TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )

        # Determine output geometry type
        output_geom_type = layer_info[0]["geometry_type"]
        if params.promote_to_multi and not output_geom_type.startswith("Multi"):
            output_geom_type = f"Multi{output_geom_type}"

        return output_geom_type
