"""Entity resolver node — runs between guardrail and planner.

Purpose
-------
1. When the user message contains an explicit entity ID (CUST_xxx, ACC_xxx, …),
   store it in per-thread entity memory so future turns can reference it.

2. When the user message contains a pronoun or demonstrative phrase (he/she/his/
   this account/that customer/…) with NO explicit ID, rewrite the message using
   the most-recently stored entity for this thread — enabling natural multi-turn
   conversation.

Design constraints
------------------
- Fully deterministic (regex only, no LLM).
- Modifies ``user_message`` in state; preserves the original in ``original_message``.
- Thread-scoped: each thread_id has independent entity memory.
"""
import re
from typing import Optional

from app.services.entity_extractor import extract_entity
from app.services.thread_memory import get_last_entity, store_entity

# ── Explicit entity-ID patterns in messages ──────────────────────────────────
_ENTITY_ID_RE = re.compile(
    r"\b(CUST_\w+|ACC_\w+|CARD_\w+|MERCH_\w+|TXN_\w+|PROD_\w+)\b",
    re.IGNORECASE,
)

_ENTITY_ID_PREFIXES: list[tuple[str, str]] = [
    ("CUST_",  "customer"),
    ("ACC_",   "account"),
    ("CARD_",  "card"),
    ("MERCH_", "merchant"),
    ("TXN_",   "transaction"),
    ("PROD_",  "product"),
]


def _entity_type_from_id(entity_id: str) -> str:
    uid = entity_id.upper()
    for prefix, etype in _ENTITY_ID_PREFIXES:
        if uid.startswith(prefix):
            return etype
    return "entity"


# ── Pronoun / demonstrative patterns ─────────────────────────────────────────
_PRONOUN_RE = re.compile(
    r"\b("
    r"he|she|they|him|her|them"
    r"|his\s+\w+|her\s+\w+|their\s+\w+"                             # possessive + noun
    r"|its\s+\w+"                                                    # for non-person entities
    r"|this\s+(?:customer|account|card|user|person|merchant|transaction)"
    r"|that\s+(?:customer|account|card|user|person|merchant|transaction)"
    r"|the\s+(?:same|above|said)\s+(?:customer|account|card|user|person|merchant)"
    r")\b",
    re.IGNORECASE,
)


def _rewrite_with_entity(message: str, entity: dict) -> str:
    """Replace pronoun references with the explicit entity reference.

    Examples
    --------
    "what is his balance?"  →  "what is customer CUST_100's balance?"
    "show this account's tx" →  "show account ACC_001's tx"
    """
    etype = entity["entity_type"]   # e.g. "customer"
    eid   = entity["entity_id"]     # e.g. "CUST_100"
    id_ref = f"{etype} {eid}"       # "customer CUST_100"

    msg = message

    # ── Demonstrative noun phrases (replace whole phrase) ────────────────────
    for noun_pattern in (
        r"this\s+(?:customer|account|card|user|person|merchant|transaction)",
        r"that\s+(?:customer|account|card|user|person|merchant|transaction)",
        r"the\s+(?:same|above|said)\s+(?:customer|account|card|user|person|merchant)",
    ):
        msg = re.sub(rf"\b{noun_pattern}\b", id_ref, msg, flags=re.IGNORECASE)

    # ── Possessive pronouns → "<entity_type> <entity_id>'s" ──────────────────
    possessive_ref = f"{id_ref}'s"
    for pron in ("his", "her", "their", "its"):
        msg = re.sub(rf"\b{pron}\b", possessive_ref, msg, flags=re.IGNORECASE)

    # ── Subject / object pronouns → "<entity_type> <entity_id>" ─────────────
    for pron in ("he", "she", "they", "him", "them", "it"):
        msg = re.sub(rf"\b{pron}\b", id_ref, msg, flags=re.IGNORECASE)

    return msg.strip()


def entity_resolver_node(state: dict) -> dict:
    """Resolve pronoun follow-ups and store newly mentioned entities.

    Mutates ``user_message`` in state (keeping original in ``original_message``)
    when a pronoun is resolved.  Otherwise returns state unchanged.
    """
    from app.services.config_service import config_svc
    if not config_svc.get_bool("graph.enable_entity_resolver", True):
        return state
    message   = state.get("user_message", "")
    thread_id = state.get("thread_id", "")
    steps     = list(state.get("reasoning_steps") or [])

    # ── 1. Does the message contain an explicit entity ID? ───────────────────
    #    If so, store it and pass through — no rewriting needed.
    id_match = _ENTITY_ID_RE.search(message)
    if id_match:
        raw_id = id_match.group(0).upper()
        etype  = _entity_type_from_id(raw_id)
        store_entity(thread_id, etype, raw_id, "")
        steps.append(
            f"Entity resolver: detected {etype} {raw_id} in message — stored in thread memory."
        )
        return {
            **state,
            "reasoning_steps": steps,
            "last_entity":     {"entity_type": etype, "entity_id": raw_id, "entity_name": ""},
        }

    # ── 2. Does the message use pronouns / demonstratives? ───────────────────
    if not _PRONOUN_RE.search(message):
        last_entity = get_last_entity(thread_id) or {}
        return {**state, "reasoning_steps": steps, "last_entity": last_entity}

    # ── 3. Resolve pronoun against the most-recently stored entity ───────────
    last_entity = get_last_entity(thread_id)
    if not last_entity:
        steps.append(
            "Entity resolver: pronoun detected but no prior entity in thread memory — "
            "cannot resolve.  Passing original message to planner."
        )
        return {**state, "reasoning_steps": steps, "last_entity": {}}

    rewritten = _rewrite_with_entity(message, last_entity)
    steps.append(
        f"Entity resolver: pronoun resolved — "
        f"{last_entity['entity_type']} {last_entity['entity_id']}. "
        f"'{message}'  →  '{rewritten}'"
    )
    return {
        **state,
        "user_message":    rewritten,
        "original_message": message,
        "resolved_entity": last_entity,
        "last_entity":     last_entity,
        "reasoning_steps": steps,
    }
