"""Base class for Windmill tool scripts.

This module provides BaseToolRunner - an abstract base class that handles
the common workflow for all GOAT tools:

1. Run analysis (implemented by subclass)
2. Ingest results into DuckLake
3. Create layer metadata in PostgreSQL
4. Optionally link to a project
5. Return standardized output

Subclasses only need to implement:
- process() - the actual analysis logic
- tool_class - the analysis tool class
- output_geometry_type - "point", "line", "polygon", or None
- default_output_name - default layer name

Example:
    class BufferToolRunner(BaseToolRunner[BufferToolParams]):
        tool_class = BufferTool
        output_geometry_type = "polygon"
        default_output_name = "Buffer"

        def process(self, params, temp_dir):
            # Run buffer analysis
            # Return (output_path, metadata)
            ...

    # Windmill entry point
    def main(params: BufferToolParams):
        runner = BufferToolRunner()
        runner.init_from_env()
        return runner.run(params)
"""

import asyncio
import logging
import os
import tempfile
import uuid as uuid_module
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, Self, TypeVar

import asyncpg
import duckdb

from goatlib.models.io import DatasetMetadata
from goatlib.tools.db import ToolDatabaseService
from goatlib.tools.schemas import ToolInputBase, ToolOutputBase

logger = logging.getLogger(__name__)

TParams = TypeVar("TParams", bound=ToolInputBase)


@dataclass
class ToolSettings:
    """Settings for tool execution, loaded from environment."""

    # PostgreSQL connection (for layer metadata)
    postgres_server: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # DuckLake settings
    ducklake_postgres_uri: str
    ducklake_catalog_schema: str
    ducklake_data_dir: str

    # OD matrix / travel time matrices
    od_matrix_base_path: str = "/app/data/traveltime_matrices"

    # S3 settings (shared for DuckLake and uploads)
    s3_provider: str = "hetzner"  # hetzner, aws, minio
    s3_endpoint_url: str | None = None
    s3_public_endpoint_url: str | None = None  # Public URL for presigned URLs
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region_name: str = "us-east-1"
    s3_bucket_name: str | None = None  # Bucket for user uploads/imports

    # Schema for customer tables
    customer_schema: str = "customer"

    # Routing settings
    goat_routing_url: str = "http://localhost:8200/api/v2/routing"
    goat_routing_authorization: str | None = None
    r5_url: str = "http://localhost:7070"
    r5_region_mapping_path: str | None = None

    # Geocoding settings
    geocoding_url: str | None = None
    geocoding_authorization: str | None = None

    def get_s3_client(self: Self) -> Any:
        """Create boto3 S3 client with provider-specific config.

        Returns configured S3 client for Hetzner, MinIO, or AWS.
        """
        import boto3
        from botocore.client import Config

        extra_kwargs = {}
        if self.s3_endpoint_url:
            extra_kwargs["endpoint_url"] = self.s3_endpoint_url

        provider = self.s3_provider.lower()
        if provider == "hetzner":
            extra_kwargs["config"] = Config(
                signature_version="s3v4",
                s3={
                    "payload_signing_enabled": False,
                    "addressing_style": "virtual",
                },
            )
        elif provider == "minio":
            extra_kwargs["config"] = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )
        # AWS uses defaults

        return boto3.client(
            "s3",
            aws_access_key_id=self.s3_access_key_id,
            aws_secret_access_key=self.s3_secret_access_key,
            region_name=self.s3_region_name,
            **extra_kwargs,
        )

    def get_s3_public_client(self: Self) -> Any:
        """Create boto3 S3 client for public URL signing.

        Returns configured S3 client using the public endpoint URL for
        generating presigned URLs that are accessible from outside the cluster.
        Falls back to the regular S3 client if no public endpoint is configured.
        """
        import boto3
        from botocore.client import Config

        # Use public endpoint if available, otherwise fall back to internal
        endpoint_url = self.s3_public_endpoint_url or self.s3_endpoint_url

        extra_kwargs = {}
        if endpoint_url:
            extra_kwargs["endpoint_url"] = endpoint_url

        provider = self.s3_provider.lower()
        if provider == "hetzner":
            extra_kwargs["config"] = Config(
                signature_version="s3v4",
                s3={
                    "payload_signing_enabled": False,
                    "addressing_style": "virtual",
                },
            )
        elif provider == "minio":
            extra_kwargs["config"] = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )
        # AWS uses defaults

        return boto3.client(
            "s3",
            aws_access_key_id=self.s3_access_key_id,
            aws_secret_access_key=self.s3_secret_access_key,
            region_name=self.s3_region_name,
            **extra_kwargs,
        )

    @classmethod
    def _get_secret(cls: type[Self], name: str, default: str = "") -> str:
        """Get a secret value from Windmill or environment variable.

        First tries Windmill variable (for secrets stored in Windmill),
        then falls back to environment variable.
        """
        # Try Windmill variable first (path: f/goat/{name})
        try:
            import wmill

            path = f"f/goat/{name}"
            value = wmill.get_variable(path)
            if value:
                return value
        except Exception:
            pass  # wmill not available or variable doesn't exist

        # Fall back to environment variable
        return os.environ.get(name, default)

    @classmethod
    def from_env(cls: type[Self]) -> Self:
        """Load settings from environment variables and Windmill secrets.

        Non-sensitive config is read from environment variables.
        Sensitive values (passwords, keys) are read from Windmill secrets first,
        falling back to environment variables for local development.
        """
        # Get base connection info (try Windmill vars first, then env vars)
        pg_server = cls._get_secret("POSTGRES_SERVER", "db")
        pg_port = cls._get_secret("POSTGRES_PORT", "5432")
        pg_user = cls._get_secret("POSTGRES_USER", "postgres")
        pg_db = cls._get_secret("POSTGRES_DB", "goat")
        pg_password = cls._get_secret("POSTGRES_PASSWORD", "postgres")

        # Build default URI from components (uses db hostname, not localhost)
        default_uri = (
            f"postgresql://{pg_user}:{pg_password}@{pg_server}:{pg_port}/{pg_db}"
        )

        return cls(
            postgres_server=pg_server,
            postgres_port=int(pg_port),
            postgres_user=pg_user,
            postgres_password=pg_password,
            postgres_db=pg_db,
            ducklake_postgres_uri=cls._get_secret("POSTGRES_DATABASE_URI", default_uri),
            ducklake_catalog_schema=cls._get_secret(
                "DUCKLAKE_CATALOG_SCHEMA", "ducklake"
            ),
            ducklake_data_dir=cls._get_secret(
                "DUCKLAKE_DATA_DIR", "/app/data/ducklake"
            ),
            od_matrix_base_path=cls._get_secret(
                "OD_MATRIX_BASE_PATH", "/app/data/traveltime_matrices"
            ),
            s3_provider=cls._get_secret("S3_PROVIDER", "hetzner").lower(),
            s3_endpoint_url=cls._get_secret("S3_ENDPOINT_URL", ""),
            s3_public_endpoint_url=cls._get_secret("S3_PUBLIC_ENDPOINT_URL", "")
            or None,
            s3_access_key_id=cls._get_secret("S3_ACCESS_KEY_ID", ""),
            s3_secret_access_key=cls._get_secret("S3_SECRET_ACCESS_KEY", ""),
            s3_region_name=cls._get_secret("S3_REGION_NAME", "")
            or cls._get_secret("S3_REGION", "us-east-1"),
            s3_bucket_name=cls._get_secret("S3_BUCKET_NAME", ""),
            customer_schema=cls._get_secret("CUSTOMER_SCHEMA", "customer"),
            goat_routing_url=cls._get_secret(
                "GOAT_ROUTING_URL", "http://goat-dev:8200/api/v2/routing"
            ),
            goat_routing_authorization=cls._get_secret("GOAT_ROUTING_AUTHORIZATION", "")
            or None,
            r5_url=cls._get_secret("R5_URL", "https://r5.routing.plan4better.de"),
            r5_region_mapping_path=cls._get_secret(
                "R5_REGION_MAPPING_PATH", "/app/data/gtfs/r5_region_mapping.parquet"
            ),
            geocoding_url=cls._get_secret("GEOCODING_URL", "") or None,
            geocoding_authorization=cls._get_secret("GEOCODING_AUTHORIZATION", "")
            or None,
        )


class SimpleToolRunner:
    """Base class with shared infrastructure for all tool runners.

    Provides:
    - Settings loading from environment
    - Logging configuration for Windmill
    - DuckDB/DuckLake connection management
    - S3 client management
    - PostgreSQL connection pool

    Subclasses: BaseToolRunner (for analysis tools), LayerDeleteRunner, LayerExportRunner
    """

    def __init__(self: Self) -> None:
        """Initialize runner."""
        self.settings: ToolSettings | None = None
        self._duckdb_con: duckdb.DuckDBPyConnection | None = None
        self._s3_client: Any | None = None

    @staticmethod
    def _configure_logging_for_windmill() -> None:
        """Configure Python logging to output to stdout for Windmill."""
        import sys

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(handler)

    def init_from_env(self: Self) -> None:
        """Initialize settings from environment variables."""
        self._configure_logging_for_windmill()
        self.settings = ToolSettings.from_env()

    def init(self: Self, settings: ToolSettings) -> None:
        """Initialize with explicit settings."""
        self.settings = settings

    def _get_duckdb_connection(self: Self) -> duckdb.DuckDBPyConnection:
        """Create and configure a DuckDB connection with DuckLake attached."""
        if self.settings is None:
            raise RuntimeError("Settings not initialized. Call init_from_env() first.")

        con = duckdb.connect()

        for ext in ["spatial", "httpfs", "postgres", "ducklake"]:
            con.execute(f"INSTALL {ext}; LOAD {ext};")

        if self.settings.s3_endpoint_url:
            con.execute(f"""
                SET s3_endpoint = '{self.settings.s3_endpoint_url}';
                SET s3_access_key_id = '{self.settings.s3_access_key_id or ""}';
                SET s3_secret_access_key = '{self.settings.s3_secret_access_key or ""}';
                SET s3_url_style = 'path';
                SET s3_use_ssl = false;
            """)

        storage_path = self.settings.ducklake_data_dir
        con.execute(f"""
            ATTACH 'ducklake:postgres:{self.settings.ducklake_postgres_uri}' AS lake (
                DATA_PATH '{storage_path}',
                METADATA_SCHEMA '{self.settings.ducklake_catalog_schema}',
                OVERRIDE_DATA_PATH true
            )
        """)
        return con

    def _is_retriable_ducklake_error(self: Self, error: Exception) -> bool:
        """Check if a DuckLake error is retriable (connection/transaction issues)."""
        error_msg = str(error).lower()
        return (
            "ssl syscall error" in error_msg
            or "eof detected" in error_msg
            or "connection" in error_msg
            or "transactioncontext" in error_msg
            or "failed to commit" in error_msg
            or "rollback" in error_msg
        )

    def _execute_with_retry(
        self: Self,
        operation: str,
        sql: str,
        max_retries: int = 2,
    ) -> Any:
        """Execute a DuckDB/DuckLake SQL statement with retry logic.

        Args:
            operation: Description of the operation for logging
            sql: SQL statement to execute
            max_retries: Maximum number of retry attempts

        Returns:
            Result of the execute() call
        """
        for attempt in range(max_retries + 1):
            try:
                return self.duckdb_con.execute(sql)
            except Exception as e:
                if self._is_retriable_ducklake_error(e) and attempt < max_retries:
                    logger.warning(
                        "DuckLake %s error (attempt %d/%d), reconnecting: %s",
                        operation,
                        attempt + 1,
                        max_retries + 1,
                        e,
                    )
                    # Force reconnection by clearing the cached connection
                    if self._duckdb_con:
                        try:
                            self._duckdb_con.close()
                        except Exception:
                            pass
                    self._duckdb_con = None
                    continue
                raise

    @property
    def duckdb_con(self: Self) -> duckdb.DuckDBPyConnection:
        """Get or create DuckDB connection (cached)."""
        if self._duckdb_con is None:
            self._duckdb_con = self._get_duckdb_connection()
        return self._duckdb_con

    @property
    def s3_client(self: Self) -> Any:
        """Get or create S3 client (cached)."""
        if self._s3_client is None:
            if self.settings is None:
                raise RuntimeError("Settings not initialized")
            self._s3_client = self.settings.get_s3_client()
        return self._s3_client

    @property
    def s3_public_client(self: Self) -> Any:
        """Get S3 client for generating public presigned URLs.

        Uses the public endpoint URL if configured, otherwise falls back
        to the internal S3 client. This ensures presigned URLs are
        accessible from outside the cluster.
        """
        if self.settings is None:
            raise RuntimeError("Settings not initialized")
        return self.settings.get_s3_public_client()

    def get_layer_table_path(self: Self, user_id: str, layer_id: str) -> str:
        """Build DuckLake table path from user and layer IDs."""
        user_schema = f"user_{user_id.replace('-', '')}"
        table_name = f"t_{layer_id.replace('-', '')}"
        return f"lake.{user_schema}.{table_name}"

    async def get_postgres_pool(self: Self) -> asyncpg.Pool:
        """Create PostgreSQL connection pool."""
        if self.settings is None:
            raise RuntimeError("Settings not initialized")

        return await asyncpg.create_pool(
            host=self.settings.postgres_server,
            port=self.settings.postgres_port,
            user=self.settings.postgres_user,
            password=self.settings.postgres_password,
            database=self.settings.postgres_db,
            min_size=1,
            max_size=5,
        )

    def cleanup(self: Self) -> None:
        """Clean up resources."""
        if self._duckdb_con:
            try:
                self._duckdb_con.close()
            except Exception:
                pass
            self._duckdb_con = None


class BaseToolRunner(SimpleToolRunner, ABC, Generic[TParams]):
    """Base class for analysis tools that create new layers.

    Handles the common workflow:
    - DuckLake ingestion
    - Layer creation in PostgreSQL
    - Project linking
    - Standardized output format

    Subclasses implement the actual analysis in process().

    Attributes:
        tool_class: The analysis tool class (must have OUTPUT_GEOMETRY_TYPE).
    """

    # Subclasses must define this - used for OUTPUT_GEOMETRY_TYPE and DEFAULT_OUTPUT_NAME
    tool_class: type = None  # type: ignore[assignment]

    def __init__(self: Self) -> None:
        """Initialize tool runner."""
        super().__init__()
        self.db_service: ToolDatabaseService | None = None

    @abstractmethod
    def process(
        self: Self, params: TParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run the analysis and return output parquet path + metadata.

        This is where the actual tool logic goes. Subclasses must implement this.

        Args:
            params: Tool-specific parameters (validated Pydantic model)
            temp_dir: Temporary directory for intermediate files

        Returns:
            Tuple of (output_parquet_path, metadata)
        """
        pass

    # Subclasses should set these
    output_geometry_type: str | None = None
    default_output_name: str = "Tool Output"

    def get_feature_layer_type(self: Self, params: TParams) -> str:
        """Return the feature_layer_type for the output.

        Override if the tool creates something other than "tool" type.

        Args:
            params: Tool parameters

        Returns:
            "standard", "tool", or "street_network"
        """
        return "tool"

    def compute_quantile_breaks(
        self: Self,
        table_name: str,
        column_name: str,
        num_breaks: int = 6,
        strip_zeros: bool = True,
    ) -> dict[str, Any] | None:
        """Compute quantile breaks for a column using DuckDB.

        Args:
            table_name: Full table path (e.g., "lake.user_xxx.t_yyy")
            column_name: Column name to compute breaks for
            num_breaks: Number of break values (default 6 to match 7-color palette)
            strip_zeros: Whether to exclude zero values (default True)

        Returns:
            Dict with breaks, min, max, mean, std_dev, method, attribute
        """
        from goatlib.analysis.schemas.statistics import ClassBreakMethod
        from goatlib.analysis.statistics import calculate_class_breaks

        try:
            result = calculate_class_breaks(
                con=self.duckdb_con,
                table_name=table_name,
                attribute=column_name,
                method=ClassBreakMethod.quantile,
                num_breaks=num_breaks,
                strip_zeros=strip_zeros,
            )

            if result.breaks:
                # Remove duplicates and sort
                unique_breaks = sorted(set(result.breaks))
                # Remove min from breaks if present (keep max as last break)
                if result.min is not None and result.min in unique_breaks:
                    unique_breaks.remove(result.min)

                return {
                    "breaks": unique_breaks,
                    "min": result.min,
                    "max": result.max,
                    "mean": result.mean,
                    "std_dev": result.std_dev,
                    "method": "quantile",
                    "attribute": column_name,
                }
        except Exception as e:
            logger.warning("Failed to compute quantile breaks: %s", e)

        return None

    def get_layer_properties(
        self: Self,
        params: TParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return custom layer properties (style) for the output.

        Override in subclasses to provide tool-specific styles (e.g., heatmaps).
        If None is returned, default style will be generated based on geometry type.

        Args:
            params: Tool parameters
            metadata: Dataset metadata from analysis
            table_info: DuckLake table info (for computing quantile breaks)

        Returns:
            Style dict or None for default style
        """
        return None

    def export_layer_to_parquet(self: Self, layer_id: str, user_id: str) -> str:
        """Export a DuckLake layer to a temporary parquet file.

        Args:
            layer_id: Layer UUID string
            user_id: User UUID string

        Returns:
            Path to the temporary parquet file
        """
        import tempfile

        table_name = self.get_layer_table_path(user_id, layer_id)

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".parquet", delete=False, prefix="layer_"
        )
        temp_path = temp_file.name
        temp_file.close()

        self._execute_with_retry(
            "export layer",
            f"COPY {table_name} TO '{temp_path}' (FORMAT PARQUET, COMPRESSION ZSTD)",
        )
        logger.info("Exported layer %s to %s", layer_id, temp_path)

        return temp_path

    def is_layer_id(self: Self, value: str | None) -> bool:
        """Check if a string value looks like a layer UUID.

        Args:
            value: String to check

        Returns:
            True if the value appears to be a UUID (36 chars with dashes)
        """
        if not value or not isinstance(value, str):
            return False
        # UUIDs are 36 characters with format: 8-4-4-4-12
        return len(value) == 36 and value.count("-") == 4

    def resolve_layer_paths(
        self: Self,
        items: list,
        user_id: str,
        path_field: str = "input_path",
    ) -> list:
        """Resolve layer IDs to parquet file paths in a list of Pydantic models.

        For each item in the list, if the path_field contains a layer UUID,
        export it to a parquet file and update the field with the file path.
        Also fetches and sets the layer name if not already provided.

        Args:
            items: List of Pydantic model instances (e.g., opportunities)
            user_id: User UUID for accessing layers
            path_field: Name of the field containing the layer ID/path

        Returns:
            New list with resolved paths and names
        """
        resolved = []
        for item in items:
            input_value = getattr(item, path_field, None)
            if self.is_layer_id(input_value):
                # Export the layer to parquet
                parquet_path = self.export_layer_to_parquet(input_value, user_id)
                logger.info(f"Exported layer {input_value} to {parquet_path}")

                # Fetch layer name if item has 'name' field and it's not set
                item_dict = item.model_dump()
                if "name" in item_dict and not item_dict.get("name"):
                    layer_info = asyncio.get_event_loop().run_until_complete(
                        self.db_service.get_layer_info(input_value)
                    )
                    if layer_info and layer_info.get("name"):
                        item_dict["name"] = layer_info["name"]
                        logger.info(
                            f"Set layer name from database: {layer_info['name']}"
                        )

                item_dict[path_field] = parquet_path
                resolved.append(type(item)(**item_dict))
            else:
                resolved.append(item)
        return resolved

    def run(self: Self, params: TParams) -> dict[str, Any]:
        """Main entry point - runs the full tool workflow.

        1. Generate output layer ID
        2. Run analysis (subclass implements)
        3. Ingest to DuckLake
        4. Create layer in PostgreSQL
        5. Optionally add to project
        6. Return standardized output

        Args:
            params: Validated tool parameters

        Returns:
            Dict with layer metadata (ToolOutputBase format)
        """
        output_layer_id = str(uuid_module.uuid4())
        output_name = params.output_name or self.default_output_name

        logger.info(
            f"Starting tool: {self.__class__.__name__} "
            f"(user={params.user_id}, output={output_layer_id})"
        )

        # Initialize db_service early so it's available in process() for resolve_layer_paths
        asyncio.get_event_loop().run_until_complete(self._init_db_service())

        with tempfile.TemporaryDirectory(
            prefix=f"{self.__class__.__name__.lower()}_"
        ) as temp_dir:
            temp_path = Path(temp_dir)

            # Step 1: Run analysis (subclass implements this)
            output_parquet, metadata = self.process(params, temp_path)
            logger.info(
                f"Analysis complete: {metadata.feature_count or 0} features "
                f"at {output_parquet}"
            )

            # Step 2: Ingest to DuckLake
            table_info = self._ingest_to_ducklake(
                user_id=params.user_id,
                layer_id=output_layer_id,
                parquet_path=output_parquet,
            )
            logger.info(f"DuckLake table created: {table_info['table_name']}")

            # Refresh database pool - connections may have gone stale during long analysis
            asyncio.get_event_loop().run_until_complete(self._close_db_service())

            # Step 3 & 4: Create layer + optional project link
            result_info = asyncio.get_event_loop().run_until_complete(
                self._create_db_records(
                    output_layer_id=output_layer_id,
                    params=params,
                    output_name=output_name,
                    metadata=metadata,
                    table_info=table_info,
                )
            )

        # Close the database pool
        asyncio.get_event_loop().run_until_complete(self._close_db_service())

        # Step 5: Build and return output
        # Note: folder_id is resolved inside _create_db_records if not provided
        # Detect geometry type from the actual parquet/DuckLake table
        detected_geom_type = table_info.get("geometry_type")
        is_feature = bool(detected_geom_type)
        output = ToolOutputBase(
            layer_id=output_layer_id,
            name=output_name,
            folder_id=result_info["folder_id"],
            user_id=params.user_id,
            project_id=params.project_id,
            layer_project_id=result_info.get("layer_project_id"),
            type="feature" if is_feature else "table",
            feature_layer_type=self.get_feature_layer_type(params)
            if is_feature
            else None,
            geometry_type=detected_geom_type,
            feature_count=table_info.get("feature_count", 0),
            extent=table_info.get("extent"),
            table_name=table_info["table_name"],
        )

        logger.info(f"Tool completed: {output_layer_id} ({output_name})")
        return output.model_dump()

    def _ingest_to_ducklake(
        self: Self,
        user_id: str,
        layer_id: str,
        parquet_path: Path,
    ) -> dict[str, Any]:
        """Ingest parquet file into DuckLake.

        Creates a new table in DuckLake from a GeoParquet file.
        The table is stored at lake.user_{user_id}.t_{layer_id}.

        Args:
            user_id: User UUID string
            layer_id: Layer UUID string
            parquet_path: Path to the parquet file

        Returns:
            Table info dict with table_name, feature_count, extent, geometry_type, columns, size
        """
        table_name = self.get_layer_table_path(user_id, layer_id)
        user_schema = f"user_{user_id.replace('-', '')}"

        # Get file size before ingestion
        file_size = parquet_path.stat().st_size if parquet_path.exists() else 0

        # Retry logic for connection issues with DuckLake
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                con = self.duckdb_con

                # Ensure user schema exists
                con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{user_schema}")

                # Create table from parquet (use OR REPLACE for retry safety)
                con.execute(f"""
                    CREATE TABLE {table_name} AS
                    SELECT * FROM read_parquet('{parquet_path}')
                """)
                logger.info(
                    "Created DuckLake table: %s from %s", table_name, parquet_path
                )

                # Get table info
                table_info = self._get_table_info(con, table_name)
                table_info["table_name"] = table_name
                table_info["size"] = file_size

                return table_info

            except Exception as e:
                if self._is_retriable_ducklake_error(e) and attempt < max_retries:
                    logger.warning(
                        "DuckLake ingest error (attempt %d/%d), reconnecting: %s",
                        attempt + 1,
                        max_retries + 1,
                        e,
                    )
                    # Force reconnection by clearing the cached connection
                    if self._duckdb_con:
                        try:
                            self._duckdb_con.close()
                        except Exception:
                            pass
                    self._duckdb_con = None
                    # Small delay before retry to let connection issues settle
                    import time

                    time.sleep(0.5)
                    continue
                raise

    def _get_table_info(
        self: Self, con: duckdb.DuckDBPyConnection, table_name: str
    ) -> dict[str, Any]:
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

        # Detect geometry column
        geom_col = None
        for col_name, col_type in columns.items():
            if "GEOMETRY" in col_type.upper():
                geom_col = col_name
                break

        geometry_type = None
        extent = None
        extent_wkt = None

        if geom_col:
            # Get geometry type
            type_result = con.execute(f"""
                SELECT DISTINCT ST_GeometryType({geom_col})
                FROM {table_name}
                WHERE {geom_col} IS NOT NULL
                LIMIT 1
            """).fetchone()
            if type_result:
                geometry_type = type_result[0]

            # Get extent
            extent_result = con.execute(f"""
                SELECT
                    ST_XMin(ST_Extent({geom_col})),
                    ST_YMin(ST_Extent({geom_col})),
                    ST_XMax(ST_Extent({geom_col})),
                    ST_YMax(ST_Extent({geom_col}))
                FROM {table_name}
            """).fetchone()
            if extent_result and all(v is not None for v in extent_result):
                extent = list(extent_result)
                extent_wkt = (
                    f"POLYGON(({extent[0]} {extent[1]}, {extent[2]} {extent[1]}, "
                    f"{extent[2]} {extent[3]}, {extent[0]} {extent[3]}, "
                    f"{extent[0]} {extent[1]}))"
                )

        return {
            "columns": columns,
            "feature_count": feature_count,
            "geometry_type": geometry_type,
            "extent": extent,
            "extent_wkt": extent_wkt,
        }

    async def _init_db_service(self: Self) -> None:
        """Initialize database service and connection pool.

        This is called early in run() so db_service is available for
        resolve_layer_paths() during process().
        """
        if self.settings is None:
            raise RuntimeError("Settings not initialized. Call init_from_env() first.")

        if self.db_service is not None:
            return  # Already initialized

        self._db_pool = await asyncpg.create_pool(
            host=self.settings.postgres_server,
            port=self.settings.postgres_port,
            user=self.settings.postgres_user,
            password=self.settings.postgres_password,
            database=self.settings.postgres_db,
            min_size=1,
            max_size=5,
        )

        self.db_service = ToolDatabaseService(
            self._db_pool, schema=self.settings.customer_schema
        )

    async def _close_db_service(self: Self) -> None:
        """Close database connection pool."""
        if hasattr(self, "_db_pool") and self._db_pool is not None:
            await self._db_pool.close()
            self._db_pool = None
            self.db_service = None

    async def _create_db_records(
        self: Self,
        output_layer_id: str,
        params: TParams,
        output_name: str,
        metadata: DatasetMetadata,
        table_info: dict[str, Any],
        custom_properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create layer record and optionally link to project.

        Args:
            output_layer_id: UUID for the new layer
            params: Tool parameters
            output_name: Layer display name
            metadata: Dataset metadata from analysis
            table_info: DuckLake table info
            custom_properties: Optional custom layer properties (style).
                               If None, get_layer_properties() is called.

        Returns:
            Dict with folder_id and layer_project_id (if added to project)
        """
        if self.db_service is None:
            await self._init_db_service()

        # Resolve folder_id: use provided value, or derive from project_id
        folder_id = params.folder_id
        if not folder_id and params.project_id:
            folder_id = await self.db_service.get_project_folder_id(params.project_id)
            if not folder_id:
                raise ValueError(
                    f"Could not find folder for project {params.project_id}"
                )
            logger.info(
                f"Derived folder_id={folder_id} from project_id={params.project_id}"
            )

        if not folder_id:
            raise ValueError(
                "folder_id is required, or project_id must be provided to derive it"
            )

        # Determine layer type from actual geometry in the data
        detected_geom_type = table_info.get("geometry_type")
        is_feature = bool(detected_geom_type)
        layer_type = "feature" if is_feature else "table"
        feature_layer_type = self.get_feature_layer_type(params) if is_feature else None

        # Get custom layer properties (style) from parameter or subclass
        if custom_properties is None:
            custom_properties = self.get_layer_properties(params, metadata, table_info)

        # Create layer metadata (returns generated properties)
        layer_properties = await self.db_service.create_layer(
            layer_id=output_layer_id,
            user_id=params.user_id,
            folder_id=folder_id,
            name=output_name,
            layer_type=layer_type,
            feature_layer_type=feature_layer_type,
            geometry_type=detected_geom_type,
            extent_wkt=table_info.get("extent_wkt"),
            feature_count=table_info.get("feature_count", 0),
            size=table_info.get("size", 0),
            properties=custom_properties,
        )

        # Add to project if requested
        layer_project_id = None
        if params.project_id:
            layer_project_id = await self.db_service.add_to_project(
                layer_id=output_layer_id,
                project_id=params.project_id,
                name=output_name,
                properties=layer_properties,
            )

        return {"folder_id": folder_id, "layer_project_id": layer_project_id}
