import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

AUDIT_DIR = Path(__file__).resolve().parent
AUDIT_FILE = AUDIT_DIR / "audit_log.jsonl"

class AuditEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str  # e.g., TASK_CREATED, APPROVAL_REQUESTED, APPROVAL_GRANTED, EVIDENCE_OVERRIDE_APPROVED
    task_id: str
    actor: str = "system" # "operator", "agent", "system", or user ID
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    risk_level: Optional[str] = None
    override: bool = False
    override_reason: Optional[str] = None
    evidence_verdict: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AuditLogger:
    def __init__(self, log_path: Path = AUDIT_FILE):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, entry: AuditEntry) -> AuditEntry:
        """
        Appends an audit entry as a single JSON line.
        Guarantees append-only immutable persistence. Never stores CoT.
        """
        data = entry.model_dump(mode="json")
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            # Fallback output to stdout if disk write fails
            print(f"[AUDIT LOGGING ERROR] Could not write audit log: {e}")
        return entry

    def get_entries(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Reads audit entries in reverse chronological order (newest first).
        """
        if not self.log_path.exists():
            return []
            
        entries = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            if task_id is None or record.get("task_id") == task_id:
                                entries.append(record)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[AUDIT LOG READ ERROR]: {e}")
            return []
            
        # Reverse to get newest first, limit results
        return list(reversed(entries))[:limit]

# Global singleton
audit_logger = AuditLogger()
