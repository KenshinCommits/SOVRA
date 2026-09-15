# Testing Strategy

## RAG Tests
- Verify parsing extracts text accurately.
- Verify chunks retain filename and page numbers.
- Verify vector retrieval returns the highest semantic match.

## Model Tests
- Ensure `OllamaModelProvider` successfully streams/generates text.
- Ensure the Model Router correctly matches `TaskFingerprint` to the registered model capabilities.

## Acceptance Test (Phase 8)
Upload an Industrial SOP PDF. Ask the agent to generate an inspection report.
- Must cite correct pages.
- Must not hallucinate tools.
- Must wait at the Evidence Gate.
- Must output a valid DOCX file.\n