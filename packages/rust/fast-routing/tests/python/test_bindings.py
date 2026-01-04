#!/usr/bin/env python3
"""
Test suite for fast-routing Python bindings.

This module contains comprehensive tests for the Python bindings
of the fast-routing Rust library.
"""

import random
import time
from pathlib import Path
import pytest


class TestFastRoutingBindings:
    """Test class for fast-routing Python bindings."""
    
    @pytest.fixture(scope="class")
    def routing_module(self):
        """Import and return the routing module."""
        try:
            import fast_routing_py as routing
            return routing
        except ImportError:
            pytest.skip("fast_routing_py not available - run: maturin develop")
    
    @pytest.fixture(scope="class")
    def network_path(self):
        """Return the path to the test network."""
        network_path = Path("data/network.parquet")
        if not network_path.exists():
            pytest.skip(f"Network file not found: {network_path}")
        return str(network_path)
    
    def test_import_module(self, routing_module):
        """Test that the module can be imported."""
        assert routing_module is not None
        print("✓ Successfully imported fast_routing_py")
    
    def test_load_network(self, routing_module, network_path):
        """Test network loading."""
        start_time = time.time()
        network = routing_module.load_network(network_path)
        load_time = time.time() - start_time
        
        assert network is not None
        print(f"✓ Network loaded in {load_time:.2f}s")
    
    def test_network_info(self, routing_module, network_path):
        """Test network information retrieval."""
        network = routing_module.load_network(network_path)
        info = network.get_network_info()
        
        assert "node_count" in info
        assert "edge_count" in info
        assert info["node_count"] > 0
        assert info["edge_count"] > 0
        
        print(f"✓ Network info: {info['node_count']} nodes, {info['edge_count']} edges")
    
    def test_single_isochrone(self, routing_module, network_path):
        """Test single isochrone calculation."""
        network = routing_module.load_network(network_path)
        all_nodes = network.get_all_node_ids()
        
        if len(all_nodes) == 0:
            pytest.skip("No nodes available for testing")
        
        start_node = random.choice(all_nodes)
        max_cost = 600.0  # 10 minutes
        
        start_time = time.time()
        result = network.calculate_isochrone(start_node, max_cost)
        calc_time = time.time() - start_time
        
        assert result is not None
        assert result.max_cost == max_cost
        assert result.start_node == start_node
        assert result.reachable_nodes >= 0
        
        print(f"✓ Isochrone calculated in {calc_time:.3f}s")
        print(f"  Reached {result.reachable_nodes} nodes from node {start_node}")
    
    def test_multiple_isochrones_same_start(self, routing_module, network_path):
        """Test multiple isochrone calculations from same start point."""
        network = routing_module.load_network(network_path)
        all_nodes = network.get_all_node_ids()
        
        if len(all_nodes) == 0:
            pytest.skip("No nodes available for testing")
        
        start_node = random.choice(all_nodes)
        time_thresholds = [300.0, 600.0, 900.0]  # Multiple thresholds
        
        start_time = time.time()
        multi_results = network.calculate_isochrone_multiple_times(
            start_node, time_thresholds
        )
        total_time = time.time() - start_time
        
        assert len(multi_results) == len(time_thresholds)
        
        # Check that results are for the same start node
        for result in multi_results:
            assert result.start_node == start_node
        
        avg_time = total_time / len(multi_results)
        print(f"✓ {len(multi_results)} isochrones with different thresholds: avg {avg_time:.3f}s per calculation")
    
    def test_batch_isochrones(self, routing_module, network_path):
        """Test batch isochrone calculations."""
        network = routing_module.load_network(network_path)
        all_nodes = network.get_all_node_ids()
        
        if len(all_nodes) < 3:
            pytest.skip("Need at least 3 nodes for batch testing")
        
        # Select a few random nodes for batch processing
        batch_nodes = random.sample(all_nodes, min(3, len(all_nodes)))
        cost_thresholds = [600.0, 1200.0]  # 10 and 20 minutes
        
        start_time = time.time()
        batch_results = network.calculate_batch_isochrones(batch_nodes, cost_thresholds)
        batch_time = time.time() - start_time
        
        expected_results = len(batch_nodes) * len(cost_thresholds)
        assert len(batch_results) == expected_results
        
        print(f"✓ Batch calculation: {len(batch_results)} isochrones in {batch_time:.3f}s")
        print(f"  Average: {batch_time/len(batch_results):.3f}s per isochrone")
    
    def test_random_nodes_generation(self, routing_module, network_path):
        """Test random node generation utility."""
        network = routing_module.load_network(network_path)
        
        num_random = 10
        random_nodes = routing_module.get_random_nodes(network, num_random)
        
        assert len(random_nodes) == min(num_random, network.get_network_info()["node_count"])
        assert len(set(random_nodes)) == len(random_nodes)  # All unique
        
        print(f"✓ Generated {len(random_nodes)} random nodes: {random_nodes[:5]}...")


def test_performance_benchmark():
    """Performance benchmark test using pytest-benchmark."""
    pytest.skip("Benchmark test requires pytest-benchmark and proper setup")


if __name__ == "__main__":
    # Allow running as script for quick testing
    print("Running fast-routing Python binding tests...")
    pytest.main([__file__, "-v"])