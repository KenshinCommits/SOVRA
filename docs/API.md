# API Documentation

## SYSTEM & MODELS

### `GET /health`
- **Purpose**: Service health check.
- **Response**: `{"status": "ok"}`

### `GET /system/status`
- **Purpose**: Verify Ollama connection, Qdrant status, and list active models.
- **Response**: `{"ollama_connected": true, "models_available": [...]}`

### `GET /models`
- **Purpose**: List registered model capabilities, aliases, and tiers.

### `POST /models/route`
- **Purpose**: Test task fingerprinting and model routing policy.
- **Request**: `{"prompt": "string"}`
- **Response**: `{"selected_model": "...", "reasoning": "..."}`

### `POST /models/generate`
- **Purpose**: Route and generate text using the optimal local model.

---

## KNOWLEDGE & RAG

### `POST /documents/upload`
- **Purpose**: Ingest, parse, chunk, and index a document into local Qdrant vector storage.
- **Request**: `multipart/form-data` with `file`.
- **Response**: `{"status": "success", "document_id": "...", "filename": "...", "chunks_indexed": N}`

### `POST /knowledge/search`
- **Purpose**: Query the local knowledge base and retrieve ranked citation chunks.
- **Request**: `{"query": "string", "top_k": 3}`
- **Response**: `{"results": [{"score": 0.85, "filename": "...", "page": 1, "text": "..."}]}`

---

## AGENT CORE & WORKSPACE

### `POST /agent/tasks`
- **Purpose**: Create and initiate an autonomous ReAct loop task.
- **Request**: `{"prompt": "string"}`
- **Response**: `TaskStatusResponse` with full task state, step history, and selected model.

### `GET /agent/tasks/{task_id}`
- **Purpose**: Poll the current status, step timeline, deliverables, and approval state of an agent task.
- **Response**: `TaskStatusResponse`

### `GET /agent/tools`
- **Purpose**: Enumerate all registered tools in the agent tool registry, along with risk levels and permissions.
- **Response**: List of tool schemas.

---

## EVIDENCE GATE & HUMAN APPROVAL (Phase 6)

### `POST /agent/tasks/{task_id}/approve`
- **Purpose**: Grant human authorization to resume execution of a sensitive action halted at `APPROVAL_REQUIRED`.
- **Request Body (JSON)**:
  ```json
  {
    "actor": "lead_operator",
    "override": false,
    "override_reason": "Optional justification when override is false; mandatory when override is true"
  }
  ```
- **Validation Rules**:
  - Task must be in `APPROVAL_REQUIRED`.
  - Approval request must not be expired (`expires_at > now` within 30m).
  - If Evidence Gate verdict is `INSUFFICIENT` or `MISSING`: `override` must be `true` and `override_reason` must be non-empty; otherwise returns HTTP 400.
- **Response**: `TaskStatusResponse` with `approval_request.status = "APPROVED"`.

### `POST /agent/tasks/{task_id}/reject`
- **Purpose**: Reject a pending sensitive action, terminating task execution safely.
- **Request Body (JSON)**:
  ```json
  {
    "actor": "lead_operator",
    "reason": "Operator rejected action due to unverified parameters"
  }
  ```
- **Response**: `TaskStatusResponse` with `task.status = "FAILURE"` and `approval_request.status = "REJECTED"`.

### `GET /agent/tasks/{task_id}/evidence`
- **Purpose**: Retrieve verified citations and Evidence Gate evaluation for a given task.
- **Response**:
  ```json
  {
    "task_id": "...",
    "evidence_records": [...],
    "verification": {
      "verdict": "SUFFICIENT",
      "max_score": 0.82,
      "requires_override": false,
      "details": "..."
    }
  }
  ```

### `GET /agent/audit`
- **Purpose**: Query the immutable append-only audit trail.
- **Query Parameters**:
  - `task_id` (optional): Filter entries by task ID.
  - `limit` (default: 50, max: 500): Number of entries to retrieve.
- **Response**: `{"entries": [...], "count": N}`