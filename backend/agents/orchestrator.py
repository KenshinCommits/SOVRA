import json
import re
import ast
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from backend.agents.state import AgentTask, AgentStep, AgentState, ApprovalRequest, ApprovalStatus
from backend.tools.registry import registry
from backend.tools.builtins import * # Ensure tools are registered
from backend.models.router import ModelRouter
from backend.models.provider import model_provider
from backend.evidence.gate import evidence_gate
from backend.audit.logger import audit_logger, AuditEntry
from backend.rag.retriever import Retriever

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        self.max_steps = 10
        self.router = ModelRouter(model_provider)
        self.retriever = Retriever()

    async def create_task(self, prompt: str) -> AgentTask:
        task = AgentTask(prompt=prompt)
        # Determine optimal model for this task
        try:
            routing_decision = await self.router.route(prompt)
            task.selected_model = routing_decision.selected_model
        except Exception as e:
            logger.warning(f"Router failed, fallback to general model: {e}")
            task.selected_model = "qwen3.5:9b"
        
        self.tasks[task.task_id] = task
        
        audit_logger.log(AuditEntry(
            task_id=task.task_id,
            action="TASK_CREATED",
            actor="operator",
            details={"prompt": prompt, "model": task.selected_model}
        ))
        return task

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        task = self.tasks.get(task_id)
        if task and task.approval_request and task.approval_request.is_expired():
            if task.approval_request.status == ApprovalStatus.PENDING:
                task.approval_request.status = ApprovalStatus.EXPIRED
                task.status = AgentState.FAILURE
                task.final_result = "Approval request expired after 30 minutes."
                audit_logger.log(AuditEntry(
                    task_id=task_id,
                    action="APPROVAL_EXPIRED",
                    actor="system",
                    tool_name=task.approval_request.tool_name,
                    risk_level=task.approval_request.risk_level
                ))
        return task

    def _build_system_prompt(self) -> str:
        tools_list = json.dumps(registry.list_tools(), indent=2)
        return f"""You are the SOVRA Agent (Sovereign Operations & Reasoning Agent).
You are an expert industrial assistant that can plan and execute actions.
You operate in a strictly controlled local environment.

Available Tools:
{tools_list}

INSTRUCTIONS:
You operate in a loop: PLAN -> ACT -> OBSERVE -> VERIFY.
Analyze the user's request and the history of your steps.
If you need to use a tool, return a JSON object with EXACTLY this structure:
{{
  "thought": "Your public reasoning about what you will do next",
  "tool_call": {{"name": "tool_name", "args": {{"arg1": "val1"}}}}
}}

If you have achieved the goal, or cannot proceed, return a JSON object with EXACTLY this structure:
{{
  "thought": "I have completed the task",
  "final_result": "The final answer or summary"
}}

DO NOT return any markdown wrapping (e.g. no ```json). Just the raw JSON object.
DO NOT use tools that are not listed above.
"""

    def _build_context(self, task: AgentTask) -> str:
        ctx = f"User Request: {task.prompt}\n\nExecution History:\n"
        for i, step in enumerate(task.steps):
            ctx += f"Step {i+1} [{step.state}]:\n"
            if step.thought:
                ctx += f"Thought: {step.thought}\n"
            if step.tool_call:
                ctx += f"Action: {json.dumps(step.tool_call)}\n"
            if step.tool_result:
                ctx += f"Observation: {step.tool_result}\n"
            if step.error:
                ctx += f"Error: {step.error}\n"
            ctx += "\n"
        return ctx

    async def step(self, task_id: str) -> AgentTask:
        """Executes a single iteration of the ReAct loop for a task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError("Task not found")
            
        if task.status in (AgentState.SUCCESS, AgentState.FAILURE):
            return task

        # Check for expired approval
        if task.approval_request and task.approval_request.is_expired():
            if task.approval_request.status == ApprovalStatus.PENDING:
                task.approval_request.status = ApprovalStatus.EXPIRED
                task.status = AgentState.FAILURE
                task.final_result = "Approval request expired after 30 minutes."
                audit_logger.log(AuditEntry(
                    task_id=task_id,
                    action="APPROVAL_EXPIRED",
                    actor="system",
                    tool_name=task.approval_request.tool_name,
                    risk_level=task.approval_request.risk_level
                ))
            return task
            
        # If task is awaiting human approval, do not proceed automatically
        if task.status == AgentState.APPROVAL_REQUIRED:
            if task.approval_request and task.approval_request.status == ApprovalStatus.PENDING:
                return task
            
        if len(task.steps) >= self.max_steps:
            task.status = AgentState.FAILURE
            task.final_result = "Max steps reached without completing the goal."
            return task
            
        # Check if we are resuming from an approved state
        if task.steps and task.steps[-1].state == AgentState.ACT and not task.steps[-1].tool_result and not task.steps[-1].error:
            # If an approval request exists, verify it was approved
            if task.approval_request:
                if task.approval_request.status != ApprovalStatus.APPROVED:
                    return task
            # We are ready to execute the pending tool call
            return self._execute_pending_tool(task)

        # Set status to PLAN
        task.status = AgentState.PLAN
        task.updated_at = datetime.utcnow()
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_context(task)

        # Call the selected model
        response_text = ""
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nAgent Response:"
            response_text = await model_provider.generate_text(task.selected_model, full_prompt)
            
            response_data = self._parse_model_response(response_text)
            
            step = AgentStep(
                state=AgentState.ACT,
                thought=response_data.get("thought", "Proceeding...")
            )
            
            # Normalize tool call variations
            if "tool_call" not in response_data:
                if "action" in response_data and isinstance(response_data["action"], dict) and "name" in response_data["action"]:
                    response_data["tool_call"] = response_data["action"]
                elif "tool" in response_data and "args" in response_data:
                    response_data["tool_call"] = {"name": response_data["tool"], "args": response_data.get("args", {})}
                elif "name" in response_data and ("args" in response_data or "arguments" in response_data or "parameters" in response_data):
                    args = response_data.get("args") or response_data.get("arguments") or response_data.get("parameters") or {}
                    response_data["tool_call"] = {"name": response_data["name"], "args": args}

            # Normalize final result variations
            if "final_result" not in response_data and "tool_call" not in response_data:
                for k in ("result", "answer", "summary", "response", "output"):
                    if k in response_data and isinstance(response_data[k], str):
                        response_data["final_result"] = response_data[k]
                        break

            if "final_result" in response_data:
                step.state = AgentState.SUCCESS
                task.final_result = response_data["final_result"]
                task.status = AgentState.SUCCESS
                task.steps.append(step)
                return task
                
            elif "tool_call" in response_data:
                step.tool_call = response_data["tool_call"]
                task.steps.append(step)
                
                tool_name = step.tool_call.get("name")
                tool_args = step.tool_call.get("args", {})
                
                # Check tool definition & permission
                tool_def = registry.get_tool(tool_name)
                
                if tool_def and tool_def.permission == "execute":
                    # EVIDENCE GATE EVALUATION
                    verification = evidence_gate.evaluate(task.steps, tool_name, tool_args)
                    risk_level = "HIGH" if tool_name == "execute_sandboxed_code" else "MEDIUM"
                    
                    approval_req = ApprovalRequest(
                        task_id=task.task_id,
                        tool_name=tool_name,
                        tool_args=tool_args,
                        risk_level=risk_level,
                        reason=f"Action '{tool_name}' requires operator authorization.",
                        evidence_verification=verification.model_dump(mode="json")
                    )
                    step.approval_request = approval_req
                    task.approval_request = approval_req
                    task.status = AgentState.APPROVAL_REQUIRED
                    
                    audit_logger.log(AuditEntry(
                        task_id=task.task_id,
                        action="APPROVAL_REQUESTED",
                        actor="agent",
                        tool_name=tool_name,
                        tool_args=tool_args,
                        risk_level=risk_level,
                        evidence_verdict=verification.verdict.value,
                        details={"verification": verification.model_dump(mode="json")}
                    ))
                    return task
                
                task.status = AgentState.OBSERVE
                return self._execute_pending_tool(task)
                
            else:
                step.state = AgentState.FAILURE
                step.error = f"Model did not return a tool_call or final_result. Parsed: {response_data}"
                task.status = AgentState.FAILURE
                task.final_result = step.error
                task.steps.append(step)
                return task
                
        except json.JSONDecodeError:
            step = AgentStep(
                state=AgentState.FAILURE,
                error=f"Failed to parse model JSON response. Raw output: {response_text}"
            )
            task.status = AgentState.FAILURE
            task.final_result = step.error
            task.steps.append(step)
            return task
        except Exception as e:
            logger.exception("Exception during task execution")
            err_msg = f"{type(e).__name__}: {str(e)}"
            step = AgentStep(
                state=AgentState.FAILURE,
                error=err_msg
            )
            task.status = AgentState.FAILURE
            task.final_result = f"Exception during execution: {err_msg}"
            task.steps.append(step)
            return task

    def _parse_model_response(self, text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 1. Try direct JSON parse (strict=False permits literal newlines inside strings)
        try:
            data = json.loads(cleaned, strict=False)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        # 2. Try ast.literal_eval (handles single-quoted string values/keys)
        try:
            data = ast.literal_eval(cleaned)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        # 3. Try regex extraction of { ... }
        match = re.search(r"(\{[\s\S]*\})", cleaned)
        if match:
            try:
                data = json.loads(match.group(1), strict=False)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
            try:
                data = ast.literal_eval(match.group(1))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

        # 4. Handle ReAct style: Thought: ... Action: { ... }
        thought_match = re.search(r"Thought:\s*(.*?)(?=(?:Action:|Final Result:|$))", cleaned, re.DOTALL | re.IGNORECASE)
        thought_text = thought_match.group(1).strip() if thought_match else "Analyzing..."

        action_match = re.search(r"Action:\s*(\{[\s\S]*?\})", cleaned, re.IGNORECASE)
        if action_match:
            try:
                action_data = json.loads(action_match.group(1).strip(), strict=False)
                if "name" in action_data:
                    return {"thought": thought_text, "tool_call": action_data}
                elif "tool_call" in action_data:
                    return {"thought": thought_text, "tool_call": action_data["tool_call"]}
            except Exception:
                pass

        # 4. Handle ReAct style: Final Result: ...
        final_match = re.search(r"Final Result:\s*(.*)", cleaned, re.DOTALL | re.IGNORECASE)
        if final_match:
            return {"thought": thought_text, "final_result": final_match.group(1).strip()}

        # 5. Fallback JSONDecodeError
        raise json.JSONDecodeError("Could not extract valid JSON or ReAct action", cleaned, 0)

    def _execute_pending_tool(self, task: AgentTask) -> AgentTask:
        step = task.steps[-1]
        tool_name = step.tool_call.get("name")
        tool_args = step.tool_call.get("args", {})
        
        task.status = AgentState.OBSERVE
        try:
            result = registry.execute(tool_name, tool_args)
            step.tool_result = str(result)
            
            # If knowledge_search, also populate structured evidence on step
            if tool_name == "knowledge_search":
                try:
                    q = tool_args.get("query", "")
                    k = tool_args.get("top_k", 3)
                    evidence_items = self.retriever.retrieve_context(query=q, top_k=k)
                    step.evidence = evidence_items
                except Exception as e:
                    logger.warning(f"Could not attach structured evidence: {e}")

            audit_logger.log(AuditEntry(
                task_id=task.task_id,
                action="TOOL_CALLED",
                actor="agent",
                tool_name=tool_name,
                tool_args=tool_args,
                details={"success": True}
            ))
        except Exception as e:
            step.error = str(e)
            audit_logger.log(AuditEntry(
                task_id=task.task_id,
                action="TOOL_CALLED",
                actor="agent",
                tool_name=tool_name,
                tool_args=tool_args,
                details={"success": False, "error": str(e)}
            ))
            
        task.status = AgentState.VERIFY
        return task

    def approve_task(self, task_id: str, actor: str = "operator", override: bool = False, override_reason: Optional[str] = None) -> AgentTask:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError("Task not found")
            
        if task.status != AgentState.APPROVAL_REQUIRED or not task.approval_request:
            raise ValueError("Task does not require approval")
            
        app_req = task.approval_request
        if app_req.is_expired():
            app_req.status = ApprovalStatus.EXPIRED
            task.status = AgentState.FAILURE
            task.final_result = "Approval request expired after 30 minutes."
            audit_logger.log(AuditEntry(
                task_id=task_id,
                action="APPROVAL_EXPIRED",
                actor="system",
                tool_name=app_req.tool_name,
                risk_level=app_req.risk_level
            ))
            raise ValueError("Approval request has expired (30-minute limit exceeded)")
            
        if app_req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request already resolved with status: {app_req.status}")
            
        # Check Evidence Gate requirement
        verdict = (app_req.evidence_verification or {}).get("verdict")
        if verdict in ("INSUFFICIENT", "MISSING"):
            if not override or not override_reason or not override_reason.strip():
                raise ValueError(f"Evidence is {verdict}. Explicit override flag and justification reason are strictly required.")
            app_req.override = True
            app_req.override_reason = override_reason.strip()
            
            # Log evidence override specifically (User Requirement 3)
            audit_logger.log(AuditEntry(
                task_id=task_id,
                action="EVIDENCE_OVERRIDE_APPROVED",
                actor=actor,
                tool_name=app_req.tool_name,
                tool_args=app_req.tool_args,
                risk_level=app_req.risk_level,
                override=True,
                override_reason=app_req.override_reason,
                evidence_verdict=verdict,
                details={"verification": app_req.evidence_verification}
            ))
        else:
            # Standard approval logging
            audit_logger.log(AuditEntry(
                task_id=task_id,
                action="APPROVAL_GRANTED",
                actor=actor,
                tool_name=app_req.tool_name,
                tool_args=app_req.tool_args,
                risk_level=app_req.risk_level,
                evidence_verdict=verdict
            ))
            
        app_req.status = ApprovalStatus.APPROVED
        app_req.decided_at = datetime.utcnow()
        app_req.decided_by = actor
        
        # Resume execution
        task.status = AgentState.ACT
        return task

    def reject_task(self, task_id: str, actor: str = "operator", reason: Optional[str] = None) -> AgentTask:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError("Task not found")
            
        if task.status != AgentState.APPROVAL_REQUIRED or not task.approval_request:
            raise ValueError("Task does not require approval")
            
        app_req = task.approval_request
        if app_req.is_expired():
            app_req.status = ApprovalStatus.EXPIRED
            task.status = AgentState.FAILURE
            task.final_result = "Approval request expired after 30 minutes."
            audit_logger.log(AuditEntry(
                task_id=task_id,
                action="APPROVAL_EXPIRED",
                actor="system",
                tool_name=app_req.tool_name,
                risk_level=app_req.risk_level
            ))
            raise ValueError("Approval request has expired")
            
        if app_req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request already resolved with status: {app_req.status}")
            
        app_req.status = ApprovalStatus.REJECTED
        app_req.decided_at = datetime.utcnow()
        app_req.decided_by = actor
        if reason:
            app_req.override_reason = reason.strip()
            
        task.status = AgentState.FAILURE
        task.final_result = f"Action rejected by operator ({actor}): {reason or 'No reason provided'}"
        if task.steps:
            task.steps[-1].state = AgentState.FAILURE
            task.steps[-1].error = f"Execution rejected by operator: {reason or 'Rejected'}"
            
        audit_logger.log(AuditEntry(
            task_id=task_id,
            action="APPROVAL_REJECTED",
            actor=actor,
            tool_name=app_req.tool_name,
            tool_args=app_req.tool_args,
            risk_level=app_req.risk_level,
            override_reason=reason
        ))
        return task

# Global orchestrator instance
orchestrator = AgentOrchestrator()
