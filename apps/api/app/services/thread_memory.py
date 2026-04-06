"""In-process thread memory: stores the last few turns per thread_id.

Each entry keeps the user message, the generated SQL, and a compact
summary of the result rows so the LLM can resolve follow-up pronouns.
"""
from collections import deque
from threading import Lock
from typing import Optional

_MAX_TURNS = 3

# { thread_id: deque([{user_message, sql, row_summary, columns}]) }
_store: dict[str, deque] = {}
# { thread_id: {entity_type, entity_id, entity_name} }  — most-recent entity per thread
_entity_store: dict[str, dict] = {}
_lock = Lock()


def store_turn(thread_id: str, user_message: str, sql: str, rows: list, columns: list) -> None:
    """Save a completed query turn for this thread."""
    if not thread_id:
        return
    # Compact row summary: first 5 rows, key columns only (avoid huge payloads)
    summary_rows = rows[:5] if rows else []
    with _lock:
        if thread_id not in _store:
            _store[thread_id] = deque(maxlen=_MAX_TURNS)
        _store[thread_id].append({
            "user_message": user_message,
            "sql": sql,
            "columns": columns,
            "row_summary": summary_rows,
        })


def get_context(thread_id: str) -> list[dict]:
    """Return recent turns for this thread (oldest first)."""
    if not thread_id:
        return []
    with _lock:
        return list(_store.get(thread_id, []))


def store_entity(thread_id: str, entity_type: str, entity_id: str, entity_name: str = "") -> None:
    """Persist the most-recently referenced entity for this thread."""
    if not thread_id or not entity_id:
        return
    with _lock:
        _entity_store[thread_id] = {
            "entity_type": entity_type,
            "entity_id":   entity_id,
            "entity_name": entity_name,
        }


def get_last_entity(thread_id: str) -> Optional[dict]:
    """Return the most-recently stored entity for this thread, or None."""
    if not thread_id:
        return None
    with _lock:
        return _entity_store.get(thread_id)
