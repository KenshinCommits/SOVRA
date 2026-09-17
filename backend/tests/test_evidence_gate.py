import pytest
from datetime import datetime
from backend.evidence.gate import EvidenceGate, EvidenceVerdict, EvidenceRecord
from backend.agents.state import AgentStep, AgentState

def test_evidence_gate_missing_evidence():
    gate = EvidenceGate(min_score_threshold=0.35)
    # Empty step history
    steps = [
        AgentStep(state=AgentState.PLAN, thought="Planning task"),
        AgentStep(state=AgentState.ACT, thought="Listing files", tool_call={"name": "list_project_files", "args": {}})
    ]
    verification = gate.evaluate(steps, "execute_sandboxed_code", {"code": "print('hello')"})
    assert verification.verdict == EvidenceVerdict.MISSING
    assert verification.requires_override is True
    assert len(verification.records) == 0

def test_evidence_gate_sufficient_evidence():
    gate = EvidenceGate(min_score_threshold=0.35)
    # History with structured evidence exceeding threshold
    steps = [
        AgentStep(
            state=AgentState.OBSERVE,
            thought="Found SOP documentation",
            tool_call={"name": "knowledge_search", "args": {"query": "pump inspection"}},
            evidence=[
                {
                    "filename": "Pump_Inspection_SOP.pdf",
                    "page": 3,
                    "chunk_index": 1,
                    "score": 0.82,
                    "text": "Check bearing vibration and seal temperature every 500 hours."
                }
            ]
        )
    ]
    verification = gate.evaluate(steps, "generate_docx", {"filename": "report.docx", "content": "test"})
    assert verification.verdict == EvidenceVerdict.SUFFICIENT
    assert verification.requires_override is False
    assert verification.max_score == 0.82
    assert len(verification.records) == 1
    assert verification.records[0].source_doc == "Pump_Inspection_SOP.pdf"
    assert verification.records[0].page == 3

def test_evidence_gate_insufficient_evidence():
    gate = EvidenceGate(min_score_threshold=0.35)
    # Evidence exists but relevance is low
    steps = [
        AgentStep(
            state=AgentState.OBSERVE,
            thought="Found unrelated document",
            tool_call={"name": "knowledge_search", "args": {"query": "pump inspection"}},
            evidence=[
                {
                    "filename": "General_Safety.pdf",
                    "page": 1,
                    "chunk_index": 0,
                    "score": 0.22,
                    "text": "General workplace safety notices."
                }
            ]
        )
    ]
    verification = gate.evaluate(steps, "execute_sandboxed_code", {"code": "import os"})
    assert verification.verdict == EvidenceVerdict.INSUFFICIENT
    assert verification.requires_override is True
    assert verification.max_score == 0.22
    assert "below confidence threshold" in verification.details

def test_evidence_gate_parsed_string_evidence():
    gate = EvidenceGate(min_score_threshold=0.35)
    # Formatted string tool_result
    steps = [
        AgentStep(
            state=AgentState.OBSERVE,
            thought="Retrieved raw output",
            tool_call={"name": "knowledge_search", "args": {"query": "cooling system"}},
            tool_result="[Source: Cooling_Manual.docx, Page: 5, Score: 0.74]\nCooling flow rate must be maintained at 120 L/min."
        )
    ]
    verification = gate.evaluate(steps, "generate_docx", {"filename": "cooling.docx", "content": "cool"})
    assert verification.verdict == EvidenceVerdict.SUFFICIENT
    assert len(verification.records) == 1
    assert verification.records[0].source_doc == "Cooling_Manual.docx"
    assert verification.records[0].page == 5
    assert verification.records[0].score == 0.74
