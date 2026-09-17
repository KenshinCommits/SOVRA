import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.evidence.gate import EvidenceGate, EvidenceVerdict
from backend.agents.state import AgentTask, AgentStep, AgentState, ApprovalRequest
from backend.agents.orchestrator import orchestrator
from backend.tools.registry import registry
from backend.tools.tabular import exec_analyze_tabular_data
from backend.tools.vision import exec_analyze_engineering_drawing
from backend.ingestion.parsers import DocumentParser
from backend.sandbox.executor import SandboxExecutor

client = TestClient(app)

def test_failure_missing_evidence():
    """Verify that sensitive action without citations triggers MISSING verdict and blocks approval."""
    gate = EvidenceGate(min_score_threshold=0.35)
    steps = [AgentStep(state=AgentState.PLAN, thought="Directly generate report")]
    verification = gate.evaluate(steps, "generate_docx", {"filename": "report.docx", "content": "data"})
    assert verification.verdict == EvidenceVerdict.MISSING
    assert verification.requires_override is True

    # Test orchestrator blocks approval
    task = AgentTask(prompt="Generate report without citations")
    task.steps = steps
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="generate_docx",
        tool_args={"filename": "report.docx", "content": "data"},
        evidence_verification=verification.model_dump(mode="json")
    )
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    resp = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "tester", "override": False})
    assert resp.status_code == 400
    assert "override" in resp.json()["detail"].lower()

def test_failure_irrelevant_evidence():
    """Verify that low-relevance citations trigger INSUFFICIENT verdict and require override."""
    gate = EvidenceGate(min_score_threshold=0.35)
    steps = [
        AgentStep(
            state=AgentState.OBSERVE,
            tool_call={"name": "knowledge_search", "args": {"query": "unrelated"}},
            evidence=[{"filename": "doc.txt", "score": 0.12, "text": "Noise content", "page": 1}]
        )
    ]
    verification = gate.evaluate(steps, "generate_docx", {"filename": "audit.docx", "content": "data"})
    assert verification.verdict == EvidenceVerdict.INSUFFICIENT
    assert verification.requires_override is True
    assert verification.max_score == 0.12

def test_failure_unsupported_file():
    """Verify that uploading or parsing an unsupported file format fails gracefully."""
    fake_path = Path("test_fake.exe")
    fake_path.touch()
    try:
        with pytest.raises(ValueError) as exc_info:
            DocumentParser.parse_file(str(fake_path))
        assert "unsupported" in str(exc_info.value).lower()
    finally:
        if fake_path.exists():
            fake_path.unlink()

def test_failure_malformed_csv():
    """Verify that malformed or empty CSV produces clean error message without unhandled crash."""
    bad_csv = Path("bad_telemetry.csv")
    with open(bad_csv, "w", encoding="utf-8") as f:
        f.write("")  # completely empty file
    try:
        result = exec_analyze_tabular_data(str(bad_csv))
        assert "Error" in result
    finally:
        if bad_csv.exists():
            bad_csv.unlink()

def test_failure_failed_tool():
    """Verify that executing non-existent tool or path traversal returns clear error."""
    # 1. Non-existent tool
    with pytest.raises(ValueError) as exc_info:
        registry.execute("non_existent_tool_xyz", {})
    assert "unknown" in str(exc_info.value).lower()

    # 2. Path traversal in reading file
    res = registry.execute("read_file", {"path": "../../etc/passwd"})
    assert "access denied" in res.lower()

def test_failure_sandbox_execution_error():
    """Verify that sandbox execution captures runtime errors cleanly without backend crash."""
    sandbox = SandboxExecutor(max_execution_time=5)
    # Python code that raises an unhandled ZeroDivisionError
    res = sandbox.execute("x = 1 / 0\nprint(x)")
    assert res["status"] == "error"
    assert "ZeroDivisionError" in res["output"]

def test_failure_sandbox_timeout():
    """Verify that infinite loop code in sandbox is cleanly terminated by timeout."""
    sandbox = SandboxExecutor(max_execution_time=2)
    res = sandbox.execute("import time\nwhile True: time.sleep(1)")
    assert res["status"] == "timeout"
    assert "timed out" in res["output"].lower() or res["execution_time_seconds"] >= 2.0
