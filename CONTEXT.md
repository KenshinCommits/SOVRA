# SOVRA CONTEXT

## Identity
SOVRA (Sovereign Operations & Reasoning Agent) is a 100% on-premise, air-gapped agentic AI workbench.

## Problem
SIH26117: Confidential industrial environments (SOPs, P&IDs, internal code) cannot use cloud APIs due to data privacy. They need a secure, local-first agent that provides real deliverables and auditable actions.

## Core architecture
User → API → Agent Orchestrator (Phase 4) → Model Router (Phase 3) → Local Ollama Models ↔ Local RAG (Phase 2) / Tools ↔ Evidence Gate → Verified Output.

## Current implementation
- FastAPI Backend & React Frontend working.
- Ollama connection verified.
- Local Knowledge Base (Qdrant + sentence-transformers) working (Upload, Embed, Chunk, Retrieve, Cite).
- Model Layer & Router working (Abstracts Ollama, fingerprints tasks, routes to specific models).

## Current models
Ollama is running locally with: `qwen3.5:9b`, `qwen3:14b`, `qwen2.5-coder:latest`, `qwen2.5-coder:14b`, `gemma4:12b` (vision verified), `deepseek-r1:7b`.

## Current roadmap
Phase 1, 2, and 3 are COMPLETE.
Next is **Phase 4: Agent Core + Tool Registry**.

## Critical constraints
- 100% Offline / Local-first.
- Model-agnostic architecture.
- Real deliverables (not just chat).
- Human control & Evidence-based outputs.

## Important terminology
- **SOP**: Standard Operating Procedure
- **P&ID**: Piping and Instrumentation Diagram
- **RAG**: Retrieval-Augmented Generation
- **Evidence Gate**: Human-in-the-loop validation layer.
- **Model Router**: Dynamic logic to pick the best model for a sub-task.

## Current development task
Phase 4: Agent Core + Tool Registry (Implement Reason/Act loop and basic tools).

## Rules for AI
- DO NOT use cloud APIs.
- DO NOT hallucinate functionality or citations.
- READ ProjectStatus.md and AGENTS.md before modifying code.
- NEVER provide unrestricted host shell access to the agent.\n