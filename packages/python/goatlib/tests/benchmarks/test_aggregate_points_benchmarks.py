"""
Benchmark tests for Aggregate Points operations with large datasets.

This benchmark tests aggregating population points (~1M in Oberbayern)
onto landuse polygons (~2.4M polygons).
"""

import time
from pathlib import Path
from typing import Tuple

import duckdb

from goatlib.analysis.geoanalysis.aggregate_points import AggregatePointsTool
from goatlib.analysis.schemas.aggregate import (
    AggregatePointsParams,
    AggregationAreaType,
    ColumnStatistic,
    StatisticsOperation,
)


def benchmark_aggregate_points_landuse_oberbayern() -> Tuple[float, float, str, int]:
    """
    Benchmark aggregate points operation with Oberbayern population points
    aggregated onto Oberbayern landuse polygons (~2.4M polygons).

    This tests performance with many small polygons (landuse parcels).

    Returns:
        Tuple of (execution_time_seconds, output_size_mb, output_file_path, point_count)
    """
    # Test data paths
    test_data_dir = Path(__file__).parent.parent / "data" / "vector"
    result_dir = Path(__file__).parent.parent / "result"

    points_data = str(test_data_dir / "census.parquet")
    landuse_data = str(test_data_dir / "landuse_clip.parquet")
    output_path = str(result_dir / "aggregate_points_landuse_oberbayern.parquet")
    oberbayern_points_path = str(result_dir / "oberbayern_points.parquet")

    # Check if landuse file exists
    if not Path(landuse_data).exists():
        raise FileNotFoundError(f"Oberbayern landuse file not found: {landuse_data}")

    # Clean up any existing output
    if Path(output_path).exists():
        Path(output_path).unlink()
    if Path(oberbayern_points_path).exists():
        Path(oberbayern_points_path).unlink()

    # Oberbayern bounding box
    xmin, ymin, xmax, ymax = 10.71, 47.39, 13.10, 49.09

    # Filter points to Oberbayern extent
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")

    print("🔧 Filtering points to Oberbayern extent...")
    con.execute(f"""
        COPY (
            SELECT * FROM read_parquet('{points_data}')
            WHERE ST_X(geom) BETWEEN {xmin} AND {xmax}
            AND ST_Y(geom) BETWEEN {ymin} AND {ymax}
        ) TO '{oberbayern_points_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    point_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{oberbayern_points_path}')"
    ).fetchone()[0]
    landuse_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{landuse_data}')"
    ).fetchone()[0]
    con.close()

    # Set up aggregate parameters
    params = AggregatePointsParams(
        source_path=oberbayern_points_path,
        area_type=AggregationAreaType.polygon,
        area_layer_path=landuse_data,
        column_statistics=ColumnStatistic(
            operation=StatisticsOperation.sum,
            field="einwohner",
        ),
        output_path=output_path,
    )

    print("🔧 Benchmark: Oberbayern Points to Landuse Polygons")
    print(f"📊 Input: Oberbayern population grid ({point_count:,} points)")
    print(f"🗺️  Area layer: Oberbayern landuse ({landuse_count:,} polygons)")
    print("📈 Operation: SUM(einwohner)")
    print(f"💾 Output: {output_path}")

    # Start timing
    start_time = time.time()

    # Run aggregate operation (increase memory for large dataset benchmark)
    tool = AggregatePointsTool()
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
    print(f"🔷 Throughput: {point_count / execution_time:,.0f} points/second")

    return execution_time, output_size_mb, output_path, point_count


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 GOAT AGGREGATE POINTS BENCHMARK")
    print("=" * 60)
    print()

    try:
        exec_time, file_size, output_file, point_count = (
            benchmark_aggregate_points_landuse_oberbayern()
        )
        print()
        print("=" * 60)
        print("📋 BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"   Points processed: {point_count:,}")
        print(f"   Execution Time: {exec_time:.2f}s")
        print(f"   Output Size: {file_size:.2f} MB")
        print(f"   Performance: {point_count / exec_time:,.0f} points/second")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        raise
