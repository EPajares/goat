"""
Central path configuration for processes app.

This module sets up sys.path to access:
1. Workspace venv site-packages (for goatlib dependencies like duckdb, pyproj)
2. goatlib source (editable install in uv workspace)
3. Core app source

Import this module FIRST in any file that needs goatlib or core imports.
"""

import sys

# Dynamically determine Python version for site-packages path
_python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"

# Add paths in order of priority (first = highest)
_PATHS_TO_ADD = [
    f"/app/.venv/lib/{_python_version}/site-packages",  # goatlib dependencies
    "/app/packages/python/goatlib/src",  # goatlib source
    "/app/apps/core/src",  # core app
    "/app/apps/processes/src",  # processes lib
]

for path in _PATHS_TO_ADD:
    if path not in sys.path:
        sys.path.insert(0, path)
