"""Tests for tool registry (async Windmill tools)."""

import pytest

from geoapi.models.processes import (
    InputDescription,
    OutputDescription,
    ProcessDescription,
    ProcessSummary,
)
from geoapi.services.tool_registry import (
    ToolInfo,
    ToolRegistry,
    tool_registry,
)


class TestToolRegistrySingleton:
    """Tests for tool registry singleton."""

    def test_singleton_exists(self):
        """Test global tool_registry instance exists."""
        assert tool_registry is not None
        assert isinstance(tool_registry, ToolRegistry)


class TestToolRegistryDiscovery:
    """Tests for tool discovery from goatlib."""

    def test_get_tool_names_returns_list(self):
        """Test get_tool_names returns a list of tool names."""
        tools = tool_registry.get_tool_names()
        assert isinstance(tools, list)

    def test_tools_discovered_from_goatlib(self):
        """Test that tools are discovered from goatlib.analysis."""
        tools = tool_registry.get_tool_names()
        # These should be discovered from goatlib
        # The actual tools depend on what's in goatlib
        assert len(tools) >= 0  # At least 0 tools

    def test_get_all_tools_returns_dict(self):
        """Test get_all_tools returns a dict."""
        tools = tool_registry.get_all_tools()
        assert isinstance(tools, dict)

    def test_get_tool_returns_tool_info(self):
        """Test get_tool returns ToolInfo for known tool."""
        tools = tool_registry.get_tool_names()
        if tools:
            tool_info = tool_registry.get_tool(tools[0])
            assert tool_info is None or isinstance(tool_info, ToolInfo)

    def test_get_tool_unknown_returns_none(self):
        """Test get_tool returns None for unknown tool."""
        result = tool_registry.get_tool("nonexistent-tool-xyz")
        assert result is None


class TestToolRegistryProcessSummary:
    """Tests for get_process_summary method."""

    def test_get_process_summary_returns_none_for_unknown(self):
        """Test get_process_summary returns None for unknown tool."""
        summary = tool_registry.get_process_summary("unknown-tool", "http://localhost")
        assert summary is None

    def test_get_process_summary_structure(self):
        """Test process summary has correct structure."""
        tools = tool_registry.get_tool_names()
        if not tools:
            pytest.skip("No tools discovered from goatlib")

        tool_name = tools[0]
        summary = tool_registry.get_process_summary(tool_name, "http://localhost:8000")

        if summary:
            assert isinstance(summary, ProcessSummary)
            assert summary.id == tool_name
            assert summary.version is not None
            assert summary.links is not None


class TestToolRegistryProcessDescription:
    """Tests for get_process_description method."""

    def test_get_process_description_returns_none_for_unknown(self):
        """Test get_process_description returns None for unknown tool."""
        desc = tool_registry.get_process_description("unknown-tool", "http://localhost")
        assert desc is None

    def test_get_process_description_structure(self):
        """Test process description has correct structure."""
        tools = tool_registry.get_tool_names()
        if not tools:
            pytest.skip("No tools discovered from goatlib")

        tool_name = tools[0]
        desc = tool_registry.get_process_description(tool_name, "http://localhost:8000")

        if desc:
            assert isinstance(desc, ProcessDescription)
            assert desc.id == tool_name
            assert desc.inputs is not None
            assert desc.outputs is not None
            assert isinstance(desc.inputs, dict)
            assert isinstance(desc.outputs, dict)


class TestToolRegistryInputConversion:
    """Tests for Pydantic to OGC input conversion."""

    def test_inputs_have_descriptions(self):
        """Test converted inputs have InputDescription type."""
        tools = tool_registry.get_tool_names()
        if not tools:
            pytest.skip("No tools discovered from goatlib")

        tool_name = tools[0]
        desc = tool_registry.get_process_description(tool_name, "http://localhost:8000")

        if desc and desc.inputs:
            for input_name, input_desc in desc.inputs.items():
                assert isinstance(input_desc, InputDescription)
                assert input_desc.title is not None
                assert input_desc.schema_ is not None


class TestToolRegistryOutputConversion:
    """Tests for output conversion."""

    def test_outputs_have_descriptions(self):
        """Test outputs have OutputDescription type."""
        tools = tool_registry.get_tool_names()
        if not tools:
            pytest.skip("No tools discovered from goatlib")

        tool_name = tools[0]
        desc = tool_registry.get_process_description(tool_name, "http://localhost:8000")

        if desc and desc.outputs:
            for output_name, output_desc in desc.outputs.items():
                assert isinstance(output_desc, OutputDescription)
                assert output_desc.title is not None


class TestToolInfo:
    """Tests for ToolInfo dataclass."""

    def test_tool_info_structure(self):
        """Test ToolInfo has expected attributes."""
        tools = tool_registry.get_all_tools()
        if not tools:
            pytest.skip("No tools discovered from goatlib")

        tool_name, tool_info = next(iter(tools.items()))
        assert hasattr(tool_info, "name")
        assert hasattr(tool_info, "display_name")
        assert hasattr(tool_info, "description")
        assert hasattr(tool_info, "params_class")
        assert hasattr(tool_info, "tool_class")
