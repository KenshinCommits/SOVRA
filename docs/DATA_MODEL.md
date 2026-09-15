# Data Model

## Document Ingestion
```json
{
  "document_id": "uuid",
  "filename": "string",
  "content_type": "string"
}
```

## Vector Chunk Payload
```json
{
  "text": "Extracted text chunk...",
  "document_id": "uuid",
  "filename": "string",
  "page": "int | null",
  "section": "string | null",
  "chunk_index": "int"
}
```

## Task Fingerprint (Router)
```json
{
  "modality": "text | multimodal",
  "complexity": "low | medium | high",
  "requires_code": "boolean",
  "requires_vision": "boolean"
}
```\n