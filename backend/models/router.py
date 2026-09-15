import json
import re
from pydantic import BaseModel
from backend.models.registry import get_model_registry
from backend.models.provider import ModelProvider

class TaskFingerprint(BaseModel):
    modality: str
    complexity: str  # "low", "medium", "high"
    requires_code: bool
    requires_vision: bool

class RouterDecision(BaseModel):
    selected_model: str
    reason: str
    task_fingerprint: TaskFingerprint

class ModelRouter:
    """
    Intelligent Model Router that dynamically selects the best local model
    for a given task without hardcoding specific model names in the agent logic.
    """
    def __init__(self, provider: ModelProvider):
        self.provider = provider
        # Fast lightweight model for routing logic
        self.routing_model = "qwen2.5-coder:latest" 

    async def extract_fingerprint(self, prompt: str, has_images: bool) -> TaskFingerprint:
        if has_images:
            return TaskFingerprint(
                modality="multimodal",
                complexity="high", # Image processing is inherently complex
                requires_code=False,
                requires_vision=True
            )
            
        system_prompt = """You are an AI task routing analyst. Your job is to classify the user's prompt.
Analyze the prompt and return a RAW JSON object with EXACTLY these keys:
{
  "complexity": "low" | "medium" | "high",
  "requires_code": true | false
}
Use "high" complexity for: complex logical puzzles, advanced reasoning, intricate step-by-step math problems, or deep architectural design.
Use "medium" complexity for: standard questions, simple code generation, and standard reasoning.
Use "low" complexity for: basic facts, simple translations, or short queries.
Do not return any markdown wrapping, just the raw JSON."""

        try:
            # We use format="json" if supported, or just trust the system prompt.
            # We'll pass temperature 0 for deterministic output.
            raw_response = await self.provider.generate_text(
                model_name=self.routing_model,
                prompt=prompt,
                system=system_prompt,
                temperature=0.0,
                format="json"
            )
            
            # Clean up potential markdown if the model ignored format="json"
            cleaned = re.sub(r'```json|```', '', raw_response).strip()
            data = json.loads(cleaned)
            
            return TaskFingerprint(
                modality="text",
                complexity=data.get("complexity", "medium").lower(),
                requires_code=bool(data.get("requires_code", False)),
                requires_vision=False
            )
        except Exception as e:
            print(f"Router LLM fingerprinting failed: {e}. Falling back to heuristics.")
            # Fallback heuristics
            complexity = "high" if len(prompt) > 500 else "medium"
            requires_code = bool(re.search(r'(code|script|python|javascript|function|html|css)', prompt.lower()))
            return TaskFingerprint(
                modality="text",
                complexity=complexity,
                requires_code=requires_code,
                requires_vision=False
            )

    async def route(self, prompt: str, has_images: bool = False) -> RouterDecision:
        fingerprint = await self.extract_fingerprint(prompt, has_images)
        registry = get_model_registry()
        
        candidates = registry
        
        # 1. Filter by modality/vision
        if fingerprint.requires_vision:
            candidates = [m for m in candidates if m.capabilities.vision_support]
            if not candidates:
                raise ValueError("No vision-capable models available in the registry.")
                
        # 2. If it requires code, prioritize coding strength
        if fingerprint.requires_code and not fingerprint.requires_vision:
            # Sort by coding strength descending
            candidates = sorted(candidates, key=lambda m: m.capabilities.coding_strength, reverse=True)
            if fingerprint.complexity == "high":
                selected = candidates[0]
                reason = "Complex coding task routed to highest coding strength model."
            else:
                # Use a lightweight coding model if available, else best coding model
                lightweight = [m for m in candidates if "latest" in m.name or "7b" in m.name]
                selected = lightweight[0] if lightweight else candidates[0]
                reason = "Standard coding task routed to lightweight coding model."
                
        # 3. For general text tasks
        elif not fingerprint.requires_vision:
            # Sort by reasoning strength descending
            candidates = sorted(candidates, key=lambda m: m.capabilities.reasoning_strength, reverse=True)
            if fingerprint.complexity == "high":
                selected = candidates[0]
                reason = "Complex reasoning task routed to highest reasoning strength model."
            else:
                # Find a balanced model (e.g., general purpose agent model)
                balanced = [m for m in candidates if "9b" in m.name or "8b" in m.name]
                selected = balanced[0] if balanced else candidates[0]
                reason = "General text task routed to standard agent model."
                
        else:
            selected = candidates[0]
            reason = "Vision task routed to multimodal candidate."

        return RouterDecision(
            selected_model=selected.name,
            reason=reason,
            task_fingerprint=fingerprint
        )
