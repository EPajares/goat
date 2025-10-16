import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Iterator, Self

import duckdb
from osgeo import gdal

from goatlib.config import settings
from goatlib.io.formats import (
    ALL_EXTS,
    FileFormat,
)
from goatlib.io.utils import detect_path_type
from goatlib.models.io import DatasetMetadata

logger = logging.getLogger(__name__)


class IOConverter:
    """
    Core converter: any input → Parquet/GeoParquet or COG GeoTIFF.
    Works locally and on S3.
    """

    def __init__(self: Self) -> None:
        self.con = duckdb.connect(database=":memory:")
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
    # Vector / Tabular → Parquet / GeoParquet
    # ------------------------------------------------------------------
    def to_parquet(
        self: Self,
        src_path: str,
        out_path: str | Path,
        geometry_col: str | None = None,
        target_crs: str | None = None,
    ) -> DatasetMetadata:
        """
        Convert any file to Parquet / GeoParquet using DuckDB Spatial.

        Parameters
        ----------
        src_path : str
            Input dataset (local path, S3 URL, HTTP URL, or ZIP archive).
        out_path : str | Path
            Destination Parquet file to create.
        geometry_col : str | None
            Optional explicit geometry column name.
        target_crs : str | None
            CRS to transform geometries to (e.g. "EPSG:3857").
            If None → no reprojection.

        Returns
        -------
        DatasetMetadata
            Metadata describing the converted dataset.
        """
        p = Path(src_path)
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # Handle ZIP archives (extract supported files, recurse)
        # ------------------------------------------------------------------
        if p.suffix.lower() == FileFormat.ZIP.value:
            logger.info("Processing ZIP archive: %s", src_path)
            for extracted in self._extract_supported_from_zip(src_path):
                try:
                    return self.to_parquet(
                        str(extracted),
                        out,
                        geometry_col=geometry_col,
                        target_crs=target_crs,
                    )
                finally:
                    shutil.rmtree(extracted.parent, ignore_errors=True)
            raise ValueError(f"No convertible dataset found in {src_path}")

        # ------------------------------------------------------------------
        # Read metadata via ST_Read_Meta to detect geometry + CRS
        # ------------------------------------------------------------------
        geom = geometry_col
        geom_type: str | None = None
        srid: str | None = None

        try:
            meta_row = self.con.execute(
                f"SELECT * FROM ST_Read_Meta('{src_path}')"
            ).fetchone()
            # meta_row → (path, driver, layer_name, [layer_meta_dicts])
            if meta_row and len(meta_row) >= 4:
                layer_list = meta_row[3]
                if isinstance(layer_list, list) and layer_list:
                    layer = layer_list[0]
                    geom_fields = layer.get("geometry_fields") or []
                    if geom_fields:
                        geom_field = geom_fields[0]
                        geom = geom or geom_field.get("name")
                        geom_type = geom_field.get("type")
                        crs_info = geom_field.get("crs") or {}
                        auth_name = crs_info.get("auth_name")
                        auth_code = crs_info.get("auth_code")
                        if auth_name and auth_code:
                            srid = f"{auth_name}:{auth_code}"
        except Exception as e:
            logger.warning("ST_Read_Meta parsing failed for %s: %s", src_path, e)

        # ------------------------------------------------------------------
        # Build query and optional transformation
        # ------------------------------------------------------------------
        from_crs = srid or "EPSG:4326"
        if geom and target_crs:
            transform_expr = (
                f"ST_Transform({geom}, '{from_crs}', '{target_crs}') AS {geom}"
            )
            query = f"SELECT *, {transform_expr} FROM ST_Read('{src_path}')"
        else:
            query = f"SELECT * FROM ST_Read('{src_path}')"

        # ------------------------------------------------------------------
        # Pre‑validate dataset not empty
        # ------------------------------------------------------------------
        sample = self.con.execute(f"{query} LIMIT 1").fetchone()
        if sample is None:
            raise ValueError(f"{src_path} appears to be empty or malformed.")

        # ------------------------------------------------------------------
        # Write to Parquet / GeoParquet
        # ------------------------------------------------------------------
        logger.info(
            "DuckDB COPY start | src=%s → %s | target CRS=%s",
            src_path,
            out,
            target_crs or "None",
        )
        self.con.execute(f"COPY ({query}) TO '{out}' (FORMAT PARQUET);")
        logger.info("DuckDB COPY done → %s", out)

        # ------------------------------------------------------------------
        # Validate written file non‑empty
        # ------------------------------------------------------------------
        count = self.con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{out}')"
        ).fetchone()[0]
        if count == 0:
            raise ValueError(f"{src_path} produced an empty Parquet file.")

        # ------------------------------------------------------------------
        # Return metadata
        # ------------------------------------------------------------------
        return DatasetMetadata(
            path=src_path,
            source_type="vector" if geom else "tabular",
            format="parquet",
            storage_backend=detect_path_type(src_path),
            geometry_type=geom_type or geom or None,
            crs=target_crs or srid,
            feature_count=count,
        )

    def _detect_geometry_column(self: Self, path: str) -> str | None:
        """Peek at ST_Read result to find a geometry column, if any."""
        try:
            # Run lightweight query that returns 1 row
            rel = self.con.execute(f"SELECT * FROM ST_Read('{path}') LIMIT 1")
            names = [d[0] for d in rel.description or []]
            for name in names:
                if name.lower().startswith("geom"):
                    return name
            return None
        except Exception:
            # If ST_Read fails (e.g., non‑spatial CSV), just return None
            return None

    # ------------------------------------------------------------------
    # Raster → COG TIFF
    # ------------------------------------------------------------------
    def to_cog(
        self: Self,
        src_path: str,
        out_path: str | Path,
        target_crs: str | None = None,
    ) -> DatasetMetadata:
        """
        Convert any raster to a Cloud‑Optimized GeoTIFF (COG).
        If target_crs is provided, reproject the raster to that CRS.

        Parameters
        ----------
        src_path : str
            Input raster dataset (local or S3 path, zipped, etc.)
        out_path : str | Path
            Destination .tif file.
        target_crs : str | None
            CRS to reproject to, e.g. 'EPSG:3857'.  If None, keep source CRS.
        """
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # ---- Open source raster (read metadata only) --------------------
        ds = gdal.Open(str(src_path))
        if ds is None:
            raise FileNotFoundError(f"Cannot open raster {src_path}")
        proj_wkt: str | None = ds.GetProjectionRef() or ds.GetProjection() or None

        # ---- Determine target and reprojection options -----------------
        options = {"format": "COG", "creationOptions": ["COMPRESS=LZW", "TILED=YES"]}
        translate_opts = gdal.TranslateOptions(**options)

        if target_crs:
            # Use gdal.Warp for reprojection before COG translation
            warp_opts = gdal.WarpOptions(dstSRS=target_crs)
            tmp_reproj = out.parent / f"{out.stem}_tmp.tif"
            logger.info("Reprojecting raster %s → %s", src_path, target_crs)
            gdal.Warp(str(tmp_reproj), ds, options=warp_opts)
            src_ds_for_translate = str(tmp_reproj)
        else:
            src_ds_for_translate = str(src_path)

        # ---- Translate into COG GeoTIFF ----------------------------
        logger.info(
            "GDAL Translate start | src=%s → %s | target CRS=%s",
            src_path,
            out,
            target_crs or "None",
        )
        gdal.Translate(str(out), src_ds_for_translate, options=translate_opts)
        logger.info("GDAL Translate done → %s", out)

        # clean up temporary reprojection
        try:
            if target_crs:
                Path(src_ds_for_translate).unlink(missing_ok=True)
        except Exception:
            pass
        ds = None  # release file handles

        # ---- Build and return metadata -----------------------------
        return DatasetMetadata(
            path=src_path,
            source_type="raster",
            format="tif",
            crs=target_crs or proj_wkt or None,
            storage_backend=detect_path_type(src_path),
        )

    # ------------------------------------------------------------------
    # Helper: extract supported files from ZIP
    # ------------------------------------------------------------------
    def _extract_supported_from_zip(self: Self, zip_path: str) -> Iterator[Path]:
        """
        Yield complete shapefile sets or other supported single files from a ZIP.
        For a .shp layer all sidecar files (.shx, .dbf, .prj, etc.) are also extracted.
        """
        tmp_dir = Path(tempfile.mkdtemp(prefix="goatlib_zip_"))
        with zipfile.ZipFile(zip_path) as z:
            members = z.namelist()
            # Candidate single files we want to expose for conversion
            supported = [m for m in members if Path(m).suffix.lower() in ALL_EXTS]

            if not supported:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                raise ValueError(f"No supported files found in {zip_path}")

            for m in supported:
                suffix = Path(m).suffix.lower()
                name_no_ext = Path(m).stem

                # ---- If Shapefile: extract full set with the same basename ----
                if suffix == FileFormat.SHP.value:
                    related = [
                        n
                        for n in members
                        if Path(n).stem == name_no_ext and not n.endswith("/")
                    ]
                    for n in related:
                        dest = tmp_dir / Path(n).name
                        with z.open(n) as src, open(dest, "wb") as dst:
                            dst.write(src.read())
                    shp_path = tmp_dir / f"{name_no_ext}.shp"
                    yield shp_path
                    continue

                # ---- normal single file --------------------------------------
                if not m.endswith("/"):
                    dest = tmp_dir / Path(m).name
                    with z.open(m) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                    yield dest
