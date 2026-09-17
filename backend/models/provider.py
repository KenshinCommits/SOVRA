import abc
import os
import httpx
from typing import Any, Dict, Optional, List

class ModelProvider(abc.ABC):
    """
    Abstract base class for all Model Providers.
    Ensures SOVRA remains model and provider agnostic.
    """
    @abc.abstractmethod
    async def generate_text(self, model_name: str, prompt: str, system: Optional[str] = None, images: Optional[List[str]] = None, **kwargs) -> str:
        pass


class OllamaModelProvider(ModelProvider):
    """
    Provider implementation for local Ollama instances.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    async def generate_text(self, model_name: str, prompt: str, system: Optional[str] = None, images: Optional[List[str]] = None, **kwargs) -> str:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
            
        if images:
            payload["images"] = images
            
        # Merge any additional kwargs (like temperature, max_tokens, etc.) into options
        if kwargs:
            payload["options"] = kwargs
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.TimeoutException:
            raise TimeoutError(f"Model {model_name} timed out after 120s.")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Model {model_name} returned error status {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Model {model_name} inference failed: {str(e) or type(e).__name__}")

# Global singleton
model_provider = OllamaModelProvider()
