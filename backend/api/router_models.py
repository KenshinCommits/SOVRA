from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from backend.models.registry import get_model_registry, get_model_metadata, ModelMetadata
from backend.models.provider import model_provider
from backend.models.router import ModelRouter, RouterDecision

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Models"])
model_router = ModelRouter(model_provider)

class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt text to route")
    has_images: bool = Field(False, description="Whether input contains images")

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt to generate text for")
    images: Optional[List[str]] = Field(None, description="Optional base64 encoded images")
    system: Optional[str] = Field(None, description="Optional system instruction")
    force_model: Optional[str] = Field(None, description="Override dynamic routing with a specific model")

class GenerateResponse(BaseModel):
    response: str
    model_used: str
    routing_reason: str
    fingerprint: Optional[Dict[str, Any]] = None

@router.get("", response_model=List[ModelMetadata])
async def list_models():
    """Returns the static registry of supported models and their capabilities."""
    return get_model_registry()

@router.post("/route", response_model=RouterDecision)
async def route_task(req: RouteRequest):
    """
    Test endpoint for the router. Returns the routing decision without generating.
    """
    clean_prompt = req.prompt.strip()
    if not clean_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty or whitespace"
        )
    try:
        decision = await model_router.route(clean_prompt, req.has_images)
        return decision
    except Exception as e:
        logger.exception("Model routing failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model routing failed: {str(e)}"
        )

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    Routes the task to the best model and generates the response.
    """
    clean_prompt = req.prompt.strip()
    if not clean_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty or whitespace"
        )

    # 1. Determine model
    if req.force_model:
        # Validate that the model is recognized in registry
        meta = get_model_metadata(req.force_model)
        if not meta:
            available = [m.name for m in get_model_registry()]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{req.force_model}' is not recognized. Available models: {', '.join(available)}"
            )
        selected_model = req.force_model
        reason = "Forced by operator"
        fingerprint = None
    else:
        try:
            has_images = bool(req.images and len(req.images) > 0)
            decision = await model_router.route(clean_prompt, has_images)
            selected_model = decision.selected_model
            reason = decision.reason
            fingerprint = decision.task_fingerprint.model_dump()
        except Exception as e:
            logger.exception("Dynamic routing failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Routing error: {str(e)}"
            )

    # 2. Generate response
    try:
        response_text = await model_provider.generate_text(
            model_name=selected_model,
            prompt=clean_prompt,
            system=req.system,
            images=req.images
        )
        return GenerateResponse(
            response=response_text,
            model_used=selected_model,
            routing_reason=reason,
            fingerprint=fingerprint
        )
    except Exception as e:
        logger.exception(f"Inference error with model '{selected_model}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed with model '{selected_model}': {str(e)}"
        )
