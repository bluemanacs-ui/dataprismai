from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, default="default")
    user_id = Column(String, nullable=False, default="anonymous")
    title = Column(String, nullable=False, default="New Conversation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_msg_conversation_id", "conversation_id"),)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, default="default")
    user_id = Column(String, nullable=False, default="anonymous")
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(String, primary_key=True)
    thread_id = Column(String, nullable=False)
    graph_state_json = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="running")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    __table_args__ = (Index("ix_agent_runs_thread_id", "thread_id"),)


class AppConfig(Base):
    """Runtime configuration overrides stored in Postgres.

    Only entries explicitly saved via the Config UI are persisted here.
    All other values fall through to environment variables / defaults defined
    in config_schema.py.
    """
    __tablename__ = "app_config"
    key = Column(String, primary_key=True)          # e.g.  "llm.model"
    value = Column(Text, nullable=False)             # always stored as string
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
