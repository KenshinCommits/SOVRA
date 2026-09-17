# SOVRA Architecture

## System Overview
SOVRA (Sovereign Operations & Reasoning Agent) is a modular, local-first industrial AI workbench consisting of a React + TypeScript frontend and a FastAPI Python backend. The system coordinates sovereign RAG, policy-based Model Routing, safe Docker sandboxed execution, an Evidence Gate, and human-in-the-loop authorization.

## Data Flow
```text
User Request (Industrial Console UI)
  │
  ▼
FastAPI Gateway (/agent/tasks)
  │
  ▼
Agent Orchestrator
  │
  ├──► Model Router ──► Local Ollama (qwen3.5, qwen2.5-coder, etc.)
  │
  ├──► Tool Registry (Read-only tools: knowledge_search, read_file)
  │      └──► Qdrant Vector Engine (Local Docker, sentence-transformers)
  │
  └──► Sensitive Tool Detection (permission="execute")
         │
         ▼
     Evidence Gate Evaluation (gate.py)
         ├── Citation Extraction & Relevance Scoring (threshold: 0.35)
         └── Verdict: SUFFICIENT | INSUFFICIENT | MISSING
         │
         ▼
     Approval State Machine (state.py)
         ├── State: APPROVAL_REQUIRED (30-minute auto-expiry window)
         ├── Policy Lock if Evidence is INSUFFICIENT/MISSING
         └── Human Decision:
               ├── APPROVE (with mandatory override & reason if locked)
               └── REJECT (safe termination)
         │
         ▼
     Execution Layer (Docker Sandbox / python-docx / openpyxl / python-pptx)
         │
         ▼
     Append-Only Audit Logger (audit_log.jsonl)
         └── Records action, actor, override reason, and evidence verdict
```

## Core Subsystems

### 1. Evidence Gate (`backend/evidence/`)
- Intercepts any tool marked with `permission="execute"` before invocation.
- Aggregates citations from prior task steps (both structured and parsed).
- Computes min, max, and average relevance metrics against a 0.35 threshold.
- Automatically triggers a policy lock if evidence is insufficient or missing.

### 2. Human Authorization & State Engine (`backend/agents/`)
- Manages states: `PLAN`, `ACT`, `OBSERVE`, `VERIFY`, `APPROVAL_REQUIRED`, `SUCCESS`, `FAILURE`.
- Manages approval statuses: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`.
- Enforces 30-minute time-to-live (`is_expired()`).

### 3. Immutable Audit Logging (`backend/audit/`)
- Append-only JSONL log guaranteeing chronological non-repudiation.
- Explicitly logs `EVIDENCE_OVERRIDE_APPROVED` events with operator identification, tool target, and justification.
- Completely excludes internal hidden chain-of-thought `<think>` tags.

### 4. Sandboxed Execution & Deliverables (`backend/sandbox/`, `backend/tools/`)
- Network-disabled Docker container (`network_mode="none"`) for running untrusted generated Python code.
- Dedicated artifact directory generating verified DOCX, XLSX, and PPTX reports with path-traversal protections.

### 5. Multimodal Engineering Vision Subsystem (`backend/tools/vision.py`)
- Direct integration for inspecting P&ID schematics, mechanical drawings, and equipment diagrams using local vision models.
- Thumbnail optimization and strict visual observation extraction (pumps, valves, instrumentation loops, design notes).
- Enforces an explicit safety rule: visual observation confirms physical topology only; any operational compliance or maintenance conclusion strictly requires supporting evidence retrieved from verified SOP documentation.
- Demarcates all demo schematics with synthetic asset badges.

### 6. Deterministic Tabular Telemetry Engine (`backend/tools/tabular.py`)
- Python-native deterministic calculation pipeline executing exact statistical math (mean, min, max, std, variance) across telemetry datasets without LLM arithmetic hallucination.
- Automated rule auditing against operational limits (vibration alarms, bearing temperature limits, seal leakage thresholds).
- Generates verified audit records and feeds exact values directly into Excel spreadsheet deliverable generators (`generate_xlsx`).