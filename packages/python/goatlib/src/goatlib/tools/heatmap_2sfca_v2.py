"""Heatmap 2SFCA V2 — on-the-fly via local C++ routing.

Per-formula Windmill entry point for the v2 heatmap stack. Pre-binds
heatmap_type=two_sfca so users get a dedicated "Heatmap 2SFCA V2" toolbox
tile alongside the legacy matrix-based tool.
"""

from goatlib.tools.heatmap_v2 import (
    Heatmap2SFCAV2ToolRunner as Heatmap2SFCAV2ToolRunner,
    Heatmap2SFCAV2WindmillParams as Heatmap2SFCAV2WindmillParams,
)


def main(params: Heatmap2SFCAV2WindmillParams) -> dict:
    """Windmill entry point."""
    runner = Heatmap2SFCAV2ToolRunner()
    runner.init_from_env()
    try:
        return runner.run(params)
    finally:
        runner.cleanup()
