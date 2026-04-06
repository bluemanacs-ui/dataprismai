# =============================================================================
# DataPrismAI — FastAPI Application Entry Point
# =============================================================================
# Registers all API routers, configures CORS from environment variables, and
# warms the SchemaRegistry on startup so the first request is never cold.
#
# Routers:
#   /chat      — natural-language query endpoint (POST /chat/query)
#   /semantic  — metric catalog & semantic layer browser
#   /skills    — skill catalog (read-only)
#   /langgraph — LangGraph state + debug endpoints
#   /api/store — session / report persistence
# =============================================================================
from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.semantic import router as semantic_router
from app.api.skills import router as skills_router
from app.api.langgraph import router as langgraph_router
from app.api.store import router as store_router
from app.api.model import router as model_router
from app.core.config import settings
from app.services.schema_registry import registry as _schema_registry

logger = logging.getLogger(__name__)

app = FastAPI(title="DataPrismAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(semantic_router)
app.include_router(skills_router)
app.include_router(langgraph_router)
app.include_router(model_router)
app.include_router(store_router, prefix="/api")


@app.on_event("startup")
async def _warm_schema_registry() -> None:
    """Eagerly load SchemaRegistry so the first chat request isn't cold.

    Runs in a thread-pool executor to avoid blocking the event loop during I/O.
    Failure is non-fatal — the registry will retry on the first incoming request
    (throttled at 30 s intervals via ensure_loaded).
    """
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, _schema_registry.ensure_loaded)
        table_count = len(_schema_registry.known_table_names())
        logger.info("SchemaRegistry warmed at startup: %d tables loaded.", table_count)
    except Exception as exc:
        logger.warning(
            "SchemaRegistry startup warm-up failed (will retry on first request): %s", exc
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "DataPrismAI API"}
