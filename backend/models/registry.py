from pydantic import BaseModel
from typing import List, Optional

class ModelCapabilities(BaseModel):
    modality: str  # e.g., "text", "multimodal"
    context_window: int
    reasoning_strength: int  # 1 (low) to 10 (high)
    coding_strength: int     # 1 (low) to 10 (high)
    vision_support: bool
    description: str

class ModelMetadata(BaseModel):
    name: str
    provider: str
    capabilities: ModelCapabilities

# The SOVRA Model Registry
# This abstracts away the underlying provider from the agent logic.
SOVRA_MODELS = [
    ModelMetadata(
        name="qwen3.5:9b",
        provider="ollama",
        capabilities=ModelCapabilities(
            modality="text",
            context_window=32768,
            reasoning_strength=6,
            coding_strength=5,
            vision_support=False,  # While it might have vision, gemma4 is our designated vision candidate
            description="General purpose lightweight agent model for standard tasks."
        )
    ),
    ModelMetadata(
        name="qwen3:14b",
        provider="ollama",
        capabilities=ModelCapabilities(
            modality="text",
            context_window=32768,
            reasoning_strength=8,
            coding_strength=6,
            vision_support=False,
            description="Strong reasoning model for complex logical tasks."
        )
    ),
    ModelMetadata(
        name="deepseek-r1:7b",
        provider="ollama",
        capabilities=ModelCapabilities(
            modality="text",
            context_window=131072,
            reasoning_strength=9, # High reasoning due to CoT
            coding_strength=7,
            vision_support=False,
            description="Deep reasoning model with Chain-of-Thought for intricate problem solving."
        )
    ),
    ModelMetadata(
        name="qwen2.5-coder:14b",
        provider="ollama",
        capabilities=ModelCapabilities(
            modality="text",
            context_window=32768,
            reasoning_strength=7,
            coding_strength=9,
            vision_support=False,
            description="Heavyweight coding model for complex software engineering tasks."
        )
    ),
    ModelMetadata(
        name="qwen2.5-coder:latest", # typically 7b
        provider="ollama",
        capabilities=ModelCapabilities(
            modality="text",
            context_window=32768,
            reasoning_strength=5,
            coding_strength=8,
            vision_support=False,
            description="Lightweight coding model for simple scripts and fast execution."
        )
    ),
    ModelMetadata(
        name="gemma4:12b",
        provider="ollama",
        capabilities=ModelCapabilities(
            modality="multimodal",
            context_window=262144,
            reasoning_strength=7,
            coding_strength=6,
            vision_support=True,
            description="Multimodal candidate with verified vision support."
        )
    )
]

def get_model_registry() -> List[ModelMetadata]:
    return SOVRA_MODELS

def get_model_metadata(name: str) -> Optional[ModelMetadata]:
    for model in SOVRA_MODELS:
        if model.name == name:
            return model
    return None
