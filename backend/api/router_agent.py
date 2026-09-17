from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from backend.agents.orchestrator import orchestrator
from backend.agents.state import AgentTask
from backend.tools.registry import registry
from backend.audit.logger import audit_logger
from backend.evidence.gate import evidence_gate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent Workspace"])

class TaskCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The operational instruction or prompt for the agent")

class TaskStatusResponse(BaseModel):
    task: AgentTask

class ApproveTaskRequest(BaseModel):
    actor: str = Field("operator", min_length=1, description="Identifier of the approving operator")
    override: bool = Field(False, description="Explicit override flag for sub-threshold evidence")
    override_reason: Optional[str] = Field(None, description="Mandatory reason required when override is true")

class RejectTaskRequest(BaseModel):
    actor: str = Field("operator", min_length=1, description="Identifier of the rejecting operator")
    reason: Optional[str] = Field(None, description="Optional explanation for rejection")

class TaskEvidenceResponse(BaseModel):
    task_id: str
    evidence_records: List[Dict[str, Any]]
    verification: Dict[str, Any]

class AuditLogsResponse(BaseModel):
    entries: List[Dict[str, Any]]
    count: int

async def _run_agent_loop(task_id: str):
    """Background task to run the agent loop until success/failure/approval."""
    task = orchestrator.get_task(task_id)
    if not task:
        return
    
    while task.status not in ("SUCCESS", "FAILURE", "APPROVAL_REQUIRED"):
        await orchestrator.step(task_id)

@router.post("/tasks", response_model=TaskStatusResponse, status_code=status.HTTP_200_OK)
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    clean_prompt = request.prompt.strip()
    if not clean_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task prompt cannot be empty or whitespace only"
        )
    try:
        task = await orchestrator.create_task(clean_prompt)
        background_tasks.add_task(_run_agent_loop, task.task_id)
        return TaskStatusResponse(task=task)
    except Exception as e:
        logger.exception("Task creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task creation failed: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    clean_id = task_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task ID cannot be empty"
        )
    task = orchestrator.get_task(clean_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{clean_id}' not found"
        )
    return TaskStatusResponse(task=task)

@router.get("/tools")
async def list_tools() -> List[Dict[str, Any]]:
    return registry.list_tools()

@router.post("/tasks/{task_id}/approve", response_model=TaskStatusResponse)
async def approve_task(
    task_id: str, 
    background_tasks: BackgroundTasks, 
    body: Optional[ApproveTaskRequest] = None
):
    req = body or ApproveTaskRequest()
    clean_id = task_id.strip()
    
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task ID cannot be empty"
        )
        
    task = orchestrator.tasks.get(clean_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{clean_id}' not found"
        )
        
    if task.approval_request and task.approval_request.is_expired():
        orchestrator.get_task(clean_id)  # triggers expiry cleanup
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval request has expired (30-minute limit exceeded)"
        )

    if task.status != "APPROVAL_REQUIRED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task does not require approval"
        )

    if req.override and (not req.override_reason or not req.override_reason.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit justification reason ('override_reason') is required when override is enabled."
        )
        
    try:
        updated_task = orchestrator.approve_task(
            task_id=clean_id,
            actor=req.actor.strip() or "operator",
            override=req.override,
            override_reason=req.override_reason.strip() if req.override_reason else None
        )
        background_tasks.add_task(_run_agent_loop, clean_id)
        return TaskStatusResponse(task=updated_task)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Approval processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval processing failed: {str(e)}"
        )

@router.post("/tasks/{task_id}/reject", response_model=TaskStatusResponse)
async def reject_task(
    task_id: str,
    body: Optional[RejectTaskRequest] = None
):
    req = body or RejectTaskRequest()
    clean_id = task_id.strip()
    
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task ID cannot be empty"
        )

    task = orchestrator.tasks.get(clean_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{clean_id}' not found"
        )
        
    if task.approval_request and task.approval_request.is_expired():
        orchestrator.get_task(clean_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval request has expired (30-minute limit exceeded)"
        )

    if task.status != "APPROVAL_REQUIRED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task does not require approval"
        )
        
    try:
        updated_task = orchestrator.reject_task(
            task_id=clean_id,
            actor=req.actor.strip() or "operator",
            reason=req.reason.strip() if req.reason else None
        )
        return TaskStatusResponse(task=updated_task)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Rejection processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rejection processing failed: {str(e)}"
        )

@router.get("/tasks/{task_id}/evidence", response_model=TaskEvidenceResponse)
async def get_task_evidence(task_id: str):
    clean_id = task_id.strip()
    task = orchestrator.get_task(clean_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{clean_id}' not found"
        )
    
    records = evidence_gate.extract_evidence(task.steps)
    verification = evidence_gate.evaluate(task.steps, "action", {})
    return TaskEvidenceResponse(
        task_id=clean_id,
        evidence_records=[r.model_dump() for r in records],
        verification=verification.model_dump()
    )

@router.get("/audit", response_model=AuditLogsResponse)
async def get_audit_logs(
    task_id: Optional[str] = Query(None, description="Filter logs by task ID"),
    limit: int = Query(50, ge=1, le=500, description="Max number of logs to return")
):
    clean_task_id = task_id.strip() if task_id else None
    entries = audit_logger.get_entries(task_id=clean_task_id, limit=limit)
    return AuditLogsResponse(entries=entries, count=len(entries))
