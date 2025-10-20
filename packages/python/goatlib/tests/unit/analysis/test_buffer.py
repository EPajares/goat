from pathlib import Path

from goatlib.analysis.schemas.vector import BufferParams
from goatlib.analysis.vector.buffer import BufferTool


def test_buffer_tool_basic(tmp_path: Path, data_root: Path) -> None:
    """Test BufferTool with DuckDB Spatial-compatible BufferParams."""

    # Prepare test input (replace with an existing small dataset in your test repo)
    input_path = data_root / "analysis" / "example.parquet"
    # input_path = data_root / "io" / "vector" / "valid" / "geojson" / "polygon.geojson"
    work_dir = tmp_path / "buffer_test"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Initialize parameters using the new DuckDB-only BufferParams schema
    params = BufferParams(
        input_path=str(input_path),
        output_path=str(work_dir / "buffer_result.parquet"),
        distances=[100.0],  # single distance → wrap in a list
        dissolve=False,  # equivalent of union=False
        num_triangles=8,  # smoother buffer edges
        cap_style="CAP_ROUND",  # endpoint style (converted to CAP_ROUND internally)
        join_style="JOIN_ROUND",  # corner join style (converted to JOIN_ROUND internally)
        mitre_limit=1.0,  # only relevant if join_style="mitre"
        output_crs="EPSG:4326",  # reproject or keep CRS
    )

    # Run the buffer analysis tool
    tool = BufferTool()
    results = tool.run(params)

    # Basic assertions on output
    assert isinstance(results, list)
    assert len(results) == 1

    out_path, metadata = results[0]
    assert out_path.exists(), f"Output file not found: {out_path}"
    assert out_path.suffix == ".parquet"

    # Metadata validation — ensure something was buffered
    assert (
        getattr(metadata, "feature_count", 0) > 0
    ), "Expected features in buffer output"
