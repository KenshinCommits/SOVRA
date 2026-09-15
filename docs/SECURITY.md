# Security Architecture

## Principles
SOVRA is designed for highly confidential industrial environments. It operates completely on-premise and air-gapped.

## Implemented Controls
- **Local Models**: All LLM inference occurs on local hardware via Ollama.
- **Local Embeddings**: Vectorization uses local `sentence-transformers`.
- **Local Vector DB**: Qdrant runs locally.

## Planned Controls
- **Network Isolation / Sandboxing**: Future generated code will execute in a Docker container without network access to the host.
- **Evidence Gate**: Human-in-the-loop validation for critical deliverables.
- **Audit Logging**: Immutable logging of all actions and prompts.

## Threat Model & Mitigations
- **Threat**: Prompt Injection leading to host compromise.
- **Mitigation**: Agent tools do not have unrestricted host shell access. Execution is sandboxed.
- **Threat**: Data exfiltration.
- **Mitigation**: Air-gapped deployment; no cloud APIs.

*Note: SOVRA does not claim to be "100% secure". Risks such as container escape vulnerabilities in the planned sandbox remain and must be managed at the infrastructure level.*\n