# SOVRA Architecture

## System Overview
SOVRA is a modular, local-first workbench consisting of a React frontend and a FastAPI Python backend. The backend coordinates RAG, Model Routing, and Agent execution.

## Data Flow
```text
User (Frontend) 
  → API (FastAPI) 
    → Agent Orchestrator 
      → Model Router 
        → Local Model (Ollama)
      → Tools / RAG (Qdrant)
    → Evidence Gate (Approval)
  → Verified Output (DOCX/XLSX)
→ Audit Log
```

## Components

### Frontend (React + Vite)
- Sovereign Mode Dashboard displaying system health.
- Knowledge Base upload UI.
- Agent Workspace and Evidence Gate UI.

### Backend (FastAPI)
- **Model Layer**: `ModelProvider` abstractions.
- **Model Router**: LLM-based task fingerprinting to route to the best local model.
- **Agent Layer**: Orchestrates ReAct loops.
- **RAG & Ingestion**: Document parsers, chunking, and local embeddings (`sentence-transformers`).
- **Qdrant**: Local vector database running in Docker.
- **Sandbox**: Docker-based execution environment for generated code.
- **Evidence Gate**: Pauses agent execution for human review.
- **Output Generation**: Compiles agent findings into DOCX/XLSX.
- **Audit System**: Records all traces.

### Boundaries
- The Agent Layer never talks directly to Ollama; it requests inference from the Model Router.
- The RAG system operates independently of the LLM generation layer.\n