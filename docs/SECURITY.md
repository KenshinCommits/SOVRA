# Security Architecture

## Principles
SOVRA is designed for sovereign, confidential, and high-consequence industrial operations. It operates completely on-premise and air-gapped without external cloud AI dependencies.

## Implemented Security Controls
- **Local AI Inference**: All LLM processing occurs strictly on local hardware via Ollama. No data ever leaves the local environment.
- **Local Vector & Embedding Security**: Embeddings are computed with local `sentence-transformers` models; indexed in a local Qdrant container without external phone-home telemetry.
- **Docker Execution Sandbox**: Dynamic code execution executes in ephemeral Docker containers with `--network none`, CPU/memory limits, dedicated workspace isolation, and execution timeouts (Phase 5).
- **Filesystem Traversal Defenses**: All filesystem and artifact path operations validate safe containment within project directories, blocking path traversal (`../`) and unauthorized host access.
- **Evidence Gate Verification**: Sensitive actions require verified citations with quantitative relevance scores meeting or exceeding the 0.35 threshold.
- **Policy Lock on Weak Evidence**: If evidence is `INSUFFICIENT` or `MISSING`, automated approval is blocked. Execution can only proceed if an authorized operator explicitly passes `override=true` along with a mandatory audit justification reason.
- **Human Authorization Gate**: Tools with `permission="execute"` cannot auto-execute; they enter `APPROVAL_REQUIRED` and require manual operator sign-off.
- **30-Minute Approval Window**: Pending authorization requests strictly expire after 30 minutes to prevent stale, unmonitored execution.
- **Append-Only Audit Logging**: All lifecycle events, tool invocations, approval decisions, operator rejections, expiries, and `EVIDENCE_OVERRIDE_APPROVED` events are recorded in an append-only JSONL log with zero hidden CoT leakage.

## Threat Model & Mitigations
- **Threat**: Prompt injection manipulating tool calls or exfiltrating data.
  - *Mitigation*: Agent tools do not have unrestricted host shell access. Tool arguments are strictly typed and validated against Pydantic schemas. Code runs in isolated Docker containers with zero network access.
- **Threat**: Hallucinated citations or unverified automated interventions.
  - *Mitigation*: Evidence Gate evaluates real source citations before execution. Citation fabrication is blocked; unverified citations trigger an automatic policy lock requiring manual operator justification.
- **Threat**: Accidental or unauthorized tool execution.
  - *Mitigation*: Human approval gate with operator identification, risk level indicators, and 30-minute auto-expiry.