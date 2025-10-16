from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSettingsModel(BaseSettings):
    """Base configuration model with uv/.env support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class CommonSettings(BaseSettingsModel):
    """Common environment variables shared across services."""

    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
