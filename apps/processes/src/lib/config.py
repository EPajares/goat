"""Configuration for Processes service using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    APP_NAME: str = "GOAT Processes API"
    DEBUG: bool = False
    API_VERSION: str = "1.0.0"

    # Server Settings (for URL generation fallbacks)
    PROCESSES_HOST: str = Field(
        default="localhost", description="Host for URL generation"
    )
    PROCESSES_PORT: int = Field(default=8200, description="Port for URL generation")

    # Data directory
    DATA_DIR: str = Field(default="/app/data")

    # PostgreSQL settings (for DuckLake catalog)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_SERVER: str = Field(default="db")  # Docker service name
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="goat")

    # DuckLake settings
    DUCKLAKE_CATALOG_SCHEMA: str = Field(default="ducklake")
    DUCKLAKE_DATA_DIR: str = Field(default="/app/data/ducklake")

    # Redis settings (for Motia state)
    MOTIA_REDIS_HOST: str = Field(default="redis")
    MOTIA_REDIS_PORT: int = Field(default=6379)
    MOTIA_DISABLE_MEMORY_SERVER: bool = Field(default=True)

    # Keycloak settings (for JWT validation)
    AUTH: bool = Field(default=True, description="Enable JWT signature verification")
    KEYCLOAK_ISSUER: str = Field(
        default="https://auth.dev.plan4better.de/realms/p4b",
        description="Keycloak issuer URL (full URL including realm)",
        alias="NEXT_PUBLIC_KEYCLOAK_ISSUER",
    )

    # S3/MinIO settings (for DuckLake storage - optional)
    DUCKLAKE_S3_ENDPOINT: Optional[str] = None
    DUCKLAKE_S3_BUCKET: Optional[str] = None
    DUCKLAKE_S3_ACCESS_KEY: Optional[str] = None
    DUCKLAKE_S3_SECRET_KEY: Optional[str] = None

    # S3 settings (for file imports/exports)
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_REGION: str = Field(default="eu-central-1")
    S3_ENDPOINT_URL: Optional[str] = None  # e.g., for Hetzner/MinIO
    S3_PUBLIC_ENDPOINT_URL: Optional[str] = None
    S3_PROVIDER: str = Field(default="aws")  # aws, hetzner, minio
    S3_BUCKET_NAME: str = Field(default="goat")
    S3_BUCKET_PATH: str = Field(default="")

    # Print/Report settings
    PRINT_FRONTEND_URL: str = Field(
        default="http://web:3000",
        description="Next.js frontend URL for print preview pages",
    )
    PRINT_OUTPUT_DIR: str = Field(
        default="prints", description="S3 subdirectory for print outputs"
    )
    PRINT_FIRST_PAGE_TIMEOUT_MS: int = Field(
        default=60000, description="Timeout in ms for first page (loads assets)"
    )
    PRINT_SUBSEQUENT_PAGE_TIMEOUT_MS: int = Field(
        default=30000, description="Timeout in ms for atlas pages (cached assets)"
    )
    PRINT_ATLAS_BATCH_SIZE: int = Field(
        default=5, description="Number of atlas pages to render in parallel"
    )

    @property
    def default_host_port(self) -> str:
        """Get default host:port string for URL generation."""
        return f"{self.PROCESSES_HOST}:{self.PROCESSES_PORT}"

    @property
    def POSTGRES_DATABASE_URI(self) -> str:
        """Construct PostgreSQL URI."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ASYNC_POSTGRES_DATABASE_URI(self) -> str:
        """Construct async PostgreSQL URI for SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {
        "env_file": "/app/.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # Ignore extra env vars
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Singleton instance for easy import
settings = get_settings()
