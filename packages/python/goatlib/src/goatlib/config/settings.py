from typing import Self

from goatlib.config.base import CommonSettings
from goatlib.config.io import IOSettings


class Settings:
    """Unified access point for all config domains."""

    def __init__(self: Self) -> None:
        self.common = CommonSettings()
        self.io = IOSettings()


settings = Settings()
