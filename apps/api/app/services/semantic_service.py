import re
from app.semantic.catalog import SEMANTIC_CATALOG
from app.semantic.db_loader import get_accessible_tables

# Raw table names in cc_analytics schema — queries referencing these go direct.
# This regex is rebuilt lazily from SchemaRegistry so new tables auto-register.
_RAW_TABLE_RE_STATIC = re.compile(
    r"\braw_(?:customer|transaction|card|account|payment|merchant|dispute|fraud_alert|statement|card_account)\b",
    re.IGNORECASE,
)


def _get_any_table_re() -> re.Pattern:
    """Return a live regex matching any known table name (raw_*, ddm_*, dp_*, audit_*, etc.)."""
    try:
        from app.services.schema_registry import registry
        return registry.table_name_regex()
    except Exception:
        return _RAW_TABLE_RE_STATIC

# Patterns that signal a row-level lookup / drill-down — NOT an aggregation query.
# When matched, bypass metric routing entirely and let the LLM build the SQL.
_ROW_LEVEL_RE = re.compile(
    r"\b("
    r"list|show me|show sample|show \d+|show all|show distinct|show|find|get|fetch|give me|display|print|return|pull|retrieve"
    r"|sample data|sample from|sample of|sample records|raw data|table data|raw table"
    r"|first \d+|first few|first record|last \d+|last record"
    r"|name starts? with|name like|whose name|called|named"
    r"|random \d+|random sample|sample \d+|pick \d+|select \d+"
    r"|all customers|every customer|individual|detail|full view|full profile"
    r"|phone|email|address|contact|account number|id|lookup"
    r"|top \d* customers?|top spending customers?|highest spending customers?"
    r"|biggest spenders?|who spend|who spent|who has the highest spend"
    r"|customer with|customers with|customers in|customers from|customers whose"
    r"|customer name|customer list|customer record"
    r")\b",
    re.IGNORECASE,
)

# Aggregation/analytics signals that SHOULD use metric routing
_AGGREGATION_RE = re.compile(
    r"\b(rate|ratio|average|avg|total|sum|trend|compare|breakdown|distribution)\b",
    re.IGNORECASE,
)


def _is_row_level_query(message: str) -> bool:
    """Return True when the message is clearly asking for individual rows, not aggregated metrics."""
    # Any direct table reference (raw_*, ddm_*, dp_*, audit_*, etc.) is always row-level
    if _get_any_table_re().search(message):
        return True
    has_row_intent = bool(_ROW_LEVEL_RE.search(message))
    has_agg_intent = bool(_AGGREGATION_RE.search(message))
    return has_row_intent and not has_agg_intent


def _score_keywords(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in text_lower)


def _load_intent_domain_keywords() -> dict[str, tuple[str, int]]:
    """Load intent_domain_mapping from StarRocks → {keyword: (domain, weight)}."""
    try:
        import mysql.connector
        from app.core.config import settings
        conn = mysql.connector.connect(
            host=settings.starrocks_host, port=settings.starrocks_port,
            user=settings.starrocks_user, password=settings.starrocks_password,
            database=settings.starrocks_database, connection_timeout=4,
        )
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT keyword, domain, weight FROM cc_analytics.intent_domain_mapping")
        result = {r["keyword"].lower(): (r["domain"], int(r["weight"])) for r in cur.fetchall()}
        conn.close()
        return result
    except Exception:
        return {}


# Module-level cache — loaded once
_INTENT_KW: dict[str, tuple[str, int]] = {}
_INTENT_KW_LOADED = False


def _get_intent_keywords() -> dict[str, tuple[str, int]]:
    global _INTENT_KW, _INTENT_KW_LOADED
    if not _INTENT_KW_LOADED:
        _INTENT_KW = _load_intent_domain_keywords()
        _INTENT_KW_LOADED = True
    return _INTENT_KW


def _domain_boost(message_lower: str, domain: str) -> float:
    """Sum of weights for intent_domain_mapping keywords matching this message for a domain."""
    total = 0.0
    for kw, (kw_domain, weight) in _get_intent_keywords().items():
        if kw_domain == domain and kw in message_lower:
            total += weight * 0.1  # scale so boost doesn't swamp keyword score
    return total


def resolve_semantic_context(message: str, persona: str) -> dict:
    raw_message = message.strip()
    message = raw_message.lower()

    # Row-level queries (list, find, random N, name starts with…) skip metric routing
    if _is_row_level_query(raw_message):
        return {
            "metric": "",
            "dimensions": [],
            "engine": "starrocks",
            "domain": "Credit Card Analytics",
            "definition": "",
            "persona": persona,
            "free_form": True,
        }

    metric_candidates = []
    # Resolve which semantic tables this persona may access (None = no restriction)
    allowed_tables = get_accessible_tables(persona)
    for metric in SEMANTIC_CATALOG["metrics"]:
        # Skip metrics whose source_table is blocked for this persona
        if allowed_tables is not None:
            src = metric.get("source_table", "").replace("cc_analytics.", "")
            if src and src not in allowed_tables:
                continue
        kw_score = _score_keywords(message, metric["keywords"])
        # Boost score using DB intent_domain_mapping weights for this metric's domain
        boost = _domain_boost(message, metric.get("domain", ""))
        score = kw_score + boost
        metric_candidates.append((score, metric))

    metric_candidates.sort(key=lambda item: item[0], reverse=True)
    best_score = metric_candidates[0][0] if metric_candidates else 0
    best_metric = metric_candidates[0][1] if best_score >= 1 else None

    matched_dimensions = []
    for dimension in SEMANTIC_CATALOG["dimensions"]:
        if _score_keywords(message, dimension["keywords"]) > 0:
            matched_dimensions.append(dimension["name"])

    if best_metric is None:
        return {
            "metric": "",
            "dimensions": matched_dimensions,
            "engine": "starrocks",
            "domain": "Credit Card Analytics",
            "definition": "",
            "persona": persona,
            "free_form": True,
        }

    return {
        "metric": best_metric["name"],
        "dimensions": matched_dimensions,
        "engine": best_metric["engine"],
        "domain": best_metric["domain"],
        "definition": best_metric["definition"],
        "persona": persona,
    }
