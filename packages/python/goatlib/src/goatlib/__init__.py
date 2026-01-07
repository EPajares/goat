"""
goatlib — Core geospatial analytics and I/O library used in the GOAT platform.
"""

from importlib.metadata import version

try:
    __version__ = version("goatlib")
except Exception:
    __version__ = "0.0.0-dev"
