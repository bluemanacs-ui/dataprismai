"""Planner node — deterministic, rule-first intent classification.

Intent types:
  preview_data  — user wants to see literal rows from a specific table
  schema_query  — user wants the schema / column list for a table
  metric_query  — user wants aggregated metrics / KPIs
  insight_query — user wants narrative insight / summary / recommendation
  explanation   — user wants a concept explained
  report        — user wants to export / save a report

response_mode maps intent to render mode:
  preview_data  → "table"
  schema_query  → "schema"
  metric_query  → "metric"
  insight_query → "insight"
  explanation   → "insight"
  report        → "metric"
"""
import re
from app.services.schema_registry import registry as _schema_registry

# Patterns that strongly indicate a request for literal rows from a named table.
# Must include an explicit table-like name (containing underscore and alphanums).
_PREVIEW_VERBS_RE = re.compile(
    r"\b(preview|sample|show\s+(?:me\s+)?(?:\d+\s+)?(?:rows?|records?|data|entries)|"
    r"select\s+\*|display|fetch|pull|get|list|dump)\b",
    re.IGNORECASE,
)

# Schema / describe patterns
_SCHEMA_VERBS_RE = re.compile(
    r"\b(describe|desc(?:ribe)?|schema|columns?|fields?|structure|definition|metadata|"
    r"what\s+(?:columns?|fields?|attributes?))\b",
    re.IGNORECASE,
)

# Aggregation / metric patterns
_METRIC_VERBS_RE = re.compile(
    r"\b(total|count|rate|ratio|trend|average|avg|sum|breakdown|distribution|"
    r"compare|top\s+\d+|ranking|by\s+(?:country|region|segment|month|category|"
    r"merchant|product|channel|year|quarter|week))\b",
    re.IGNORECASE,
)

# Insight / narrative patterns
_INSIGHT_VERBS_RE = re.compile(
    r"\b(insight|summary|summari[sz]e|recommend|why|what\s+should|key\s+(?:issues?|insights?|findings?|"
    r"trends?|risks?)|analyse|analyze|portfolio\s+(?:health|performance)|focus\s+on)\b",
    re.IGNORECASE,
)

# Detect an explicit table name — built from config.graph.table_name_prefixes (or fallback static regex)
_TABLE_NAME_RE = re.compile(
    r"\b((raw|ddm|dp|semantic|audit)_[a-z][a-z0-9_]{2,}|[a-z][a-z0-9_]{2,}_mapping)\b",
    re.IGNORECASE,
)

# Default entity ID → table map (config-driven at runtime via _get_entity_map)
_DEFAULT_ENTITY_ID_TABLE_MAP: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\b(CUST_\w+)\b",  re.IGNORECASE), "raw_customers",    "customer_id"),
    (re.compile(r"\b(ACC_\w+)\b",   re.IGNORECASE), "raw_card_accounts", "account_id"),
    (re.compile(r"\b(CARD_\w+)\b",  re.IGNORECASE), "raw_cards",         "card_id"),
    (re.compile(r"\b(TXN_\w+)\b",   re.IGNORECASE), "raw_transactions",  "transaction_id"),
    (re.compile(r"\b(MERCH_\w+)\b", re.IGNORECASE), "raw_merchants",     "merchant_id"),
]


def _get_entity_map() -> list[tuple[re.Pattern, str, str]]:
    """Return entity ID map — uses the default map (config exposes prefixes for transparency)."""
    return _DEFAULT_ENTITY_ID_TABLE_MAP


_RESPONSE_MODE: dict[str, str] = {
    "preview_data": "table",
    "schema_query": "schema",
    "metric_query": "metric",
    "insight_query": "insight",
    "explanation": "insight",
    "report": "metric",
}


def _extract_literal_table(message: str) -> str | None:
    """Return the first known table name found in the message.

    Primary path: live SchemaRegistry regex — covers ALL objects in cc_analytics
    regardless of naming convention (semantic_*, dp_*, *_mapping, etc.).

    Fallback: static prefix/suffix regex — used when the registry is empty
    (e.g. first request before StarRocks is ready) so intent detection still works.
    """
    # Primary: registry-backed regex covers every known table name
    reg_rx = _schema_registry.table_name_regex()
    m = reg_rx.search(message)
    if m:
        return m.group(1).lower()
    # Fallback: static regex (handles startup window before registry is warm)
    m2 = _TABLE_NAME_RE.search(message)
    return m2.group(0).lower() if m2 else None


def planner_node(state: dict) -> dict:
    message = state.get("user_message", "")
    msg_lower = message.lower()

    literal_table = _extract_literal_table(message)
    entity_filter: dict | None = None

    # ── Rule 0: entity lookup — CUST_xxx, ACC_xxx, CARD_xxx, TXN_xxx, MERCH_xxx ─
    # Highest priority: structured entity IDs imply a direct row lookup in the
    # corresponding raw table, regardless of other verbs in the message.
    for id_re, id_table, id_col in _get_entity_map():
        m = id_re.search(message)
        if m:
            entity_filter = {"col": id_col, "val": m.group(1)}
            literal_table = id_table
            intent_type = "preview_data"
            break
    else:
        # ── Rule 1: schema_query — "describe raw_customer" / "what columns in …" ─
        if _SCHEMA_VERBS_RE.search(message) and literal_table:
            intent_type = "schema_query"

        # ── Rule 2: preview_data — explicit table + preview/show/list/select * ───
        elif literal_table and _PREVIEW_VERBS_RE.search(message):
            intent_type = "preview_data"

        # ── Rule 3: bare table reference with no aggregation / insight signal ────
        # e.g. "raw_customer" or "show dp_risk_signals" without metric words
        elif literal_table and not _METRIC_VERBS_RE.search(message) and not _INSIGHT_VERBS_RE.search(message):
            intent_type = "preview_data"

        # ── Rule 4: insight / narrative ──────────────────────────────────────────
        elif _INSIGHT_VERBS_RE.search(message):
            intent_type = "insight_query"

        # ── Rule 5: aggregation / metric ─────────────────────────────────────────
        elif _METRIC_VERBS_RE.search(message):
            intent_type = "metric_query"

        # ── Rule 6: schema words WITHOUT a table name — could be concept explain ─
        elif _SCHEMA_VERBS_RE.search(message):
            intent_type = "explanation"

        # ── Rule 7: report / export ──────────────────────────────────────────────
        elif any(w in msg_lower for w in ("save", "report", "export")):
            intent_type = "report"

        # ── Default: metric query (current system behaviour) ─────────────────────
        else:
            intent_type = "metric_query"

    response_mode = _RESPONSE_MODE.get(intent_type, "metric")

    steps = list(state.get("reasoning_steps") or [])
    tbl_note = f" (table: {literal_table})" if literal_table else ""
    entity_note = f", entity_filter={entity_filter['col']}={entity_filter['val']}" if entity_filter else ""
    steps.append(f"Planner: intent={intent_type}, response_mode={response_mode}{tbl_note}{entity_note}.")

    return {
        **state,
        "intent": intent_type,          # legacy field kept for backwards compat
        "intent_type": intent_type,
        "response_mode": response_mode,
        "literal_table_name": literal_table or "",
        "entity_filter": entity_filter,
        "reasoning_steps": steps,
    }

