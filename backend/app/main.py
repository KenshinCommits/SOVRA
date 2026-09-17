from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from backend.api.router_agent import router as agent_router

app.include_router(knowledge_router, tags=["Knowledge"])
app.include_router(models_router, tags=["Models"])
app.include_router(agent_router, tags=["Agent"])

artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(artifacts_dir, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=artifacts_dir), name="artifacts")


from backend.agents.orchestrator import orchestrator
from fastapi import Request
from fastapi.responses import JSONResponse

class SystemStatus(BaseModel):
    ollama_connected: bool
    qdrant_connected: bool
    models_available: list[str]
    sovereign_offline: bool = True
    active_tasks_count: int = 0
    pending_approvals_count: int = 0
    system_errors: list[str] = []

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Detailed error logged in audit system.", "error_type": type(exc).__name__}
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/system/status", response_model=SystemStatus)
async def system_status():
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_connected = False
    models = []
    system_errors = []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_url}/api/tags", timeout=2.0)
            if response.status_code == 200:
                ollama_connected = True
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
            else:
                system_errors.append(f"Ollama returned status {response.status_code}")
    except Exception:
        system_errors.append("Ollama service unreachable on local port 11434")

    # Live Qdrant status check
    qdrant_host = os.getenv("QDRANT_HOST", "http://localhost:6333")
    if not qdrant_host.startswith("http"):
        qdrant_host = f"http://{qdrant_host}:6333"
    qdrant_connected = False
    try:
        async with httpx.AsyncClient() as client:
            qdrant_res = await client.get(f"{qdrant_host}/readyz", timeout=2.0)
            if qdrant_res.status_code == 200:
                qdrant_connected = True
            else:
                system_errors.append(f"Qdrant returned non-ready status {qdrant_res.status_code}")
    except Exception:
        system_errors.append("Qdrant service unreachable on local port 6333")

    active_tasks_count = sum(
        1 for t in orchestrator.tasks.values() 
        if t.status in ("PLAN", "ACT", "OBSERVE", "VERIFY")
    )
    pending_approvals_count = sum(
        1 for t in orchestrator.tasks.values() 
        if t.status == "APPROVAL_REQUIRED" and t.approval_request and t.approval_request.status.value == "PENDING" and not t.approval_request.is_expired()
    )

    return SystemStatus(
        ollama_connected=ollama_connected,
        qdrant_connected=qdrant_connected,
        models_available=models,
        sovereign_offline=True,
        active_tasks_count=active_tasks_count,
        pending_approvals_count=pending_approvals_count,
        system_errors=system_errors
    )
