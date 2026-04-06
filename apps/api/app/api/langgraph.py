"""LangGraph router — thin wrapper exposing the compiled 13-node graph via REST.

The primary chat endpoint is POST /chat/query (see app/api/chat.py).
This router provides a lower-level /langgraph/invoke endpoint for testing
and direct graph access.
"""
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Optional

from app.graph_runtime import compiled_graph

router = APIRouter(prefix="/langgraph", tags=["langgraph"])


class GraphInvokeRequest(BaseModel):
    message: str
    persona: str = "analyst"
    workspace_id: str = "default"
    thread_id: Optional[str] = None
    user_id: str = "anonymous"


@router.post("/invoke")
def invoke_graph(payload: GraphInvokeRequest) -> dict[str, Any]:
    thread_id = payload.thread_id or str(uuid.uuid4())
    initial_state = {
        "thread_id": thread_id,
        "user_id": payload.user_id,
        "workspace_id": payload.workspace_id,
        "persona": payload.persona,
        "user_message": payload.message,
    }
    result = compiled_graph.invoke(initial_state)
    return {"thread_id": thread_id, **result}
