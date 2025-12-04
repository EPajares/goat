import gc
import logging
import time
from pathlib import Path

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import pytest
from goatlib.analysis.network.network_processor import (
    InMemoryNetworkParams,
    InMemoryNetworkProcessor,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- Helper Functions ---
def get_memory_mb():
    process = psutil.Process()
    mem_info = process.memory_info()
    return {"rss": mem_info.rss / (1024**2), "vms": mem_info.vms / (1024**2)}


def print_memory(stage, current, baseline):
    rss_delta = current["rss"] - baseline["rss"]
    vms_delta = current["vms"] - baseline["vms"]
    print(
        f"{stage:<28} | RSS: {current['rss']:>7.1f} MB (+{rss_delta:6.1f}) | VMS: {current['vms']:>8.1f} MB (+{vms_delta:7.1f})"
    )


# --- Main Benchmark ---
def run_benchmark(network_path: str | None = None):
    # Get network path from conftest fixture location if not provided
    if network_path is None:
        network_path = str(
            Path(__file__).parent.parent / "data" / "network" / "network.parquet"
        )

    if not (PSUTIL_AVAILABLE and Path(network_path).exists()):
        print("psutil or network file not available. Aborting benchmark.")
        return

    print("=" * 80)
    print("🧠 In-Memory Network Processor: Performance and Memory Benchmark")
    print("=" * 80)

    gc.collect()
    baseline_memory = get_memory_mb()
    print(
        f"Baseline                     | RSS: {baseline_memory['rss']:>7.1f} MB          | VMS: {baseline_memory['vms']:>8.1f} MB"
    )

    stages = []
    params = InMemoryNetworkParams(network_path=network_path)
    total_time_start = time.perf_counter()

    with InMemoryNetworkProcessor(params) as proc:
        stages.append(("After Loading", get_memory_mb()))
        stats = proc.get_network_stats()
        original_table = proc.network_table_name
        filtered = proc.apply_sql_query(
            f"SELECT * FROM {original_table} WHERE length_m > 100"
        )
        stages.append(("After Filtering", get_memory_mb()))

        split, _ = proc.split_edge_at_point(
            latitude=48.13, longitude=11.58, base_table=filtered
        )
        stages.append(("After Edge Split", get_memory_mb()))

        proc.cleanup_intermediate_tables()
        stages.append(("After Intermediate Cleanup", get_memory_mb()))

    total_time_end = time.perf_counter()
    gc.collect()
    stages.append(("Final (After Full Cleanup)", get_memory_mb()))

    # Print all stages
    for stage_name, memory_data in stages:
        print_memory(stage_name, memory_data, baseline_memory)

    # Summary
    total_duration = total_time_end - total_time_start
    peak_rss = max(stage_data["rss"] for _, stage_data in stages)
    print("-" * 80)
    print("📊 Summary:")
    print(f"Total processing time: {total_duration:.3f} seconds")
    print(
        f"Peak Physical Memory (RSS) Increase: {peak_rss - baseline_memory['rss']:.1f} MB"
    )
    print(f"Processing Rate: {stats['edge_count'] / total_duration:,.0f} edges/second")
    print("=" * 80)


# --- Pytest Version Using Conftest Fixture ---
def test_benchmark_with_fixture(network_file: Path):
    """Pytest version of the benchmark that uses the conftest network_file fixture."""
    if not PSUTIL_AVAILABLE:
        pytest.skip("psutil not available for memory monitoring")

    run_benchmark(str(network_file))


if __name__ == "__main__":
    run_benchmark()
