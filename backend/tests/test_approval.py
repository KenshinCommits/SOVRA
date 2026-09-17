import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.agents.orchestrator import orchestrator
from backend.agents.state import AgentTask, AgentStep, AgentState, ApprovalRequest, ApprovalStatus
from backend.audit.logger import audit_logger

client = TestClient(app)

def test_approval_sufficient_evidence():
    # Setup a task in APPROVAL_REQUIRED with sufficient evidence
    task = AgentTask(prompt="Generate pump inspection report")
    step = AgentStep(
        state=AgentState.ACT,
        tool_call={"name": "generate_docx", "args": {"filename": "pump_report.docx", "content": "Sample"}},
        evidence=[
            {"filename": "Pump_SOP.pdf", "page": 2, "score": 0.85, "text": "Bearing tolerance is 0.05mm."}
        ]
    )
    task.steps.append(step)
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="generate_docx",
        tool_args={"filename": "pump_report.docx", "content": "Sample"},
        risk_level="MEDIUM",
        evidence_verification={
            "verdict": "SUFFICIENT",
            "max_score": 0.85,
            "requires_override": False
        }
    )
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    # Approve without override
    response = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "lead_engineer"})
    assert response.status_code == 200
    res_task = response.json()["task"]
    assert res_task["approval_request"]["status"] == "APPROVED"
    assert res_task["approval_request"]["decided_by"] == "lead_engineer"
    assert res_task["approval_request"]["override"] is False

def test_approval_blocked_on_insufficient_evidence_without_override():
    task = AgentTask(prompt="Execute unsafe code without enough evidence")
    step = AgentStep(
        state=AgentState.ACT,
        tool_call={"name": "execute_sandboxed_code", "args": {"code": "print(1)"}}
    )
    task.steps.append(step)
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="execute_sandboxed_code",
        tool_args={"code": "print(1)"},
        risk_level="HIGH",
        evidence_verification={
            "verdict": "INSUFFICIENT",
            "max_score": 0.15,
            "requires_override": True
        }
    )
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    # Try to approve without override flag/reason -> should fail
    response = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "tester", "override": False})
    assert response.status_code == 400
    assert "override" in response.json()["detail"].lower()

def test_approval_succeeds_with_override_and_reason():
    task = AgentTask(prompt="Execute code with manual override")
    step = AgentStep(
        state=AgentState.ACT,
        tool_call={"name": "execute_sandboxed_code", "args": {"code": "print(1)"}}
    )
    task.steps.append(step)
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="execute_sandboxed_code",
        tool_args={"code": "print(1)"},
        risk_level="HIGH",
        evidence_verification={
            "verdict": "MISSING",
            "max_score": 0.0,
            "requires_override": True
        }
    )
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    # Approve with explicit override and justification reason
    override_reason = "Manual calibration check confirmed on site by Senior Tech"
    response = client.post(f"/agent/tasks/{task.task_id}/approve", json={
        "actor": "senior_operator",
        "override": True,
        "override_reason": override_reason
    })
    assert response.status_code == 200
    res_task = response.json()["task"]
    assert res_task["approval_request"]["status"] == "APPROVED"
    assert res_task["approval_request"]["override"] is True
    assert res_task["approval_request"]["override_reason"] == override_reason

    # Verify audit log recorded EVIDENCE_OVERRIDE_APPROVED
    entries = audit_logger.get_entries(task_id=task.task_id)
    override_entries = [e for e in entries if e.get("action") == "EVIDENCE_OVERRIDE_APPROVED"]
    assert len(override_entries) > 0
    assert override_entries[0]["override_reason"] == override_reason
    assert override_entries[0]["actor"] == "senior_operator"

def test_approval_30min_expiry():
    task = AgentTask(prompt="Old pending task")
    step = AgentStep(state=AgentState.ACT)
    task.steps.append(step)
    
    # Create an expired approval request (created 35 minutes ago)
    past_time = datetime.utcnow() - timedelta(minutes=35)
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="generate_docx",
        tool_args={},
        created_at=past_time,
        expires_at=past_time + timedelta(minutes=30),
        status=ApprovalStatus.PENDING,
        evidence_verification={"verdict": "SUFFICIENT"}
    )
    assert app_req.is_expired() is True
    
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    # Attempting to approve an expired request should fail with 400
    response = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "operator"})
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

def test_operator_rejection():
    task = AgentTask(prompt="Task to reject")
    step = AgentStep(state=AgentState.ACT)
    task.steps.append(step)
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="execute_sandboxed_code",
        tool_args={"code": "os.system('rm -rf /')"},
        risk_level="CRITICAL",
        evidence_verification={"verdict": "MISSING"}
    )
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    rejection_reason = "Unsafe command detected; code execution forbidden."
    response = client.post(f"/agent/tasks/{task.task_id}/reject", json={
        "actor": "security_officer",
        "reason": rejection_reason
    })
    assert response.status_code == 200
    res_task = response.json()["task"]
    assert res_task["approval_request"]["status"] == "REJECTED"
    assert res_task["status"] == "FAILURE"
    assert rejection_reason in res_task["final_result"]

def test_approval_security_edge_cases():
    # 1. Invalid Task ID -> 404
    res = client.post("/agent/tasks/non-existent-id/approve", json={"actor": "operator"})
    assert res.status_code == 404

    # 2. Task not requiring approval -> 400
    task = AgentTask(prompt="Normal task")
    task.status = AgentState.PLAN
    orchestrator.tasks[task.task_id] = task
    res = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "operator"})
    assert res.status_code == 400
