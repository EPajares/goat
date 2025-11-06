"""
MOTIS routing adapter package.

This package contains all MOTIS-specific adapter implementations including:
- motis_adapter: Main adapter interface
- motis_client: HTTP client for MOTIS API
- motis_converters: Request/response conversion utilities
- motis_mappings: Transport mode and other mappings
"""

from .motis_adapter import MotisPlanApiAdapter, create_motis_adapter

__all__ = ["MotisPlanApiAdapter", "create_motis_adapter"]
