"""Storage backends for GOAT.

This module provides storage abstractions for DuckLake (GeoParquet + PostgreSQL catalog).
"""

from goatlib.storage.ducklake import BaseDuckLakeManager

__all__ = ["BaseDuckLakeManager"]
