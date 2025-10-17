# src/goatlib/io/converter.py
from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Self
from urllib.parse import urlparse

import duckdb
import requests
from osgeo import gdal

from goatlib.config import settings
from goatlib.io.formats import ALL_EXTS, FileFormat
from goatlib.io.utils import detect_path_type
from goatlib.models.io import DatasetMetadata
from goatlib.utils.progress import ProgressReporter

logger = logging.getLogger(__name__)

ColumnMapping = dict[str, str]


@dataclass
class SourceInfo:
    """Container for source file information."""

    path: str
    is_remote: bool
    path_obj: Path | None
    layer_name: str | None = None
    is_wfs_xml: bool = False


@dataclass
class GeometryInfo:
    """Container for geometry-related information."""

    has_geometry: bool = False
    source_column: str | None = None
    output_column: str | None = None
    geom_type: str | None = None
    srid: str | None = None


class IOConverter:
    """
    Core converter: any input → Parquet/GeoParquet or COG GeoTIFF.
    Works locally, over HTTP, and on S3.
    """

    def __init__(self: Self, progress_reporter: ProgressReporter | None = None) -> None:
        self.con = duckdb.connect(database=":memory:")
        self._setup_duckdb_extensions()
        self.progress_reporter = progress_reporter

    def _setup_duckdb_extensions(self: Self) -> None:
        """Configure DuckDB with necessary extensions and settings."""
        self.con.execute("INSTALL spatial; LOAD spatial;")
        self.con.execute("INSTALL httpfs; LOAD httpfs;")

        io = settings.io
        self.con.execute("SET s3_region = $1;", [io.s3_region])
        if io.s3_endpoint_url:
            self.con.execute("SET s3_endpoint = $1;", [io.s3_endpoint_url])
        if io.s3_access_key_id:
            self.con.execute("SET s3_access_key_id = $1;", [io.s3_access_key_id])
        if io.s3_secret_access_key:
            self.con.execute(
                "SET s3_secret_access_key = $1;", [io.s3_secret_access_key]
            )

    def _update_progress(
        self: Self, progress: float, message: str, current_item: str = None
    ) -> None:
        """Helper method to update progress if reporter is available."""
        if self.progress_reporter:
            from goatlib.utils.progress import ProgressState

            self.progress_reporter.update(
                ProgressState(
                    current=progress, message=message, current_item=current_item
                )
            )

    # ------------------------------------------------------------------
    # Vector/Tabular → Parquet / GeoParquet
    # ------------------------------------------------------------------
    def to_parquet(
        self: Self,
        src_path: str,
        out_path: str | Path,
        geometry_col: str | None = None,
        target_crs: str | None = None,
        column_mapping: ColumnMapping | None = None,
        timeout: int | None = None,
        progress_reporter: ProgressReporter | None = None,
    ) -> DatasetMetadata:
        """
        Convert any vector/tabular dataset to Parquet/GeoParquet.

        Args:
            src_path: Source path (file, URL, or virtual dataset)
            out_path: Output path for Parquet file
            geometry_col: Geometry column name for spatial data
            target_crs: Target CRS for reprojection
            column_mapping: Dictionary for column renaming
            timeout: Timeout for HTTP requests
            progress_reporter: Progress reporter instance

        Returns:
            DatasetMetadata with conversion results
        """
        reporter = progress_reporter or self.progress_reporter
        self._update_progress(10, "Starting conversion", src_path)

        try:
            # Preprocess source
            src_info = self._preprocess_source(src_path, timeout)
            out = Path(out_path)
            out.parent.mkdir(parents=True, exist_ok=True)

            # Handle archive formats
            if self._is_archive_format(src_info):
                return self._handle_archive_conversion(
                    src_info,
                    out,
                    geometry_col,
                    target_crs,
                    column_mapping,
                    timeout,
                    reporter,
                )

            # Convert single file
            return self._convert_single_file(
                src_info, out, geometry_col, target_crs, column_mapping, reporter
            )

        except Exception as e:
            self._update_progress(0, f"Conversion failed: {e}", src_path)
            raise

    def _preprocess_source(
        self: Self, src_path: str, timeout: int | None
    ) -> SourceInfo:
        """Preprocess source path and extract information."""
        self._update_progress(20, "Preprocessing source", src_path)

        # Download HTTP sources
        downloaded_path = self._download_if_http(src_path, timeout)

        # Parse virtual dataset syntax
        base_path, layer_name = self._parse_virtual_dataset(downloaded_path)

        # Check if it's a local file
        path_obj = (
            Path(base_path)
            if urlparse(base_path).scheme not in {"http", "https"}
            else None
        )

        # Detect WFS XML
        is_wfs_xml = self._is_wfs_xml_datasource(path_obj) if path_obj else False

        return SourceInfo(
            path=base_path,
            is_remote=path_obj is None,
            path_obj=path_obj,
            layer_name=layer_name,
            is_wfs_xml=is_wfs_xml,
        )

    def _parse_virtual_dataset(self: Self, path: str) -> tuple[str, str | None]:
        """Parse virtual dataset syntax '<file>::<layer>'."""
        if "::" in path:
            base, layer_name = path.split("::", 1)
            return base, layer_name
        return path, None

    def _is_wfs_xml_datasource(self: Self, path_obj: Path | None) -> bool:
        """Check if file is a WFS XML datasource."""
        if not path_obj or path_obj.suffix.lower() != ".xml" or not path_obj.exists():
            return False

        try:
            head = path_obj.read_text(encoding="utf-8", errors="ignore")[:200]
            return "<OGRWFSDataSource" in head
        except Exception:
            return False

    def _is_archive_format(self: Self, src_info: SourceInfo) -> bool:
        """Check if source is an archive format that needs extraction."""
        if not src_info.path_obj:
            return False
        return src_info.path_obj.suffix.lower() in {
            FileFormat.ZIP.value,
            FileFormat.KMZ.value,
        }

    def _handle_archive_conversion(
        self: Self,
        src_info: SourceInfo,
        out_path: Path,
        geometry_col: str | None,
        target_crs: str | None,
        column_mapping: ColumnMapping | None,
        timeout: int | None,
        reporter: ProgressReporter | None,
    ) -> DatasetMetadata:
        """Handle conversion of archive formats (ZIP, KMZ)."""
        self._update_progress(
            30, f"Processing {src_info.path_obj.suffix.upper()} archive", src_info.path
        )

        if src_info.path_obj.suffix.lower() == FileFormat.ZIP.value:
            return self._handle_zip_conversion(
                src_info.path,
                out_path,
                geometry_col,
                target_crs,
                column_mapping,
                timeout,
                reporter,
            )
        else:  # KMZ
            return self._handle_kmz_conversion(
                src_info.path,
                out_path,
                geometry_col,
                target_crs,
                column_mapping,
                timeout,
                reporter,
            )

    def _handle_zip_conversion(
        self: Self,
        zip_path: str,
        out_path: Path,
        geometry_col: str | None = None,
        target_crs: str | None = None,
        column_mapping: ColumnMapping | None = None,
        timeout: int | None = None,
        reporter: ProgressReporter | None = None,
    ) -> DatasetMetadata:
        """Handle ZIP archive conversion."""
        for extracted in self._extract_supported_from_zip(zip_path):
            try:
                return self.to_parquet(
                    str(extracted),
                    out_path,
                    geometry_col=geometry_col,
                    target_crs=target_crs,
                    column_mapping=column_mapping,
                    timeout=timeout,
                    progress_reporter=reporter,
                )
            finally:
                if extracted.parent.name.startswith("goatlib_zip_"):
                    shutil.rmtree(extracted.parent, ignore_errors=True)
        raise ValueError(f"No convertible dataset found in {zip_path}")

    def _handle_kmz_conversion(
        self: Self,
        kmz_path: str,
        out_path: Path,
        geometry_col: str | None = None,
        target_crs: str | None = None,
        column_mapping: ColumnMapping | None = None,
        timeout: int | None = None,
        reporter: ProgressReporter | None = None,
    ) -> DatasetMetadata:
        """Handle KMZ archive conversion."""
        tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_kmz_"))
        try:
            with zipfile.ZipFile(kmz_path) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".kml"):
                        dest = tmp_dir / Path(name).name
                        with zf.open(name) as src, open(dest, "wb") as dst:
                            dst.write(src.read())
                        logger.info("Extracted KML %s from KMZ %s", dest, kmz_path)
                        return self.to_parquet(
                            str(dest),
                            out_path,
                            geometry_col=geometry_col,
                            target_crs=target_crs,
                            column_mapping=column_mapping,
                            timeout=timeout,
                            progress_reporter=reporter,
                        )
                raise ValueError(f"No .kml found inside KMZ {kmz_path}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _convert_single_file(
        self: Self,
        src_info: SourceInfo,
        out_path: Path,
        geometry_col: str | None,
        target_crs: str | None,
        column_mapping: ColumnMapping | None,
        reporter: ProgressReporter | None,
    ) -> DatasetMetadata:
        """Convert a single file to Parquet/GeoParquet."""
        self._update_progress(40, "Analyzing source format", src_info.path)

        # Build source reader
        st_read = self._build_source_reader(src_info)

        # Detect geometry information
        geom_info = self._detect_geometry_info(src_info, st_read, geometry_col)

        # Build conversion query
        query = self._build_conversion_query(
            st_read, geom_info, target_crs, column_mapping
        )

        # Validate query returns data
        self._validate_query_returns_data(query)

        # Execute conversion
        self._update_progress(70, "Writing Parquet file", src_info.path)
        self._execute_parquet_conversion(query, out_path, geom_info.has_geometry)

        # Build metadata
        self._update_progress(90, "Finalizing metadata", src_info.path)
        return self._build_parquet_metadata(
            out_path, src_info.path, geom_info, target_crs
        )

    def _build_source_reader(self: Self, src_info: SourceInfo) -> str:
        """Build appropriate source reader SQL fragment."""
        if src_info.is_wfs_xml:
            return f"ST_Read('{src_info.path}', allowed_drivers=ARRAY['WFS'])"
        elif src_info.layer_name:
            return f"ST_Read('{src_info.path}', layer='{src_info.layer_name}')"
        elif (
            src_info.path_obj
            and src_info.path_obj.suffix.lower() == FileFormat.TXT.value
        ):
            return f"read_csv_auto('{src_info.path}', header=True)"
        elif (
            src_info.path_obj
            and src_info.path_obj.suffix.lower() == FileFormat.PARQUET.value
        ):
            return f"read_parquet('{src_info.path}')"
        else:
            return f"ST_Read('{src_info.path}')"

    def _detect_geometry_info(
        self: Self, src_info: SourceInfo, st_read: str, user_geometry_col: str | None
    ) -> GeometryInfo:
        """Detect geometry column and CRS information."""
        geom_info = GeometryInfo()

        # Only detect geometry for spatial reads
        if not st_read.startswith("ST_Read("):
            return geom_info

        try:
            meta_row = self.con.execute(
                f"SELECT * FROM ST_Read_Meta('{src_info.path}')"
            ).fetchone()
            if not meta_row or len(meta_row) < 4:
                return geom_info

            layer_list = meta_row[3]
            if not isinstance(layer_list, list) or not layer_list:
                return geom_info

            # Find target layer
            target_layer = None
            if src_info.layer_name:
                target_layer = next(
                    (
                        layer
                        for layer in layer_list
                        if layer.get("name") == src_info.layer_name
                    ),
                    None,
                )
            else:
                target_layer = layer_list[0]

            if target_layer:
                geom_fields = target_layer.get("geometry_fields") or []
                if geom_fields:
                    gf = geom_fields[0]
                    geom_info.has_geometry = True
                    geom_info.source_column = user_geometry_col or gf.get("name")
                    geom_info.geom_type = gf.get("type")

                    # Determine output column name
                    if geom_info.source_column:
                        geom_info.output_column = "geometry"  # Standardize output name

                    # Extract CRS info
                    crs_info = gf.get("crs") or {}
                    auth_name = crs_info.get("auth_name")
                    auth_code = crs_info.get("auth_code")
                    if auth_name and auth_code:
                        geom_info.srid = f"{auth_name}:{auth_code}"

        except Exception as e:
            logger.debug("ST_Read_Meta parse failed for %s: %s", src_info.path, e)

        return geom_info

    def _build_conversion_query(
        self: Self,
        st_read: str,
        geom_info: GeometryInfo,
        target_crs: str | None,
        column_mapping: ColumnMapping | None,
    ) -> str:
        """Build the conversion query with proper column handling."""
        # Build select list with column mapping
        select_list = self._build_select_list(st_read, column_mapping)

        # Handle geometry transformation if needed
        if geom_info.has_geometry and target_crs and geom_info.source_column:
            from_crs = geom_info.srid or "EPSG:4326"
            transform_expr = f"ST_Transform(\"{geom_info.source_column}\", '{from_crs}', '{target_crs}') AS \"{geom_info.output_column}\""

            if select_list == "*":
                return f'SELECT * EXCLUDE ("{geom_info.source_column}"), {transform_expr} FROM {st_read}'
            else:
                # Remove original geometry column from select list and add transformed one
                filtered_cols = [
                    col
                    for col in select_list.split(", ")
                    if f'"{geom_info.source_column}"' not in col
                ]
                filtered_cols.append(transform_expr)
                return f"SELECT {', '.join(filtered_cols)} FROM {st_read}"

        return f"SELECT {select_list} FROM {st_read}"

    def _build_select_list(
        self: Self, st_read: str, column_mapping: ColumnMapping | None
    ) -> str:
        """Build SELECT list with optional column renaming."""
        if not column_mapping:
            return "*"

        try:
            col_info = self.con.execute(f"SELECT * FROM {st_read} LIMIT 0").description
            all_cols = [c[0] for c in col_info]

            select_parts = []
            for col in all_cols:
                col_quoted = f'"{col}"'
                if col in column_mapping:
                    select_parts.append(f'{col_quoted} AS "{column_mapping[col]}"')
                else:
                    select_parts.append(col_quoted)

            return ", ".join(select_parts)

        except Exception as e:
            logger.warning("Could not introspect source columns for renaming: %s", e)
            return "*"

    def _validate_query_returns_data(self: Self, query: str) -> None:
        """Validate that the query returns at least one row."""
        try:
            result = self.con.execute(f"{query} LIMIT 1").fetchone()
            if result is None:
                raise ValueError("Source dataset is empty")
        except Exception as e:
            raise ValueError(f"Failed to execute query: {e}")

    def _execute_parquet_conversion(
        self: Self, query: str, out_path: Path, has_geometry: bool
    ) -> None:
        """Execute the conversion query and save to Parquet."""
        logger.info("DuckDB COPY start | query → %s", out_path)
        self.con.execute(
            f"COPY ({query}) TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD);"
        )

    def _build_parquet_metadata(
        self: Self,
        out_path: Path,
        src_path: str,
        geom_info: GeometryInfo,
        target_crs: str | None,
    ) -> DatasetMetadata:
        """Build metadata for Parquet conversion result."""
        try:
            count = self.con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{out_path}')"
            ).fetchone()[0]
        except Exception:
            count = 0

        return DatasetMetadata(
            path=str(out_path),
            source_type="vector" if geom_info.has_geometry else "tabular",
            format="parquet",
            storage_backend=detect_path_type(str(out_path)),
            geometry_type=geom_info.geom_type,
            crs=target_crs or geom_info.srid or None,
            feature_count=count,
        )

    # ------------------------------------------------------------------
    # Raster → COG TIFF
    # ------------------------------------------------------------------

    def to_cog(
        self: Self,
        src_path: str,
        out_path: str | Path,
        target_crs: str | None = None,
        progress_reporter: ProgressReporter | None = None,
    ) -> DatasetMetadata:
        """Convert any raster to a Cloud-Optimized GeoTIFF (COG)."""
        # Use method-level reporter if provided, otherwise instance-level
        reporter = progress_reporter or self.progress_reporter

        # Update progress using the reporter directly
        if reporter:
            from goatlib.utils.progress import ProgressState

            reporter.update(ProgressState(10, "Opening raster", src_path))

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        ds = gdal.Open(str(src_path))
        if ds is None:
            raise FileNotFoundError(f"Cannot open raster {src_path}")

        try:
            proj_wkt = ds.GetProjectionRef() or ds.GetProjection() or None

            options = {"format": "COG", "creationOptions": ["COMPRESS=LZW"]}

            if target_crs:
                if reporter:
                    reporter.update(ProgressState(30, "Reprojecting raster", src_path))
                with tempfile.TemporaryDirectory(prefix="goatlib_cog_") as tmp_dir:
                    tmp_reproj = Path(tmp_dir) / f"{out.stem}_tmp.tif"
                    warp_opts = gdal.WarpOptions(dstSRS=target_crs)
                    gdal.Warp(str(tmp_reproj), ds, options=warp_opts)

                    if reporter:
                        reporter.update(ProgressState(70, "Creating COG", src_path))
                    translate_opts = gdal.TranslateOptions(**options)
                    gdal.Translate(str(out), str(tmp_reproj), options=translate_opts)
            else:
                if reporter:
                    reporter.update(ProgressState(50, "Creating COG", src_path))
                translate_opts = gdal.TranslateOptions(**options)
                gdal.Translate(str(out), ds, options=translate_opts)

            if reporter:
                reporter.update(ProgressState(100, "COG conversion complete", src_path))

            return DatasetMetadata(
                path=str(out_path),
                source_type="raster",
                format="tif",
                crs=target_crs or proj_wkt or None,
                storage_backend=detect_path_type(src_path),
            )

        finally:
            ds = None

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _extract_supported_from_zip(self: Self, zip_path: str) -> Iterator[Path]:
        """Extract supported files from a ZIP archive."""
        tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_zip_"))
        try:
            with zipfile.ZipFile(zip_path) as z:
                members = z.namelist()
                supported = [m for m in members if Path(m).suffix.lower() in ALL_EXTS]

                if not supported:
                    raise ValueError(f"No supported files found in {zip_path}")

                for m in supported:
                    if m.endswith("/"):
                        continue
                    dest = tmp_dir / Path(m).name
                    with z.open(m) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                    yield dest
        except Exception:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise

    def _download_if_http(self: Self, src_path: str, timeout: int | None = None) -> str:
        """Download HTTP/HTTPS sources to a local temp file."""
        parsed = urlparse(src_path)
        scheme = (parsed.scheme or "").lower()

        if scheme not in {"http", "https"}:
            return src_path

        # Normalize URL
        if scheme in {"http", "https"} and not src_path.startswith(f"{scheme}://"):
            src_path = src_path.replace(f"{scheme}:/", f"{scheme}://", 1)

        effective_timeout = timeout if timeout is not None else 120

        self._update_progress(15, "Downloading remote file", src_path)

        r = requests.get(src_path, stream=True, timeout=effective_timeout)
        r.raise_for_status()

        tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_http_"))
        filename = Path(parsed.path).name or "downloaded_file"
        tmp_file = tmp_dir / filename

        with open(tmp_file, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

        logger.info("Downloaded %s → %s", src_path, tmp_file)
        return str(tmp_file)
