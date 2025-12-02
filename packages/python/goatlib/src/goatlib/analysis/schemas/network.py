from pathlib import Path
from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator


class NetworkProcessorParams(BaseModel):
    """Parameters for network processing with optional artificial edges."""

    input_path: str | Path = Field(..., description="Path to input network dataset")
    output_path: Optional[str | Path] = Field(None, description="Output file path")

    custom_sql: str = Field(..., description="SQL query to extract network data")
    output_crs: Optional[str] = Field("EPSG:4326", description="Target CRS")

    origin_points_path: Optional[str | Path] = Field(
        None, description="Points for artificial edges"
    )
    buffer_distance: float = Field(100.0, description="Search distance (meters)")
    max_connections_per_point: int = Field(3, description="Max edges per point")
    artificial_node_id_start: int = Field(1_000_000_000, description="Starting node ID")
    artificial_edge_id_start: int = Field(2_000_000_000, description="Starting edge ID")

    @model_validator(mode="after")
    def validate_params(self: Self) -> "NetworkProcessorParams":
        input_p = Path(self.input_path)
        if not input_p.exists() or not input_p.is_file():
            raise ValueError(f"Input file does not exist: {self.input_path}")

        if self.origin_points_path:
            points_p = Path(self.origin_points_path)
            if not points_p.exists() or not points_p.is_file():
                raise ValueError(
                    f"Origin points file does not exist: {self.origin_points_path}"
                )

        if self.output_path and not Path(self.output_path).parent.exists():
            raise ValueError(
                f"Output directory does not exist: {Path(self.output_path).parent}"
            )

        if not self.custom_sql.strip():
            raise ValueError("custom_sql cannot be empty")
        if self.buffer_distance <= 0:
            raise ValueError("Buffer distance must be positive")
        if self.max_connections_per_point < 1:
            raise ValueError("Must connect to at least 1 edge per point")

        return self

    @property
    def creates_artificial_edges(self) -> bool:
        """Check if this configuration will create artificial edges."""
        return self.origin_points_path is not None
