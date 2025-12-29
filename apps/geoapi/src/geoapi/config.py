"""Configuration for GeoAPI service."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    APP_NAME: str = "GOAT GeoAPI"
    DEBUG: bool = False

    # PostgreSQL settings for DuckLake catalog
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_OUTER_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "goat")

    # DuckLake settings
    DUCKLAKE_CATALOG_SCHEMA: str = os.getenv("DUCKLAKE_CATALOG_SCHEMA", "ducklake")
    # Must match core app's data path since they share the same catalog
    DUCKLAKE_DATA_DIR: str = os.getenv("DUCKLAKE_DATA_DIR", "/app/data/ducklake")

    # S3/MinIO settings (optional)
    DUCKLAKE_S3_ENDPOINT: Optional[str] = os.getenv("DUCKLAKE_S3_ENDPOINT")
    DUCKLAKE_S3_BUCKET: Optional[str] = os.getenv("DUCKLAKE_S3_BUCKET")
    DUCKLAKE_S3_ACCESS_KEY: Optional[str] = os.getenv("DUCKLAKE_S3_ACCESS_KEY")
    DUCKLAKE_S3_SECRET_KEY: Optional[str] = os.getenv("DUCKLAKE_S3_SECRET_KEY")

    # MVT Settings
    MAX_FEATURES_PER_TILE: int = 15000
    DEFAULT_TILE_BUFFER: int = 256
    DEFAULT_EXTENT: int = 4096

    # Connection pool size for concurrent tile requests
    # Lower values reduce idle connections that can go stale
    DUCKLAKE_POOL_SIZE: int = int(os.getenv("GEOAPI_DUCKLAKE_POOL_SIZE", "4"))

    # Timeout Settings (in seconds)
    REQUEST_TIMEOUT: int = int(os.getenv("GEOAPI_REQUEST_TIMEOUT", "30"))
    TILE_TIMEOUT: int = int(
        os.getenv("GEOAPI_TILE_TIMEOUT", "30")
    )  # Increased for large datasets
    FEATURE_TIMEOUT: int = int(os.getenv("GEOAPI_FEATURE_TIMEOUT", "30"))
    PROCESS_TIMEOUT: int = int(os.getenv("GEOAPI_PROCESS_TIMEOUT", "60"))

    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]

    @property
    def POSTGRES_DATABASE_URI(self) -> str:
        """Construct PostgreSQL URI."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = {"env_prefix": "GEOAPI_", "case_sensitive": True}


settings = Settings()
