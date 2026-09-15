# Product Requirements Document (PRD)

## Problem (SIH26117)
Industrial environments deal with highly confidential data (SOPs, P&IDs, blueprints, internal code). They cannot utilize cloud-based LLMs due to data sovereignty and security risks. 

## Target Users
- Plant Engineers
- Quality Assurance Inspectors
- Internal Developers
- Compliance Officers

## Industrial Context
Users need to generate inspection reports from manuals, analyze P&IDs, process CSV/engineering data, and write internal automation scripts.

## Current Pain Points
- Manual data entry from SOPs to reports.
- Disconnected tools for analysis.
- Lack of secure AI assistants that can actually execute tasks.

## SOVRA Solution
A Sovereign On-Premise Agentic AI Workbench using open-weight models. It ingests confidential files, plans multi-step workflows, and produces verifiable deliverables in an air-gapped environment.

## Goals
- Provide 100% local AI assistance.
- Ensure strict data privacy.
- Automate report generation and data analysis.
- Create an auditable trail of AI actions.

## Non-Goals
- Cloud API integrations (OpenAI/Anthropic).
- Replacing human approval for critical actions.
- General consumer chatbot features.

## Core Capabilities
- Local Knowledge Base & RAG.
- Dynamic Model Routing.
- Agentic workflow orchestration.
- Sandboxed tool execution.
- Human-in-the-loop Evidence Gate.

## Primary Workflows
1. Inspection report → approval note.
2. P&ID → review.
3. CSV → engineering calculation.
4. Internal tool → code.

## MVP Scope
- Local FastAPI/React setup.
- Basic RAG with Qdrant.
- Rule-based Model Router.
- Basic Agent Loop with 1-2 tools.
- Simple Code Sandbox.

## Future / Enterprise Scope
- Advanced distributed model inference (vLLM).
- Scalable Kubernetes sandboxes.
- Active Directory / SSO integration.
- Fine-tuned specialized models (Inkling).

## Success Criteria
- 100% local execution.
- Accurate RAG citations (no hallucinations).
- Successful routing of tasks to specialized models.
- Successful generation of a real deliverable (DOCX/XLSX).

## Constraints
- MVP Hardware: 16-24 GB VRAM, 32+ GB system RAM. Limits model sizes to 7B-14B 4-bit quantized.

## Risks
- Local model hallucination rates vs cloud models.
- OCR/PDF parsing accuracy on complex industrial documents.\n