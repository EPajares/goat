# src/goatlib/io/converter.py
import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Self
from urllib.parse import urlparse

import duckdb

from goatlib.config import settings
from goatlib.io.formats import ALL_EXTS, FileFormat
from goatlib.io.utils import detect_path_type, download_if_remote
from goatlib.models.io import DatasetMetadata

if TYPE_CHECKING:
    pass

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
    is_wkt: bool = False  # True if geometry is WKT text that needs conversion


class IOConverter:
    """
    Core converter: any input → Parquet/GeoParquet or COG GeoTIFF.
    Works locally, over HTTP, and on S3.
    """

    def __init__(self: Self) -> None:
        self.con = duckdb.connect(database=":memory:")
        self._setup_duckdb_extensions()

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

        Returns:
            DatasetMetadata with conversion results
        """
        logger.info("Starting conversion: %s", src_path)

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
                )

            # Convert single file
            return self._convert_single_file(
                src_info, out, geometry_col, target_crs, column_mapping
            )

        except Exception as e:
            logger.error("Conversion failed for %s: %s", src_path, e)
            raise

    def _preprocess_source(
        self: Self, src_path: str, timeout: int | None
    ) -> SourceInfo:
        """Preprocess source path and extract information."""
        logger.debug("Preprocessing source: %s", src_path)

        # Download HTTP sources
        downloaded_path = download_if_remote(src_path, timeout)

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
    ) -> DatasetMetadata:
        """Handle conversion of archive formats (ZIP, KMZ)."""
        logger.info(
            "Processing %s archive: %s", src_info.path_obj.suffix.upper(), src_info.path
        )

        if src_info.path_obj.suffix.lower() == FileFormat.ZIP.value:
            return self._handle_zip_conversion(
                src_info.path,
                out_path,
                geometry_col,
                target_crs,
                column_mapping,
                timeout,
            )
        else:  # KMZ
            return self._handle_kmz_conversion(
                src_info.path,
                out_path,
                geometry_col,
                target_crs,
                column_mapping,
                timeout,
            )

    def _handle_zip_conversion(
        self: Self,
        zip_path: str,
        out_path: Path,
        geometry_col: str | None = None,
        target_crs: str | None = None,
        column_mapping: ColumnMapping | None = None,
        timeout: int | None = None,
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
    ) -> DatasetMetadata:
        """Convert a single file to Parquet/GeoParquet."""
        logger.debug("Analyzing source format: %s", src_info.path)

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
        logger.info("Writing Parquet file: %s", out_path)
        self._execute_parquet_conversion(query, out_path, geom_info.has_geometry)

        # Build metadata
        logger.debug("Finalizing metadata for: %s", out_path)
        return self._build_parquet_metadata(
            out_path, src_info.path, geom_info, target_crs
        )

    def _build_source_reader(self: Self, src_info: SourceInfo) -> str:
        """Build appropriate source reader SQL fragment."""
        if src_info.is_wfs_xml:
            return f"ST_Read('{src_info.path}', allowed_drivers=ARRAY['WFS'])"
        elif src_info.layer_name:
            return f"ST_Read('{src_info.path}', layer='{src_info.layer_name}')"
        elif src_info.path_obj and src_info.path_obj.suffix.lower() in (
            FileFormat.TXT.value,
            FileFormat.CSV.value,
            FileFormat.TSV.value,
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

        # For CSV/tabular reads, check for WKT geometry columns
        if st_read.startswith("read_csv") or st_read.startswith("read_parquet"):
            return self._detect_tabular_geometry(st_read, user_geometry_col)

        # Check if this is a tabular format read via ST_Read (XLSX, etc.)
        # that might have WKT geometry columns
        if src_info.path_obj and src_info.path_obj.suffix.lower() in (
            FileFormat.XLSX.value,
            FileFormat.CSV.value,
            FileFormat.TSV.value,
            FileFormat.TXT.value,
        ):
            # Try to detect WKT geometry in tabular format
            tabular_geom = self._detect_tabular_geometry(st_read, user_geometry_col)
            if tabular_geom.has_geometry:
                return tabular_geom
            # If no WKT found, continue with ST_Read detection

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

    def _detect_tabular_geometry(
        self: Self, st_read: str, user_geometry_col: str | None
    ) -> GeometryInfo:
        """Detect WKT geometry column in tabular data (CSV, XLSX, TSV, etc.).

        Looks for columns named 'geometry', 'geom', 'wkt', 'wkt_geom', 'the_geom'
        that contain WKT text representations.

        Raises:
            ValueError: If geometry coordinates are outside WGS84 bounds
                (longitude: -180 to 180, latitude: -90 to 90).
        """
        geom_info = GeometryInfo()

        # Known WKT geometry column names (case-insensitive)
        wkt_column_names = {"geometry", "geom", "wkt", "wkt_geom", "the_geom"}

        try:
            # Get column info from CSV
            col_info = self.con.execute(f"SELECT * FROM {st_read} LIMIT 0").description
            all_cols = [c[0] for c in col_info]

            # Find geometry column
            geom_col = None
            if user_geometry_col:
                # User specified geometry column
                if user_geometry_col in all_cols:
                    geom_col = user_geometry_col
            else:
                # Auto-detect by name
                for col in all_cols:
                    if col.lower() in wkt_column_names:
                        geom_col = col
                        break

            if not geom_col:
                logger.debug("No WKT geometry column found in tabular data")
                return geom_info

            # Verify it contains WKT by checking first non-null value
            try:
                sample = self.con.execute(
                    f'SELECT "{geom_col}" FROM {st_read} WHERE "{geom_col}" IS NOT NULL LIMIT 1'
                ).fetchone()
                if sample and sample[0]:
                    val = str(sample[0]).strip().upper()
                    # Check if it looks like WKT
                    wkt_prefixes = (
                        "POINT",
                        "LINESTRING",
                        "POLYGON",
                        "MULTIPOINT",
                        "MULTILINESTRING",
                        "MULTIPOLYGON",
                        "GEOMETRYCOLLECTION",
                    )
                    if val.startswith(wkt_prefixes):
                        # Validate coordinates are within WGS84 bounds
                        self._validate_wgs84_bounds(st_read, geom_col)

                        geom_info.has_geometry = True
                        geom_info.source_column = geom_col
                        geom_info.output_column = "geometry"
                        geom_info.srid = "EPSG:4326"  # Assume WGS84 for WKT
                        geom_info.is_wkt = True  # Mark as WKT for conversion
                        logger.info("Detected WKT geometry column: %s", geom_col)
            except ValueError:
                # Re-raise validation errors
                raise
            except Exception as e:
                logger.debug("Could not verify WKT column %s: %s", geom_col, e)

        except ValueError:
            # Re-raise validation errors from bounds check
            raise
        except Exception as e:
            logger.debug("Tabular geometry detection failed: %s", e)

        return geom_info

    def _validate_wgs84_bounds(self: Self, st_read: str, geom_col: str) -> None:
        """Validate that WKT geometry coordinates are within WGS84 bounds.

        For CSV/tabular files, we assume coordinates should be in WGS84
        (EPSG:4326). This validation rejects files with coordinates outside
        valid WGS84 bounds which likely indicates the data is in a projected
        coordinate system (e.g., EPSG:3857).

        Args:
            st_read: The DuckDB source reader expression
            geom_col: Name of the WKT geometry column

        Raises:
            ValueError: If coordinates are outside WGS84 bounds
                (longitude: -180 to 180, latitude: -90 to 90)
        """
        # WGS84 bounds
        MIN_LON, MAX_LON = -180.0, 180.0
        MIN_LAT, MAX_LAT = -90.0, 90.0

        try:
            # Calculate bounding box of all geometries
            # ST_GeomFromText converts WKT to geometry, ST_Extent gets bbox
            bbox = self.con.execute(
                f"""
                SELECT
                    ST_XMin(ST_Extent_Agg(geom)) as min_x,
                    ST_YMin(ST_Extent_Agg(geom)) as min_y,
                    ST_XMax(ST_Extent_Agg(geom)) as max_x,
                    ST_YMax(ST_Extent_Agg(geom)) as max_y
                FROM (
                    SELECT ST_GeomFromText("{geom_col}") as geom
                    FROM {st_read}
                    WHERE "{geom_col}" IS NOT NULL
                )
                """
            ).fetchone()

            if bbox and all(v is not None for v in bbox):
                min_x, min_y, max_x, max_y = bbox

                # Check if any coordinate is outside WGS84 bounds
                out_of_bounds = (
                    min_x < MIN_LON
                    or max_x > MAX_LON
                    or min_y < MIN_LAT
                    or max_y > MAX_LAT
                )

                if out_of_bounds:
                    raise ValueError(
                        f"CSV geometry coordinates are outside WGS84 bounds. "
                        f"Detected extent: [{min_x:.2f}, {min_y:.2f}, {max_x:.2f}, {max_y:.2f}]. "
                        f"WGS84 bounds are [{MIN_LON}, {MIN_LAT}, {MAX_LON}, {MAX_LAT}]. "
                        f"CSV files must contain coordinates in WGS84 (EPSG:4326). "
                        f"Please convert your data to WGS84 before uploading."
                    )

                logger.debug(
                    "WGS84 bounds validation passed. Extent: [%.2f, %.2f, %.2f, %.2f]",
                    min_x,
                    min_y,
                    max_x,
                    max_y,
                )

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.warning("Could not validate WGS84 bounds: %s", e)
            # Don't fail if we can't validate - let conversion proceed

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

        # Handle geometry conversion/transformation if needed
        if geom_info.has_geometry and geom_info.source_column:
            from_crs = geom_info.srid or "EPSG:4326"

            # Build geometry expression: WKT text → geometry, optionally transform
            if geom_info.is_wkt:
                # Convert WKT text to geometry
                geom_expr = f'ST_GeomFromText("{geom_info.source_column}")'
                if target_crs and target_crs != from_crs:
                    # Use always_xy to ensure consistent X,Y (lon,lat) axis order
                    geom_expr = f"ST_Transform({geom_expr}, '{from_crs}', '{target_crs}', always_xy := true)"
                geom_expr = f'{geom_expr} AS "{geom_info.output_column}"'
            elif target_crs:
                # Already geometry, just transform
                # Use always_xy to ensure consistent X,Y (lon,lat) axis order
                # Many WFS services return lat,lon order which causes issues
                geom_expr = f"ST_Transform(\"{geom_info.source_column}\", '{from_crs}', '{target_crs}', always_xy := true) AS \"{geom_info.output_column}\""
            else:
                # No transformation needed
                geom_expr = None

            if geom_expr:
                if select_list == "*":
                    return f'SELECT * EXCLUDE ("{geom_info.source_column}"), {geom_expr} FROM {st_read}'
                else:
                    # Remove original geometry column from select list and add converted one
                    filtered_cols = [
                        col
                        for col in select_list.split(", ")
                        if f'"{geom_info.source_column}"' not in col
                    ]
                    filtered_cols.append(geom_expr)
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
        logger.debug("DuckDB COPY start: %s", out_path)
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
    ) -> DatasetMetadata:
        """Convert any raster to a Cloud-Optimized GeoTIFF (COG)."""
        from osgeo import gdal

        logger.info("Converting raster to COG: %s", src_path)

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        ds = gdal.Open(str(src_path))
        if ds is None:
            raise FileNotFoundError(f"Cannot open raster {src_path}")

        try:
            proj_wkt = ds.GetProjectionRef() or ds.GetProjection() or None

            options = {"format": "COG", "creationOptions": ["COMPRESS=LZW"]}

            if target_crs:
                logger.info("Reprojecting raster to %s: %s", target_crs, src_path)
                with tempfile.TemporaryDirectory(prefix="goatlib_cog_") as tmp_dir:
                    tmp_reproj = Path(tmp_dir) / f"{out.stem}_tmp.tif"
                    warp_opts = gdal.WarpOptions(dstSRS=target_crs)
                    gdal.Warp(str(tmp_reproj), ds, options=warp_opts)

                    logger.info("Creating COG: %s", out_path)
                    translate_opts = gdal.TranslateOptions(**options)
                    gdal.Translate(str(out), str(tmp_reproj), options=translate_opts)
            else:
                logger.info("Creating COG: %s", out_path)
                translate_opts = gdal.TranslateOptions(**options)
                gdal.Translate(str(out), ds, options=translate_opts)

            logger.info("COG conversion complete: %s", out_path)

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
