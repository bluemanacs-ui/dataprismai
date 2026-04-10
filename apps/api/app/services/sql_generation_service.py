from app.schemas.sql import SQLGenerationResult
from app.prompts.sql_prompt_builder import build_sql_prompt, _STATIC_SCHEMA_CONTEXT
from app.services.llm_service import generate_with_ollama
from app.services.response_parser import parse_model_json
from app.services.vanna_service import vanna_service
from app.services.schema_registry import registry as _schema_registry
from app.semantic.catalog import METRIC_CANONICAL_SQL, METRIC_SQL_BY_DIMENSION
import logging
import re

logger = logging.getLogger(__name__)


def _enrich_with_dictionary(semantic_context: dict) -> None:
    """Fetch table + column definitions from dic_tables/dic_columns and inject
    into semantic_context["dictionary_context"] for LLM-mode prompts.
    Falls back to SchemaRegistry live DESCRIBE data (accurate column names) then
    static schema context when StarRocks is unreachable.
    No-ops if dictionary_context is already populated (avoids double-fetch)."""
    if semantic_context.get("dictionary_context"):
        return
    try:
        import os, mysql.connector
        conn = mysql.connector.connect(
            host=os.getenv("STARROCKS_HOST", "localhost"),
            port=int(os.getenv("STARROCKS_PORT", "9030")),
            user=os.getenv("STARROCKS_USER", "root"),
            password=os.getenv("STARROCKS_PASSWORD", ""),
            database=os.getenv("STARROCKS_DATABASE", "cc_analytics"),
            connection_timeout=5,
        )
        cur = conn.cursor(dictionary=True)
        # Use GROUP BY to deduplicate in case seed was run multiple times
        cur.execute("""
            SELECT table_name, MAX(display_name) display_name, MAX(description) description,
                   MAX(layer) layer, MAX(domain) domain
            FROM dic_tables WHERE is_active=1
            GROUP BY table_name ORDER BY MAX(layer), table_name
        """)
        tables = cur.fetchall()
        cur.execute("""
            SELECT table_name, column_name, MAX(display_name) display_name,
                   MAX(description) description, MAX(data_type) data_type,
                   MAX(enum_values) enum_values, MAX(business_rule) business_rule
            FROM dic_columns
            GROUP BY table_name, column_name ORDER BY table_name, MIN(column_id)
        """)
        columns = cur.fetchall()
        cur.execute("""
            SELECT from_table, from_column, to_table, to_column,
                   MAX(relationship_type) relationship_type, MAX(description) description
            FROM dic_relationships
            GROUP BY from_table, from_column, to_table, to_column ORDER BY from_table
        """)
        relationships = cur.fetchall()
        conn.close()
        if not tables:
            raise Exception("dic_tables is empty — using live schema fallback")
        # Build compact text representation
        col_map: dict[str, list] = {}
        for c in columns:
            col_map.setdefault(c["table_name"], []).append(c)
        lines = [
            "Database: cc_analytics (StarRocks / MySQL-compatible)",
            "Countries: SG (Singapore/SGD), MY (Malaysia/MYR), IN (India/INR)",
            "Data covers 2025 full year (Jan–Dec 2025)",
            "",
        ]
        for t in tables:
            tname = t["table_name"]
            lines.append(f"\n### {tname} ({t['layer']}/{t['domain']}) — {t['description']}")
            for c in col_map.get(tname, []):
                note = c.get("business_rule") or c.get("enum_values") or ""
                lines.append(f"  - {c['column_name']} {c['data_type']}: {c['description']}" + (f"  [{note}]" if note else ""))
        # Supplement with SchemaRegistry for any table not in dic but with live columns
        try:
            live_tables = _schema_registry.all_tables()
            dic_names = {t["table_name"] for t in tables}
            extra = {k: v for k, v in live_tables.items()
                     if k not in dic_names and v["category"] in ("semantic", "dp", "ddm", "raw")
                     and v["columns"]}
            if extra:
                lines.append("\n### Additional Tables (from live schema)")
                for tname, meta in sorted(extra.items()):
                    lines.append(f"\n{tname}: {', '.join(meta['columns'])}")
        except Exception:
            pass
        # Append relationship / FK model
        if relationships:
            lines.append("\n### Data Model Relationships (use for JOINs)")
            for r in relationships:
                desc = f"  {r['description']}" if r.get("description") else ""
                lines.append(f"  {r['from_table']}.{r['from_column']} → {r['to_table']}.{r['to_column']}  [{r['relationship_type']}]{desc}")
        semantic_context["dictionary_context"] = "\n".join(lines)
    except Exception as exc:
        # Fallback 1: use SchemaRegistry's live DESCRIBE data (accurate exact column names)
        try:
            live_ctx = _schema_registry.build_schema_context()
            if live_ctx and len(live_ctx) > 100:
                logger.info("_enrich_with_dictionary: using SchemaRegistry live schema (%s)", exc)
                semantic_context["dictionary_context"] = live_ctx
                return
        except Exception as reg_exc:
            logger.warning("_enrich_with_dictionary: SchemaRegistry also failed: %s", reg_exc)
        # Fallback 2: static compiled schema context (last resort)
        logger.warning("_enrich_with_dictionary: injecting static schema context (%s)", exc)
        semantic_context["dictionary_context"] = _STATIC_SCHEMA_CONTEXT



def _known_tables() -> frozenset[str]:
    """Live set of all queryable table names from SchemaRegistry."""
    return _schema_registry.known_table_names()


def _any_table_regex() -> re.Pattern:
    """Live regex matching any known table name in user messages."""
    return _schema_registry.table_name_regex()


def _tables_by_category(category: str) -> dict:
    return _schema_registry.tables_by_category(category)


# Detects an explicit snake_case object name after "for/from/in/of/table/view"
_EXPLICIT_TABLE_RE = re.compile(
    r"\b(?:for|from|in|of|table|view|object|dataset|source)\s+([a-z][a-z0-9_]{3,})",
    re.IGNORECASE,
)


def _unknown_table_sql(message: str) -> str | None:
    """If the query references an explicit snake_case name that isn't a known table,
    return a sentinel SQL so response_node can give a helpful 'not found' message."""
    known = _known_tables()
    for m in _EXPLICIT_TABLE_RE.finditer(message.lower()):
        name = m.group(1).lower()
        _SKIP = {"the", "all", "any", "this", "that", "each", "top", "data",
                 "customer", "customers", "segment", "rate", "count", "card",
                 "account", "transaction", "merchant", "payment", "fraud"}
        if name in _SKIP:
            continue
        if ("_" in name or len(name) > 10) and name not in known:
            return f"SELECT 'Table or view \'{name}\' was not found in this system.' AS not_found"
    return None


_COUNT_INTENT_RE = re.compile(
    r"\b(count|how many|total count|number of records?|how much|total records?|row count|size of)\b",
    re.IGNORECASE,
)

_DISTINCT_COL_RE = re.compile(
    r"\bdistinct\s+(\w+)",
    re.IGNORECASE,
)


def _direct_table_sql(message: str) -> str | None:
    """
    If the message explicitly names any known table (raw_*, ddm_*, dp_*, audit_*, etc.),
    generate simple SELECT SQL without the LLM.
    Respects COUNT/DISTINCT intents.
    """
    pattern = _any_table_regex()
    m = pattern.search(message)
    if not m:
        return None
    table_key = m.group(1).lower()
    table_meta = _schema_registry.get_table(table_key)
    if not table_meta:
        return None
    qualified = table_meta["qualified"]

    # COUNT intent
    if _COUNT_INTENT_RE.search(message):
        dist_m = _DISTINCT_COL_RE.search(message)
        if dist_m:
            col = dist_m.group(1)
            # Validate col exists
            if col in table_meta["columns"] or col in ("*",):
                return f"SELECT COUNT(DISTINCT {col}) AS distinct_{col}_count FROM {qualified}"
        return f"SELECT COUNT(*) AS total_count FROM {qualified}"

    # Default: SELECT * with limit
    limit_m = re.search(r"\b(\d+)\b", message)
    limit = min(int(limit_m.group(1)), 200) if limit_m else 20
    return f"SELECT * FROM {qualified} LIMIT {limit}"


# Phrases that indicate the user wants a specific grouping/ranking
_GROUPING_INTENT_RE = re.compile(
    r"\b(which|who|what|highest|lowest|most|least|top|bottom|rank|compare|comparison|breakdown|per |by |across |between|split)\b",
    re.IGNORECASE,
)

# Maps words found in "by <X>" phrases to canonical dimension names
_GROUPING_TO_DIM = {
    "country": "Geography", "countries": "Geography", "country code": "Geography",
    "geography": "Geography", "region": "Geography", "location": "Geography",
    "merchant": "Merchant Category", "merchant category": "Merchant Category",
    "merchant type": "Merchant Category", "category": "Merchant Category",
    "mcc": "Merchant Category",
    "segment": "Segment", "customer segment": "Segment", "customer type": "Segment",
    "tier": "Segment", "risk tier": "Segment",
    "product type": "Segment", "product category": "Segment", "product": "Segment",
    "card type": "Segment", "card product": "Segment", "card tier": "Segment",
    "account type": "Segment",
    "channel": "Channel",
    "age band": "Age Band", "age group": "Age Band", "age": "Age Band",
    "overdue bucket": "Overdue Bucket", "dpd bucket": "Overdue Bucket",
    "legal entity": "Legal Entity", "entity": "Legal Entity",
}


def _has_grouping_intent(message: str) -> bool:
    return bool(_GROUPING_INTENT_RE.search(message))


# ---------------------------------------------------------------------------
# Pre-LLM analytical patterns for cross-table queries the LLM gets wrong
# ---------------------------------------------------------------------------
# Each entry: (compiled_regex, sql_template)
# sql_template may contain {limit} which is filled from the message.
# IMPORTANT: more-specific semantic-table patterns must appear BEFORE
# generic raw-table patterns so they match first.
_ANALYTICAL_PATTERNS: list[tuple] = [
    # ── Semantic table patterns (correct columns, always work) ───────────────

    # Monthly transaction trend (use raw_deposit_transaction — most rows, best perf)
    (
        re.compile(
            r"\b(monthly|month.?by.?month|trend)\b.{0,60}\b(transaction|txn|volume|count|spend)\b"
            r"|\b(transaction|txn|volume|spend)\b.{0,60}\b(trend|monthly|by.?month|over.?time)\b"
            r"|\b(how|show|what)\b.{0,30}\b(transaction|txn|volume)\b.{0,40}\b(over.?time|each.?month|per.?month|monthly|trend)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT DATE_FORMAT(txn_date, '%Y-%m') AS txn_month, country_code,"
            " COUNT(*) AS txn_count,"
            " ROUND(SUM(amount), 0) AS total_amount,"
            " ROUND(AVG(amount), 2) AS avg_txn_amount"
            " FROM cc_analytics.raw_deposit_transaction"
            " GROUP BY DATE_FORMAT(txn_date, '%Y-%m'), country_code"
            " ORDER BY txn_month ASC"
        ),
    ),

    # Suspicious transactions by merchant category
    (
        re.compile(
            r"\b(suspicious|is_suspicious|suspect)\b.{0,80}\b(merchant.?categor\w*|categor\w+)\b"
            r"|\b(merchant.?categor\w*|categor\w+)\b.{0,80}\b(suspicious|suspect).{0,40}\b(transaction|volume|count)\b"
            r"|\b(top|most)\b.{0,30}\b(merchant.?categor\w*|categor\w+)\b.{0,80}\b(suspicious|suspect)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT merchant_category, COUNT(*) AS suspicious_count,"
            " ROUND(SUM(amount), 0) AS total_amount,"
            " ROUND(AVG(fraud_score), 3) AS avg_fraud_score"
            " FROM cc_analytics.semantic_transaction_summary"
            " WHERE is_suspicious = 1"
            " GROUP BY merchant_category"
            " ORDER BY suspicious_count DESC"
            " LIMIT {limit}"
        ),
    ),
    # Fraud transactions by merchant category
    (
        re.compile(
            r"\b(fraud|is_fraud|confirmed.?fraud)\b.{0,60}\b(merchant.?categor\w*|categor\w+)\b"
            r"|\b(merchant.?categor\w*|categor\w+)\b.{0,60}\b(fraud).{0,40}\b(transaction|volume|count|rate|amount)\b"
            r"|\b(top|most)\b.{0,30}\b(merchant.?categor\w*|categor\w+)\b.{0,60}\b(fraud)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT merchant_category, COUNT(*) AS fraud_count,"
            " ROUND(SUM(amount), 0) AS fraud_amount,"
            " ROUND(AVG(fraud_score), 3) AS avg_fraud_score"
            " FROM cc_analytics.semantic_transaction_summary"
            " WHERE is_fraud = 1"
            " GROUP BY merchant_category"
            " ORDER BY fraud_count DESC"
            " LIMIT {limit}"
        ),
    ),
    # Fraud rate by country / country fraud breakdown
    (
        re.compile(
            r"\b(fraud.?rate|fraud.?trend|fraud.?level)\b.{0,60}\b(country|countries|country.?code|nation|region)\b"
            r"|\b(country|countries)\b.{0,60}\b(fraud.?rate|fraud.?trend|highest.?fraud|fraud.?breakdown)\b"
            r"|\b(which|what)\b.{0,30}\b(country|countries)\b.{0,60}\b(fraud|highest.?fraud|most.?fraud)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT country_code, customer_segment,"
            " SUM(fraud_txn) AS fraud_txn_count,"
            " SUM(total_txn) AS total_txn,"
            " ROUND(AVG(fraud_rate) * 100, 3) AS avg_fraud_rate_pct,"
            " ROUND(AVG(avg_fraud_score), 3) AS avg_fraud_score"
            " FROM cc_analytics.semantic_risk_metrics"
            " GROUP BY country_code, customer_segment"
            " ORDER BY avg_fraud_rate_pct DESC"
            " LIMIT {limit}"
        ),
    ),
    # Decline reasons breakdown
    (
        re.compile(
            r"\b(decline.?reason|declined.?reason|reason.{0,10}declin|why.{0,20}declin)\b"
            r"|\b(declin\w+)\b.{0,40}\b(breakdown|split|distribution|by.?reason|reason)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT decline_reason, COUNT(*) AS declined_count,"
            " ROUND(SUM(amount), 0) AS declined_amount"
            " FROM cc_analytics.semantic_transaction_summary"
            " WHERE is_declined = 1 AND decline_reason IS NOT NULL"
            " GROUP BY decline_reason"
            " ORDER BY declined_count DESC"
        ),
    ),
    # Transaction breakdown by channel
    (
        re.compile(
            r"\b(channel)\b.{0,60}\b(fraud|decline|transaction|spend|volume|breakdown|split)\b"
            r"|\b(fraud|decline|transaction|spend)\b.{0,40}\b(by.?channel|per.?channel|across.?channel|channel.?breakdown)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT channel,"
            " COUNT(*) AS total_txn,"
            " SUM(is_fraud) AS fraud_count,"
            " SUM(is_declined) AS declined_count,"
            " ROUND(SUM(amount), 0) AS total_amount,"
            " ROUND(100.0 * SUM(is_fraud) / COUNT(*), 3) AS fraud_rate_pct"
            " FROM cc_analytics.semantic_transaction_summary"
            " GROUP BY channel"
            " ORDER BY total_txn DESC"
        ),
    ),
    # Overdue / at-risk customers
    (
        re.compile(
            r"\b(overdue|past.?due|delinquent|late.?payment|missed.?payment|at.?risk)\b.{0,60}\b(customer|customers|account|accounts)\b"
            r"|\b(customer|customers|account|accounts)\b.{0,40}\b(overdue|past.?due|delinquent|late.?payment)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT customer_name, country_code, customer_segment,"
            " payment_status, overdue_bucket, overdue_days,"
            " ROUND(total_due, 0) AS total_due,"
            " ROUND(amount_still_owed, 0) AS amount_still_owed,"
            " consecutive_late_months"
            " FROM cc_analytics.semantic_payment_status"
            " WHERE payment_status IN ('overdue', 'paid_minimum') OR overdue_days > 0"
            " ORDER BY amount_still_owed DESC"
            " LIMIT {limit}"
        ),
    ),
    # Payment status breakdown
    (
        re.compile(
            r"\b(payment.?status|payment.?breakdown|payment.?distribution|how.{0,20}paid)\b"
            r"|\b(paid.?full|paid.?partial|minimum.?due|overdue.?bucket)\b.{0,40}\b(breakdown|split|count|summary)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT payment_status,"
            " COUNT(*) AS account_count,"
            " ROUND(SUM(total_due), 0) AS total_due,"
            " ROUND(SUM(amount_still_owed), 0) AS amount_still_owed"
            " FROM cc_analytics.semantic_payment_status"
            " GROUP BY payment_status"
            " ORDER BY account_count DESC"
        ),
    ),
    # Portfolio KPIs
    (
        re.compile(
            r"\b(portfolio.?kpis?\b|portfolio.?health|portfolio.?metric|portfolio.?performance)\b"
            r"|\b(utilization|delinquency.?rate|full.?payment.?rate|npl.?rate|churn.?rate)\b.{0,60}\b(country|month|quarter|trend|by)\b"
            r"|\bportfolio\b.{0,30}\b(kpis?|health|metric|performance|summary)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT kpi_month, country_code,"
            " total_customers, active_customers,"
            " ROUND(total_spend_volume, 0) AS total_spend,"
            " ROUND(spend_growth_pct * 100, 2) AS spend_growth_pct,"
            " ROUND(avg_utilization_pct * 100, 2) AS avg_utilization_pct,"
            " ROUND(fraud_rate * 100, 3) AS fraud_rate_pct,"
            " ROUND(delinquency_rate * 100, 3) AS delinquency_rate_pct,"
            " ROUND(full_payment_rate * 100, 2) AS full_payment_rate_pct,"
            " ROUND(estimated_interest_income, 0) AS est_interest_income"
            " FROM cc_analytics.semantic_portfolio_kpis"
            " ORDER BY kpi_month DESC, country_code"
            " LIMIT {limit}"
        ),
    ),
    # Top spending customers (semantic_spend_metrics — aggregated by year_month)
    (
        re.compile(
            r"\b(top|highest|biggest|most)\b.{0,20}\b(spend|spending|spender|spent)\b.{0,20}\b(customer|customers)\b"
            r"|\b(customer|customers|who)\b.{0,30}\b(highest|most|top)\b.{0,10}\b(spend|spending|spent)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT customer_id, country_code, customer_segment,"
            " ROUND(SUM(total_spend), 0) AS total_spend,"
            " SUM(total_transactions) AS txn_count,"
            " top_category"
            " FROM cc_analytics.semantic_spend_metrics"
            " GROUP BY customer_id, country_code, customer_segment, top_category"
            " ORDER BY total_spend DESC"
            " LIMIT {limit}"
        ),
    ),
    # Spend by category
    (
        re.compile(
            r"\b(spend|spending|spent|total.?spend)\b.{0,50}\b(merchant.?categor\w*|categor\w+)\b"
            r"|\b(merchant.?categor\w*|categor\w+)\b.{0,50}\b(spend|spending|spent|breakdown|split)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT country_code, customer_segment,"
            " ROUND(SUM(food_dining_spend), 0) AS food_dining,"
            " ROUND(SUM(shopping_retail_spend), 0) AS retail_shopping,"
            " ROUND(SUM(travel_transport_spend), 0) AS travel_transport,"
            " ROUND(SUM(entertainment_spend), 0) AS entertainment,"
            " ROUND(SUM(utilities_spend), 0) AS utilities,"
            " ROUND(SUM(healthcare_spend), 0) AS healthcare,"
            " ROUND(SUM(other_spend), 0) AS other"
            " FROM cc_analytics.semantic_spend_metrics"
            " GROUP BY country_code, customer_segment"
            " ORDER BY country_code"
        ),
    ),

    # ── Raw table patterns (fixed column names) — fallback for direct raw queries ─

    # Customers by deposit account count (no card tables in deposit banking)
    (
        re.compile(
            r"\b(customer|customers|who|people|person)\b.{0,50}\b(card|cards|number of card|most card|high.*card|multi.*card)\b"
            r"|\b(high|most|more|top|many|highest|multiple)\b.{0,20}\b(card|cards)\b.{0,30}\b(customer|customers)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT account_id, customer_id, deposit_type,"
            " current_balance, currency_code, status"
            " FROM cc_analytics.raw_deposit_account"
            " ORDER BY current_balance DESC"
            " LIMIT {limit}"
        ),
    ),
    # Customers by transaction count
    (
        re.compile(
            r"\b(customer|customers|who)\b.{0,50}\b(most transaction|highest transaction|high.*transaction|active|number of transaction|many transaction)\b"
            r"|\b(top|most|high) transact.{0,30}\b(customer|customers)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT full_name, customer_segment, country_code,"
            " COUNT(*) AS txn_count,"
            " ROUND(SUM(amount), 0) AS total_spend"
            " FROM cc_analytics.semantic_transaction_summary"
            " GROUP BY full_name, customer_segment, country_code"
            " ORDER BY txn_count DESC"
            " LIMIT {limit}"
        ),
    ),
    # Spend trends over time (monthly)
    (
        re.compile(
            r"\b(spend.?trend|spending.?trend|trend.{0,20}spend|monthly.?spend|spend.{0,20}over.?time)"
            r"|\b(analyse|analyze)\b.{0,40}\b(spend|spending|expenditure)\b"
            r"|\b(spend|spending)\b.{0,40}\b(analys|pattern|summary|overview|recommend)",
            re.IGNORECASE,
        ),
        (
            "SELECT DATE_FORMAT(txn_date, '%Y-%m') AS month,"
            " COUNT(*) AS transaction_count,"
            " ROUND(SUM(amount), 2) AS total_spend,"
            " ROUND(AVG(amount), 2) AS avg_transaction_amount,"
            " COUNT(DISTINCT customer_id) AS unique_customers"
            " FROM cc_analytics.raw_deposit_transaction"
            " WHERE txn_date IS NOT NULL"
            " GROUP BY month"
            " ORDER BY month DESC"
            " LIMIT 24"
        ),
    ),
    # Merchants by transaction count (not by category — explicit merchant names)
    (
        re.compile(
            r"\b(merchant|merchants)\b.{0,50}\b(most transaction|highest transaction|active|busiest)\b"
            r"|\b(busiest)\b.{0,20}\b(merchant|merchants)\b",
            re.IGNORECASE,
        ),
        (
            "SELECT merchant_name, merchant_category,"
            " COUNT(*) AS txn_count,"
            " ROUND(SUM(amount), 0) AS total_amount"
            " FROM cc_analytics.semantic_transaction_summary"
            " GROUP BY merchant_name, merchant_category"
            " ORDER BY txn_count DESC"
            " LIMIT {limit}"
        ),
    ),
]


_HIGH_INTENT_RE = re.compile(
    r"\b(high|highest|most|top|more than|greater|many|maximum|max)\b",
    re.IGNORECASE,
)


def _analytical_pattern_sql(message: str) -> str | None:
    """Check pre-defined analytical patterns before falling back to LLM."""
    explicit_limit_m = re.search(r"\b(?:top|first|limit)\s*(\d+)\b|\bshow\s+(\d+)\b", message, re.IGNORECASE)
    explicit_limit = None
    if explicit_limit_m:
        explicit_limit = min(int(explicit_limit_m.group(1) or explicit_limit_m.group(2)), 500)

    high_intent = bool(_HIGH_INTENT_RE.search(message))

    for pattern, sql_tpl in _ANALYTICAL_PATTERNS:
        if pattern.search(message):
            # Honour explicit limit or cap at 500 for high-intent "show all" queries
            limit = explicit_limit or (500 if high_intent else 20)
            sql = sql_tpl.format(limit=limit)
            return sql
    return None


def _extract_explicit_grouping_dim(message: str) -> str | None:
    """
    Pull the user's explicit 'by X' / 'per X' / 'segment by X' grouping out of
    the message and map it to a canonical dimension name.
    Returns None if no explicit grouping target is found.
    """
    msg = message.lower()
    # Patterns: "segment by/as <X>", "by <X>", "per <X>", "grouped by <X>",
    #           "across <X>", "among <X>", "between <X>"
    candidates = re.findall(
        r'(?:segment(?:ed)?\s+(?:by|as|into|on)\s+|by\s+|per\s+|grouped\s+by\s+|breakdown\s+(?:by\s+)?'
        r'|across\s+|among\s+|between\s+|compare\s+(?:across\s+)?)'
        r'([a-z][a-z\s]{2,30}?)(?=\s+to\b|\s+and\b|\s+for\b|\s+in\b|\s+with\b|\s+find\b|[,.]|$)',
        msg,
    )
    for candidate in candidates:
        candidate = candidate.strip()
        # Exact match first
        if candidate in _GROUPING_TO_DIM:
            return _GROUPING_TO_DIM[candidate]
        # Partial match (scan tokens)
        for phrase, dim in _GROUPING_TO_DIM.items():
            if phrase in candidate or candidate in phrase:
                return dim
    return None


def _pick_canonical_sql(semantic_context: dict, message: str) -> str | None:
    """
    1. If user message contains an explicit 'by X' grouping, use matching dimension SQL.
    2. If there's grouping intent without an explicit target, defer to LLM.
    3. Otherwise fall back to the default canonical SQL for the metric.
    """
    metric = semantic_context.get("metric")
    if not metric:
        return None

    # --- Step 1: explicit 'by X' in the message ---
    explicit_dim = _extract_explicit_grouping_dim(message)
    if explicit_dim:
        variant = METRIC_SQL_BY_DIMENSION.get((metric, explicit_dim))
        if variant:
            return variant
        # User wants a grouping we don't have a canonical for → let LLM handle it
        return None

    # --- Step 2: dimension matched by semantic resolver, no explicit 'by X' ---
    matched_dims = semantic_context.get("dimensions", [])
    for dim in matched_dims:
        variant = METRIC_SQL_BY_DIMENSION.get((metric, dim))
        if variant:
            return variant

    # --- Step 3: fall back to the default canonical SQL for this metric ---
    # Always prefer canonical over a potentially-broken LLM response.
    # The canonical is designed to be a safe, always-valid default.
    if metric in METRIC_CANONICAL_SQL:
        return METRIC_CANONICAL_SQL[metric]

    return None


def _replace_semantic_model_table(sql: str, semantic_context: dict) -> str:
    if "semantic_model_table" in sql:
        source = semantic_context.get("source_table") or "cc_analytics.raw_deposit_transaction"
        return sql.replace("semantic_model_table", source)
    return sql


def generate_sql_from_question(message: str, persona: str, semantic_context: dict, prior_context: list | None = None, chat_mode: str = "hybrid") -> SQLGenerationResult:
    """Generate SQL for *message*.

    chat_mode:
      "pattern" — only use pre-built pattern matching; return empty if no match.
      "llm"     — skip patterns, go straight to Vanna/Ollama with full data dict context.
      "hybrid"  — pattern first, LLM fallback (default / legacy behaviour).
    """
    # ── PATTERN mode: only use deterministic patterns ─────────────────────────
    if chat_mode == "pattern":
        raw_sql = _direct_table_sql(message)
        if raw_sql:
            return SQLGenerationResult(sql=raw_sql, explanation="Direct table lookup (pattern mode).", assumptions=["Pattern mode — no LLM used."])
        analytical_sql = _analytical_pattern_sql(message)
        if analytical_sql:
            return SQLGenerationResult(sql=analytical_sql, explanation="Matched analytical pattern (pattern mode).", assumptions=["Pattern mode — no LLM used."])
        canonical = _pick_canonical_sql(semantic_context, message)
        if canonical:
            return SQLGenerationResult(sql=canonical, explanation="Canonical metric SQL (pattern mode).", assumptions=["Pattern mode — no LLM used."])
        return SQLGenerationResult(sql="", explanation="No pattern matched this query in pattern mode.", assumptions=["Pattern mode — LLM disabled."])

    # ── LLM mode: skip patterns, use full dict context + Ollama/Vanna ─────────
    if chat_mode == "llm":
        # Inject data dictionary context into semantic_context
        _enrich_with_dictionary(semantic_context)
        if vanna_service.is_ready():
            try:
                result = vanna_service.generate_sql(message, semantic_context)
                sql = result.get("sql", "").strip()
                if sql:
                    sql = _replace_semantic_model_table(sql, semantic_context)
                    return SQLGenerationResult(sql=sql, explanation=result.get("explanation", "LLM mode (Vanna)."), assumptions=result.get("assumptions", []), llm_was_used=True)
            except Exception:
                pass
        prompt = build_sql_prompt(message, persona, semantic_context, prior_context)
        raw_output = generate_with_ollama(prompt)
        try:
            parsed = parse_model_json(raw_output)
            sql = parsed.get("sql", "").strip()
            if not sql:
                raise ValueError("empty sql")
            sql = _replace_semantic_model_table(sql, semantic_context)
            return SQLGenerationResult(sql=sql, explanation=parsed.get("explanation", "LLM mode."), assumptions=parsed.get("assumptions", []), llm_was_used=True)
        except Exception:
            return SQLGenerationResult(sql="", explanation="LLM failed to generate valid SQL.", assumptions=["LLM mode — parse error."], llm_was_used=True)

    # ── HYBRID mode (default): pattern first, LLM fallback ────────────────────
    # Fast path 1: direct table reference (raw_*, ddm_*, dp_*, audit_*, etc.) — no LLM needed
    raw_sql = _direct_table_sql(message)
    if raw_sql:
        return SQLGenerationResult(
            sql=raw_sql,
            explanation=f"Direct table sample query.",
            assumptions=["Direct table lookup — no aggregation applied.", "LIMIT capped at 200 rows."],
        )

    # Fast path 2: cross-table analytical pattern — correct JOIN SQL without LLM
    analytical_sql = _analytical_pattern_sql(message)
    if analytical_sql:
        return SQLGenerationResult(
            sql=analytical_sql,
            explanation="Matched known analytical pattern — pre-built JOIN query used.",
            assumptions=["Pattern-matched query — no LLM call needed.", "Joins raw tables directly."],
        )

    # Fast path 3: explicit reference to an unknown table/view — no LLM call, signal caller
    # (actual message is composed in vanna_sql_node to avoid StarRocks execution)
    unknown_sql = _unknown_table_sql(message)
    if unknown_sql:
        return SQLGenerationResult(
            sql=unknown_sql,
            explanation="Unknown table or view referenced.",
            assumptions=[],
        )

    canonical = _pick_canonical_sql(semantic_context, message)

    if canonical:
        explicit_dim = _extract_explicit_grouping_dim(message)
        matched_dims = semantic_context.get("dimensions", [])
        routing_note = f"dimension '{explicit_dim}'" if explicit_dim else f"matched dimensions {matched_dims}"
        return SQLGenerationResult(
            sql=canonical,
            explanation=f"Dimension-aware SQL for metric '{semantic_context.get('metric')}' via {routing_note}.",
            assumptions=["Semantic catalog path used.", "Real synthetic tables are queried directly."],
        )

    # Enrich with data dictionary before any LLM call (balanced + auto paths)
    _enrich_with_dictionary(semantic_context)

    if vanna_service.is_ready():
        try:
            result = vanna_service.generate_sql(message, semantic_context)
            sql = result.get("sql", "").strip()
            explanation = result.get("explanation", "").strip()
            assumptions = result.get("assumptions", [])

            if sql:
                sql = _replace_semantic_model_table(sql, semantic_context)
                return SQLGenerationResult(
                    sql=sql,
                    explanation=explanation or "SQL generated by Vanna.",
                    assumptions=assumptions if isinstance(assumptions, list) else [],
                )
        except Exception:
            pass

    prompt = build_sql_prompt(message, persona, semantic_context, prior_context)
    raw_output = generate_with_ollama(prompt)

    try:
        parsed = parse_model_json(raw_output)

        sql = parsed.get("sql", "").strip()
        explanation = parsed.get("explanation", "").strip()
        assumptions = parsed.get("assumptions", [])

        if not sql:
            raise ValueError("Missing sql in model response")

        sql = _replace_semantic_model_table(sql, semantic_context)

        return SQLGenerationResult(
            sql=sql,
            explanation=explanation or "SQL generated from semantic context.",
            assumptions=assumptions if isinstance(assumptions, list) else [],
            llm_was_used=True,
        )
    except Exception:
        metric = semantic_context.get("metric", "")
        if metric in METRIC_CANONICAL_SQL:
            return SQLGenerationResult(
                sql=METRIC_CANONICAL_SQL[metric],
                explanation=f"Canonical fallback SQL for metric '{metric}'.",
                assumptions=["Canonical fallback path used."],
            )
        return SQLGenerationResult(
            sql=(
                "SELECT DATE_FORMAT(txn_date, '%Y-%m') AS month, "
                "COUNT(*) AS transaction_count, ROUND(SUM(amount), 2) AS total_amount "
                "FROM cc_analytics.raw_deposit_transaction "
                "WHERE txn_date IS NOT NULL "
                "GROUP BY month ORDER BY month DESC LIMIT 24"
            ),
            explanation="LLM parsing failed; returning monthly summary as fallback.",
            assumptions=["LLM fallback: could not parse model output."],
        )
