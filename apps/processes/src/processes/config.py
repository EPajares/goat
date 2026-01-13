"""Configuration for Processes API service."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    APP_NAME: str = "GOAT Processes API"
    DEBUG: bool = False

    # Authentication settings
    AUTH: bool = os.getenv("AUTH", "true").lower() == "true"
    KEYCLOAK_SERVER_URL: str = os.getenv(
        "KEYCLOAK_SERVER_URL", "https://auth.dev.plan4better.de"
    )
    REALM_NAME: str = os.getenv("REALM_NAME", "p4b")

    # PostgreSQL settings for DuckLake catalog
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_OUTER_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "goat")

    @property
    def POSTGRES_DATABASE_URI(self) -> str:
        """Construct PostgreSQL connection URI for DuckLake."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Schema settings
    CUSTOMER_SCHEMA: str = os.getenv("CUSTOMER_SCHEMA", "customer")

    # Windmill settings for job execution
    WINDMILL_URL: str = os.getenv("WINDMILL_URL", "http://windmill-server:8000")
    WINDMILL_WORKSPACE: str = os.getenv("WINDMILL_WORKSPACE", "goat")
    WINDMILL_TOKEN: str = os.getenv("WINDMILL_TOKEN", "")

    # DuckLake settings
    DUCKLAKE_CATALOG_SCHEMA: str = os.getenv("DUCKLAKE_CATALOG_SCHEMA", "ducklake")
    # Must match core/geoapi data path since they share the same catalog
    DUCKLAKE_DATA_DIR: str = os.getenv("DUCKLAKE_DATA_DIR", "/app/data/ducklake")
    DUCKLAKE_S3_ENDPOINT: Optional[str] = os.getenv("DUCKLAKE_S3_ENDPOINT")
    DUCKLAKE_S3_BUCKET: Optional[str] = os.getenv("DUCKLAKE_S3_BUCKET")
    DUCKLAKE_S3_ACCESS_KEY: Optional[str] = os.getenv("DUCKLAKE_S3_ACCESS_KEY")
    DUCKLAKE_S3_SECRET_KEY: Optional[str] = os.getenv("DUCKLAKE_S3_SECRET_KEY")

    # Traveltime matrices directory for heatmap tools
    TRAVELTIME_MATRICES_DIR: str = os.getenv(
        "TRAVELTIME_MATRICES_DIR", "/app/data/traveltime_matrices"
    )

    # S3/MinIO settings (shared for DuckLake and uploads)
    S3_PROVIDER: str = os.getenv("S3_PROVIDER", "hetzner").lower()
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID: Optional[str] = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: Optional[str] = os.getenv("S3_SECRET_ACCESS_KEY")
    S3_REGION_NAME: str = os.getenv("S3_REGION_NAME") or os.getenv(
        "S3_REGION", "us-east-1"
    )
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")

    # Timeout Settings (in seconds)
    REQUEST_TIMEOUT: int = int(os.getenv("PROCESSES_REQUEST_TIMEOUT", "30"))

    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]

    # Print worker URL (for PrintReport tool to render pages)
    PRINT_BASE_URL: str = os.getenv("PRINT_BASE_URL", "http://goat-web:3000")

    # Routing settings for catchment area tools
    GOAT_ROUTING_URL: str = os.getenv(
        "GOAT_ROUTING_URL", "http://goat-routing:8200/api/v2/routing"
    )
    GOAT_ROUTING_AUTHORIZATION: Optional[str] = os.getenv("GOAT_ROUTING_AUTHORIZATION")
    R5_URL: str = os.getenv("R5_URL", "https://r5.routing.plan4better.de")
    R5_REGION_MAPPING_PATH: str = os.getenv(
        "R5_REGION_MAPPING_PATH", "/app/config/r5_region_mapping.json"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()
