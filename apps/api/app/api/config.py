# =============================================================================
# DataPrismAI — /config API Router
# =============================================================================
# GET  /config          → full structured config (all sections, metadata, values)
# PATCH /config         → update one or more config keys
# POST  /config/reset   → remove a DB override (revert to env/default)
# POST  /config/refresh → force reload ConfigService cache from DB
# =============================================================================

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.config_service import config_svc
from app.core.config_schema import CONFIG_MAP

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["config"])


class ConfigPatchRequest(BaseModel):
    updates: dict[str, str]


class ConfigResetRequest(BaseModel):
    key: str


@router.get("")
def get_config():
    """Return the full structured configuration with metadata, grouped by section."""
    try:
        return config_svc.get_all_sections()
    except Exception as exc:
        logger.error("GET /config failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("")
def patch_config(body: ConfigPatchRequest):
    """Update one or more config keys. Read-only keys are rejected."""
    if not body.updates:
        raise HTTPException(status_code=400, detail="No updates provided.")

    # Validate all keys exist and are not readonly before writing
    errors: list[str] = []
    for key in body.updates:
        entry = CONFIG_MAP.get(key)
        if entry is None:
            errors.append(f"Unknown config key: {key!r}")
        elif entry.is_readonly:
            errors.append(f"Key {key!r} is read-only.")
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    try:
        config_svc.set_many(body.updates)
        return {"ok": True, "saved": len(body.updates)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("PATCH /config failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/reset")
def reset_config(body: ConfigResetRequest):
    """Remove a DB override for the given key (reverts to env/default)."""
    entry = CONFIG_MAP.get(body.key)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Unknown config key: {body.key!r}")
    if entry.is_readonly:
        raise HTTPException(status_code=422, detail=f"Key {body.key!r} is read-only.")
    try:
        config_svc.reset(body.key)
        return {"ok": True, "key": body.key, "reverted_to": entry.env_default()}
    except Exception as exc:
        logger.error("POST /config/reset failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/refresh")
def refresh_config():
    """Force reload the ConfigService cache from the database."""
    try:
        config_svc.refresh()
        return {"ok": True, "message": "Config cache refreshed from database."}
    except Exception as exc:
        logger.error("POST /config/refresh failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
