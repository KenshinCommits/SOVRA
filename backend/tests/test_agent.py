import pytest
from backend.tools.registry import registry, Tool
from backend.tools.builtins import exec_list_project_files, exec_read_file
from backend.agents.orchestrator import orchestrator
from backend.agents.state import AgentState

def test_tool_registration():
    assert registry.get_tool("knowledge_search") is not None
    assert registry.get_tool("list_project_files") is not None
    
    # Try unregistered tool
    with pytest.raises(ValueError):
        registry.execute("unknown_tool", {})

def test_path_traversal():
    # Should be blocked
    result = exec_read_file("../../../etc/passwd")
    assert "Error: Access denied" in result
    
    result = exec_list_project_files("../../../")
    assert "Error: Access denied" in result

@pytest.mark.asyncio
async def test_orchestrator_create_task():
    task = await orchestrator.create_task("Test prompt")
    assert task is not None
    assert task.status == AgentState.PLAN
    assert task.selected_model is not None
