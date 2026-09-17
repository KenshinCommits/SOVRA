# SOVRA Test Suite & Verification Documentation

## Overview
SOVRA maintains a rigorous, multi-layered verification strategy enforcing sovereign, air-gapped, zero-cloud operations. All 24 backend automated tests, 7 failure mode tests, empirical benchmarks, and 3 browser E2E industrial workflows are verified and passing.

---

## 1. Automated Test Suites

### 1.1 Summary of Automated Tests (24/24 Passing)
Run command:
```bash
PYTHONPATH=. .venv/bin/pytest backend/tests/ -v
```

| Test Module | Test Name | Purpose / Invariant Verified | Status |
|-------------|-----------|------------------------------|--------|
| `test_agent.py` | `test_tool_registration` | Registry discovers all registered built-in tools with schemas and permissions. | **PASSED** |
| `test_agent.py` | `test_path_traversal` | Path traversal attacks (`../../etc/passwd`) are blocked on file system tools. | **PASSED** |
| `test_agent.py` | `test_orchestrator_create_task` | Orchestrator initializes tasks and queries router for model selection. | **PASSED** |
| `test_approval.py` | `test_approval_sufficient_evidence` | Sufficient evidence (score >= 0.35) permits operator approval and execution. | **PASSED** |
| `test_approval.py` | `test_approval_blocked_on_insufficient_evidence_without_override` | Insufficient evidence blocks approval unless explicit override + reason provided. | **PASSED** |
| `test_approval.py` | `test_approval_succeeds_with_override_and_reason` | Valid override with human reason allows execution and logs audit trail. | **PASSED** |
| `test_approval.py` | `test_approval_30min_expiry` | Approval requests older than 30 minutes expire automatically. | **PASSED** |
| `test_approval.py` | `test_operator_rejection` | Operator rejection halts task with reason and prevents tool invocation. | **PASSED** |
| `test_approval.py` | `test_approval_security_edge_cases` | Re-approving decided requests or unauthorized state transitions rejected. | **PASSED** |
| `test_evidence_gate.py` | `test_evidence_gate_missing_evidence` | Missing evidence triggers `MISSING` verdict and requires override. | **PASSED** |
| `test_evidence_gate.py` | `test_evidence_gate_sufficient_evidence` | Retrieved evidence above threshold yields `SUFFICIENT` verdict. | **PASSED** |
| `test_evidence_gate.py` | `test_evidence_gate_insufficient_evidence` | Sub-threshold evidence yields `INSUFFICIENT` verdict. | **PASSED** |
| `test_evidence_gate.py` | `test_evidence_gate_parsed_string_evidence` | Extracts structured citations from text output when structured list is empty. | **PASSED** |
| `test_failures.py` | `test_failure_missing_evidence` | Sensitive action without RAG evidence blocked by Evidence Gate. | **PASSED** |
| `test_failures.py` | `test_failure_irrelevant_evidence` | Irrelevant retrieved evidence blocked by Evidence Gate thresholding. | **PASSED** |
| `test_failures.py` | `test_failure_unsupported_file` | Non-supported image formats (`.xyz`, `.bmp`) rejected cleanly with clear errors. | **PASSED** |
| `test_failures.py` | `test_failure_malformed_csv` | Corrupted/unparseable CSV files rejected without crashing the tabular tool. | **PASSED** |
| `test_failures.py` | `test_failure_failed_tool` | Attempting to call non-existent tools returns structured failure observation. | **PASSED** |
| `test_failures.py` | `test_failure_sandbox_execution_error` | Syntax/runtime errors in Docker sandbox isolated and returned as error output. | **PASSED** |
| `test_failures.py` | `test_failure_sandbox_timeout` | Infinite loops or runaway code in Docker sandbox timed out safely (<=10s). | **PASSED** |
| `test_sandbox.py` | `test_sandbox_network_disabled` | Sandbox enforces `network_mode="none"`; egress sockets raise `NetworkUnreachable`. | **PASSED** |
| `test_sandbox.py` | `test_sandbox_timeout` | Code exceeding execution timeout terminated by Docker container engine. | **PASSED** |
| `test_sandbox.py` | `test_sandbox_basic_math` | Deterministic Python calculation executes cleanly and returns stdout. | **PASSED** |
| `test_sandbox.py` | `test_path_traversal_blocked_artifacts` | Writing outside `/artifacts` in deliverable generators blocked. | **PASSED** |

---

## 2. Failure Mode Test Suite (`backend/tests/test_failures.py`)
To prevent fragile demonstrations and ensure enterprise resilience under unexpected conditions, 7 dedicated failure scenarios are continuously audited:
1. **Missing Evidence Failure:** Sensitive tool invocation attempted with 0 prior retrieved evidence records.
2. **Irrelevant Evidence Failure:** Evidence records present but semantic similarity scores below minimum confidence threshold (0.35).
3. **Unsupported Image Format:** Passing corrupted or unsupported image extensions to the vision tool returns descriptive errors without backend crashes.
4. **Malformed Tabular Data:** Corrupted CSV data with ragged rows returns parse failure warnings without crashing the execution loop.
5. **Unknown Tool Invocations:** Hallucinated tool names are intercepted by `ToolRegistry.execute()` and returned as failure observations to the agent.
6. **Docker Sandbox Runtime Errors:** Division by zero or exceptions inside the container return non-zero exit codes with exact tracebacks.
7. **Sandbox Execution Timeout:** Execution of `while True: pass` terminated within 10 seconds.

---

## 3. Ground-Truth Benchmarks (`backend/benchmarks/benchmark_suite.py`)
Empirical benchmark suite measuring system fidelity against known ground truth (never fabricated):
- **SOP Semantic Retrieval Hit Rate:** 100.0%
- **Out-of-Domain Retrieval Rejection:** 100.0%
- **Citation Fidelity:** 100.0%
- **Deterministic Tabular Math Error:** 0.0000%
- **P&ID Drawing Tag Extraction Recall:** 100.0%
- **Evidence Gate Sensitivity Compliance:** 100.0%

Detailed methodology and metrics are documented in [`docs/BENCHMARKS.md`](file:///Users/rithwikthummanapally/Projects/SOVRA%20SIH/docs/BENCHMARKS.md).

---

## 4. End-to-End Industrial Workflows Verified in Browser

### Workflow 1: Inspection Audit & Deliverable Generation
1. **Trigger:** `WF-1: Pump SOP & DOCX` preset button in Agent Workspace.
2. **Execution:** Agent retrieves `Pump_Inspection_SOP_Rev3.txt` from local Qdrant collection, parses vibration (<= 4.5 mm/s) and bearing temp (50-72°C) thresholds.
3. **Evidence Gate:** Identifies that measured vibration (5.4 mm/s) and temperature (84°C) exceed standard limits. Sensitive action triggers `APPROVAL_REQUIRED`.
4. **Human Approval:** Operator reviews source document citations, snippet, and confidence score (0.74). Approves execution.
5. **Deliverable:** Word document `pump_audit_report.docx` generated and verified on disk (36.7 KB) and downloadable over HTTP.

### Workflow 2: Engineering P&ID Visual Inspection
1. **Trigger:** `WF-2: P&ID Drawing Inspection` preset button.
2. **Execution:** Local vision pipeline inspects `data/pid_cooling_loop.png`, extracting pumps (`P-104A`, `P-104B`), valves (`V-101A/B`, `V-102A/B`, `CV-103A/B`), flush line (`NV-106`), and instrumentation (`PI-101`, `PI-104`, `VT-104A`, `TT-104A`).
3. **Safety Notice:** Pipeline strictly asserts that visual observation confirms physical topology only; operational limits require retrieved SOP evidence.
4. **Cross-Reference:** Agent executes `knowledge_search` against SOP, verifying operating compliance.

### Workflow 3: Deterministic CSV Telemetry Analysis & Spreadsheet Deliverable
1. **Trigger:** `WF-3: Telemetry CSV & XLSX` preset button.
2. **Execution:** `analyze_tabular_data` processes `data/vibration_telemetry.csv` (100 records) using deterministic numerical calculations:
   - Mean RMS Vibration: `4.05 mm/s`
   - Peak RMS Vibration: `6.68 mm/s`
   - Threshold Exceedances (> 4.5 mm/s): `35 / 100 (35.0%)`
3. **Evidence Gate:** Sensitive generation of spreadsheet deliverable pauses at `APPROVAL_REQUIRED`.
4. **Deliverable:** Excel deliverable `telemetry_audit.xlsx` generated and verified on disk (5.0 KB) and downloadable over HTTP.