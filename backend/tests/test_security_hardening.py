import pytest
from fastapi.testclient import TestClient
import io

from backend.app.main import app
from backend.tools.registry import registry
from backend.agents.orchestrator import orchestrator
from backend.agents.state import ApprovalStatus

client = TestClient(app)

def test_oversized_upload_blocked():
    """Verify that uploading files larger than 25MB is rejected with 413."""
    oversized_data = io.BytesIO(b"0" * (26 * 1024 * 1024)) # 26 MB
    oversized_data.name = "giant_document.txt"
    
    response = client.post(
        "/documents/upload",
        files={"file": ("giant_document.txt", oversized_data, "text/plain")}
    )
    assert response.status_code in (413, 400)
    assert "exceeds maximum allowed size" in response.json().get("detail", "")

def test_unsupported_upload_format_blocked():
    """Verify that unsupported extensions (.exe, .bin) are rejected with 400."""
    fake_exe = io.BytesIO(b"MZ\x90\x00malicious binary content")
    fake_exe.name = "payload.exe"
    
    response = client.post(
        "/documents/upload",
        files={"file": ("payload.exe", fake_exe, "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json().get("detail", "")

def test_invalid_task_id_404():
    """Verify that requesting a non-existent task ID returns 404 Not Found."""
    response = client.get("/agent/tasks/non-existent-task-id-12345")
    assert response.status_code == 404
    assert "not found" in response.json().get("detail", "").lower()

def test_empty_prompt_blocked():
    """Verify that creating a task with an empty or whitespace prompt is rejected with 400/422."""
    response = client.post(
        "/agent/tasks",
        json={"prompt": "    "}
    )
    assert response.status_code in (400, 422)

def test_unrecognized_model_forced():
    """Verify that forcing an unregistered/unavailable model returns 400 Bad Request."""
    response = client.post(
        "/models/generate",
        json={
            "prompt": "Test prompt",
            "force_model": "non-existent-hallucinated-model-v99"
        }
    )
    assert response.status_code == 400
    assert "not recognized" in response.json().get("detail", "").lower()

def test_deep_path_traversal_blocked():
    """Verify that path traversal attempts on tools are blocked."""
    traversal_paths = [
        "../../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "/etc/shadow",
        "artifacts/../../sensitive.key"
    ]
    for p in traversal_paths:
        res = registry.execute("read_file", {"path": p})
        assert "access denied" in str(res).lower() or "error" in str(res).lower()

def test_qdrant_live_health():
    """Verify that system status endpoint returns live Qdrant health."""
    response = client.get("/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "qdrant_connected" in data
    assert "ollama_connected" in data
    assert data["sovereign_offline"] is True

@pytest.mark.asyncio
async def test_approval_missing_override_reason():
    """Verify that approving a task with override=True but empty reason is rejected."""
    task = await orchestrator.create_task("Test approval override validation")
    
    # Simulate an approval request
    from backend.agents.state import ApprovalRequest
    req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="generate_docx",
        tool_args={"content": "test", "filename": "test.docx"},
        risk_level="MEDIUM",
        reason="Test approval",
        evidence_verification={"verdict": "INSUFFICIENT"}
    )
    task.approval_request = req
    task.status = "APPROVAL_REQUIRED"
    
    # Attempt to approve with override=True but no reason
    response = client.post(
        f"/agent/tasks/{task.task_id}/approve",
        json={"actor": "operator", "override": True, "override_reason": "   "}
    )
    assert response.status_code == 400
    assert "justification reason" in response.json().get("detail", "").lower()
