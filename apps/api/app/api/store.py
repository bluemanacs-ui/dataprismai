"""Store API — conversations, messages, reports CRUD endpoints."""
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.repositories import ConversationRepository, ReportRepository

router = APIRouter(prefix="/store", tags=["store"])


# ── Pydantic schemas ────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    workspace_id: str = "default"
    user_id: str = "anonymous"
    title: str = "New Conversation"


class MessageCreate(BaseModel):
    role: str
    content: str
    payload: dict[str, Any] | None = None


class ReportCreate(BaseModel):
    workspace_id: str = "default"
    user_id: str = "anonymous"
    title: str
    summary: str = ""
    payload: dict[str, Any] | None = None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _conv_to_dict(c) -> dict:
    return {
        "id": c.id,
        "workspace_id": c.workspace_id,
        "user_id": c.user_id,
        "title": c.title,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _msg_to_dict(m) -> dict:
    return {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "role": m.role,
        "content": m.content,
        "payload": json.loads(m.payload_json) if m.payload_json else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _report_to_dict(r) -> dict:
    return {
        "id": r.id,
        "workspace_id": r.workspace_id,
        "user_id": r.user_id,
        "title": r.title,
        "summary": r.summary,
        "payload": json.loads(r.payload_json) if r.payload_json else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


# ── Conversation routes ─────────────────────────────────────────────────────

@router.get("/conversations")
def list_conversations(workspace_id: str = "default", db: Session = Depends(get_db)):
    repo = ConversationRepository(db)
    return [_conv_to_dict(c) for c in repo.list(workspace_id)]


@router.post("/conversations", status_code=201)
def create_conversation(body: ConversationCreate, db: Session = Depends(get_db)):
    repo = ConversationRepository(db)
    c = repo.create(workspace_id=body.workspace_id, user_id=body.user_id, title=body.title)
    return _conv_to_dict(c)


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    repo = ConversationRepository(db)
    c = repo.get(conversation_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conv_to_dict(c)


@router.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    repo = ConversationRepository(db)
    if not repo.get(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [_msg_to_dict(m) for m in repo.get_messages(conversation_id)]


@router.post("/conversations/{conversation_id}/messages", status_code=201)
def add_message(conversation_id: str, body: MessageCreate, db: Session = Depends(get_db)):
    repo = ConversationRepository(db)
    if not repo.get(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    m = repo.add_message(
        conversation_id=conversation_id,
        role=body.role,
        content=body.content,
        payload=body.payload,
    )
    return _msg_to_dict(m)


# ── Report routes ───────────────────────────────────────────────────────────

@router.get("/reports")
def list_reports(workspace_id: str = "default", db: Session = Depends(get_db)):
    repo = ReportRepository(db)
    return [_report_to_dict(r) for r in repo.list(workspace_id)]


@router.post("/reports", status_code=201)
def create_report(body: ReportCreate, db: Session = Depends(get_db)):
    repo = ReportRepository(db)
    r = repo.create(
        workspace_id=body.workspace_id,
        user_id=body.user_id,
        title=body.title,
        summary=body.summary,
        payload=body.payload,
    )
    return _report_to_dict(r)
