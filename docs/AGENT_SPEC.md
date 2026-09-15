# Agent Specification

## Core Loop
The future SOVRA agent operates on a ReAct loop:
1. **PLAN**: Analyze user request and define steps.
2. **ACT**: Select and execute a tool (via Sandboxed execution or Knowledge Base).
3. **OBSERVE**: Read tool output.
4. **VERIFY**: Check if the goal is met or if Evidence Gate approval is needed.

## State Management
- Task state includes history, current deliverables, and pending approvals.

## Transparency
- The UI will show operational traces (e.g., "Agent is querying Knowledge Base for 'Pump SOP'").
- Hidden Chain-of-Thought (e.g., `<think>` tags from reasoning models) will NOT be exposed to the user, ensuring a clean, industrial UI.

## Termination Conditions
- Goal achieved (Deliverable ready).
- Max iterations reached.
- Evidence Gate rejection.\n