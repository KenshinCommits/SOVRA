# Changelog

All notable changes to the SOVRA project will be documented in this file.

## [Unreleased]

## [0.4.0] - 2026-09-15

### Added
- **Agent Orchestrator:** Implemented a full ReAct loop orchestrator (`PLAN -> ACT -> OBSERVE -> VERIFY`).
- **Task State Tracking:** Introduced detailed history tracking via `AgentTask` and `AgentStep` models.
- **Tool Registry:** Created a modular tool registry with initial built-ins (`knowledge_search`, `list_project_files`, `read_file`).
- **Security:** Path traversal prevention applied to file system tools.
- **API:** New `POST /agent/tasks` and `GET /agent/tasks/{task_id}` polling endpoints for asynchronous agent operation.
- **Frontend:** Built `AgentWorkspacePanel.tsx` and refactored UI into a tabbed layout to seamlessly view real-time agent execution traces.

## [0.3.0] - 2026-09-15

### Added
- **Phase 3 (Model Layer & Router)**: 
  - Abstract `ModelProvider` and `OllamaModelProvider`.
  - Model Registry defining `qwen3.5:9b`, `qwen3:14b`, `qwen2.5-coder:14b`, `qwen2.5-coder:latest`, `deepseek-r1:7b`, and `gemma4:12b`.
  - Policy-based Model Router using task fingerprinting.
  - Verification of `gemma4:12b` multimodal capabilities.
  - `/models`, `/models/route`, `/models/generate` APIs.
  - `ModelsTestPanel.tsx` in frontend.

- **Phase 2 (Knowledge Base & RAG Pipeline)**:
  - Local Qdrant integration.
  - Local embeddings via `sentence-transformers` (`all-MiniLM-L6-v2`).
  - Document parsing (PDF, TXT, DOCX, CSV, XLSX).
  - Chunking with source metadata (filename, page, chunk id).
  - Backend API (`/documents/upload`, `/knowledge/search`).
  - Frontend UI (`KnowledgeBasePanel`, `SearchTestPanel`).

- **Phase 1 (Architecture & Setup)**:
  - FastAPI backend and React+Vite+TypeScript frontend.
  - Basic project structure and CORS.
  - Ollama connectivity detection and `/system/status` API.
  - Sovereign Mode dashboard.

### Known Limitations
- Initial RAG verification used a TXT SOP document. Full PDF page-level citation validation is planned.
- Agent Core, Tool Registry, Code Sandbox, and Evidence Gate are not yet implemented.\n