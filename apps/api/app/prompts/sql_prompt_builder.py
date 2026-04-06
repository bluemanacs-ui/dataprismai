# =============================================================================
# DataPrismAI — SQL Prompt Builder
# =============================================================================
# Builds the SQL-generation prompt from live schema context (SchemaRegistry)
# with a static fallback if StarRocks is unreachable at startup.
#
# HOW TO UPDATE THE SCHEMA CONTEXT:
#   The schema context is built automatically by SchemaRegistry from live
#   DESCRIBE TABLE queries.  No manual edits are needed as tables change.
#
# HOW TO CHANGE THE STATIC FALLBACK:
#   Edit _STATIC_SCHEMA_CONTEXT below.  The fallback is only used when
#   StarRocks is completely unreachable at startup.
# =============================================================================
_STATIC_SCHEMA_CONTEXT = """
Database: cc_analytics (StarRocks / MySQL-compatible)
Countries: SG (Singapore / SGD), MY (Malaysia / MYR), IN (India / INR)
Data year: 2025 (full year Jan–Dec 2025; all tables cover 2025-01 to 2025-12)

=== PRIMARY: Semantic Tables (prefer for all analytics queries) ===

semantic_customer_360(as_of_date, customer_id, country_code, legal_entity, full_name, first_name, last_name,
  customer_segment, risk_rating, kyc_status, age, age_band, credit_score, credit_band,
  primary_account_id, account_type, current_balance, available_balance, credit_limit, utilization_pct,
  total_accounts, mtd_spend, last_month_spend, spend_change_pct, top_spend_category,
  payment_status, total_due, days_to_due, is_overdue, consecutive_late, active_fraud_alerts,
  currency_code, created_at)

semantic_transaction_summary(transaction_id, account_id, customer_id, country_code, legal_entity,
  full_name, customer_segment, transaction_date, txn_year_month, amount, currency_code,
  transaction_type, channel, merchant_name, merchant_category, merchant_risk_tier,
  auth_status, decline_reason, is_approved, is_declined, is_fraud, fraud_score, is_suspicious,
  is_international, created_at)

semantic_spend_metrics(spend_month, customer_id, country_code, legal_entity, full_name, customer_segment,
  total_spend, food_dining, retail_shopping, travel_transport, healthcare, entertainment,
  utilities, grocery, hotel, fuel, other_spend, transaction_count, avg_txn_amount,
  top_category, top_merchant, mom_spend_change_pct, currency_code, created_at)

semantic_payment_status(as_of_date, account_id, customer_id, country_code, legal_entity,
  full_name, customer_segment, statement_month, due_date, days_to_due,
  minimum_due, total_due, amount_paid, amount_outstanding,
  payment_status, overdue_days, overdue_bucket, consecutive_late,
  late_fee, interest_at_risk, is_giro_enrolled, preferred_method, currency_code, created_at)

semantic_risk_metrics(metric_date, country_code, legal_entity, customer_segment,
  total_txn, approved_txn, declined_txn, fraud_txn, suspicious_txn,
  total_amount, fraud_amount, fraud_rate, decline_rate, avg_fraud_score,
  delinquency_1_30, delinquency_31_60, delinquency_61_90, delinquency_91plus,
  high_risk_accounts, currency_code, created_at)

semantic_portfolio_kpis(kpi_month, country_code, legal_entity,
  total_customers, active_customers, new_customers, customer_growth_pct, churn_rate,
  total_spend, spend_growth_pct, avg_balance, avg_utilization,
  fraud_rate, decline_rate, delinquency_rate, full_payment_rate, npl_rate,
  est_interest_income, currency_code, fx_rate_to_usd, created_at)

=== SECONDARY: Raw Tables (for specific lookups) ===

raw_customer(customer_id, country_code, legal_entity, first_name, last_name, date_of_birth,
  gender, email, phone, city, nationality, id_type, customer_segment, kyc_status, risk_rating,
  annual_income, currency_code, occupation, credit_score, created_at)

raw_transaction(transaction_id, account_id, customer_id, country_code, transaction_date,
  amount, currency_code, transaction_type, channel, merchant_id, merchant_name,
  merchant_category, auth_status, decline_reason, is_fraud, fraud_score, fraud_tier,
  is_international, is_contactless, created_at)

raw_account(account_id, customer_id, country_code, account_type, product_code, currency_code,
  current_balance, available_balance, credit_limit, interest_rate, account_status,
  open_date, cycle_day, created_at)

raw_statement(statement_id, account_id, customer_id, country_code, statement_month,
  statement_date, closing_balance, total_spend, minimum_due, total_due, due_date,
  payment_status, credit_limit, utilization_rate, transaction_count, created_at)

raw_payment(payment_id, account_id, customer_id, country_code, payment_date, due_date,
  statement_month, minimum_due, total_due, payment_amount, payment_method,
  payment_status, overdue_days, created_at)

raw_merchant(merchant_id, country_code, merchant_name, merchant_category, mcc_code,
  city, is_online, risk_tier, fraud_rate, decline_rate, created_at)

=== Join Keys ===
semantic_customer_360.customer_id             → semantic_spend_metrics.customer_id
semantic_customer_360.customer_id             → semantic_payment_status.customer_id
semantic_customer_360.primary_account_id      → semantic_payment_status.account_id
semantic_transaction_summary.country_code     → semantic_risk_metrics.country_code
semantic_portfolio_kpis.country_code          → semantic_risk_metrics.country_code (same month)
raw_account.customer_id                       → raw_customer.customer_id
raw_transaction.account_id                    → raw_account.account_id
raw_transaction.merchant_id                   → raw_merchant.merchant_id

=== Important Query Rules ===
- Always prefix table names: cc_analytics.semantic_customer_360
- Use DATE_FORMAT(col, '%Y-%m') for monthly grouping; do NOT use date_trunc
- customer_segment values (lowercase): mass, affluent, premium
- payment_status values: paid_full, paid_partial, paid_minimum, overdue, pending
- transaction_type values: purchase, declined
- auth_status values: approved, declined
- overdue_bucket values: current, '1-30 days', '31-60 days'
- channel values: online, pos, contactless, mobile, atm
- legal_entity values: SG_BANK, MY_BANK, IN_BANK
- risk_rating values: low, medium, high
- kyc_status values: verified, pending, enhanced_dd
- credit_band values: poor, fair, good, very_good, excellent
- age_band values: 18-25, 26-35, 36-45, 46-55, 56-65, 65+
- merchant_risk_tier values: low, medium
- fraud_score > 0.6 = suspicious; > 0.85 = high risk; is_suspicious=1 for flagged
- For customer name lookups: WHERE full_name LIKE '%Name%' or WHERE first_name = 'Name'
- For spend by category: use semantic_spend_metrics pre-aggregated columns (food_dining, retail_shopping, travel_transport, grocery, entertainment, utilities, healthcare, hotel, fuel, other_spend)
- For top-N spending customers: SELECT full_name, total_spend FROM cc_analytics.semantic_spend_metrics ORDER BY total_spend DESC LIMIT N
- Country code mapping: Malaysia='MY', Singapore='SG', India='IN'
- For multi-country queries, GROUP BY country_code to show per-country breakdown
- semantic_portfolio_kpis is best for executive/portfolio-level KPI questions (fraud_rate, delinquency_rate, full_payment_rate are stored as decimals — multiply by 100 for %)
- semantic_risk_metrics.delinquency_1_30, delinquency_31_60, delinquency_61_90, delinquency_91plus are all decimal ratios — multiply by 100 for %
- avg_utilization in semantic_portfolio_kpis and utilization_pct in semantic_customer_360 are decimals (0–1) — multiply by 100 for %
"""
# Maps UI time-range labels to SQL WHERE clauses (StarRocks / MySQL-compat DATE_SUB)
_TIME_RANGE_SQL: dict[str, str] = {
    "L7D":  "transaction_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
    "L1M":  "transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)",
    "LQ":   "transaction_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)",
    "L1Y":  "transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)",
    # ALL = no filter
}

# Alternate date column names used in non-transaction tables
_DATE_COL_ALIASES: dict[str, str] = {
    "semantic_customer_360":       "as_of_date",
    "semantic_portfolio_kpis":     "kpi_month",
    "semantic_payment_status":     "as_of_date",
    "semantic_spend_metrics":      "spend_month",
    "semantic_risk_metrics":       "metric_date",
}


def _build_time_filter(time_range: str, table_hint: str = "") -> str:
    """Return a SQL WHERE fragment for the given time range, or empty string for ALL."""
    if not time_range or time_range == "ALL":
        return ""
    interval_map = {
        "L7D": "INTERVAL 7 DAY",
        "L1M": "INTERVAL 1 MONTH",
        "LQ":  "INTERVAL 3 MONTH",
        "L1Y": "INTERVAL 1 YEAR",
    }
    interval = interval_map.get(time_range.upper())
    if not interval:
        return ""
    date_col = _DATE_COL_ALIASES.get(table_hint, "transaction_date")
    return f"{date_col} >= DATE_SUB(CURDATE(), {interval})"


def _get_schema_context() -> str:
    """Return the live schema context string, falling back to static if needed."""
    try:
        from app.services.schema_registry import registry
        ctx = registry.build_schema_context()
        if ctx:
            return ctx
    except Exception:
        pass
    return _STATIC_SCHEMA_CONTEXT


def build_sql_prompt(message: str, persona: str, semantic_context: dict, prior_context: list | None = None) -> str:
    metric = semantic_context.get("metric", "")
    dimensions = ", ".join(semantic_context.get("dimensions", []))
    domain = semantic_context.get("domain", "Credit Card Analytics")
    definition = semantic_context.get("definition", "")
    time_range = semantic_context.get("time_range", "ALL")

    # Build time range instruction
    time_block = ""
    if time_range and time_range != "ALL":
        interval_labels = {
            "L7D": "last 7 days",
            "L1M": "last 1 month",
            "LQ":  "last quarter (3 months)",
            "L1Y": "last 1 year",
        }
        label = interval_labels.get(time_range.upper(), time_range)
        # Table-specific date columns
        date_hint = (
            "Use DATE_SUB(CURDATE(), INTERVAL 7 DAY) for L7D, INTERVAL 1 MONTH for L1M, "
            "INTERVAL 3 MONTH for LQ, INTERVAL 1 YEAR for L1Y. "
            "For transaction tables use `transaction_date`, for customer/portfolio tables use `as_of_date`, "
            "for payment tables use `payment_date`."
        )
        time_block = (
            f"\n- TIME FILTER REQUIRED: Filter results to the {label}. "
            f"Add an appropriate WHERE clause with a date range. {date_hint}"
        )

    # Build prior conversation context block
    prior_block = ""
    if prior_context:
        lines = []
        for turn in prior_context[-3:]:  # last 3 turns
            lines.append(f"User asked: {turn.get('user_message', '')}")
            if turn.get("sql"):
                lines.append(f"SQL used: {turn['sql'][:400]}")
            if turn.get("row_summary"):
                rows_str = str(turn["row_summary"][:5])
                lines.append(f"Result rows (sample): {rows_str[:600]}")
        if lines:
            prior_block = (
                "\n\n===CONVERSATION HISTORY (use this to resolve pronouns and follow-up questions)===\n"
                + "\n".join(lines)
                + "\n=== END OF HISTORY ===\n"
                "\nIMPORTANT pronoun resolution rules:\n"
                "1. If the current question contains pronouns (he, she, his, her, they, this) or "
                "references like 'the same', ALWAYS resolve them from the conversation history.\n"
                "2. To resolve the reference, REUSE the WHERE clause / filter condition from the "
                "prior SQL (e.g. if prior SQL had WHERE first_name='Daniel', use that same filter).\n"
                "3. Do NOT invent or guess customer_id values. If no ID is visible in the result rows, "
                "use the name or filter from the prior SQL instead.\n"
                "4. Only change the SELECT columns to match what the new question is asking for."
            )

    return f"""You are DataPrismAI, a SQL generation assistant for credit-card analytics.

Rules:
- Generate valid MySQL/StarRocks-compatible SELECT SQL only
- Use ONLY the tables and columns listed in the schema below — do NOT invent table or column names
- ALWAYS prefer semantic_* tables over raw_* tables for analytics queries
- For single-table queries prefer a simple SELECT with no JOINs unless the question clearly requires data from multiple tables
- When using JOINs, always qualify every column with the table alias (e.g. t.amount, c.customer_id)
- Do not use date_trunc — use DATE_FORMAT(col, '%Y-%m') for monthly grouping
- Output valid JSON only, no markdown fences
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE{time_block}

Schema:
{_get_schema_context()}

Semantic context:
- Domain: {domain}
- Metric: {metric}
- Definition: {definition}
- Dimensions: {dimensions}
- Time range: {time_range}{prior_block}

User question:
{message}

Return JSON exactly like:
{{
  "sql": "string",
  "explanation": "string",
  "assumptions": ["string"]
}}
""".strip()
