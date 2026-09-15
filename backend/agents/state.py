from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class AgentState(str, Enum):
    PLAN = "PLAN"
    ACT = "ACT"
    OBSERVE = "OBSERVE"
    VERIFY = "VERIFY"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class AgentStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: AgentState
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    thought: Optional[str] = None # DO NOT USE FOR HIDDEN CoT, this is for public facing plan text.
    tool_call: Optional[Dict[str, Any]] = None # {"name": "...", "args": {...}}
    tool_result: Optional[str] = None
    evidence: Optional[List[Dict[str, Any]]] = None # To store retrieved citations or results
    error: Optional[str] = None

class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    status: AgentState = AgentState.PLAN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    steps: List[AgentStep] = []
    final_result: Optional[str] = None
    selected_model: Optional[str] = None

