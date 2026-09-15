from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.agents.orchestrator import orchestrator
from backend.agents.state import AgentTask
from backend.tools.registry import registry

router = APIRouter(prefix="/agent", tags=["Agent Workspace"])

class TaskCreateRequest(BaseModel):
    prompt: str

class TaskStatusResponse(BaseModel):
    task: AgentTask

async def _run_agent_loop(task_id: str):
    """Background task to run the agent loop until success/failure."""
    task = orchestrator.get_task(task_id)
    if not task:
        return
    
    while task.status not in ("SUCCESS", "FAILURE"):
        await orchestrator.step(task_id)

@router.post("/tasks", response_model=TaskStatusResponse)
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    try:
        task = await orchestrator.create_task(request.prompt)
        # Kick off background execution loop
        background_tasks.add_task(_run_agent_loop, task.task_id)
        return TaskStatusResponse(task=task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(task=task)

@router.get("/tools")
async def list_tools() -> List[Dict[str, Any]]:
    return registry.list_tools()
