from datetime import datetime
from typing import Literal, Optional, Self, Tuple

from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    """
    Canonical metadata describing any dataset ingested or produced by goatlib.

    It is deliberately lightweight — enough for discovery, provenance, and
    OGC API – Features/Processes integration, while keeping I/O modules fast.
    """

    # ---- Identification -------------------------------------------------
    path: str = Field(..., description="Original source path or URI (local/S3/HTTP)")
    source_type: Literal["vector", "tabular", "raster", "remote"] = Field(
        ..., description="High‑level dataset type"
    )

    # ---- Format + driver info -------------------------------------------
    driver: Optional[str] = Field(
        None, description="GDAL, DuckDB or other driver name used to read the data"
    )
    format: Optional[str] = Field(
        None, description="Format/extension after normalisation"
    )

    # ---- Spatial details -------------------------------------------------
    crs: Optional[str] = Field(
        None, description="Coordinate reference system (WKT / EPSG code)"
    )
    geometry_type: Optional[str] = Field(
        None, description="Geometry type for vector layers (Point/Line/Polygon)"
    )
    feature_count: Optional[int] = Field(None, description="Number of features or rows")
    band_count: Optional[int] = Field(None, description="Number of raster bands")
    size: Optional[Tuple[int, int]] = Field(
        None, description="Raster width × height in pixels"
    )

    # ---- Storage + provenance -------------------------------------------
    storage_backend: Optional[str] = Field(
        None, description="Backend used (local | s3 | http)"
    )
    checksum: Optional[str] = Field(
        None, description="Optional SHA‑256 hash of source content"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when metadata was created",
    )

    # ---- Convenience ----------------------------------------------------
    def short_summary(self: Self) -> str:
        """Return a compact human‑readable summary."""
        info = f"[{self.source_type}] {self.format or ''}"
        extra = []
        if self.feature_count:
            extra.append(f"{self.feature_count} features")
        if self.band_count:
            extra.append(f"{self.band_count} bands")
        if self.size:
            extra.append(f"{self.size[0]}×{self.size[1]} px")
        if extra:
            info += "  – " + ", ".join(extra)
        return info
