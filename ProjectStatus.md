# Current Status

- **Project:** SOVRA
- **Current phase:** Phase 4 (Agent Core)
- **Overall status:** Phase 1, 2, and 3 Complete
- **Last updated:** 2026-09-15

## Completed
- **Phase 1:** Architecture & Setup
- **Phase 2:** Knowledge Base / Qdrant / RAG (MVP Verified)
- **Phase 3:** Model Layer + Model Router (MVP Verified)

## Current architecture
A FastAPI backend serving a React frontend. The backend handles local document ingestion, chunks text, embeds via `sentence-transformers`, stores in a local Docker Qdrant DB. A Model Router takes prompts, fingerprints the task via a lightweight LLM, and dynamically routes requests to the optimal local Ollama model.

## Working services
- **Frontend:** VERIFIED (React + Vite running on port 5173)
- **Backend:** VERIFIED (FastAPI running on port 8000)
- **Ollama:** VERIFIED (Running locally on port 11434)
- **Qdrant:** VERIFIED (Running locally via Docker on port 6333)

## Available models
- `qwen3.5:9b` (General SOVRA model)
- `qwen3:14b` (Stronger reasoning)
- `qwen2.5-coder:14b` (Coding)
- `qwen2.5-coder:latest` (Lightweight coding / router logic)
- `gemma4:12b` (Multimodal/vision candidate - VERIFIED)
- `deepseek-r1:7b` (Reasoning candidate)

## Implemented features
- API health and system status endpoints.
- Sovereign Mode UI Dashboard.
- RAG Pipeline: Document upload, parsing, chunking, local embedding, indexing.
- Knowledge Search API with preserved citation metadata.
- Model Abstraction Layer (`ModelProvider`).
- Model Registry and Policy-Based Router logic.

## Known issues
None blocking current development.

## Known limitations
- PDF page-level citation testing needs robust verification (Initial testing was TXT).
- Multimodal verification on complex industrial P&IDs not yet fully tested.
- Full agent Reason/Act loop not yet implemented.
- Sandbox not yet implemented.
- Evidence Gate not yet implemented.
- Audit system not yet complete.

## Next task
**Phase 4:** Agent Core + Tool Registry

## Do not do
- Do not add external API dependencies (OpenAI/Claude).
- Do not hardcode model names in agent logic (use the router).
- Do not fabricate test results.

## Recent changes
- Phase 3 Completion: Added ModelProvider, OllamaModelProvider, ModelRegistry, ModelRouter, and tested text, reasoning, code, and vision routing.

## Verification commands
- `docker-compose up -d` (Start Qdrant)
- `curl http://localhost:11434/api/tags` (Check Ollama)
- `source .venv/bin/activate && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000` (Backend)
- `cd frontend && npm run dev` (Frontend)

## Definition of done
Phase 4 is complete when the Agent Core can execute a multi-step ReAct loop utilizing at least one registered tool and the local Model Router, without human intervention during the loop.\n