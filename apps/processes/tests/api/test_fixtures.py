"""Test fixtures for Motia analysis service.

NOTE: Tests have been reorganized into:
- tests/unit/test_tool_registry.py - Unit tests for tool registry
- tests/unit/test_layer_tool_wrapper.py - Unit tests for layer tool wrapper
- tests/api/test_job_persistence.py - API tests for job persistence

This file contains fixture validation tests only.
"""

# Add paths for imports
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/processes/src")

from lib.tool_registry import get_tool

# --- fixture validation tests ---


@pytest.mark.asyncio
async def test_project_fixture(test_project, test_user, test_folder):
    """Test that project fixture creates a valid project."""
    assert test_project is not None
    assert test_project.id is not None
    assert test_project.user_id == test_user.id
    assert test_project.folder_id == test_folder.id
    assert test_project.name == "Test Analysis Project"
    print(f"[TEST] Project created: {test_project.id}")


@pytest.mark.asyncio
async def test_scenario_fixture(test_scenario, test_project, test_user):
    """Test that scenario fixture creates a valid scenario."""
    assert test_scenario is not None
    assert test_scenario.id is not None
    assert test_scenario.user_id == test_user.id
    assert test_scenario.project_id == test_project.id
    assert test_scenario.name == "Test Scenario"
    print(f"[TEST] Scenario created: {test_scenario.id}")


@pytest.mark.asyncio
async def test_layer_params_with_project_scenario(
    test_project, test_scenario, test_user
):
    """Test that LayerParams accepts project_id and scenario_id."""
    tool_info = get_tool("clip")
    assert tool_info is not None

    # Verify schema includes project_id and scenario_id
    fields = tool_info.layer_params_class.model_fields
    assert "project_id" in fields
    assert "scenario_id" in fields
    assert "save_results" in fields

    # Verify we can create params with these fields
    params = tool_info.layer_params_class(
        user_id=str(test_user.id),
        input_layer_id=str(uuid4()),
        overlay_layer_id=str(uuid4()),
        project_id=str(test_project.id),
        scenario_id=str(test_scenario.id),
        save_results=True,
    )

    assert params.project_id == str(test_project.id)
    assert params.scenario_id == str(test_scenario.id)
    assert params.save_results is True
    print(
        f"[TEST] Params with project/scenario: project={params.project_id}, scenario={params.scenario_id}"
    )
