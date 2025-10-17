# src/goatlib/io/discover.py
from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import boto3
import duckdb
import requests

from goatlib.io.formats import ALL_EXTS, FileFormat
from goatlib.io.utils import detect_path_type

logger = logging.getLogger(__name__)


class DiscoveryError(Exception):
    """Custom exception for discovery-related errors."""

    pass


@contextmanager
def temporary_download(url: str, timeout: int = 300) -> Iterator[Path]:
    """
    Context manager for downloading remote files with automatic cleanup.

    Args:
        url: Remote URL to download
        timeout: Request timeout in seconds

    Yields:
        Path to downloaded temporary file
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_remote_"))
    local_path = tmp_dir / Path(urlparse(url).path).name

    try:
        logger.info("Downloading %s → %s", url, local_path)
        path_type = detect_path_type(url)
        if path_type == "http":
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        elif path_type == "s3":
            parts = url.split("/", 3)
            if len(parts) < 4:
                raise DiscoveryError(f"Invalid S3 URL: {url}")

            bucket = parts[2]
            key = parts[3]
            boto3.client("s3").download_file(bucket, key, str(local_path))

        else:
            raise DiscoveryError(f"Unsupported remote scheme: {url}")

        yield local_path

    except Exception as e:
        # Clean up on error
        if local_path.exists():
            local_path.unlink(missing_ok=True)
        raise DiscoveryError(f"Failed to download {url}: {e}") from e

    finally:
        # Always clean up temp directory
        if tmp_dir.exists():
            for item in tmp_dir.iterdir():
                if item.is_file():
                    item.unlink()
            tmp_dir.rmdir()


def _discover_gpkg_layers(gpkg: Path) -> list[str]:
    """
    Discover GeoPackage layers using parameterized queries for safety.

    Args:
        gpkg: Path to GeoPackage file

    Returns:
        List of virtual paths in format 'file::layer'
    """
    try:
        # Use context manager for proper resource cleanup
        with duckdb.connect(database=":memory:") as con:
            con.execute("INSTALL spatial; LOAD spatial;")

            # Use parameterized query to prevent SQL injection
            result = con.execute(
                "SELECT * FROM ST_Read_Meta(?)", [str(gpkg)]
            ).fetchone()

            if not result or len(result) < 4:
                return [str(gpkg)]

            layers = result[3]
            if not isinstance(layers, list) or not layers:
                return [str(gpkg)]

            return [f"{gpkg}::{layer['name']}" for layer in layers]

    except Exception as e:
        logger.warning("Failed to introspect GeoPackage layers for %s: %s", gpkg, e)
        return [str(gpkg)]


def _discover_from_dir(directory: Path) -> Iterator[Path]:
    """
    Discover convertible files in a directory recursively.

    Args:
        directory: Directory to scan

    Yields:
        Paths to discovered convertible files
    """
    try:
        for path in directory.rglob("*"):
            # Skip system files and directories
            if path.name.startswith("._") or path.name == ".DS_Store":
                continue
            if not path.is_file():
                continue

            ext = path.suffix.lower()

            if ext == FileFormat.GPKG.value:
                yield from (Path(v) for v in _discover_gpkg_layers(path))
            elif ext == FileFormat.ZIP.value:
                yield from _discover_from_zip(path)
            elif ext in ALL_EXTS:
                yield path

    except PermissionError as e:
        raise DiscoveryError(f"Permission denied accessing {directory}: {e}") from e


@contextmanager
def _extract_zip_safely(zip_path: Path) -> Iterator[Path]:
    """
    Safely extract ZIP contents to temporary directory.

    Args:
        zip_path: Path to ZIP file

    Yields:
        Path to temporary extraction directory
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_zip_"))

    try:
        with zipfile.ZipFile(zip_path) as zf:
            # Check for potentially malicious ZIP files
            total_size = sum(zf.getinfo(name).file_size for name in zf.namelist())
            if total_size > 500 * 1024 * 1024:  # 500MB limit
                raise DiscoveryError(f"ZIP file too large: {total_size} bytes")

            # Extract supported files
            for name in zf.namelist():
                if name.endswith("/"):  # Skip directories
                    continue

                dest = tmp_dir / Path(name).name
                if dest.name.startswith("._") or dest.name == ".DS_Store":
                    continue

                with zf.open(name) as src, open(dest, "wb") as dst:
                    dst.write(src.read())

        yield tmp_dir

    except zipfile.BadZipFile as e:
        raise DiscoveryError(f"Invalid ZIP archive: {zip_path}") from e
    except Exception:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    finally:
        # This ensures cleanup even if the context manager isn't properly closed
        pass


def _discover_from_zip(zip_path: Path) -> Iterator[Path]:
    """
    Discover convertible files within a ZIP archive.

    Args:
        zip_path: Path to ZIP file

    Yields:
        Paths to discovered convertible files
    """
    with _extract_zip_safely(zip_path) as tmp_dir:
        for item_path in tmp_dir.iterdir():
            if not item_path.is_file():
                continue
            if item_path.name.startswith("._") or item_path.name == ".DS_Store":
                continue

            ext = item_path.suffix.lower()

            # Handle nested archives
            if ext == FileFormat.ZIP.value:
                try:
                    yield from _discover_from_zip(item_path)
                except zipfile.BadZipFile:
                    logger.warning("Invalid nested ZIP: %s", item_path)
                continue

            # Handle GeoPackages
            if ext == FileFormat.GPKG.value:
                yield from (Path(v) for v in _discover_gpkg_layers(item_path))
                continue

            # Handle Shapefiles (need to group related files)
            if ext == FileFormat.SHP.value:
                base_name = item_path.stem
                shp_dir = tmp_dir / f"{base_name}_set"
                shp_dir.mkdir(exist_ok=True)

                # Move all files with the same base name to the shapefile directory
                for related_file in tmp_dir.iterdir():
                    if (
                        related_file.is_file()
                        and related_file.stem == base_name
                        and related_file.suffix.lower()
                        in {".shp", ".shx", ".dbf", ".prj", ".cpg"}
                    ):
                        related_file.rename(shp_dir / related_file.name)

                yield shp_dir / f"{base_name}.shp"
                continue

            # Handle other supported formats
            if ext in ALL_EXTS:
                yield item_path


def discover_inputs(src_path: str | Path) -> list[str]:
    """
    Discover convertible dataset paths in file, folder, ZIP, or remote URL.

    Args:
        src_path: Source path to discover

    Returns:
        List of discovered dataset paths

    Raises:
        DiscoveryError: If discovery fails
        FileNotFoundError: If source path doesn't exist
    """
    parsed = urlparse(str(src_path))
    is_remote = parsed.scheme in {"http", "https", "s3"}

    try:
        if is_remote:
            return _discover_remote_inputs(str(src_path))
        else:
            return _discover_local_inputs(Path(src_path))

    except Exception as e:
        if isinstance(e, (DiscoveryError, FileNotFoundError)):
            raise
        raise DiscoveryError(f"Discovery failed for {src_path}: {e}") from e


def _discover_remote_inputs(url: str) -> list[str]:
    """Discover inputs from remote sources."""
    path_lower = urlparse(url).path.lower()

    if path_lower.endswith(FileFormat.ZIP.value):
        logger.info("Remote ZIP detected → download & expand: %s", url)
        with temporary_download(url) as local_copy:
            return [str(p) for p in _discover_from_zip(local_copy)]
    else:
        logger.debug("Remote single file detected → pass through: %s", url)
        return [url]


def _discover_local_inputs(path: Path) -> list[str]:
    """Discover inputs from local sources."""
    if not path.exists():
        raise FileNotFoundError(f"Source path not found: {path}")

    if path.is_dir():
        return [str(p) for p in _discover_from_dir(path)]

    ext = path.suffix.lower()

    if ext == FileFormat.ZIP.value:
        return [str(p) for p in _discover_from_zip(path)]
    elif ext == FileFormat.GPKG.value:
        return _discover_gpkg_layers(path)
    else:
        return [str(path)]
