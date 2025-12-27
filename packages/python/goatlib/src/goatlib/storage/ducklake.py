"""Base DuckLake connection manager.

Single connection with lock for thread-safety.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager
from typing import Any, Generator, Protocol
from urllib.parse import unquote, urlparse

import duckdb

logger = logging.getLogger(__name__)


class DuckLakeSettings(Protocol):
    """Protocol for settings objects that configure DuckLake."""

    POSTGRES_DATABASE_URI: str
    DUCKLAKE_CATALOG_SCHEMA: str
    DUCKLAKE_DATA_DIR: str | None
    DUCKLAKE_S3_ENDPOINT: str | None
    DUCKLAKE_S3_BUCKET: str | None
    DUCKLAKE_S3_ACCESS_KEY: str | None
    DUCKLAKE_S3_SECRET_KEY: str | None


class BaseDuckLakeManager:
    """Single DuckDB connection with lock for thread-safety."""

    REQUIRED_EXTENSIONS = ["spatial", "httpfs", "postgres", "ducklake"]

    def __init__(self, read_only: bool = False) -> None:
        self._connection: duckdb.DuckDBPyConnection | None = None
        self._lock = threading.Lock()
        self._postgres_uri: str | None = None
        self._storage_path: str | None = None
        self._catalog_schema: str | None = None
        self._s3_endpoint: str | None = None
        self._s3_access_key: str | None = None
        self._s3_secret_key: str | None = None
        self._extensions_installed: bool = False
        self._read_only: bool = read_only

    def init(self, settings: DuckLakeSettings) -> None:
        """Initialize DuckLake connection."""
        self._postgres_uri = settings.POSTGRES_DATABASE_URI
        self._catalog_schema = settings.DUCKLAKE_CATALOG_SCHEMA
        self._s3_endpoint = getattr(settings, "DUCKLAKE_S3_ENDPOINT", None)
        self._s3_access_key = getattr(settings, "DUCKLAKE_S3_ACCESS_KEY", None)
        self._s3_secret_key = getattr(settings, "DUCKLAKE_S3_SECRET_KEY", None)

        s3_bucket = getattr(settings, "DUCKLAKE_S3_BUCKET", None)
        if s3_bucket:
            self._storage_path = s3_bucket
        else:
            data_dir = getattr(settings, "DUCKLAKE_DATA_DIR", None)
            if data_dir:
                self._storage_path = data_dir
                os.makedirs(self._storage_path, exist_ok=True)
            else:
                base_dir = getattr(settings, "DATA_DIR", "/tmp")
                self._storage_path = os.path.join(base_dir, "ducklake")
                os.makedirs(self._storage_path, exist_ok=True)

        self._create_connection()
        logger.info("DuckLake initialized: catalog=%s", self._catalog_schema)

    def init_from_params(
        self,
        postgres_uri: str,
        storage_path: str,
        catalog_schema: str = "ducklake",
        s3_endpoint: str | None = None,
        s3_access_key: str | None = None,
        s3_secret_key: str | None = None,
    ) -> None:
        """Initialize DuckLake with explicit parameters."""
        self._postgres_uri = postgres_uri
        self._catalog_schema = catalog_schema
        self._storage_path = storage_path
        self._s3_endpoint = s3_endpoint
        self._s3_access_key = s3_access_key
        self._s3_secret_key = s3_secret_key

        if not storage_path.startswith("s3://"):
            os.makedirs(storage_path, exist_ok=True)

        self._create_connection()
        logger.info("DuckLake initialized: catalog=%s", self._catalog_schema)

    def _create_connection(self) -> None:
        """Create and configure the DuckDB connection."""
        con = duckdb.connect()
        self._install_extensions(con)
        self._load_extensions(con)
        self._setup_s3(con)
        self._attach_ducklake(con)
        self._connection = con

    def close(self) -> None:
        """Close the connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("DuckLake connection closed")

    @contextmanager
    def connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get DuckDB connection (with lock)."""
        if not self._connection:
            raise RuntimeError("DuckLakeManager not initialized")
        with self._lock:
            yield self._connection

    def reconnect(self) -> None:
        """Reconnect to DuckLake."""
        with self._lock:
            if self._connection:
                try:
                    self._connection.close()
                except Exception:
                    pass
            self._create_connection()
            logger.info("DuckLake reconnected")

    def execute(self, query: str, params: tuple | list | None = None) -> list[Any]:
        with self.connection() as con:
            if params:
                return con.execute(query, params).fetchall()
            return con.execute(query).fetchall()

    def execute_one(self, query: str, params: tuple | list | None = None) -> Any:
        with self.connection() as con:
            if params:
                return con.execute(query, params).fetchone()
            return con.execute(query).fetchone()

    def execute_df(self, query: str, params: tuple | list | None = None) -> Any:
        with self.connection() as con:
            if params:
                return con.execute(query, params).fetchdf()
            return con.execute(query).fetchdf()

    def execute_with_retry(
        self, query: str, params: tuple | list | None = None, max_retries: int = 1
    ) -> Any:
        """Execute with retry on connection failure."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return self.execute(query, params)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning("Query failed (attempt %d): %s", attempt + 1, e)
                    self.reconnect()
        raise last_error

    def _install_extensions(self, con: duckdb.DuckDBPyConnection) -> None:
        if self._extensions_installed:
            return
        for ext in self.REQUIRED_EXTENSIONS:
            con.execute(f"INSTALL {ext}")
        logger.info("Installed DuckDB extensions: %s", self.REQUIRED_EXTENSIONS)
        self._extensions_installed = True

    def _load_extensions(self, con: duckdb.DuckDBPyConnection) -> None:
        for ext in self.REQUIRED_EXTENSIONS:
            con.execute(f"LOAD {ext}")

    def _setup_s3(self, con: duckdb.DuckDBPyConnection) -> None:
        if self._s3_endpoint:
            con.execute(f"SET s3_endpoint = '{self._s3_endpoint}'")
            con.execute("SET s3_url_style = 'path'")
        if self._s3_access_key:
            con.execute(f"SET s3_access_key_id = '{self._s3_access_key}'")
        if self._s3_secret_key:
            con.execute(f"SET s3_secret_access_key = '{self._s3_secret_key}'")

    def _parse_postgres_uri(self) -> dict[str, str]:
        uri = self._postgres_uri
        if uri.startswith("postgresql://"):
            uri = uri.replace("postgresql://", "postgres://", 1)
        parsed = urlparse(uri)
        params = {}
        if parsed.hostname:
            params["host"] = parsed.hostname
        if parsed.port:
            params["port"] = str(parsed.port)
        if parsed.username:
            params["user"] = unquote(parsed.username)
        if parsed.password:
            params["password"] = unquote(parsed.password)
        if parsed.path and parsed.path != "/":
            params["dbname"] = parsed.path.lstrip("/")
        return params

    def _attach_ducklake(self, con: duckdb.DuckDBPyConnection) -> None:
        params = self._parse_postgres_uri()
        libpq_str = " ".join(f"{k}={v}" for k, v in params.items())

        options = [
            f"DATA_PATH '{self._storage_path}'",
            f"METADATA_SCHEMA '{self._catalog_schema}'",
        ]
        if self._read_only:
            options.append("READ_ONLY true")
        options.append("OVERRIDE_DATA_PATH true")
        options_str = ", ".join(options)

        attach_sql = f"ATTACH 'ducklake:postgres:{libpq_str}' AS lake ({options_str})"
        con.execute(attach_sql)
        mode = "read-only" if self._read_only else "read-write"
        logger.info("DuckLake catalog attached (%s)", mode)
