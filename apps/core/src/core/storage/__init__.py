"""Storage backends for user geospatial data.

This module provides an abstraction layer for storing user data,
supporting multiple backends:
- PostgreSQL/PostGIS (legacy)
- DuckLake with GeoParquet (new)
"""

from core.storage.ducklake import DuckLakeManager, ducklake_manager

__all__ = [
    "DuckLakeManager",
    "ducklake_manager",
]
