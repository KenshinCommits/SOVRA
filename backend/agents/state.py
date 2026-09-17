from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timedelta

class AgentState(str, Enum):
    PLAN = "PLAN"
    ACT = "ACT"
    OBSERVE = "OBSERVE"
    VERIFY = "VERIFY"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class ApprovalRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    tool_name: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str = "Sensitive operation requires human authorization."
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=30))
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    override: bool = False
    override_reason: Optional[str] = None
    evidence_verification: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        if self.status == ApprovalStatus.PENDING and datetime.utcnow() > self.expires_at:
            return True
        return self.status == ApprovalStatus.EXPIRED

class AgentStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: AgentState
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    thought: Optional[str] = None # DO NOT USE FOR HIDDEN CoT, this is for public facing plan text.
    tool_call: Optional[Dict[str, Any]] = None # {"name": "...", "args": {...}}
    tool_result: Optional[str] = None
    evidence: Optional[List[Dict[str, Any]]] = None # To store retrieved citations or results
    approval_request: Optional[ApprovalRequest] = None
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
    approval_request: Optional[ApprovalRequest] = None
