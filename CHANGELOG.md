# Changelog

All notable changes to the SOVRA project will be documented in this file.

## [0.8.0] - 2026-09-17

### Added (Phase 8 - Production Hardening + Demo Polish)
- **Live System Status Monitoring (`backend/app/main.py`):**
  - Replaced hardcoded `qdrant_connected = False` with live async HTTP health probe against `http://localhost:6333/readyz`.
  - `SystemStatus` response extended with `sovereign_offline`, `active_tasks_count`, `pending_approvals_count`, `system_errors`.
  - Global exception handler prevents raw traceback or internal path leakage to clients.
- **API Security Hardening:**
  - `POST /upload`: 25 MB upload size limit (streaming, memory-safe), `.pdf/.txt/.docx/.md` extension allowlist, typed `UploadResponse`.
  - `GET /documents`: Live Qdrant document index listing with chunk counts via `client.scroll()`.
  - `DELETE /documents/{id}`: Safe per-document deletion by Qdrant document ID.
  - `POST /agent/tasks`: Rejects empty/whitespace prompts (400).
  - `GET /agent/tasks/{id}`: Returns 404 for unknown task IDs.
  - `POST /agent/tasks/{id}/approve`: Enforces non-empty `override_reason` when `override=True`; blocks expired approval windows.
  - `POST /models/generate`: Validates model name against registry; rejects unrecognized or cloud models (400).
- **JSON Parser Robustness (`backend/agents/orchestrator.py`):**
  - `json.loads(strict=False)` handles LLM responses with unescaped newlines in strings.
  - `ast.literal_eval` fallback handles single-quoted Python dict output.
  - Regex `re.search` fallback extracts embedded JSON from mixed-format LLM responses.
- **Frontend Hardening (`frontend/src/`):**
  - Live SYNCED/OFFLINE Qdrant status badge in header.
  - Active Human Gate badge with pending approval count.
  - Diagnostic error banner for `system_errors`.
  - Security perimeter audit box (External APIs: BLOCKED, Network Egress: DISABLED, Evidence Gate: ACTIVE, Approval Expiry: 30 MINUTES).
  - Knowledge Base panel: live indexed document listing with per-document chunk counts and delete buttons.
- **Knowledge Base Cleanup:**
  - Removed 5 non-industrial documents (resumes, prospectuses) from Qdrant via `DELETE /documents/{id}`.
  - Index now contains only industrial SOP documents relevant to SOVRA workflows.
- **Security Hardening Test Suite (`backend/tests/test_security_hardening.py`):**
  - 8 new automated tests: oversized upload blocked, unsupported format blocked, invalid task ID 404, empty prompt 400, unrecognized model 400, deep path traversal blocked, live Qdrant health, missing override reason blocked.

### Changed
- Pytest suite expanded from 24 to 32 tests (100% pass rate).
- JSON parsing pipeline made robust to strict=False and single-quoted output.

## [0.7.0] - 2026-09-17


### Added (Phase 7 - Industrial Workflows & Demo-Ready System)
- **Workflow 1 (Inspection Audit & DOCX Deliverable):**
  - Ingests inspection findings and retrieves `Pump_Inspection_SOP_Rev3.txt` from local Qdrant collection.
  - Compares RMS vibration (5.4 mm/s vs 4.5 mm/s limit) and bearing temperature (84°C vs 75°C max limit).
  - Evaluates Evidence Gate, triggers `APPROVAL_REQUIRED`, and generates downloadable `pump_audit_report.docx` (36.7 KB).
- **Workflow 2 (Engineering P&ID Drawing Inspection & Local Vision):**
  - High-resolution schematic `data/pid_cooling_loop.png` analyzed with `analyze_engineering_drawing`.
  - Extracts pumps (`P-104A`, `P-104B`), valves (`V-101`, `V-102`, `CV-103`), flush line (`NV-106`), and instrumentation loops (`PI-101`, `PI-104`, `VT-104A`, `TT-104A`).
  - Strict safety assertion: visual observation confirms physical topology only; operational conclusions strictly require retrieved SOP evidence.
- **Workflow 3 (Deterministic CSV Telemetry & XLSX Deliverable):**
  - Python-native deterministic calculation tool `analyze_tabular_data` for `data/vibration_telemetry.csv` (100 records).
  - Calculates exact statistical metrics (Mean RMS: 4.05 mm/s, Peak: 6.68 mm/s, 35 threshold violations) with 0.0000% math error.
  - Generates verifiable Excel spreadsheet `telemetry_audit.xlsx` (5.0 KB).
- **Dedicated Failure Mode Test Suite (`backend/tests/test_failures.py`):**
  - 7 automated tests verifying system resilience against missing evidence, sub-threshold evidence, unsupported file formats, malformed CSV datasets, non-existent tools, sandbox runtime exceptions, and sandbox execution timeouts.
- **Empirical Ground-Truth Benchmark Suite (`backend/benchmarks/benchmark_suite.py`):**
  - Automated benchmark framework measuring SOP hit rate (100%), citation fidelity (100%), tabular math error (0.0000%), P&ID tag recall (100%), and Evidence Gate compliance (100%).
  - Full report documented in `docs/BENCHMARKS.md`.
- **Demo Workspace UI Enhancements (`frontend/src/components/AgentWorkspacePanel.tsx`):**
  - Quick-action preset workflow buttons (`WF-1`, `WF-2`, `WF-3`) with synthetic asset badges.
  - Interactive Evidence Gate panel, policy override controls, and audit trail drawer.
- **Full Test Verification:**
  - 24/24 backend automated tests passing (100% pass rate).
  - Browser E2E sessions verified on `http://localhost:5173`.

## [0.6.0] - 2026-09-16

### Added (Phase 6 - Evidence Gate & Human Approval)
- **Evidence Gate Subsystem (`backend/evidence/gate.py`):**
  - Citation extraction and relevance scoring against a 0.35 confidence threshold.
  - Verifies evidence sufficiency prior to executing sensitive tools.
  - Verdict states: `SUFFICIENT`, `INSUFFICIENT`, `MISSING`.
- **Human Authorization State Machine (`backend/agents/state.py`):**
  - Approval statuses: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`.
  - 30-minute approval expiry TTL (`is_expired()`).
  - Mandatory policy lock requiring explicit `override: true` and written justification reason when evidence is insufficient or missing.
- **Append-Only Immutable Audit Logger (`backend/audit/logger.py`):**
  - Persistent JSONL logging of all task lifecycle events.
  - Dedicated audit action: `EVIDENCE_OVERRIDE_APPROVED` tracking actor, tool, justification reason, and evidence verification details.
  - Zero leakage of internal hidden Chain-of-Thought.
- **API Endpoints (`backend/api/router_agent.py`):**
  - `POST /agent/tasks/{id}/approve`: authorizer sign-off with override parameters.
  - `POST /agent/tasks/{id}/reject`: operator termination with rejection reason.
  - `GET /agent/tasks/{id}/evidence`: verified citation inspection.
  - `GET /agent/audit`: queryable immutable audit logs with filtering.
- **Industrial Console UI Components (`frontend/src/components/AgentWorkspacePanel.tsx`):**
  - Verified Citation inspection block with document source, page number, and score progress bars.
  - Human Authorization Gate panel showing target tool, parameters, risk level, and 30m countdown.
  - Insufficient Evidence policy lock banner with override checkbox and justification input.
  - Real-time Audit Trail drawer with timestamped action badges.
- **RAG Retrieval Overhaul & False Positive Elimination (`backend/rag/`, `backend/ingestion/`):**
  - Enabled unit-length embedding normalization (`normalize_embeddings=True`) in `LocalEmbeddingProvider`.
  - Added configurable `score_threshold` (default 0.30) to `QdrantService.search`, `Retriever.retrieve_context`, and `POST /knowledge/search`.
  - Upgraded `TextChunker` with boundary-aware sentence/word detection, eliminating truncated and severed words at chunk seams.
  - Implemented `DELETE /documents/{document_id}` for vector index lifecycle management.
  - Fully eliminated irrelevant cross-document false positives (such as resume chunks surfacing in industrial pump queries).
- **Full Test Suite:**
  - 10 new unit and security tests in `test_evidence_gate.py` and `test_approval.py`.
  - 17/17 total backend tests passing.
  - Verified browser E2E flow with realistic pump inspection SOP and report generation.

## [0.5.0] - 2026-09-15

### Added (Phase 5 - Safe Code Execution & Real Artifact Outputs)
- Implemented safe sandboxed Python execution using Docker SDK with `--network none`.
- Implemented agent tools to generate DOCX, XLSX, and PPTX artifacts.
- Added `APPROVAL_REQUIRED` state for high-risk actions.
- Static file serving for generated artifacts.

## [0.4.0] - 2026-09-15

### Added (Phase 4 - Agent Core & Tool Registry)
- Implemented ReAct loop orchestrator (`PLAN -> ACT -> OBSERVE -> VERIFY`).
- Task state tracking via `AgentTask` and `AgentStep` models.
- Modular tool registry with `knowledge_search`, `list_project_files`, `read_file`.
- Path traversal prevention applied to file system tools.
- Asynchronous task endpoints `POST /agent/tasks` and `GET /agent/tasks/{task_id}`.

## [0.3.0] - 2026-09-15

### Added (Phase 3 - Model Layer & Router)
- ModelProvider abstraction with OllamaModelProvider.
- Policy-based Model Router using task fingerprinting.
- Model capability metadata and verification of local Ollama models.

## [0.2.0] - 2026-09-15

### Added (Phase 2 - Knowledge Base & RAG Pipeline)
- Local Qdrant integration.
- Local embeddings via `sentence-transformers`.
- Document parsing and chunking with source metadata.

## [0.1.0] - 2026-09-15

### Added (Phase 1 - Architecture & Setup)
- FastAPI backend and React+Vite+TypeScript frontend.
- Sovereign Mode dashboard and Ollama connectivity detection.