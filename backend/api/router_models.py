from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from backend.models.registry import get_model_registry, ModelMetadata
from backend.models.provider import model_provider
from backend.models.router import ModelRouter, RouterDecision

router = APIRouter(prefix="/models")

# In a full app, these might be injected via dependencies
model_router = ModelRouter(model_provider)

class RouteRequest(BaseModel):
    prompt: str
    has_images: bool = False

class GenerateRequest(BaseModel):
    prompt: str
    images: Optional[List[str]] = None
    system: Optional[str] = None
    force_model: Optional[str] = None

@router.get("", response_model=List[ModelMetadata])
async def list_models():
    """Returns the static registry of supported models and their capabilities."""
    return get_model_registry()

@router.post("/route", response_model=RouterDecision)
async def route_task(req: RouteRequest):
    """
    Test endpoint for the router. Returns the routing decision without generating.
    """
    try:
        decision = await model_router.route(req.prompt, req.has_images)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate(req: GenerateRequest):
    """
    Routes the task to the best model and generates the response.
    """
    try:
        # 1. Determine model
        if req.force_model:
            selected_model = req.force_model
            reason = "Forced by user"
            fingerprint = None
        else:
            has_images = bool(req.images and len(req.images) > 0)
            decision = await model_router.route(req.prompt, has_images)
            selected_model = decision.selected_model
            reason = decision.reason
            fingerprint = decision.task_fingerprint.dict()

        # 2. Generate response
        response_text = await model_provider.generate_text(
            model_name=selected_model,
            prompt=req.prompt,
            system=req.system,
            images=req.images
        )
        
        return {
            "response": response_text,
            "model_used": selected_model,
            "routing_reason": reason,
            "fingerprint": fingerprint
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
