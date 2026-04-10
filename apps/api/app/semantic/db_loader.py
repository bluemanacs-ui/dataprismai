"""
Dynamic semantic catalog loader.

Reads the five StarRocks metadata tables at startup and merges them with the
hardcoded keyword catalog so that:

  - New metrics added to semantic_glossary_metrics appear automatically.
  - All 26 column-mapped dimensions from semantic_dimension_mapping are available.
  - Domain routing from domain_semantic_mapping is respected.
  - Persona-level access rules from semantic_access_control are enforced.

Falls back to the unmodified hardcoded catalog if StarRocks is unreachable.
"""

import copy
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain / category → NL keyword expansions
# (the DB has no keyword column; these augment auto-generated word splits)
# ---------------------------------------------------------------------------
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "spend": [
        "spend", "spending", "purchase", "transaction amount", "expenditure",
        "volume", "sales", "category spend", "how much spent",
    ],
    "risk": [
        # NOTE: delinquency/overdue keywords intentionally omitted here — they are
        # too specific and cause false-positive matches with generic risk metrics
        # (e.g. 'Transaction Decline Rate' matching 'delinquency rate' queries).
        # Delinquency keywords live only on the hardcoded 'Delinquency Rate' metric.
        "fraud", "fraudulent", "suspicious", "risk", "decline", "dpd", "chargeback",
    ],
    "payments": [
        "payment", "paid", "overdue", "minimum payment", "outstanding",
        "due", "billing", "amount due", "repayment",
    ],
    "customer": [
        "customer", "credit score", "segment", "profile", "balance",
        "utilization", "kyc", "who is", "customer details",
    ],
    "portfolio": [
        "portfolio", "kpi", "npl", "non-performing", "churn", "growth",
        "board", "executive", "monthly report", "interest income",
    ],
    "transactions": [
        "transaction", "transactions", "txn", "approved", "declined",
        "channel", "transaction count", "transaction volume",
    ],
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "volume": ["count", "number", "total", "how many"],
    "fraud": ["fraud", "fraudulent", "suspicious", "scam", "alert"],
    "risk": ["risk", "overdue", "late", "delinquent", "past due"],
    "exposure": ["balance", "outstanding", "limit", "available credit"],
    "behavior": ["pattern", "trend", "average", "typical"],
    "performance": ["rate", "ratio", "percentage"],
    "debt": ["owe", "due", "minimum", "payment"],
    "profitability": ["revenue", "income", "profit", "earning"],
}


def _words_from_name(name: str) -> list[str]:
    return [w.lower() for w in name.replace("_", " ").split() if len(w) > 2]


def _build_metric_keywords(m: dict) -> list[str]:
    kws: set[str] = set()
    kws.update(_words_from_name(m.get("metric_name", "")))
    kws.update(_words_from_name(m.get("display_name", "")))
    kws.update(_DOMAIN_KEYWORDS.get(m.get("domain", ""), []))
    kws.update(_CATEGORY_KEYWORDS.get(m.get("category", ""), []))
    return sorted(kws)


def _build_dimension_keywords(d: dict) -> list[str]:
    kws: set[str] = set()
    kws.update(_words_from_name(d.get("dimension_name", "")))
    kws.update(_words_from_name(d.get("display_label", "")))
    return sorted(kws)


# ---------------------------------------------------------------------------
# DB fetchers
# ---------------------------------------------------------------------------

def _get_connection():
    import mysql.connector
    from app.core.config import settings
    return mysql.connector.connect(
        host=settings.starrocks_host,
        port=settings.starrocks_port,
        user=settings.starrocks_user,
        password=settings.starrocks_password,
        database=settings.starrocks_database,
        connection_timeout=5,
    )


def _fetch_glossary_metrics(cursor) -> list[dict]:
    cursor.execute(
        "SELECT metric_id, metric_name, metric_definition, metric_formula, "
        "grain, source_table, domain, is_kpi "
        "FROM cc_analytics.semantic_glossary_metrics"
    )
    rows = cursor.fetchall()
    result = []
    for m in rows:
        src = m.get("source_table") or ""
        if src and not src.startswith("cc_analytics."):
            src = f"cc_analytics.{src}"
        result.append({
            "name": m["metric_name"],
            "metric_key": m["metric_name"],
            "keywords": _build_metric_keywords(m),
            "dimensions": [],
            "engine": "starrocks",
            "domain": m["domain"] or "",
            "definition": m["metric_definition"] or "",
            "source_table": src,
            "formula": m["metric_formula"] or "",
            "category": m["domain"] or "",
        })
    return result


def _fetch_dimension_mappings(cursor) -> list[dict]:
    cursor.execute(
        "SELECT dimension_name, source_table, source_column, display_label, "
        "dimension_type, is_filterable, is_groupable "
        "FROM cc_analytics.semantic_dimension_mapping"
    )
    rows = cursor.fetchall()
    result = []
    for d in rows:
        result.append({
            "name": d["dimension_name"],
            "display_label": d["display_label"] or d["dimension_name"],
            "source_table": d["source_table"] or "",
            "source_column": d["source_column"] or "",
            "dimension_type": d["dimension_type"] or "categorical",
            "is_filterable": bool(d["is_filterable"]),
            "is_groupable": bool(d["is_groupable"]),
            "keywords": _build_dimension_keywords(d),
        })
    return result


def _fetch_domain_routing(cursor) -> dict[str, list[str]]:
    cursor.execute(
        "SELECT domain, semantic_table "
        "FROM cc_analytics.domain_semantic_mapping ORDER BY domain"
    )
    routing: dict[str, list[str]] = {}
    for row in cursor.fetchall():
        routing.setdefault(row["domain"], []).append(row["semantic_table"])
    return routing


def _fetch_access_control(cursor) -> dict[str, list[dict]]:
    try:
        cursor.execute(
            "SELECT persona, semantic_table, can_access, country_filter, "
            "restricted_columns, max_row_limit "
            "FROM cc_analytics.semantic_access_control"
        )
        result: dict[str, list[dict]] = {}
        for r in cursor.fetchall():
            restricted = [
                c.strip()
                for c in (r["restricted_columns"] or "").split(",")
                if c.strip() and c.strip().lower() not in ("none", "")
            ]
            result.setdefault(r["persona"], []).append({
                "semantic_table": r["semantic_table"],
                "can_access": bool(r["can_access"]),
                "country_filter": r["country_filter"] or None,
                "restricted_columns": restricted,
                "max_row_limit": r["max_row_limit"] or 1000,
            })
        return result
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Module-level cache — populated once on first call
_CATALOG_CACHE: Optional[dict] = None
_ACCESS_CONTROL_CACHE: Optional[dict] = None


def load_catalog_from_db() -> Optional[dict]:
    """
    Load raw catalog from DB (no merge with hardcoded).
    Returns None if StarRocks is unreachable.
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(dictionary=True)
        metrics = _fetch_glossary_metrics(cur)
        dimensions = _fetch_dimension_mappings(cur)
        domain_routing = _fetch_domain_routing(cur)
        conn.close()
        logger.info(
            "Loaded DB catalog: %d metrics, %d dimensions", len(metrics), len(dimensions)
        )
        return {"metrics": metrics, "dimensions": dimensions, "domain_routing": domain_routing}
    except Exception as exc:
        logger.warning("Could not load semantic catalog from DB: %s", exc)
        return None


def get_access_rules(persona: str) -> list[dict]:
    """
    Return access rules for the given persona.
    Returns an empty list (= allow all) if DB is unreachable or persona not found.
    Each rule: {semantic_table, can_access, country_filter, restricted_columns, max_row_limit}
    """
    global _ACCESS_CONTROL_CACHE
    if _ACCESS_CONTROL_CACHE is None:
        try:
            conn = _get_connection()
            cur = conn.cursor(dictionary=True)
            _ACCESS_CONTROL_CACHE = _fetch_access_control(cur)
            conn.close()
            logger.info("Loaded access control: %d personas", len(_ACCESS_CONTROL_CACHE))
        except Exception as exc:
            logger.warning("Could not load access control from DB: %s", exc)
            _ACCESS_CONTROL_CACHE = {}
    return _ACCESS_CONTROL_CACHE.get(persona, [])


def get_accessible_tables(persona: str) -> Optional[set[str]]:
    """
    Returns set of semantic table names the persona can access,
    or None if no rules found (= allow all).
    """
    rules = get_access_rules(persona)
    if not rules:
        return None  # no restrictions
    return {r["semantic_table"] for r in rules if r["can_access"]}


def get_row_limit_for_table(persona: str, table: str) -> int:
    """Return the max_row_limit for a persona/table combination. Default 1000."""
    for rule in get_access_rules(persona):
        if rule["semantic_table"] == table and rule["can_access"]:
            return rule["max_row_limit"]
    return 1000


def build_merged_catalog(hardcoded: dict) -> dict:
    """
    Merge live DB metadata into the hardcoded catalog:

      1. New metrics from semantic_glossary_metrics are added (hardcoded ones kept).
      2. New dimensions from semantic_dimension_mapping are added; existing hardcoded
         dimensions are enriched with source_table / source_column metadata.
      3. domain_routing dict is added from domain_semantic_mapping.

    Falls back to unmodified hardcoded if DB is unreachable.
    """
    db = load_catalog_from_db()
    if db is None:
        logger.info("Using hardcoded semantic catalog (DB unavailable)")
        return hardcoded

    result = copy.deepcopy(hardcoded)

    # ── Add new metrics from DB not already in hardcoded ─────────────────────
    existing_names_lower = {m["name"].lower() for m in result["metrics"]}
    added_metrics = 0
    for db_m in db["metrics"]:
        if db_m["name"].lower() not in existing_names_lower:
            result["metrics"].append(db_m)
            existing_names_lower.add(db_m["name"].lower())
            added_metrics += 1

    # ── Enrich / add dimensions from DB ──────────────────────────────────────
    hc_dim_map = {d["name"].lower(): d for d in result["dimensions"]}
    added_dims = 0
    for db_d in db["dimensions"]:
        dn_lower = db_d["name"].lower()
        if dn_lower in hc_dim_map:
            # Augment existing dimension with column-level metadata
            hc_dim_map[dn_lower].setdefault("source_table", db_d.get("source_table", ""))
            hc_dim_map[dn_lower].setdefault("source_column", db_d.get("source_column", ""))
            hc_dim_map[dn_lower].setdefault("dimension_type", db_d.get("dimension_type", "categorical"))
        else:
            result["dimensions"].append(db_d)
            added_dims += 1

    # ── Add domain routing ────────────────────────────────────────────────────
    result["domain_routing"] = db.get("domain_routing", {})

    logger.info(
        "Merged catalog: %d metrics (+%d from DB), %d dimensions (+%d from DB)",
        len(result["metrics"]), added_metrics,
        len(result["dimensions"]), added_dims,
    )
    return result


def reload_catalog() -> None:
    """Force re-fetch from DB on next access (clears module-level caches)."""
    global _CATALOG_CACHE, _ACCESS_CONTROL_CACHE
    _CATALOG_CACHE = None
    _ACCESS_CONTROL_CACHE = None
