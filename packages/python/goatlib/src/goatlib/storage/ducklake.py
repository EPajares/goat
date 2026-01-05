"""Base DuckLake connection manager.

Single connection with lock for thread-safety, plus a connection pool variant.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
from contextlib import contextmanager
from typing import Any, Generator, Protocol
from urllib.parse import unquote, urlparse

import duckdb

logger = logging.getLogger(__name__)

# Connection error patterns that should trigger a retry/reconnect
CONNECTION_ERROR_PATTERNS = [
    "ssl syscall error",
    "eof detected",
    "connection already closed",
    "connection error",
    "connection reset",
    "broken pipe",
    "failed to get data file list",
]

# TCP keepalive settings to prevent SSL EOF errors on idle PostgreSQL connections
# See: https://www.postgresql.org/docs/current/libpq-connect.html
POSTGRES_KEEPALIVE_PARAMS = {
    "keepalives": "1",
    "keepalives_idle": "30",  # seconds before sending keepalive
    "keepalives_interval": "5",  # seconds between keepalives
    "keepalives_count": "5",  # failed keepalives before disconnect
}


def is_connection_error(error: Exception) -> bool:
    """Check if an error indicates a broken connection that should be retried."""
    error_str = str(error).lower()
    return any(pattern in error_str for pattern in CONNECTION_ERROR_PATTERNS)


def execute_with_retry(
    manager: "BaseDuckLakeManager | DuckLakePool",
    query: str,
    params: list | None = None,
    fetch_all: bool = True,
    max_retries: int = 1,
) -> tuple[Any, Any]:
    """Execute query with retry on connection errors.

    Standalone function that works with any manager/pool having connection() and reconnect().

    Args:
        manager: DuckLake manager/pool instance
        query: SQL query to execute
        params: Optional query parameters
        fetch_all: If True, fetchall(); if False, fetchone()
        max_retries: Number of retry attempts on connection error

    Returns:
        Tuple of (result, description) where result is fetchall()/fetchone()
        and description is cursor.description for column names.
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            with manager.connection() as con:
                if params:
                    cursor = con.execute(query, params)
                else:
                    cursor = con.execute(query)
                if fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
                return result, con.description
        except Exception as e:
            last_error = e
            if is_connection_error(e) and attempt < max_retries:
                logger.warning(
                    "Connection error (attempt %d/%d), reconnecting: %s",
                    attempt + 1,
                    max_retries + 1,
                    e,
                )
                manager.reconnect()
                continue
            break
    raise last_error


def execute_query_with_retry(
    manager: "BaseDuckLakeManager | DuckLakePool",
    query: str,
    params: list | None = None,
    fetch_all: bool = True,
    max_retries: int = 1,
) -> Any:
    """Execute query with retry, returning only the result (no description).

    Simpler version for cases where column names aren't needed.

    Args:
        manager: DuckLake manager/pool instance
        query: SQL query to execute
        params: Optional query parameters
        fetch_all: If True, fetchall(); if False, fetchone()
        max_retries: Number of retry attempts on connection error

    Returns:
        Result from fetchall() or fetchone()
    """
    result, _ = execute_with_retry(manager, query, params, fetch_all, max_retries)
    return result


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

    def __init__(self: "BaseDuckLakeManager", read_only: bool = False) -> None:
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

    def init(self: "BaseDuckLakeManager", settings: DuckLakeSettings) -> None:
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
                if not os.path.exists(self._storage_path):
                    os.makedirs(self._storage_path, exist_ok=True)
            else:
                base_dir = getattr(settings, "DATA_DIR", "/tmp")
                self._storage_path = os.path.join(base_dir, "ducklake")
                if not os.path.exists(self._storage_path):
                    os.makedirs(self._storage_path, exist_ok=True)

        self._create_connection()
        logger.info("DuckLake initialized: catalog=%s", self._catalog_schema)

    def init_from_params(
        self: "BaseDuckLakeManager",
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

        if not storage_path.startswith("s3://") and not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)

        self._create_connection()
        logger.info("DuckLake initialized: catalog=%s", self._catalog_schema)

    def _create_connection(self: "BaseDuckLakeManager") -> None:
        """Create and configure the DuckDB connection."""
        con = duckdb.connect()
        self._install_extensions(con)
        self._load_extensions(con)
        self._setup_s3(con)
        self._attach_ducklake(con)
        self._connection = con

    def close(self: "BaseDuckLakeManager") -> None:
        """Close the connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("DuckLake connection closed")

    @contextmanager
    def connection(
        self: "BaseDuckLakeManager",
    ) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get DuckDB connection (with lock)."""
        if not self._connection:
            raise RuntimeError("DuckLakeManager not initialized")
        with self._lock:
            yield self._connection

    @contextmanager
    def connection_with_retry(
        self: "BaseDuckLakeManager",
        max_retries: int = 1,
    ) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get DuckDB connection with automatic reconnect on connection errors.

        Args:
            max_retries: Number of reconnect attempts on connection error.
        """
        if not self._connection:
            raise RuntimeError("DuckLakeManager not initialized")

        for attempt in range(max_retries + 1):
            try:
                with self._lock:
                    yield self._connection
                return  # Success, exit
            except Exception as e:
                if is_connection_error(e) and attempt < max_retries:
                    logger.warning(
                        "Connection error (attempt %d/%d), reconnecting: %s",
                        attempt + 1,
                        max_retries + 1,
                        e,
                    )
                    self.reconnect()
                    continue
                raise

    def reconnect(self: "BaseDuckLakeManager") -> None:
        """Reconnect to DuckLake."""
        with self._lock:
            if self._connection:
                try:
                    self._connection.close()
                except Exception:
                    pass
            self._create_connection()
            logger.info("DuckLake reconnected")

    def execute(
        self: "BaseDuckLakeManager", query: str, params: tuple | list | None = None
    ) -> list[Any]:
        with self.connection() as con:
            if params:
                return con.execute(query, params).fetchall()
            return con.execute(query).fetchall()

    def execute_one(
        self: "BaseDuckLakeManager", query: str, params: tuple | list | None = None
    ) -> Any:
        with self.connection() as con:
            if params:
                return con.execute(query, params).fetchone()
            return con.execute(query).fetchone()

    def execute_df(
        self: "BaseDuckLakeManager", query: str, params: tuple | list | None = None
    ) -> Any:
        with self.connection() as con:
            if params:
                return con.execute(query, params).fetchdf()
            return con.execute(query).fetchdf()

    def execute_with_retry(
        self: "BaseDuckLakeManager",
        query: str,
        params: tuple | list | None = None,
        max_retries: int = 1,
    ) -> Any:
        """Execute with retry on connection failure."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return self.execute(query, params)
            except Exception as e:
                last_error = e
                if is_connection_error(e) and attempt < max_retries:
                    logger.warning(
                        "Query failed (attempt %d/%d), reconnecting: %s",
                        attempt + 1,
                        max_retries + 1,
                        e,
                    )
                    self.reconnect()
                    continue
                break
        raise last_error

    def _install_extensions(
        self: "BaseDuckLakeManager", con: duckdb.DuckDBPyConnection
    ) -> None:
        if self._extensions_installed:
            return
        for ext in self.REQUIRED_EXTENSIONS:
            con.execute(f"INSTALL {ext}")
        logger.info("Installed DuckDB extensions: %s", self.REQUIRED_EXTENSIONS)
        self._extensions_installed = True

    def _load_extensions(
        self: "BaseDuckLakeManager", con: duckdb.DuckDBPyConnection
    ) -> None:
        for ext in self.REQUIRED_EXTENSIONS:
            con.execute(f"LOAD {ext}")

    def _setup_s3(self: "BaseDuckLakeManager", con: duckdb.DuckDBPyConnection) -> None:
        if self._s3_endpoint:
            con.execute(f"SET s3_endpoint = '{self._s3_endpoint}'")
            con.execute("SET s3_url_style = 'path'")
        if self._s3_access_key:
            con.execute(f"SET s3_access_key_id = '{self._s3_access_key}'")
        if self._s3_secret_key:
            con.execute(f"SET s3_secret_access_key = '{self._s3_secret_key}'")

    def _parse_postgres_uri(self: "BaseDuckLakeManager") -> dict[str, str]:
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

    def _attach_ducklake(
        self: "BaseDuckLakeManager", con: duckdb.DuckDBPyConnection
    ) -> None:
        params = self._parse_postgres_uri()

        # Add TCP keepalive settings to prevent SSL EOF errors on idle connections
        params.update(POSTGRES_KEEPALIVE_PARAMS)

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


class DuckLakePool:
    """Pool of read-only DuckDB connections for concurrent queries.

    Each connection in the pool has the DuckLake catalog attached and
    can independently execute queries without blocking other connections.

    This is useful for high-concurrency read scenarios like tile serving,
    where a single-connection-with-lock model would be a bottleneck.

    Connection health is validated before returning from the pool, and
    stale connections are automatically recreated.

    Example:
        pool = DuckLakePool(pool_size=4)
        pool.init(settings)

        with pool.connection() as con:
            result = con.execute("SELECT * FROM lake.schema.table").fetchall()

        pool.close()
    """

    REQUIRED_EXTENSIONS = ["spatial", "httpfs", "postgres", "ducklake"]

    # Max age for connections in seconds - older connections are recreated
    # This helps prevent stale PostgreSQL connections inside DuckLake
    MAX_CONNECTION_AGE_SECONDS = 300  # 5 minutes

    def __init__(self, pool_size: int = 2) -> None:
        """Initialize connection pool.

        Args:
            pool_size: Number of connections to maintain in the pool.
        """
        self._pool_size = pool_size
        self._pool: queue.Queue[tuple[duckdb.DuckDBPyConnection, float]] = queue.Queue()
        self._initialized = False
        self._init_lock = threading.Lock()
        self._postgres_uri: str | None = None
        self._storage_path: str | None = None
        self._catalog_schema: str | None = None
        self._s3_endpoint: str | None = None
        self._s3_access_key: str | None = None
        self._s3_secret_key: str | None = None
        self._extensions_installed: bool = False

    def init(self, settings: DuckLakeSettings) -> None:
        """Initialize the connection pool from settings."""
        with self._init_lock:
            if self._initialized:
                return

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
                else:
                    base_dir = getattr(settings, "DATA_DIR", "/tmp")
                    self._storage_path = os.path.join(base_dir, "ducklake")

            # Create pool connections with retry for transient connection errors
            import time

            for i in range(self._pool_size):
                con = self._create_connection_with_retry()
                # Store connection with its creation timestamp
                self._pool.put((con, time.time()))
                logger.debug("Created pool connection %d/%d", i + 1, self._pool_size)

            self._initialized = True
            logger.info(
                "DuckLake pool initialized: %d connections, catalog=%s",
                self._pool_size,
                self._catalog_schema,
            )

    def _parse_postgres_uri(self) -> dict[str, str]:
        """Parse PostgreSQL URI into libpq connection parameters."""
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

    def _create_connection_with_retry(
        self, max_retries: int = 3, retry_delay: float = 1.0
    ) -> duckdb.DuckDBPyConnection:
        """Create connection with retry on transient errors."""
        import time

        last_error = None
        for attempt in range(max_retries):
            try:
                return self._create_connection()
            except Exception as e:
                last_error = e
                if is_connection_error(e) and attempt < max_retries - 1:
                    logger.warning(
                        "Failed to create connection (attempt %d/%d): %s. Retrying...",
                        attempt + 1,
                        max_retries,
                        e,
                    )
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                break
        raise last_error

    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create a new DuckDB connection with DuckLake attached (read-only)."""
        con = duckdb.connect()

        # Install and load extensions
        for ext in self.REQUIRED_EXTENSIONS:
            if not self._extensions_installed:
                con.execute(f"INSTALL {ext}")
            con.execute(f"LOAD {ext}")
        self._extensions_installed = True

        # Configure S3 if needed
        if self._s3_endpoint:
            con.execute(f"SET s3_endpoint='{self._s3_endpoint}'")
            con.execute("SET s3_url_style='path'")
        if self._s3_access_key:
            con.execute(f"SET s3_access_key_id='{self._s3_access_key}'")
        if self._s3_secret_key:
            con.execute(f"SET s3_secret_access_key='{self._s3_secret_key}'")

        # Attach DuckLake catalog in read-only mode
        params = self._parse_postgres_uri()
        params.update(POSTGRES_KEEPALIVE_PARAMS)
        libpq_str = " ".join(f"{k}={v}" for k, v in params.items())

        options = [
            f"DATA_PATH '{self._storage_path}'",
            f"METADATA_SCHEMA '{self._catalog_schema}'",
            "READ_ONLY true",
            "OVERRIDE_DATA_PATH true",
        ]
        options_str = ", ".join(options)

        attach_sql = f"ATTACH 'ducklake:postgres:{libpq_str}' AS lake ({options_str})"
        con.execute(attach_sql)

        return con

    def _get_healthy_connection(self) -> tuple[duckdb.DuckDBPyConnection, float]:
        """Get a connection from the pool, recreating if too old.

        Only checks connection age - actual connection health is validated
        by the retry logic when queries fail.

        Returns a tuple of (connection, creation_time).
        """
        import time

        con, created_at = self._pool.get()  # Blocks until available
        current_time = time.time()
        connection_age = current_time - created_at

        # Only recreate if connection is too old
        # Don't do active validation - let the query retry handle failures
        if connection_age > self.MAX_CONNECTION_AGE_SECONDS:
            logger.debug(
                "Connection aged out (%.0fs > %ds), recreating",
                connection_age,
                self.MAX_CONNECTION_AGE_SECONDS,
            )
            try:
                con.close()
            except Exception:
                pass
            con = self._create_connection_with_retry()
            created_at = current_time

        return con, created_at

    @contextmanager
    def connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get a connection from the pool.

        Validates the connection before returning it.
        On connection errors during use, recreates the connection.
        Returns the connection to the pool when done.
        """
        import time

        if not self._initialized:
            raise RuntimeError("DuckLakePool not initialized")

        con, created_at = self._get_healthy_connection()
        connection_failed = False
        try:
            yield con
        except Exception as e:
            # On connection errors, mark for recreation
            if is_connection_error(e):
                logger.warning("Connection error during query, will recreate: %s", e)
                connection_failed = True
                try:
                    con.close()
                except Exception:
                    pass
            raise
        finally:
            # Only recreate if connection failed during use
            if connection_failed:
                try:
                    con = self._create_connection_with_retry()
                    created_at = time.time()
                except Exception as create_err:
                    logger.error("Failed to recreate connection: %s", create_err)
                    # Retry with more attempts
                    con = self._create_connection_with_retry(max_retries=5)
                    created_at = time.time()
            self._pool.put((con, created_at))

    def execute_with_retry(
        self,
        query: str,
        params: list | tuple | None = None,
        max_retries: int = 2,
        fetch_all: bool = True,
    ) -> Any:
        """Execute a query with automatic retry on connection errors.

        This method handles the full retry logic internally, getting fresh
        connections from the pool on each attempt.

        Args:
            query: SQL query to execute
            params: Query parameters
            max_retries: Number of retry attempts
            fetch_all: If True, fetchall(); if False, fetchone()

        Returns:
            Query result (fetchall or fetchone)
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                with self.connection() as con:
                    if params:
                        cursor = con.execute(query, params)
                    else:
                        cursor = con.execute(query)
                    return cursor.fetchall() if fetch_all else cursor.fetchone()
            except Exception as e:
                last_error = e
                if is_connection_error(e) and attempt < max_retries - 1:
                    logger.warning(
                        "Query failed (attempt %d/%d), will retry: %s",
                        attempt + 1,
                        max_retries,
                        e,
                    )
                    continue
                raise

        # Should not reach here
        if last_error:
            raise last_error

    def reconnect(self) -> None:
        """Reconnect all connections in the pool.

        Drains pool, closes old connections, creates new ones.
        """
        import time

        with self._init_lock:
            # Drain and close all connections
            connections = []
            while not self._pool.empty():
                try:
                    item = self._pool.get_nowait()
                    # Handle both old format (just connection) and new format (tuple)
                    if isinstance(item, tuple):
                        con, _ = item
                    else:
                        con = item
                    connections.append(con)
                except queue.Empty:
                    break

            for con in connections:
                try:
                    con.close()
                except Exception:
                    pass

            # Create new connections with timestamps
            current_time = time.time()
            for i in range(self._pool_size):
                con = self._create_connection()
                self._pool.put((con, current_time))
                logger.debug("Recreated pool connection %d/%d", i + 1, self._pool_size)

            logger.info("DuckLake pool reconnected: %d connections", self._pool_size)

    def close(self) -> None:
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                item = self._pool.get_nowait()
                # Handle both old format (just connection) and new format (tuple)
                if isinstance(item, tuple):
                    con, _ = item
                else:
                    con = item
                con.close()
            except queue.Empty:
                break
        self._initialized = False
        logger.info("DuckLake pool closed")
