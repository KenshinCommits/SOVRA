# API Documentation

## IMPLEMENTED

### `GET /health`
- **Purpose**: Server health check.
- **Response**: `{"status": "ok"}`

### `GET /system/status`
- **Purpose**: Verify Ollama connection and list models.
- **Response**: `{"ollama_connected": true, "models_available": [...]}`

### `POST /documents/upload`
- **Purpose**: Ingest a file into the knowledge base.
- **Request**: `multipart/form-data` with `file`.
- **Response**: `{"status": "success", "chunks_indexed": N}`

### `POST /knowledge/search`
- **Purpose**: Retrieve vector search results.
- **Request**: `{"query": "string", "top_k": 3}`
- **Response**: List of chunks with metadata.

### `GET /models`
- **Purpose**: List registered model capabilities.

### `POST /models/route`
- **Purpose**: Test model routing logic.

### `POST /models/generate`
- **Purpose**: Route and generate text.

## PLANNED

### `POST /agent/task`
- **Purpose**: Start an agentic workflow.\n