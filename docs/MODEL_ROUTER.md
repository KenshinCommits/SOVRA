# Model Router

## Abstraction
- **`ModelProvider`**: Abstract base class.
- **`OllamaModelProvider`**: Implementation wrapping local Ollama instances via `httpx`.

## Model Capabilities Registry
Models are defined in `backend/models/registry.py`. Current capabilities include:
- Modality (text vs multimodal).
- Reasoning strength.
- Coding strength.

## Routing Policy
1. Extract `TaskFingerprint` (Complexity, Requires Code, Requires Vision).
2. If vision required, route to vision-capable model (`gemma4:12b`).
3. If code required, sort by coding strength. Pick lightweight coder for simple tasks, heavyweight for complex.
4. If standard text, sort by reasoning strength.

## Future Support
- **Inkling / Inkling-Small**: Planned integration.
- The router is agnostic and can easily support `llama.cpp` or `vLLM` in the future by creating a new `ModelProvider`.\n