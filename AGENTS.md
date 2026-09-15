# AGENT INSTRUCTIONS

This file is CRITICAL for all AI coding agents working on this project (Antigravity, Kilo Code, ChatGPT, Claude, etc.).

## Rules for AI Agents

* Inspect before modifying. Check the actual codebase and ProjectStatus.md as the source of truth.
* Never fabricate functionality.
* Never fabricate citations in RAG.
* Never claim tests passed without actually running them.
* Never claim security guarantees without concrete evidence.
* Never use cloud AI APIs (OpenAI, Gemini, Claude, etc.) without explicit user approval.
* Keep models interchangeable. The architecture MUST remain model-agnostic.
* Keep RAG independent from models.
* Keep tools behind a registry.
* Generated code must use sandbox execution (Phase 5).
* Never provide unrestricted host shell access to the LLM agent.
* Don't modify unrelated files.
* Don't duplicate existing functionality.
* Follow the phase roadmap in docs/ROADMAP.md.
* Read relevant docs (PRD, ARCHITECTURE, DESIGN) before implementation.
* Update `ProjectStatus.md` after meaningful work.
* Update `CHANGELOG.md` for meaningful completed changes.
* Preserve backwards compatibility where practical.
* Prefer simple MVP implementations over over-engineered solutions.
* Test after changes.
* Clearly document limitations.

## Recommended Reading

Before starting a task, agents should read, when relevant:
- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `docs/DESIGN.md`
- `docs/SECURITY.md`
- `docs/ROADMAP.md`
- `ProjectStatus.md`\n