#!/usr/bin/env python3
"""
Basic usage example for fast-routing Python bindings.

This script demonstrates the fundamental functionality of the
fast-routing library from Python.
"""

import random
import time
from pathlib import Path


def main() -> None:
    """Run basic usage examples."""
    try:
        # Import the fast routing module
        import fast_routing_py as routing

        print("🚀 Fast-Routing Python Bindings Demo")
        print("=" * 40)
        print("✓ Successfully imported fast_routing_py")

        # Load the network
        network_path = "data/network.parquet"
        if not Path(network_path).exists():
            print(f"❌ Network file not found: {network_path}")
            print("Please run the download script first: ./download_munich_network.sh")
            return

        print(f"\n📊 Loading network from {network_path}...")
        start_time = time.time()
        network = routing.load_network(network_path)
        load_time = time.time() - start_time

        # Get network info
        info = network.get_network_info()
        print(f"✓ Network loaded in {load_time:.2f}s")
        print(f"  📈 Network size: {info['node_count']} nodes, {info['edge_count']} edges")

        # Get some random nodes for testing
        all_nodes = network.get_all_node_ids()
        if len(all_nodes) < 5:
            print("❌ Not enough nodes for demonstration")
            return

        print(f"\n🎲 Testing with random nodes from {len(all_nodes)} available nodes")

        # Single isochrone calculation
        start_node = random.choice(all_nodes)
        max_cost = 600.0  # 10 minutes walking

        print(f"\n⏱️  Calculating 10-minute walking catchment from node {start_node}...")
        start_time = time.time()
        result = network.calculate_isochrone(start_node, max_cost)
        calc_time = time.time() - start_time

        print(f"✓ Isochrone calculated in {calc_time:.3f}s")
        print(f"  🚶‍♂️ Reachable nodes: {result.reachable_nodes}")
        print(f"  ⏰ Max travel time: {result.max_cost/60:.1f} minutes")

        # Multiple time thresholds
        print(f"\n📊 Calculating multiple time thresholds...")
        thresholds = [300.0, 600.0, 900.0, 1200.0]  # 5, 10, 15, 20 minutes
        threshold_names = ["5min", "10min", "15min", "20min"]
        
        batch_nodes = [start_node]
        start_time = time.time()
        multi_results = network.calculate_batch_isochrones(batch_nodes, thresholds)
        batch_time = time.time() - start_time

        print(f"✓ Batch calculation completed in {batch_time:.3f}s")
        print("  📈 Results by time threshold:")
        
        for i, (threshold, name) in enumerate(zip(thresholds, threshold_names)):
            if i < len(multi_results):
                nodes = multi_results[i].reachable_nodes
                print(f"    {name:>6}: {nodes:>6} reachable nodes")

        # Performance test with multiple time thresholds
        print(f"\n🔥 Performance test: Multiple time thresholds...")
        perf_thresholds = [max_cost] * 10  # Same threshold repeated
        start_time = time.time()
        perf_results = network.calculate_isochrone_multiple_times(
            start_node, perf_thresholds
        )
        perf_time = time.time() - start_time

        num_runs = len(perf_results)
        avg_time = perf_time / num_runs
        calculations_per_sec = num_runs / perf_time

        print(f"✓ Performance test completed!")
        print(f"  📊 {num_runs} calculations in {perf_time:.3f}s")
        print(f"  ⚡ Average: {avg_time:.3f}s per calculation")
        print(f"  🚀 Speed: {calculations_per_sec:.1f} calculations/second")

        print(f"\n🎉 Demo completed successfully!")
        print(f"✨ Ready for production use with real-time catchment analysis!")

    except ImportError as e:
        print(f"❌ Failed to import fast_routing_py: {e}")
        print("Please build the Python bindings first:")
        print("  maturin develop --release")
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()