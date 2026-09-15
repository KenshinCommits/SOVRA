# Contributing to SOVRA

Welcome to the SOVRA MVP project (SIH26117). This document outlines the workflow for hackathon team members and AI agents.

## Workflow

*   **Branch Strategy**: Main branch `main` should always be runnable. Use feature branches (e.g., `feature/phase-4-agent`) for new work.
*   **Commit Style**: Use descriptive commits. e.g., `feat(rag): implement qdrant vector search`.
*   **Testing**: Write and run tests before merging. Do not claim tests passed without running them.
*   **Documentation Updates**: Update `ProjectStatus.md` and `CHANGELOG.md` when completing a phase or major feature.
*   **Code Quality**: Prefer simple, working MVP code over complex abstractions. Keep it clean and model-agnostic.
*   **Security Rules**: No hardcoded API keys. No unrestricted host shell execution.
*   **AI-Assisted Development**: If using AI coding agents, ensure they read `AGENTS.md` and `ProjectStatus.md` first.\n