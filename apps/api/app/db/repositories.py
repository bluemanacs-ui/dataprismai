import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Conversation, ConversationMessage, Report, AgentRun


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, workspace_id: str = "default") -> list:
        return self.db.query(Conversation).filter(Conversation.workspace_id == workspace_id).order_by(Conversation.created_at.desc()).all()

    def get(self, conversation_id: str) -> Conversation | None:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def create(self, workspace_id: str = "default", user_id: str = "anonymous", title: str = "New Conversation") -> Conversation:
        conv = Conversation(id=str(uuid.uuid4()), workspace_id=workspace_id, user_id=user_id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def add_message(self, conversation_id: str, role: str, content: str, payload: dict | None = None) -> ConversationMessage:
        msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            payload_json=json.dumps(payload) if payload else None,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, conversation_id: str) -> list:
        return self.db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation_id).order_by(ConversationMessage.created_at.asc()).all()


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, workspace_id: str = "default") -> list:
        return self.db.query(Report).filter(Report.workspace_id == workspace_id).order_by(Report.created_at.desc()).all()

    def create(self, workspace_id: str, user_id: str, title: str, summary: str = "", payload: dict | None = None) -> Report:
        report = Report(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            summary=summary,
            payload_json=json.dumps(payload) if payload else None,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report


class AgentRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, thread_id: str, graph_state: dict | None = None) -> AgentRun:
        run = AgentRun(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            graph_state_json=json.dumps(graph_state) if graph_state else None,
            status="running",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_state(self, run_id: str, graph_state: dict, status: str = "completed"):
        run = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run:
            run.graph_state_json = json.dumps(graph_state)
            run.status = status
            self.db.commit()
