"""
Fast Routing Python Package

High-performance routing library with contraction hierarchies for computing
walking isochrones and catchment areas.

Example usage:
    >>> import fast_routing_py as routing
    >>> network = routing.load_network("data/network.parquet")
    >>> result = network.calculate_isochrone(start_node=123456, max_cost=900)
    >>> print(f"Reachable nodes: {result.reachable_nodes}")
"""

from fast_routing_py import *

__version__ = "0.1.0"
__all__ = [
    "PyRoutingNetwork",
    "PyIsochroneResult",
    "load_network",
    "get_random_nodes",
]
