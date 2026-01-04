from goatlib.config.settings import Settings

# single global instance for import everywhere
settings = Settings()
__all__ = ["settings", "Settings"]
