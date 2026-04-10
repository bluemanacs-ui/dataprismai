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
Data year: 2025 (full year Jan-Dec 2025)

This is a full-service banking analytics platform covering credit cards, deposits, and loans.

=== SEMANTIC TABLES (pre-aggregated — PREFER for analytics queries) ===

semantic_customer_360(as_of_date, customer_id, country_code, legal_entity, full_name,
  customer_segment, risk_rating, kyc_status, age, age_band, income_band, tenure_months,
  current_balance, available_balance, credit_limit, utilization_pct,
  spend_last_30d, transaction_count_last_30d, top_spend_category,
  payment_status, total_due, days_to_due, consecutive_late_months, is_overdue,
  dw_refreshed_at)
  -- 600 rows; best for customer profile, segment, utilization, spend_last_30d queries
  -- NOTE: NO credit_score, NO credit_band, NO active_fraud_alerts, NO currency_code

semantic_spend_metrics(year_month, customer_id, country_code, legal_entity, customer_segment,
  total_spend, food_dining_spend, shopping_retail_spend, travel_transport_spend,
  healthcare_spend, entertainment_spend, utilities_spend, other_spend,
  total_transactions, unique_merchants, international_spend, spend_mom_change_pct,
  top_merchant, top_category, currency_code, dw_refreshed_at)
  -- 9,129 rows; year_month key; best for CC spend category breakdown per customer

semantic_portfolio_kpis(kpi_month, country_code, legal_entity,
  total_customers, active_customers, customer_growth_pct, churn_rate,
  total_spend_volume, spend_growth_pct, avg_spend_per_customer,
  estimated_interest_income, estimated_fee_income,
  fraud_rate, delinquency_rate, npl_rate, avg_utilization_pct,
  full_payment_rate, approval_rate, currency_code, dw_refreshed_at)
  -- 57 rows; kpi_month key; best for executive/portfolio KPI queries
  -- NOTE: NO customer_id — aggregate table; group by kpi_month, country_code only

semantic_deposit_portfolio(snapshot_month, customer_id, country_code, legal_entity,
  customer_name, customer_segment, risk_rating, currency_code,
  savings_balance, savings_interest_rate, savings_interest_ytd,
  current_balance, fd_count, total_fd_balance, fd_avg_rate, fd_maturing_next_30d,
  total_deposit_balance, deposit_mom_change_pct, has_salary_credit,
  avg_monthly_credit, avg_monthly_debit, dw_refreshed_at)
  -- 600 rows; snapshot_month key; best for deposit balance, FD, savings queries

semantic_loan_portfolio(snapshot_month, customer_id, country_code, legal_entity,
  customer_name, customer_segment, risk_rating, kyc_status, currency_code, annual_income,
  personal_loan_id, personal_loan_outstanding, personal_loan_rate, personal_loan_emi, personal_loan_status,
  home_loan_id, home_loan_outstanding, home_loan_rate, home_loan_emi, home_loan_ltv,
  auto_loan_id, auto_loan_outstanding, auto_loan_rate, auto_loan_emi,
  total_loan_outstanding, total_loan_count, total_monthly_emi,
  max_overdue_days, overdue_bucket, is_npa, total_overdue_amount,
  loan_to_income_ratio, debt_service_ratio, dw_refreshed_at)
  -- 511 rows; snapshot_month key; best for loan portfolio, NPL, overdue queries

semantic_customer_product_mix(snapshot_month, customer_id, country_code, legal_entity,
  customer_name, customer_segment, risk_rating, annual_income, age, age_band,
  total_product_count, has_credit_card, has_savings, has_current, has_fd, has_loan,
  has_personal_loan, has_home_loan, has_auto_loan,
  total_asset_balance, total_liability_balance, net_balance,
  cc_outstanding, cc_credit_limit, cc_utilization_pct, cc_spend_last_month,
  total_deposit_balance, total_loan_outstanding, total_monthly_emi,
  payment_status, consecutive_late_months, is_overdue, wallet_share_score, dw_refreshed_at)
  -- 600 rows; best for cross-product wallet share, product holdings, total relationship value

semantic_payment_status(as_of_date, customer_id, account_id, country_code, legal_entity,
  customer_name, customer_segment, account_type, statement_month,
  due_date, days_to_due, minimum_due, total_due, amount_paid, amount_still_owed,
  payment_status, overdue_days, overdue_bucket, late_fee_applied,
  is_giro_enabled, preferred_payment_method, consecutive_late_months, dw_refreshed_at)
  -- 774 rows; CC payment behavior; use amount_still_owed for outstanding balance

semantic_risk_metrics(metric_date, country_code, legal_entity, customer_segment,
  merchant_category, channel,
  total_transactions, approved_transactions, declined_transactions, decline_rate,
  fraud_transactions, fraud_amount, fraud_rate, avg_fraud_score, high_risk_transactions,
  delinquency_rate_1_30, delinquency_rate_31_60, delinquency_rate_61_90, delinquency_rate_91_plus,
  active_fraud_alerts, top_fraud_merchant, dw_refreshed_at)
  -- daily risk aggregate; use metric_date for time filters
  -- NOTE: NO customer_id — aggregate table; group by metric_date, country_code, customer_segment

=== DATA PRODUCT TABLES (richer detail than semantic) ===

dp_customer_balance_snapshot(snapshot_date, customer_id, account_id, country_code, legal_entity,
  customer_segment, account_type, currency_code,
  current_balance, available_balance, credit_limit, utilization_pct,
  outstanding_balance, min_payment_due, is_overdue, overdue_days,
  account_status, dw_refreshed_at)
  -- 774 rows; snapshot_date key; per-account CC balance snapshot

dp_customer_spend_monthly(year_month, customer_id, country_code, legal_entity,
  merchant_category, merchant_category_group,
  total_spend, transaction_count, avg_transaction_amount, max_single_transaction,
  unique_merchants, currency_code, channel_online_pct, channel_intl_pct, dw_refreshed_at)
  -- 18,611 rows; year_month key; ONE ROW PER customer/month/category — SUM to get totals

dp_transaction_enriched(transaction_id, transaction_date, year_month,
  customer_id, account_id, card_id, country_code, legal_entity, customer_segment, full_name,
  amount_local, currency_code, transaction_type, channel, merchant_id, merchant_name,
  merchant_category, merchant_category_group, mcc_code, merchant_risk_tier,
  status, decline_reason, is_fraud, fraud_score, fraud_tier,
  is_international, is_contactless, is_recurring, dw_refreshed_at)
  -- 24,000 rows; status values: approved/declined; NO auth_status column

dp_payment_status(as_of_date, account_id, customer_id, country_code, legal_entity,
  customer_segment, statement_year_month, statement_date, due_date, days_to_due,
  minimum_due, total_due, amount_paid, amount_outstanding,
  payment_status, overdue_days, overdue_bucket, late_fee, interest_at_risk,
  payment_method, is_giro_enabled, consecutive_late_months, dw_refreshed_at)
  -- 12,861 rows; CC payment status with full detail; use amount_outstanding here

dp_deposit_portfolio(snapshot_month, customer_id, country_code, legal_entity,
  customer_segment, currency_code,
  savings_balance, savings_account_count, savings_interest_rate, savings_interest_earned,
  current_balance, current_account_count,
  fd_balance, fd_count, fd_avg_rate, fd_maturing_next_30d, fd_maturing_next_90d,
  total_deposit_balance, total_deposit_accounts, total_interest_earned_ytd,
  avg_monthly_credits, avg_monthly_debits, has_salary_credit, salary_credit_amount, dw_refreshed_at)
  -- 600 rows; snapshot_month key; detailed deposit portfolio per customer
  -- NOTE: avg_monthly_credits / avg_monthly_debits (not avg_monthly_credit/debit)

dp_loan_portfolio(snapshot_month, customer_id, country_code, legal_entity,
  customer_segment, currency_code, annual_income,
  personal_loan_outstanding, personal_loan_count, personal_loan_emi,
  home_loan_outstanding, home_loan_count, home_loan_emi,
  auto_loan_outstanding, auto_loan_count, auto_loan_emi,
  total_loan_outstanding, total_loan_count, total_monthly_emi,
  max_overdue_days, overdue_loan_count, is_npa, npa_amount,
  dpd_bucket, debt_to_income_ratio, debt_service_ratio, dw_refreshed_at)
  -- 511 rows; use dpd_bucket (NOT overdue_bucket) for DPD grouping

dp_risk_signals(signal_date, customer_id, country_code, legal_entity, risk_rating,
  fraud_transaction_count, fraud_transaction_amount, fraud_rate_30d, fraud_score_avg_30d,
  card_decline_count_30d, card_decline_rate_30d, intl_transaction_count_30d,
  overdue_accounts_count, max_overdue_days, total_overdue_amount,
  composite_risk_score, risk_tier, alert_triggered, alert_type, dw_refreshed_at)
  -- 600 rows; signal_date key; daily per-customer risk snapshot

dp_portfolio_kpis(kpi_year_month, country_code, legal_entity, customer_segment, account_type,
  total_customers, active_customers, new_customers, churned_customers,
  total_transaction_volume, total_transaction_count, avg_transaction_amount,
  fraud_rate, decline_rate, delinquency_rate, overdue_amount,
  full_payment_rate, late_payment_rate, estimated_interest_income, estimated_fee_income, dw_refreshed_at)
  -- 228 rows; kpi_year_month key; by country/segment — more granular than semantic_portfolio_kpis
  -- NOTE: NO customer_id — aggregate table

=== RAW TABLES (event-level — use for specific lookups) ===

raw_customer(customer_id, first_name, last_name, country_code, legal_entity,
  customer_segment, kyc_status, risk_rating, annual_income, currency_code,
  gender, email, phone, city, occupation, acquisition_channel, created_at)
  -- 610 rows; NO full_name column — use CONCAT(first_name,' ',last_name) for name lookup
  -- NO credit_score or credit_band in this table

raw_account(account_id, customer_id, country_code, legal_entity, account_type, account_subtype,
  currency_code, current_balance, available_balance, credit_limit,
  interest_rate, status, product_code, product_name, open_date, last_activity_date)
  -- 784 rows; CC accounts; status column (not account_status); product_code (not product_id)

raw_transaction(transaction_id, account_id, card_id, customer_id, country_code, legal_entity,
  transaction_date, posting_date, amount, currency_code, transaction_type, channel,
  merchant_id, merchant_name, merchant_category, mcc_code,
  status, decline_reason, is_fraud, fraud_score, is_international, is_contactless, is_recurring)
  -- 24,012 rows; status column (not auth_status): approved/declined/pending

raw_deposit_account(deposit_id, account_id, customer_id, country_code, legal_entity,
  deposit_type, deposit_category, currency_code, current_balance, interest_rate,
  interest_earned_ytd, tenor_months, deposit_amount, maturity_date,
  has_salary_credit, status, open_date)
  -- 1,327 rows; deposit_type: SAVINGS, CURRENT, FIXED_DEPOSIT

raw_deposit_transaction(txn_id, deposit_id, account_id, customer_id, country_code,
  txn_date, amount, txn_direction, txn_type, txn_category, channel, balance_after, status)
  -- 28,392 rows; txn_date column; txn_direction: CREDIT or DEBIT

raw_loan(loan_id, account_id, customer_id, country_code, legal_entity,
  loan_type, currency_code, loan_amount, outstanding_balance, annual_interest_rate,
  emi_amount, overdue_days, dpd_bucket, npa_flag, loan_status, disbursement_date)
  -- 1,044 rows; loan_type: PERSONAL, HOME, AUTO, SME; npa_flag: 0=performing, 1=NPA
  -- COLUMNS: loan_amount (not principal_amount), emi_amount (not monthly_installment),
  --          overdue_days (not past_due_days), npa_flag (not npl_flag), loan_status (not status)

raw_loan_repayment(repayment_id, loan_id, customer_id, country_code, legal_entity,
  due_date, payment_date, emi_due, amount_paid, principal_paid, interest_paid,
  penalty_charges, overdue_days, payment_status, payment_method, payment_channel)
  -- 34,111 rows; payment_status: ON_TIME, LATE, MISSED, PARTIAL
  -- COLUMNS: amount_paid (not payment_amount), emi_due (not scheduled_amount),
  --          overdue_days (not days_late), penalty_charges (not penalty_fee)

=== Join Keys ===
raw_account.customer_id              → raw_customer.customer_id
raw_transaction.account_id           → raw_account.account_id
raw_deposit_account.customer_id      → raw_customer.customer_id
raw_deposit_transaction.deposit_id   → raw_deposit_account.deposit_id
raw_loan.customer_id                 → raw_customer.customer_id
raw_loan_repayment.loan_id           → raw_loan.loan_id
semantic_customer_360.customer_id    → semantic_spend_metrics.customer_id
semantic_customer_360.customer_id    → semantic_deposit_portfolio.customer_id
semantic_customer_360.customer_id    → semantic_loan_portfolio.customer_id
semantic_customer_360.customer_id    → semantic_customer_product_mix.customer_id

=== Important Query Rules ===
- Always prefix table names: cc_analytics.raw_customer, cc_analytics.semantic_spend_metrics
- PREFER semantic_* tables for aggregated analytics; dp_* for richer column detail
- Use DATE_FORMAT(col, '%Y-%m') for monthly grouping — do NOT use date_trunc
- StarRocks: GROUP BY must use the full column expression, NOT a SELECT alias
  CORRECT: GROUP BY DATE_FORMAT(transaction_date,'%Y-%m')  WRONG: GROUP BY txn_month
- CC transactions status: use column `status` with values 'approved'/'declined' — NOT `auth_status`
- CC transactions date: transaction_date; deposit transactions date: txn_date
- For customer name lookup: raw_customer has NO full_name — use CONCAT(first_name,' ',last_name)
  OR join to semantic_customer_360/dp_transaction_enriched which have full_name
- customer_segment values: mass, affluent, premium
- payment_status values (CC): paid_full, paid_partial, paid_minimum, overdue, pending
- loan payment_status values: ON_TIME, LATE, MISSED, PARTIAL (uppercase)
- overdue_bucket values (CC): current, '1-30 days', '31-60 days', '61-90 days', '90+ days'
- DPD in loans: use dpd_bucket column in raw_loan and dp_loan_portfolio (NOT overdue_bucket)
- channel values (CC): online, pos, contactless, mobile, atm
- legal_entity values: SG_BANK, MY_BANK, IN_BANK
- risk_rating values: low, medium, high
- utilization_pct decimal (0–1) — multiply ×100 for %; fraud_rate/delinquency_rate same
- Tables with NO customer_id (aggregate only): semantic_risk_metrics, semantic_portfolio_kpis, dp_portfolio_kpis
- semantic_payment_status: outstanding balance = amount_still_owed
- dp_payment_status: outstanding balance = amount_outstanding
- dp_deposit_portfolio: credit transactions = avg_monthly_credits; debit = avg_monthly_debits
- For deposit queries: prefer semantic_deposit_portfolio or dp_deposit_portfolio
- For loan/NPL queries: prefer semantic_loan_portfolio or dp_loan_portfolio
- For CC spend analysis: prefer semantic_spend_metrics or dp_customer_spend_monthly
- dp_customer_spend_monthly: ONE ROW PER customer/month/category — SUM to get totals
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
    "semantic_customer_360":           "as_of_date",
    "semantic_portfolio_kpis":         "kpi_month",
    "semantic_payment_status":         "as_of_date",
    "semantic_spend_metrics":          "year_month",
    "semantic_risk_metrics":           "metric_date",
    "semantic_deposit_portfolio":      "snapshot_month",
    "semantic_loan_portfolio":         "snapshot_month",
    "semantic_customer_product_mix":   "snapshot_month",
    "dp_customer_balance_snapshot":    "snapshot_date",
    "dp_customer_spend_monthly":       "year_month",
    "dp_transaction_enriched":         "transaction_date",
    "dp_payment_status":               "as_of_date",
    "dp_deposit_portfolio":            "snapshot_month",
    "dp_loan_portfolio":               "snapshot_month",
    "dp_risk_signals":                 "signal_date",
    "dp_portfolio_kpis":               "kpi_year_month",
    "raw_deposit_transaction":         "txn_date",
    "raw_loan_repayment":              "payment_date",
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
{("" + chr(10) + "Data Dictionary Context (full column definitions):" + chr(10) + semantic_context.get("dictionary_context", "") + chr(10)) if semantic_context.get("dictionary_context") else ""}
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
