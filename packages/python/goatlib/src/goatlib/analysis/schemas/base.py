from pydantic import BaseModel, Field


class BaseAnalysisParams(BaseModel):
    """Base parameters for all analysis tools."""

    output_crs: str | None = Field(
        "EPSG:4326", description="Output Coordinate Reference System (CRS)"
    )
