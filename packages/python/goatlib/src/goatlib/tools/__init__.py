"""
Windmill tool infrastructure for GOAT.

This module provides the base classes and utilities for creating
Windmill tool scripts that:
- Run goatlib analysis tools
- Ingest results into DuckLake
- Create layer metadata in PostgreSQL
- Optionally link layers to projects

Example usage:
    from goatlib.tools import BaseToolRunner, ToolInputBase, ToolSettings

    class MyToolParams(ToolInputBase):
        my_param: str

    class MyToolRunner(BaseToolRunner[MyToolParams]):
        def process(self, params, temp_dir):
            # Run analysis, return (output_path, metadata)
            ...

    # Windmill entry point
    def main(**kwargs):
        runner = MyToolRunner()
        runner.init_from_env()
        return runner.run(MyToolParams(**kwargs))
"""

from goatlib.tools.base import BaseToolRunner, ToolSettings
from goatlib.tools.buffer import BufferToolParams, BufferToolRunner
from goatlib.tools.centroid import CentroidToolParams, CentroidToolRunner
from goatlib.tools.clip import ClipToolParams, ClipToolRunner
from goatlib.tools.codegen import generate_windmill_script, python_type_to_str
from goatlib.tools.db import ToolDatabaseService
from goatlib.tools.difference import DifferenceToolParams, DifferenceToolRunner
from goatlib.tools.dissolve import DissolveToolParams, DissolveToolRunner
from goatlib.tools.geocoding import GeocodingToolParams, GeocodingToolRunner
from goatlib.tools.intersection import IntersectionToolParams, IntersectionToolRunner
from goatlib.tools.join import JoinToolParams, JoinToolRunner
from goatlib.tools.layer_delete import LayerDeleteParams, LayerDeleteRunner
from goatlib.tools.layer_delete_multi import (
    LayerDeleteMultiParams,
    LayerDeleteMultiRunner,
)
from goatlib.tools.layer_export import LayerExportParams, LayerExportRunner
from goatlib.tools.layer_import import LayerImportParams, LayerImportRunner
from goatlib.tools.origin_destination import (
    OriginDestinationToolParams,
    OriginDestinationToolRunner,
)
from goatlib.tools.print_report import PrintReportParams, PrintReportRunner
from goatlib.tools.registry import TOOL_REGISTRY, ToolDefinition, get_tool
from goatlib.tools.schemas import (
    LayerInputMixin,
    ToolInputBase,
    ToolOutputBase,
    TwoLayerInputMixin,
)
from goatlib.tools.union import UnionToolParams, UnionToolRunner

__all__ = [
    "BaseToolRunner",
    "ToolSettings",
    "ToolDatabaseService",
    "ToolInputBase",
    "ToolOutputBase",
    "LayerInputMixin",
    "TwoLayerInputMixin",
    "BufferToolParams",
    "BufferToolRunner",
    "CentroidToolParams",
    "CentroidToolRunner",
    "ClipToolParams",
    "ClipToolRunner",
    "IntersectionToolParams",
    "IntersectionToolRunner",
    "JoinToolParams",
    "JoinToolRunner",
    "DissolveToolParams",
    "DissolveToolRunner",
    "GeocodingToolParams",
    "GeocodingToolRunner",
    "UnionToolParams",
    "UnionToolRunner",
    "DifferenceToolParams",
    "DifferenceToolRunner",
    "OriginDestinationToolParams",
    "OriginDestinationToolRunner",
    "LayerImportParams",
    "LayerImportRunner",
    "LayerDeleteParams",
    "LayerDeleteRunner",
    "LayerDeleteMultiParams",
    "LayerDeleteMultiRunner",
    "LayerExportParams",
    "LayerExportRunner",
    "PrintReportParams",
    "PrintReportRunner",
    "generate_windmill_script",
    "python_type_to_str",
    "TOOL_REGISTRY",
    "ToolDefinition",
    "get_tool",
]
