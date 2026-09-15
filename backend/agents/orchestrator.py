import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from backend.agents.state import AgentTask, AgentStep, AgentState
from backend.tools.registry import registry
from backend.tools.builtins import * # Ensure tools are registered
from backend.models.router import ModelRouter
from backend.models.provider import model_provider

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        self.max_steps = 10
        self.router = ModelRouter(model_provider)

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
        return task

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self.tasks.get(task_id)

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
            
        if len(task.steps) >= self.max_steps:
            task.status = AgentState.FAILURE
            task.final_result = "Max steps reached without completing the goal."
            return task

        # Set status to PLAN
        task.status = AgentState.PLAN
        task.updated_at = datetime.utcnow()
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_context(task)

        # Call the selected model
        response_text = ""
        try:
            # For simplicity in MVP, we just append system and user prompt.
            # In a robust implementation, this would use proper ChatML formatting.
            full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nAgent Response:"
            response_text = await model_provider.generate_text(task.selected_model, full_prompt)
            
            # Parse response
            # Sometimes models return ```json ... ```
            clean_json = response_text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
                
            response_data = json.loads(clean_json.strip())
            
            step = AgentStep(
                state=AgentState.ACT,
                thought=response_data.get("thought", "Proceeding...")
            )
            
            if "final_result" in response_data:
                step.state = AgentState.SUCCESS
                task.final_result = response_data["final_result"]
                task.status = AgentState.SUCCESS
                task.steps.append(step)
                return task
                
            elif "tool_call" in response_data:
                step.tool_call = response_data["tool_call"]
                task.steps.append(step)
                
                # Execute tool
                task.status = AgentState.OBSERVE
                tool_name = step.tool_call.get("name")
                tool_args = step.tool_call.get("args", {})
                
                try:
                    result = registry.execute(tool_name, tool_args)
                    step.tool_result = str(result)
                except Exception as e:
                    step.error = str(e)
                    
                task.status = AgentState.VERIFY
                return task
                
            else:
                step.state = AgentState.FAILURE
                step.error = "Model did not return a tool_call or final_result."
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
            step = AgentStep(
                state=AgentState.FAILURE,
                error=str(e)
            )
            task.status = AgentState.FAILURE
            task.final_result = f"Exception during execution: {str(e)}"
            task.steps.append(step)
            return task

# Global orchestrator instance
orchestrator = AgentOrchestrator()
