# SOVRA (Sovereign Operations & Reasoning Agent)

## Overview
SOVRA is a 100% on-premise, air-gapped agentic AI workbench designed for confidential industrial workflows (SIH26117). It understands confidential files, plans multi-step work, uses local tools, and produces auditable deliverables without sending data to the cloud.

## Current Status
- Phase 1 (Setup) is **COMPLETE**.
- Phase 2 (Knowledge Base / RAG) is **COMPLETE**.
- Phase 3 (Model Layer & Router) is **COMPLETE**.
- Phase 4 (Agent Core) is **NEXT**.

## Tech Stack
- **Backend:** Python, FastAPI, sentence-transformers
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Local AI:** Ollama
- **Vector DB:** Qdrant (via Docker)

## Local Setup

### 1. Start Qdrant
```bash
docker-compose up -d
```

### 2. Start Backend
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 3. Start Frontend
```bash
cd frontend
npm run dev
```

### 4. Verify Ollama
Ensure Ollama is running and models are downloaded (`qwen3.5:9b`, `qwen2.5-coder:latest`, etc.).
```bash
curl http://localhost:11434/api/tags
```

## Security Principles
SOVRA enforces strict local-first, evidence-based operation. All AI inference and vector embeddings occur locally. See `docs/SECURITY.md` for details.

## Documentation
Please see the `docs/` directory for full PRD, Architecture, and Roadmap documentation.\n