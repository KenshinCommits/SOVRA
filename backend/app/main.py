from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SOVRA MVP API", description="Sovereign Operations & Reasoning Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.router_knowledge import router as knowledge_router
from backend.api.router_models import router as models_router

app.include_router(knowledge_router, tags=["Knowledge"])
app.include_router(models_router, tags=["Models"])


class SystemStatus(BaseModel):
    ollama_connected: bool
    qdrant_connected: bool
    models_available: list[str]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/system/status", response_model=SystemStatus)
async def system_status():
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_connected = False
    models = []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_url}/api/tags", timeout=2.0)
            if response.status_code == 200:
                ollama_connected = True
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
    except Exception:
        pass

    # TODO: Check Qdrant status
    qdrant_connected = False

    return SystemStatus(
        ollama_connected=ollama_connected,
        qdrant_connected=qdrant_connected,
        models_available=models
    )
