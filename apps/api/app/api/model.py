# =============================================================================
# DataPrismAI — /model API Router
# =============================================================================
# Endpoints for listing available LLM models and switching the active model
# at runtime without restarting the server.
#
# GET  /model          — list available models + active model
# POST /model/switch   — switch to a different available model
# GET  /model/status   — check which model is currently loaded in Ollama
# =============================================================================
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/model", tags=["model"])


class ModelSwitchRequest(BaseModel):
    model: str  # e.g. "qwen2.5:7b" or "qwen2.5:32b"


def _ollama_loaded_models() -> list[str]:
    """Return model names currently loaded into Ollama memory."""
    try:
        r = httpx.get(f"{settings.ollama_host}/api/ps", timeout=5)
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def _ollama_available_tags() -> list[dict]:
    """Return all pulled models from Ollama."""
    try:
        r = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5)
        return r.json().get("models", [])
    except Exception:
        return []


@router.get("")
def list_models() -> dict:
    """List configured models and which one is active."""
    configured = [m.strip() for m in settings.ollama_available_models.split(",") if m.strip()]
    pulled = [m["name"] for m in _ollama_available_tags()]
    loaded = _ollama_loaded_models()
    return {
        "active_model": settings.ollama_model,
        "available_models": [
            {
                "name": m,
                "pulled": m in pulled,
                "loaded": m in loaded,
                "active": m == settings.ollama_model,
            }
            for m in configured
        ],
    }


@router.post("/switch")
def switch_model(payload: ModelSwitchRequest) -> dict:
    """
    Switch the active LLM model at runtime.

    - Validates the requested model is in OLLAMA_AVAILABLE_MODELS.
    - Evicts the current model from Ollama memory (keep_alive=0).
    - Updates settings.ollama_model and settings.vanna_model in-process.
    - The next request will load the new model automatically.

    The switch persists until the process is restarted.
    To make it permanent, update OLLAMA_MODEL in apps/api/.env.
    """
    configured = [m.strip() for m in settings.ollama_available_models.split(",") if m.strip()]
    if payload.model not in configured:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{payload.model}' is not in OLLAMA_AVAILABLE_MODELS. "
                   f"Configured: {configured}",
        )

    # Check it's actually pulled
    pulled_names = [m["name"] for m in _ollama_available_tags()]
    if payload.model not in pulled_names:
        raise HTTPException(
            status_code=409,
            detail=f"Model '{payload.model}' is configured but not yet pulled. "
                   f"Run: docker exec dataprismai-ollama ollama pull {payload.model}",
        )

    old_model = settings.ollama_model

    # Evict the old model from GPU/RAM
    if old_model != payload.model:
        try:
            httpx.post(
                f"{settings.ollama_host}/api/generate",
                json={"model": old_model, "prompt": "", "keep_alive": 0},
                timeout=10,
            )
        except Exception:
            pass  # non-fatal — model might already be unloaded

    # Update in-process (survives until restart)
    settings.ollama_model = payload.model
    settings.vanna_model = payload.model

    return {
        "switched": True,
        "from": old_model,
        "to": payload.model,
        "note": "Switch is in-process only. Set OLLAMA_MODEL in .env to make permanent.",
    }


@router.get("/status")
def model_status() -> dict:
    """Return which model is currently loaded in Ollama memory."""
    loaded = _ollama_loaded_models()
    return {
        "active_model": settings.ollama_model,
        "loaded_in_ollama": loaded,
        "is_loaded": settings.ollama_model in loaded,
    }
