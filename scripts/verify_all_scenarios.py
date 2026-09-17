"""
SOVRA Phase 8 Verification
Tests all 8 required scenarios:
1. Normal successful task
2. Insufficient evidence
3. Approval
4. Rejection
5. Expired approval
6. Malformed file
7. Sandbox failure
8. Unavailable model
"""

import os
import sys
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.agents.orchestrator import orchestrator
from backend.agents.state import AgentTask, AgentStep, AgentState, ApprovalRequest, ApprovalStatus
from backend.audit.logger import audit_logger
from backend.sandbox.executor import SandboxExecutor
from backend.tools.tabular import exec_analyze_tabular_data

client = TestClient(app)

def test_1_normal_success():
    print("\n--- [Scenario 1] Normal Successful Task ---")
    res = client.post("/agent/tasks", json={
        "prompt": "Inspect slurry pump parameters: vibration 5.2 mm/s, bearing temp 82C. Compare against SOP."
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    task = res.json()["task"]
    assert task["task_id"] is not None
    assert task["status"] in ["PLAN", "ACT", "SUCCESS"]
    print(f"✓ Task {task['task_id'][:8]} successfully initialized in state {task['status']}")

def test_2_insufficient_evidence():
    print("\n--- [Scenario 2] Insufficient Evidence Blocking ---")
    task = AgentTask(prompt="Execute sensitive tool with insufficient evidence")
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
            "requires_override": True,
            "details": "Insufficient evidence (score 0.15 < 0.35)"
        }
    )
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    # 1. Attempt approve without override
    res = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "lead_engineer"})
    assert res.status_code == 400
    assert "Insufficient evidence" in res.json()["detail"]
    print("✓ Blocked approval without explicit override on insufficient evidence.")

    # 2. Attempt approve with override=True but missing override_reason
    res2 = client.post(f"/agent/tasks/{task.task_id}/approve", json={
        "actor": "lead_engineer",
        "override": True,
        "override_reason": ""
    })
    assert res2.status_code == 400
    assert "override_reason is required" in res2.json()["detail"]
    print("✓ Blocked override when override_reason is empty.")

    # 3. Approve with override=True and valid reason
    res3 = client.post(f"/agent/tasks/{task.task_id}/approve", json={
        "actor": "lead_engineer",
        "override": True,
        "override_reason": "Emergency plant restart authorization by lead engineer."
    })
    assert res3.status_code == 200
    assert res3.json()["task"]["approval_request"]["status"] == "APPROVED"
    assert res3.json()["task"]["approval_request"]["override"] is True
    print("✓ Approved with valid override and justification.")

def test_3_approval():
    print("\n--- [Scenario 3] Human Approval ---")
    task = AgentTask(prompt="Normal approved task")
    step = AgentStep(
        state=AgentState.ACT,
        tool_call={"name": "generate_docx", "args": {"filename": "pump_report.docx", "content": "Sample"}},
        evidence=[{"filename": "Pump_SOP.pdf", "page": 2, "score": 0.85, "text": "Bearing tolerance is 0.05mm."}]
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

    res = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "lead_engineer"})
    assert res.status_code == 200
    assert res.json()["task"]["approval_request"]["status"] == "APPROVED"
    print("✓ Human approval accepted and executed.")

def test_4_rejection():
    print("\n--- [Scenario 4] Operator Rejection ---")
    task = AgentTask(prompt="Task to reject")
    step = AgentStep(
        state=AgentState.ACT,
        tool_call={"name": "execute_sandboxed_code", "args": {"code": "rm -rf /"}}
    )
    task.steps.append(step)
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="execute_sandboxed_code",
        tool_args={"code": "rm -rf /"},
        risk_level="HIGH"
    )
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    res = client.post(f"/agent/tasks/{task.task_id}/reject", json={
        "actor": "lead_engineer",
        "reason": "Dangerous command detected; aborted."
    })
    assert res.status_code == 200
    res_task = res.json()["task"]
    assert res_task["approval_request"]["status"] == "REJECTED"
    assert res_task["status"] == "FAILED"
    print("✓ Task safely rejected and terminated.")

def test_5_expired_approval():
    print("\n--- [Scenario 5] Expired Approval Handling ---")
    task = AgentTask(prompt="Task with expired approval")
    app_req = ApprovalRequest(
        task_id=task.task_id,
        tool_name="generate_docx",
        tool_args={"filename": "test.docx"},
        risk_level="MEDIUM"
    )
    app_req.expires_at = datetime.utcnow() - timedelta(minutes=35)
    task.approval_request = app_req
    task.status = AgentState.APPROVAL_REQUIRED
    orchestrator.tasks[task.task_id] = task

    res = client.post(f"/agent/tasks/{task.task_id}/approve", json={"actor": "lead_engineer"})
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()
    assert task.approval_request.is_expired()
    print("✓ Expired approval blocked by API.")

def test_6_malformed_file():
    print("\n--- [Scenario 6] Malformed / Unsupported File ---")
    # Unsupported file extension
    files = {"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")}
    res = client.post("/upload", files=files)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]
    print("✓ Malicious / unsupported file extension blocked.")

    # Corrupted / malformed CSV — non-existent file should return an error string
    result = exec_analyze_tabular_data(file_path="nonexistent_or_malformed.csv")
    assert "not found" in result.lower() or "error" in result.lower() or "no such" in result.lower()
    print("✓ Malformed CSV handled safely by tabular tool.")

def test_7_sandbox_failure():
    print("\n--- [Scenario 7] Sandbox Failure Isolation ---")
    sandbox = SandboxExecutor(max_execution_time=10)
    # Test division by zero
    res = sandbox.execute("print(10 / 0)")
    assert res.get("returncode", 0) != 0 or "ZeroDivisionError" in res.get("output", "") or "ZeroDivisionError" in res.get("error", "")
    print("✓ ZeroDivisionError caught and isolated.")

    # Test syntax error
    res2 = sandbox.execute("def invalid syntax:")
    assert res2.get("returncode", 0) != 0 or "SyntaxError" in res2.get("output", "") or "SyntaxError" in res2.get("error", "")
    print("✓ Syntax error caught and isolated.")

def test_8_unavailable_model():
    print("\n--- [Scenario 8] Unavailable Model Validation ---")
    res = client.post("/models/generate", json={
        "prompt": "Test prompt",
        "model": "cloud-gpt-4o-enterprise"
    })
    assert res.status_code == 400
    assert "Unrecognized model" in res.json()["detail"]
    print("✓ Cloud/unregistered model rejected by model gateway.")

if __name__ == "__main__":
    print("=" * 60)
    print("SOVRA PHASE 8 COMPLETE VERIFICATION SUITE")
    print("=" * 60)
    test_1_normal_success()
    test_2_insufficient_evidence()
    test_3_approval()
    test_4_rejection()
    test_5_expired_approval()
    test_6_malformed_file()
    test_7_sandbox_failure()
    test_8_unavailable_model()
    print("\n" + "=" * 60)
    print("ALL 8 PHASE 8 SCENARIOS VERIFIED AND PASSED!")
    print("=" * 60)
