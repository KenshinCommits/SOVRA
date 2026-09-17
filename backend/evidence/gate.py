import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EvidenceVerdict(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    MISSING = "MISSING"

class EvidenceRecord(BaseModel):
    source_doc: str
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    snippet: str
    score: float
    section: Optional[str] = None

class EvidenceVerification(BaseModel):
    verdict: EvidenceVerdict
    records: List[EvidenceRecord] = Field(default_factory=list)
    min_score: float = 0.0
    max_score: float = 0.0
    avg_score: float = 0.0
    details: str
    requires_override: bool = False
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

class EvidenceGate:
    def __init__(self, min_score_threshold: float = 0.35):
        self.min_score_threshold = min_score_threshold

    def extract_evidence(self, task_steps: list) -> List[EvidenceRecord]:
        """
        Extracts evidence records from task execution steps.
        Checks both structured step.evidence and parses formatted search outputs.
        """
        records: List[EvidenceRecord] = []
        seen_keys = set()

        for step in task_steps:
            # 1. Structured step.evidence list
            if getattr(step, "evidence", None) and isinstance(step.evidence, list):
                for item in step.evidence:
                    doc = item.get("filename") or item.get("source_doc") or "Unknown"
                    score = float(item.get("score", 0.0))
                    text = item.get("text") or item.get("snippet") or ""
                    page = item.get("page")
                    chunk = item.get("chunk_index")
                    section = item.get("section")
                    
                    key = (doc, page, text[:50])
                    if key not in seen_keys:
                        seen_keys.add(key)
                        records.append(EvidenceRecord(
                            source_doc=doc,
                            page=int(page) if page is not None and str(page).isdigit() else None,
                            chunk_index=int(chunk) if chunk is not None and str(chunk).isdigit() else None,
                            snippet=text.strip(),
                            score=round(score, 4),
                            section=section
                        ))

            # 2. Parse tool_result if it was a knowledge_search or formatted text
            result_text = getattr(step, "tool_result", None)
            if result_text and "[Source:" in result_text:
                pattern = r"\[Source:\s*(.*?),\s*Page:\s*(.*?),\s*Score:\s*([0-9.]+)\]\s*\n(.*?)(?=\n---\n|\Z)"
                matches = re.findall(pattern, result_text, re.DOTALL)
                for doc, page_str, score_str, text in matches:
                    score = float(score_str)
                    clean_doc = doc.strip()
                    page_val = int(page_str.strip()) if page_str.strip().isdigit() else None
                    snippet = text.strip()
                    key = (clean_doc, page_val, snippet[:50])
                    if key not in seen_keys:
                        seen_keys.add(key)
                        records.append(EvidenceRecord(
                            source_doc=clean_doc,
                            page=page_val,
                            snippet=snippet,
                            score=round(score, 4)
                        ))

        return records

    def evaluate(self, task_steps: list, tool_name: str, tool_args: Dict[str, Any]) -> EvidenceVerification:
        """
        Evaluates evidence sufficiency prior to a sensitive action execution.
        """
        records = self.extract_evidence(task_steps)
        now = datetime.utcnow()

        if not records:
            return EvidenceVerification(
                verdict=EvidenceVerdict.MISSING,
                records=[],
                min_score=0.0,
                max_score=0.0,
                avg_score=0.0,
                details=f"No verified citations or retrieved evidence found prior to executing '{tool_name}'.",
                requires_override=True,
                evaluated_at=now
            )

        scores = [r.score for r in records]
        min_s = min(scores)
        max_s = max(scores)
        avg_s = sum(scores) / len(scores)

        if max_s < self.min_score_threshold:
            return EvidenceVerification(
                verdict=EvidenceVerdict.INSUFFICIENT,
                records=records,
                min_score=round(min_s, 4),
                max_score=round(max_s, 4),
                avg_score=round(avg_s, 4),
                details=(
                    f"Evidence found ({len(records)} citation(s)), but peak relevance score "
                    f"({max_s:.2f}) is below confidence threshold ({self.min_score_threshold:.2f})."
                ),
                requires_override=True,
                evaluated_at=now
            )

        return EvidenceVerification(
            verdict=EvidenceVerdict.SUFFICIENT,
            records=records,
            min_score=round(min_s, 4),
            max_score=round(max_s, 4),
            avg_score=round(avg_s, 4),
            details=(
                f"Evidence verified: {len(records)} source citation(s) with peak relevance {max_s:.2f} "
                f"(threshold: {self.min_score_threshold:.2f})."
            ),
            requires_override=False,
            evaluated_at=now
        )

# Default singleton instance
evidence_gate = EvidenceGate()
