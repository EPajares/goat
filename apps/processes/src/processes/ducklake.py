"""DuckLake manager instance for Processes API.

Creates a read-only singleton instance of BaseDuckLakeManager from goatlib.
Processes API only reads data for sync analytics - all writes happen through the core app.
"""

from goatlib.storage import BaseDuckLakeManager

from processes.config import settings

# Singleton instance for analytics queries (histogram, aggregation-stats, etc.)
# This allows processes and core to run concurrently without lock conflicts
ducklake_manager = BaseDuckLakeManager(
    read_only=True,
    pin_snapshot=settings.DUCKLAKE_PIN_SNAPSHOT,
    refresh_interval=settings.DUCKLAKE_SNAPSHOT_REFRESH_SECONDS,
)

# Separate singleton for preview-sql queries.
# preview_sql runs arbitrary user SQL of unknown duration, so it must not share
# the analytics lock — a slow or complex query would block all other analytics.
preview_ducklake_manager = BaseDuckLakeManager(
    read_only=True,
    pin_snapshot=settings.DUCKLAKE_PIN_SNAPSHOT,
    refresh_interval=settings.DUCKLAKE_SNAPSHOT_REFRESH_SECONDS,
)

# Separate singleton for layer-search.
# layer-search fans out unauthenticated ILIKE scans across many layers, so it
# must not share the analytics lock with authenticated analytics queries — nor
# the preview lock, since arbitrary preview-sql queries must not block search.
search_ducklake_manager = BaseDuckLakeManager(
    read_only=True,
    pin_snapshot=settings.DUCKLAKE_PIN_SNAPSHOT,
    refresh_interval=settings.DUCKLAKE_SNAPSHOT_REFRESH_SECONDS,
)
