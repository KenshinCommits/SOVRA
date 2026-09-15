# RAG Specification

## Pipeline
`UPLOAD → PARSE → EXTRACT → CHUNK → EMBED → QDRANT → RETRIEVE → CITE`

## Supported Formats
- PDF (via `pypdf` / future `docling`)
- DOCX (`python-docx`)
- TXT
- CSV / XLSX (`pandas`)

## Indexing
- Uses local `all-MiniLM-L6-v2` embeddings.
- Stored in a local Qdrant Docker instance.

## Citations
- **CRITICAL**: Citations MUST be based on actual source metadata attached to the Qdrant chunk payload.
- The LLM must be prompted to return citations exactly as provided in the context.
- Never fabricate citations.

## Status
IMPLEMENTED / VERIFIED (using TXT documents). PDF page-level parsing requires further verification.\n