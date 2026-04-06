import json
import uuid


def persist_node(state: dict) -> dict:
    try:
        from app.db.session import SessionLocal
        from app.db.repositories import ConversationRepository, AgentRunRepository
        db = SessionLocal()
        thread_id = state.get("thread_id") or str(uuid.uuid4())
        conv_repo = ConversationRepository(db)
        run_repo = AgentRunRepository(db)
        conv = conv_repo.create(
            workspace_id=state.get("workspace_id", "default"),
            user_id=state.get("user_id", "anonymous"),
            title=state.get("user_message", "New Conversation")[:80],
        )
        conv_repo.add_message(conv.id, "user", state.get("user_message", ""), None)
        conv_repo.add_message(conv.id, "assistant", state.get("answer", ""), {
            "sql": state.get("generated_sql"),
            "insights": state.get("insights"),
            "visualization_config": state.get("visualization_config"),
        })
        run_repo.create(thread_id=thread_id, graph_state={"status": "completed"})
        db.close()
        return {**state, "report_id": conv.id, "thread_id": thread_id}
    except Exception as e:
        import uuid
        return {**state, "report_id": str(uuid.uuid4()), "_persist_error": str(e)}
