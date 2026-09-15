# Requirements

## Functional Requirements
- **FR-001 (Ingestion)**: System must parse PDF, TXT, DOCX, CSV, XLSX. [Status: IMPLEMENTED / UNVERIFIED for complex PDFs]
- **FR-002 (RAG)**: System must retrieve relevant document chunks based on queries. [Status: IMPLEMENTED / VERIFIED]
- **FR-003 (Citations)**: Retrieved chunks must retain filename and page metadata. [Status: IMPLEMENTED / VERIFIED]
- **FR-004 (Routing)**: System must dynamically route tasks to specialized models. [Status: IMPLEMENTED / VERIFIED]
- **FR-005 (Agent Loop)**: System must execute a multi-step plan using tools. [Status: PLANNED]
- **FR-006 (Sandbox)**: System must execute Python code in an isolated environment. [Status: PLANNED]
- **FR-007 (Evidence Gate)**: System must block critical actions pending human approval. [Status: PLANNED]

## Non-Functional Requirements
- **NFR-001 (Local-First)**: No cloud AI API calls are permitted. [Status: IMPLEMENTED / VERIFIED]
- **NFR-002 (Agnosticism)**: Core logic must not hardcode model names. [Status: IMPLEMENTED / VERIFIED]

## Security Requirements
- **SEC-001 (Air-Gapped)**: Architecture must function without internet access after initial setup. [Status: IMPLEMENTED / VERIFIED]
- **SEC-002 (Sandboxing)**: Agent-generated code must run in a restricted Docker container. [Status: PLANNED]\n