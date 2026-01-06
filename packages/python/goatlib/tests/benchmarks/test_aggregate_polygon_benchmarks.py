"""
Benchmark tests for Aggregate Polygon operations with large datasets.

This benchmark tests aggregating landuse polygons (~113K in Munich)
onto German county polygons (~430 polygons).
"""

import time
from pathlib import Path
from typing import Tuple

from goatlib.analysis.geoanalysis.aggregate_polygon import AggregatePolygonTool
from goatlib.analysis.schemas.aggregate import (
    AggregatePolygonParams,
    AggregationAreaType,
    ColumnStatistic,
    StatisticsOperation,
)


def benchmark_aggregate_polygon_munich_landuse() -> Tuple[float, float, str, int]:
    """
    Benchmark aggregate polygon operation with Munich landuse polygons
    aggregated onto German counties.

    This tests performance with many small source polygons (landuse parcels)
    being aggregated onto larger area polygons (counties).

    Returns:
        Tuple of (execution_time_seconds, output_size_mb, output_file_path, polygon_count)
    """
    # Test data paths
    test_data_dir = Path(__file__).parent.parent / "data" / "vector"
    result_dir = Path(__file__).parent.parent / "result"

    # Ensure result directory exists
    result_dir.mkdir(parents=True, exist_ok=True)

    landuse_data = str(test_data_dir / "landuse_munich.parquet")
    counties_data = str(test_data_dir / "germany_counties.parquet")
    output_path = str(result_dir / "aggregate_polygon_munich_counties.parquet")

    # Check if landuse file exists
    if not Path(landuse_data).exists():
        raise FileNotFoundError(f"Munich landuse file not found: {landuse_data}")
    if not Path(counties_data).exists():
        raise FileNotFoundError(f"Germany counties file not found: {counties_data}")

    # Clean up any existing output
    if Path(output_path).exists():
        Path(output_path).unlink()

    # Get counts using DuckDB
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    polygon_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{landuse_data}')"
    ).fetchone()[0]
    area_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{counties_data}')"
    ).fetchone()[0]
    con.close()

    # Set up aggregate parameters
    params = AggregatePolygonParams(
        source_path=landuse_data,
        area_type=AggregationAreaType.polygon,
        area_layer_path=counties_data,
        column_statistics=ColumnStatistic(
            operation=StatisticsOperation.count,
        ),
        weighted_by_intersecting_area=False,
        output_path=output_path,
    )

    print("🔧 Benchmark: Munich Landuse Polygons to German Counties")
    print(f"📊 Source layer: Munich landuse ({polygon_count:,} polygons)")
    print(f"🗺️  Area layer: Germany counties ({area_count:,} polygons)")
    print("📈 Operation: COUNT (unweighted)")
    print(f"💾 Output: {output_path}")

    # Start timing
    start_time = time.time()

    # Run aggregate operation
    tool = AggregatePolygonTool()
    tool.con.execute("SET memory_limit='4GB';")
    results = tool.run(params)

    # End timing
    end_time = time.time()
    execution_time = end_time - start_time

    # Get result info
    output_size_mb = Path(output_path).stat().st_size / (1024 * 1024)

    print("✅ Benchmark completed!")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")
    print(f"📄 Output file size: {output_size_mb:.2f} MB")
    print(f"🗂️  Results: {len(results)} datasets created")
    print(f"🔷 Throughput: {polygon_count / execution_time:,.0f} polygons/second")

    return execution_time, output_size_mb, output_path, polygon_count


def benchmark_aggregate_polygon_weighted() -> Tuple[float, float, str, int]:
    """
    Benchmark aggregate polygon operation with weighted statistics.

    This tests the performance of weighted aggregation where statistics
    are proportionally distributed based on intersection area.

    Returns:
        Tuple of (execution_time_seconds, output_size_mb, output_file_path, polygon_count)
    """
    # Test data paths
    test_data_dir = Path(__file__).parent.parent / "data" / "vector"
    result_dir = Path(__file__).parent.parent / "result"

    # Ensure result directory exists
    result_dir.mkdir(parents=True, exist_ok=True)

    landuse_data = str(test_data_dir / "landuse_munich.parquet")
    counties_data = str(test_data_dir / "germany_counties.parquet")
    output_path = str(result_dir / "aggregate_polygon_munich_counties_weighted.parquet")

    # Check if landuse file exists
    if not Path(landuse_data).exists():
        raise FileNotFoundError(f"Munich landuse file not found: {landuse_data}")
    if not Path(counties_data).exists():
        raise FileNotFoundError(f"Germany counties file not found: {counties_data}")

    # Clean up any existing output
    if Path(output_path).exists():
        Path(output_path).unlink()

    # Get counts using DuckDB
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    polygon_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{landuse_data}')"
    ).fetchone()[0]
    area_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{counties_data}')"
    ).fetchone()[0]
    con.close()

    # Set up aggregate parameters with weighted statistics
    params = AggregatePolygonParams(
        source_path=landuse_data,
        area_type=AggregationAreaType.polygon,
        area_layer_path=counties_data,
        column_statistics=ColumnStatistic(
            operation=StatisticsOperation.count,
        ),
        weighted_by_intersecting_area=True,
        output_path=output_path,
    )

    print("🔧 Benchmark: Munich Landuse Polygons to German Counties (Weighted)")
    print(f"📊 Source layer: Munich landuse ({polygon_count:,} polygons)")
    print(f"🗺️  Area layer: Germany counties ({area_count:,} polygons)")
    print("📈 Operation: COUNT (weighted by intersection area)")
    print(f"💾 Output: {output_path}")

    # Start timing
    start_time = time.time()

    # Run aggregate operation
    tool = AggregatePolygonTool()
    tool.con.execute("SET memory_limit='4GB';")
    results = tool.run(params)

    # End timing
    end_time = time.time()
    execution_time = end_time - start_time

    # Get result info
    output_size_mb = Path(output_path).stat().st_size / (1024 * 1024)

    print("✅ Benchmark completed!")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")
    print(f"📄 Output file size: {output_size_mb:.2f} MB")
    print(f"🗂️  Results: {len(results)} datasets created")
    print(f"🔷 Throughput: {polygon_count / execution_time:,.0f} polygons/second")

    return execution_time, output_size_mb, output_path, polygon_count


def benchmark_aggregate_polygon_h3() -> Tuple[float, float, str, int]:
    """
    Benchmark aggregate polygon operation to H3 grid.

    This tests performance of aggregating polygons onto H3 hexagonal grid.

    Returns:
        Tuple of (execution_time_seconds, output_size_mb, output_file_path, polygon_count)
    """
    # Test data paths
    test_data_dir = Path(__file__).parent.parent / "data" / "vector"
    result_dir = Path(__file__).parent.parent / "result"

    # Ensure result directory exists
    result_dir.mkdir(parents=True, exist_ok=True)

    landuse_data = str(test_data_dir / "landuse_munich.parquet")
    output_path = str(result_dir / "aggregate_polygon_munich_h3.parquet")

    # Check if landuse file exists
    if not Path(landuse_data).exists():
        raise FileNotFoundError(f"Munich landuse file not found: {landuse_data}")

    # Clean up any existing output
    if Path(output_path).exists():
        Path(output_path).unlink()

    # Get counts using DuckDB
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    polygon_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{landuse_data}')"
    ).fetchone()[0]
    con.close()

    # Set up aggregate parameters with H3 grid
    params = AggregatePolygonParams(
        source_path=landuse_data,
        area_type=AggregationAreaType.h3_grid,
        h3_resolution=8,
        column_statistics=ColumnStatistic(
            operation=StatisticsOperation.count,
        ),
        output_path=output_path,
    )

    print("🔧 Benchmark: Munich Landuse Polygons to H3 Grid (resolution 8)")
    print(f"📊 Source layer: Munich landuse ({polygon_count:,} polygons)")
    print("🗺️  Area: H3 hexagonal grid at resolution 8")
    print("📈 Operation: COUNT")
    print(f"💾 Output: {output_path}")

    # Start timing
    start_time = time.time()

    # Run aggregate operation
    tool = AggregatePolygonTool()
    tool.con.execute("SET memory_limit='4GB';")
    results = tool.run(params)

    # End timing
    end_time = time.time()
    execution_time = end_time - start_time

    # Get result info
    output_size_mb = Path(output_path).stat().st_size / (1024 * 1024)

    # Get H3 cell count
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    h3_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{output_path}')"
    ).fetchone()[0]
    con.close()

    print("✅ Benchmark completed!")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")
    print(f"📄 Output file size: {output_size_mb:.2f} MB")
    print(f"🗂️  Results: {len(results)} datasets created")
    print(f"🔷 H3 cells created: {h3_count:,}")
    print(f"🔷 Throughput: {polygon_count / execution_time:,.0f} polygons/second")

    return execution_time, output_size_mb, output_path, polygon_count


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 GOAT AGGREGATE POLYGON BENCHMARK")
    print("=" * 60)
    print()

    try:
        # Run unweighted benchmark
        exec_time1, file_size1, output_file1, polygon_count = (
            benchmark_aggregate_polygon_munich_landuse()
        )
        print()

        # Run weighted benchmark
        exec_time2, file_size2, output_file2, _ = benchmark_aggregate_polygon_weighted()
        print()

        # Run H3 benchmark
        exec_time3, file_size3, output_file3, _ = benchmark_aggregate_polygon_h3()
        print()

        print("=" * 60)
        print("📋 BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"   Source polygons: {polygon_count:,}")
        print()
        print("   Unweighted Aggregation:")
        print(f"      - Execution Time: {exec_time1:.2f}s")
        print(f"      - Output Size: {file_size1:.2f} MB")
        print(f"      - Performance: {polygon_count / exec_time1:,.0f} polygons/second")
        print()
        print("   Weighted Aggregation:")
        print(f"      - Execution Time: {exec_time2:.2f}s")
        print(f"      - Output Size: {file_size2:.2f} MB")
        print(f"      - Performance: {polygon_count / exec_time2:,.0f} polygons/second")
        print()
        print("   H3 Grid Aggregation:")
        print(f"      - Execution Time: {exec_time3:.2f}s")
        print(f"      - Output Size: {file_size3:.2f} MB")
        print(f"      - Performance: {polygon_count / exec_time3:,.0f} polygons/second")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        raise
