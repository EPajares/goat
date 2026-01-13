"""DuckLake manager instance for Processes API.

Creates a read-only singleton instance of BaseDuckLakeManager from goatlib.
Processes API only reads data for sync analytics - all writes happen through the core app.
"""

from goatlib.storage import BaseDuckLakeManager

# Singleton instance in read-only mode
# This allows processes and core to run concurrently without lock conflicts
ducklake_manager = BaseDuckLakeManager(read_only=True)
