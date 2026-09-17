# Agent Specification

## Core Loop
SOVRA operates on a strictly controlled sovereign ReAct loop:
1. **PLAN**: Analyze user request, fingerprint task, route to the optimal local Ollama model, and formulate the next operational step.
2. **ACT**: Select a registered tool from the tool registry.
3. **OBSERVE**: Read structured tool output or citation metadata.
4. **VERIFY**: Evaluate task completeness and determine if sensitive tool execution requires the Evidence Gate.

## State Machine
The agent task lifecycle progresses through:
- `PLAN` -> `ACT` -> `OBSERVE` -> `VERIFY` -> `SUCCESS` / `FAILURE`
- If a tool has `permission="execute"` (e.g. `generate_docx`, `generate_xlsx`, `generate_pptx`, `execute_sandboxed_code`):
  - The agent enters `APPROVAL_REQUIRED`.
  - An `ApprovalRequest` is instantiated with risk level, tool parameters, and an evaluated `EvidenceVerification`.
  - The loop halts until explicit operator intervention.

## Evidence Gate Verification
Before any sensitive action can be approved:
- The Evidence Gate inspects all prior citations in the task history.
- Relevance score threshold: 0.35 minimum peak score.
- Verdicts:
  - `SUFFICIENT`: Evidence exceeds threshold. Operator can authorize immediately.
  - `INSUFFICIENT`: Evidence retrieved but below confidence threshold. Policy lock requires explicit operator `override: true` and written `override_reason`.
  - `MISSING`: No citations retrieved prior to execution. Policy lock requires explicit operator `override: true` and written `override_reason`.

## Human Approval & Expiry Policies
- **Approval States**: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`.
- **30-Minute Expiry**: Pending approval requests auto-expire after 30 minutes (`is_expired()`). Expired approvals terminate task execution with `FAILURE`.
- **Operator Rejection**: Operators can reject the proposed action with an audit-logged justification, causing immediate safe termination (`FAILURE`).
- **Never Auto-Bypass**: The system strictly refuses to automatically authorize execute-level tools.

## Immutable Audit Trail
All task creation, tool execution, approval requests, granted authorizations, rejections, expiries, and especially `EVIDENCE_OVERRIDE_APPROVED` events are recorded in an append-only JSONL log (`backend/audit/audit_log.jsonl`).

## Transparency & Chain-of-Thought
- Operational traces, citations, and tools are surfaced cleanly in the UI.
- Hidden Chain-of-Thought (internal `<think>` reasoning tags) is strictly filtered out of user-facing traces and audit logs.