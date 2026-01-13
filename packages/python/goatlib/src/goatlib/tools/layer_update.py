"""LayerUpdate Tool - Update layer data while preserving metadata and IDs.

This tool handles updating layer data without changing the layer ID:
1. Imports new data from S3 (file upload) or refreshes from WFS
2. Replaces DuckLake table data (DROP + CREATE)
3. Updates PostgreSQL metadata (extent, size, feature_count, etc.)
4. Preserves: layer ID, folder, name, description, tags, style, project links

Usage:
    from goatlib.tools.layer_update import LayerUpdateParams, main

    # Update from new file upload
    result = main(LayerUpdateParams(
        user_id="...",
        layer_id="...",
        s3_key="uploads/new_data.gpkg",
    ))

    # Refresh WFS layer
    result = main(LayerUpdateParams(
        user_id="...",
        layer_id="...",
        refresh_wfs=True,
    ))
"""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any, Self

from pydantic import ConfigDict, Field, model_validator

from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    ui_field,
    ui_sections,
)
from goatlib.io.converter import IOConverter
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import SimpleToolRunner
from goatlib.tools.schemas import ToolInputBase

logger = logging.getLogger(__name__)


class LayerUpdateParams(ToolInputBase):
    """Parameters for LayerUpdate tool."""

    model_config = ConfigDict(json_schema_extra=ui_sections(SECTION_INPUT))

    layer_id: str = Field(
        ...,
        description="ID of the layer to update",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            widget="layer-selector",
        ),
    )
    s3_key: str | None = Field(
        None,
        description="S3 object key for new data file (for file-based layers)",
        json_schema_extra=ui_field(
            section="input",
            field_order=2,
            mutually_exclusive_group="update_source",
        ),
    )
    refresh_wfs: bool = Field(
        False,
        description="Refresh data from WFS source (for WFS layers)",
        json_schema_extra=ui_field(
            section="input",
            field_order=3,
            mutually_exclusive_group="update_source",
        ),
    )

    @model_validator(mode="after")
    def validate_update_source(self: Self) -> Self:
        """Ensure exactly one update source is specified."""
        if not self.s3_key and not self.refresh_wfs:
            raise ValueError("Either s3_key or refresh_wfs must be specified")
        if self.s3_key and self.refresh_wfs:
            raise ValueError("Cannot specify both s3_key and refresh_wfs")
        return self


class LayerUpdateOutput(ToolInputBase):
    """Output schema for LayerUpdate tool."""

    layer_id: str
    updated: bool = False
    feature_count: int | None = None
    size: int | None = None
    geometry_type: str | None = None
    error: str | None = None


class LayerUpdateRunner(SimpleToolRunner):
    """Runner for LayerUpdate tool.

    Extends SimpleToolRunner for shared infrastructure (DuckDB, settings, logging).
    Reuses import logic from layer_import for S3 and WFS data loading.
    """

    def __init__(self: Self) -> None:
        """Initialize runner."""
        super().__init__()
        self._converter: IOConverter | None = None

    @property
    def converter(self: Self) -> IOConverter:
        """Lazy-load IOConverter."""
        if self._converter is None:
            self._converter = IOConverter()
        return self._converter

    def _get_s3_client(self: Self) -> Any:
        """Get or create S3 client."""
        if self.settings is None:
            raise RuntimeError("Settings not initialized")
        return self.settings.get_s3_client()

    def _import_from_s3(
        self: Self, s3_key: str, temp_dir: Path, output_path: Path
    ) -> DatasetMetadata:
        """Import file from S3 and convert to GeoParquet.

        Args:
            s3_key: S3 object key
            temp_dir: Temporary directory for downloaded file
            output_path: Path for output parquet file

        Returns:
            Dataset metadata from conversion
        """
        if self.settings is None:
            raise RuntimeError("Settings not initialized")

        logger.info(
            "S3 Settings: provider=%s, endpoint=%s, bucket=%s, region=%s",
            self.settings.s3_provider,
            self.settings.s3_endpoint_url,
            self.settings.s3_bucket_name,
            self.settings.s3_region_name,
        )
        logger.info("S3 Key: %s", s3_key)

        # Download file directly using boto3
        client = self._get_s3_client()
        filename = Path(s3_key).name
        local_file = temp_dir / filename

        logger.info(
            "Downloading s3://%s/%s to %s",
            self.settings.s3_bucket_name,
            s3_key,
            local_file,
        )
        client.download_file(self.settings.s3_bucket_name, s3_key, str(local_file))

        # Convert to GeoParquet using IOConverter
        metadata = self.converter.to_parquet(
            src_path=str(local_file),
            out_path=str(output_path),
            target_crs="EPSG:4326",
        )

        logger.info(
            "S3 import complete: %d features, format=%s",
            metadata.feature_count or 0,
            metadata.format,
        )
        return metadata

    def _import_from_wfs(
        self: Self,
        wfs_url: str,
        layer_name: str | None,
        temp_dir: Path,
        output_path: Path,
    ) -> DatasetMetadata:
        """Import layer from WFS service.

        Args:
            wfs_url: WFS service URL
            layer_name: Specific layer name (None = first layer)
            temp_dir: Temporary directory for intermediate files
            output_path: Path for output parquet file

        Returns:
            Dataset metadata from WFS import
        """
        logger.info("Importing from WFS: %s (layer=%s)", wfs_url, layer_name)

        # Import lazily to avoid GDAL dependency when not using WFS
        from goatlib.io.remote_source.wfs import from_wfs

        # Use goatlib WFS reader
        results = from_wfs(
            url=wfs_url,
            out_dir=str(temp_dir),
            layer=layer_name,
            target_crs="EPSG:4326",
        )

        if not results or results == (None, None):
            raise ValueError(f"No data retrieved from WFS: {wfs_url}")

        # Get first result (from_wfs can return list or tuple)
        if isinstance(results, list):
            parquet_path, metadata = results[0]
        else:
            parquet_path, metadata = results

        # Move to expected output path
        shutil.move(str(parquet_path), str(output_path))

        logger.info(
            "WFS import complete: %d features",
            metadata.feature_count or 0,
        )
        return metadata

    def _replace_ducklake_table(
        self: Self,
        layer_id: str,
        owner_id: str,
        parquet_path: Path,
    ) -> dict[str, Any]:
        """Replace DuckLake table with new data.

        Performs DROP TABLE followed by CREATE TABLE from parquet.
        Returns table metadata (feature_count, extent, geometry_type, etc.)

        Args:
            layer_id: Layer UUID
            owner_id: Layer owner's UUID
            parquet_path: Path to new parquet file

        Returns:
            Dict with table metadata
        """
        user_schema = f"user_{owner_id.replace('-', '')}"
        table_name = f"t_{layer_id.replace('-', '')}"
        full_table = f"lake.{user_schema}.{table_name}"

        # Get file size before ingestion
        file_size = parquet_path.stat().st_size if parquet_path.exists() else 0

        con = self.duckdb_con

        # Drop existing table
        logger.info("Dropping existing DuckLake table: %s", full_table)
        con.execute(f"DROP TABLE IF EXISTS {full_table}")

        # Detect geometry column for Hilbert ordering
        cols = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')"
        ).fetchall()
        geom_col = None
        for col_name, col_type, *_ in cols:
            if "GEOMETRY" in col_type.upper():
                geom_col = col_name
                break

        # Create table from parquet with Hilbert ordering for spatial locality
        if geom_col:
            con.execute(f"""
                CREATE TABLE {full_table} AS
                SELECT * FROM read_parquet('{parquet_path}')
                ORDER BY ST_Hilbert({geom_col})
            """)
            logger.info(
                "Created DuckLake table: %s (Hilbert-sorted by %s)",
                full_table,
                geom_col,
            )
        else:
            con.execute(f"""
                CREATE TABLE {full_table} AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)
            logger.info("Created DuckLake table: %s", full_table)

        # Get table metadata
        table_info = self._get_table_info(con, full_table)
        table_info["table_name"] = full_table
        table_info["size"] = file_size

        return table_info

    def _get_table_info(self: Self, con: Any, table_name: str) -> dict[str, Any]:
        """Get metadata about a DuckLake table.

        Args:
            con: DuckDB connection
            table_name: Full table path (lake.schema.table)

        Returns:
            Dict with columns, feature_count, extent, geometry_type, extent_wkt
        """
        # Get column names and types
        cols = con.execute(f"DESCRIBE {table_name}").fetchall()
        columns = {row[0]: row[1] for row in cols}

        # Get row count
        count_result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        feature_count = count_result[0] if count_result else 0

        # Find geometry column and get extent + type
        geometry_type = None
        extent = None
        extent_wkt = None

        for col_name, col_type in columns.items():
            if "GEOMETRY" in col_type.upper():
                # Get geometry type from first non-null geometry
                type_result = con.execute(f"""
                    SELECT ST_GeometryType({col_name})
                    FROM {table_name}
                    WHERE {col_name} IS NOT NULL
                    LIMIT 1
                """).fetchone()
                if type_result:
                    geometry_type = type_result[0]

                # Get extent
                extent_result = con.execute(f"""
                    SELECT ST_Extent({col_name})::VARCHAR
                    FROM {table_name}
                """).fetchone()
                if extent_result and extent_result[0]:
                    extent = extent_result[0]
                    # Convert BOX to WKT polygon for PostgreSQL
                    # BOX format: BOX(minX minY, maxX maxY)
                    try:
                        box_str = extent_result[0]
                        if box_str.startswith("BOX("):
                            coords = box_str[4:-1].split(", ")
                            min_coords = coords[0].split(" ")
                            max_coords = coords[1].split(" ")
                            min_x, min_y = float(min_coords[0]), float(min_coords[1])
                            max_x, max_y = float(max_coords[0]), float(max_coords[1])
                            extent_wkt = (
                                f"POLYGON(({min_x} {min_y}, {max_x} {min_y}, "
                                f"{max_x} {max_y}, {min_x} {max_y}, {min_x} {min_y}))"
                            )
                    except (ValueError, IndexError) as e:
                        logger.warning("Failed to parse extent: %s", e)

                break  # Only process first geometry column

        return {
            "columns": columns,
            "feature_count": feature_count,
            "extent": extent,
            "extent_wkt": extent_wkt,
            "geometry_type": geometry_type,
        }

    async def _get_layer_full_info(
        self: Self, layer_id: str, user_id: str
    ) -> dict[str, Any]:
        """Get full layer info and verify ownership.

        Args:
            layer_id: Layer UUID
            user_id: User UUID (must be owner)

        Returns:
            Dict with full layer info including other_properties

        Raises:
            PermissionError: If user doesn't own the layer
            ValueError: If layer not found
        """
        import uuid as uuid_module

        pool = await self.get_postgres_pool()

        try:
            row = await pool.fetchrow(
                f"""
                SELECT id, user_id, folder_id, name, type, data_type,
                       feature_layer_type, feature_layer_geometry_type,
                       attribute_mapping, other_properties
                FROM {self.settings.customer_schema}.layer
                WHERE id = $1
                """,
                uuid_module.UUID(layer_id),
            )

            if not row:
                raise ValueError(f"Layer not found: {layer_id}")

            owner_id = str(row["user_id"])
            if owner_id != user_id:
                raise PermissionError(
                    f"User {user_id} cannot update layer {layer_id} owned by {owner_id}"
                )

            return {
                "id": str(row["id"]),
                "user_id": owner_id,
                "folder_id": str(row["folder_id"]),
                "name": row["name"],
                "type": row["type"],
                "data_type": row["data_type"],
                "feature_layer_type": row["feature_layer_type"],
                "geometry_type": row["feature_layer_geometry_type"],
                "attribute_mapping": row["attribute_mapping"] or {},
                "other_properties": row["other_properties"] or {},
            }
        finally:
            await pool.close()

    async def _update_layer_metadata(
        self: Self,
        layer_id: str,
        feature_count: int,
        extent_wkt: str | None,
        size: int,
        geometry_type: str | None,
        attribute_mapping: dict[str, Any] | None,
    ) -> None:
        """Update layer metadata in PostgreSQL after data refresh.

        Updates only data-derived fields, preserving user-set metadata.

        Args:
            layer_id: Layer UUID
            feature_count: New feature count
            extent_wkt: New extent as WKT
            size: New file size in bytes
            geometry_type: New geometry type (normalized)
            attribute_mapping: New attribute mapping
        """
        import json
        import uuid as uuid_module

        from goatlib.tools.db import normalize_geometry_type

        pool = await self.get_postgres_pool()

        try:
            # Normalize geometry type to match schema enum
            normalized_geom = normalize_geometry_type(geometry_type)

            # Build dynamic UPDATE query
            updates = ["updated_at = NOW()"]
            params: list[Any] = [uuid_module.UUID(layer_id)]
            param_idx = 2

            # Always update size
            updates.append(f"size = ${param_idx}")
            params.append(size)
            param_idx += 1

            # Note: feature_count is not stored directly in the layer table
            # It's queried on-demand from DuckLake via geoapi

            if extent_wkt:
                updates.append(
                    f"extent = ST_Multi(ST_GeomFromText(${param_idx}, 4326))"
                )
                params.append(extent_wkt)
                param_idx += 1

            if normalized_geom:
                updates.append(f"feature_layer_geometry_type = ${param_idx}")
                params.append(normalized_geom)
                param_idx += 1

            if attribute_mapping:
                updates.append(f"attribute_mapping = ${param_idx}::jsonb")
                params.append(json.dumps(attribute_mapping))
                param_idx += 1

            await pool.execute(
                f"""
                UPDATE {self.settings.customer_schema}.layer
                SET {', '.join(updates)}
                WHERE id = $1
                """,
                *params,
            )
            logger.info(
                "Updated layer metadata: %s (features=%d, size=%d)",
                layer_id,
                feature_count or 0,
                size,
            )
        finally:
            await pool.close()

    def run(self: Self, params: LayerUpdateParams) -> dict[str, Any]:
        """Run the layer update.

        1. Verify ownership and get layer info
        2. Import new data from S3 or WFS
        3. Replace DuckLake table
        4. Update PostgreSQL metadata

        Args:
            params: Update parameters

        Returns:
            Dict with update results
        """
        import tempfile

        logger.info(
            "Starting layer update: layer_id=%s, user_id=%s, s3_key=%s, refresh_wfs=%s",
            params.layer_id,
            params.user_id,
            params.s3_key,
            params.refresh_wfs,
        )

        try:
            # Step 1: Get layer info and verify ownership
            layer_info = asyncio.get_event_loop().run_until_complete(
                self._get_layer_full_info(params.layer_id, params.user_id)
            )
            logger.info(
                "Layer info: name=%s, type=%s, data_type=%s",
                layer_info["name"],
                layer_info["type"],
                layer_info.get("data_type"),
            )

            with tempfile.TemporaryDirectory(prefix="layer_update_") as temp_dir:
                temp_path = Path(temp_dir)
                output_parquet = temp_path / "output.parquet"

                # Step 2: Import new data
                if params.refresh_wfs:
                    # Get WFS URL and layer from other_properties
                    other_props = layer_info.get("other_properties", {})
                    wfs_url = other_props.get("url")
                    wfs_layers = other_props.get("layers", [])

                    if not wfs_url:
                        raise ValueError(
                            f"Layer {params.layer_id} is not a WFS layer or missing URL"
                        )

                    # Get first layer name if list
                    wfs_layer_name = (
                        wfs_layers[0]
                        if isinstance(wfs_layers, list) and wfs_layers
                        else wfs_layers
                        if isinstance(wfs_layers, str)
                        else None
                    )

                    self._import_from_wfs(
                        wfs_url=wfs_url,
                        layer_name=wfs_layer_name,
                        temp_dir=temp_path,
                        output_path=output_parquet,
                    )
                else:
                    # Import from S3
                    self._import_from_s3(
                        s3_key=params.s3_key,  # type: ignore
                        temp_dir=temp_path,
                        output_path=output_parquet,
                    )

                # Step 3: Replace DuckLake table
                table_info = self._replace_ducklake_table(
                    layer_id=params.layer_id,
                    owner_id=layer_info["user_id"],
                    parquet_path=output_parquet,
                )
                logger.info(
                    "DuckLake table replaced: %s (%d features)",
                    table_info["table_name"],
                    table_info.get("feature_count", 0),
                )

                # Step 4: Update PostgreSQL metadata
                # Build attribute mapping from columns
                attr_mapping = {}
                for col_name, col_type in table_info.get("columns", {}).items():
                    if col_name.lower() not in ("geometry", "geom", "id"):
                        attr_mapping[col_name] = col_name

                asyncio.get_event_loop().run_until_complete(
                    self._update_layer_metadata(
                        layer_id=params.layer_id,
                        feature_count=table_info.get("feature_count", 0),
                        extent_wkt=table_info.get("extent_wkt"),
                        size=table_info.get("size", 0),
                        geometry_type=table_info.get("geometry_type"),
                        attribute_mapping=attr_mapping,
                    )
                )

            # Build output
            from goatlib.tools.db import normalize_geometry_type

            output = LayerUpdateOutput(
                user_id=params.user_id,
                layer_id=params.layer_id,
                updated=True,
                feature_count=table_info.get("feature_count"),
                size=table_info.get("size"),
                geometry_type=normalize_geometry_type(table_info.get("geometry_type")),
            )

            logger.info("Layer update completed: %s", params.layer_id)
            return output.model_dump()

        except PermissionError as e:
            logger.error("Permission denied: %s", e)
            return LayerUpdateOutput(
                user_id=params.user_id,
                layer_id=params.layer_id,
                updated=False,
                error=str(e),
            ).model_dump()
        except Exception as e:
            logger.exception("Layer update failed: %s", e)
            return LayerUpdateOutput(
                user_id=params.user_id,
                layer_id=params.layer_id,
                updated=False,
                error=str(e),
            ).model_dump()

    def cleanup(self: Self) -> None:
        """Clean up resources."""
        if self._duckdb_con:
            try:
                self._duckdb_con.close()
            except Exception:
                pass
            self._duckdb_con = None


def main(params: LayerUpdateParams) -> dict[str, Any]:
    """Windmill entry point for layer update tool."""
    runner = LayerUpdateRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
