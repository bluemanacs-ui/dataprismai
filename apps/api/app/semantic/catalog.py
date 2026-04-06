_HARDCODED_CATALOG: dict = {
    "metrics": [
        {
            "name": "Total Spend",
            "keywords": ["total spend", "spend", "transaction amount", "purchase amount", "spending", "expenditure", "volume", "sales", "how much spent", "category spend"],
            "dimensions": ["Month", "Geography", "Merchant Category", "Segment", "Channel"],
            "engine": "starrocks",
            "domain": "spend",
            "definition": "Sum of all purchase transaction amounts (approved, transaction_type=PURCHASE).",
            "source_table": "cc_analytics.semantic_spend_metrics",
        },
        {
            "name": "Delinquency Rate",
            "keywords": ["delinquency rate", "delinquency", "30+ dpd", "late payment", "overdue", "past due", "default", "missed payment", "delinquent", "days past due", "overdue bucket"],
            "dimensions": ["Month", "Segment", "Geography", "Overdue Bucket"],
            "engine": "starrocks",
            "domain": "risk",
            "definition": "Percentage of accounts with overdue payments (1+ days past due).",
            "source_table": "cc_analytics.semantic_risk_metrics",
        },
        {
            "name": "Fraud Rate",
            "keywords": ["fraud", "fraudulent", "suspicious", "scam", "fraud rate", "fraud score", "suspected fraud", "high risk", "fraud alert", "is_fraud"],
            "dimensions": ["Date", "Merchant Category", "Channel", "Geography", "Segment"],
            "engine": "starrocks",
            "domain": "risk",
            "definition": "Percentage of transactions confirmed as fraudulent by count or amount.",
            "source_table": "cc_analytics.semantic_risk_metrics",
        },
        {
            "name": "Account Utilization",
            "keywords": ["utilization", "credit utilization", "balance ratio", "credit limit", "available credit", "usage rate", "utilization rate", "utilization band"],
            "dimensions": ["Month", "Segment", "Geography"],
            "engine": "starrocks",
            "domain": "customer",
            "definition": "Average credit utilization as current_balance divided by credit_limit.",
            "source_table": "cc_analytics.semantic_customer_360",
        },
        {
            "name": "Payment Status",
            "keywords": ["payment", "payments", "payment amount", "repayment", "paid", "pay", "minimum payment", "total due", "overdue", "payment status", "amount outstanding"],
            "dimensions": ["Month", "Payment Method", "Segment", "Overdue Bucket"],
            "engine": "starrocks",
            "domain": "payments",
            "definition": "Current payment status per account including amount due, paid, and outstanding.",
            "source_table": "cc_analytics.semantic_payment_status",
        },
        {
            "name": "Portfolio KPIs",
            "keywords": ["portfolio", "kpi", "npl", "non-performing", "interest income", "churn", "growth", "executive", "board", "monthly report", "customer growth"],
            "dimensions": ["Month", "Geography", "Legal Entity"],
            "engine": "starrocks",
            "domain": "portfolio",
            "definition": "Monthly portfolio-level key performance indicators by country.",
            "source_table": "cc_analytics.semantic_portfolio_kpis",
        },
        {
            "name": "Customer Profile",
            "keywords": ["customer", "credit score", "segment", "age", "income", "kyc", "risk rating", "who is", "customer details", "profile", "balance"],
            "dimensions": ["Segment", "Age Band", "Geography", "Credit Band"],
            "engine": "starrocks",
            "domain": "customer",
            "definition": "360-degree customer view including balance, spend, payment status, and risk.",
            "source_table": "cc_analytics.semantic_customer_360",
        },
        {
            "name": "Transaction Count",
            "keywords": ["transaction count", "number of transactions", "how many transactions", "transaction volume", "transactions", "txn", "approved", "declined"],
            "dimensions": ["Date", "Merchant Category", "Channel", "Geography", "Auth Status"],
            "engine": "starrocks",
            "domain": "transactions",
            "definition": "Count of transactions processed, filterable by status, channel, and category.",
            "source_table": "cc_analytics.semantic_transaction_summary",
        },
        {
            "name": "Dispute Rate",
            "keywords": ["dispute", "disputes", "dispute rate", "chargeback", "chargebacks", "contested", "disputed transaction", "fraud dispute", "claim"],
            "dimensions": ["Merchant Category", "Geography", "Channel", "Segment", "Date"],
            "engine": "starrocks",
            "domain": "risk",
            "definition": "Ratio of disputed (fraudulent or contested) transactions to total transactions, by merchant or geography.",
            "source_table": "cc_analytics.semantic_transaction_summary",
        },
    ],
    "dimensions": [
        {"name": "Date", "keywords": ["date", "day", "period", "today", "yesterday", "last 7 days", "last 30 days"]},
        {"name": "Month", "keywords": ["month", "monthly", "billing cycle", "per month", "year-month"]},
        {"name": "Geography", "keywords": ["country", "country code", "country_code", "singapore", "malaysia", "india", "per country", "by country", "each country", "region", "location", "geography"]},
        {"name": "Merchant Category", "keywords": ["mcc", "merchant category", "merchant type", "merchant", "by merchant", "per merchant", "food", "retail", "travel", "grocery"]},
        {"name": "Channel", "keywords": ["channel", "online", "in-store", "atm", "mobile", "e-commerce", "pos", "contactless", "by channel"]},
        {"name": "Segment", "keywords": ["segment", "customer segment", "mass", "affluent", "priority", "hnw", "tier", "by segment", "per segment", "product type", "product category", "card product", "card type", "account type", "by product", "by account", "card tier"]},
        {"name": "Overdue Bucket", "keywords": ["overdue bucket", "1-30", "31-60", "61-90", "91+", "dpd", "days past due", "delinquency bucket"]},
        {"name": "Age Band", "keywords": ["age band", "age group", "25-34", "35-44", "45-54", "55+", "young", "senior", "by age"]},
        {"name": "Payment Method", "keywords": ["payment method", "giro", "paynow", "upi", "fpxpay", "bank transfer", "online banking"]},
        {"name": "Legal Entity", "keywords": ["legal entity", "sg_bank", "my_bank", "in_bank", "entity", "subsidiary", "by entity"]},
    ],
}

# Canonical SQL per metric — directly executable against StarRocks cc_analytics
METRIC_CANONICAL_SQL = {
    # Monthly spend trend across all countries
    "Total Spend": (
        "SELECT spend_month, country_code, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "SUM(transaction_count) AS transaction_count "
        "FROM cc_analytics.semantic_spend_metrics "
        "GROUP BY spend_month, country_code ORDER BY spend_month ASC, total_spend DESC LIMIT 36"
    ),
    # Transaction count by merchant category
    "Transaction Count": (
        "SELECT merchant_category, country_code, "
        "SUM(is_approved) AS approved_txn, SUM(is_declined) AS declined_txn, "
        "COUNT(*) AS total_txn "
        "FROM cc_analytics.semantic_transaction_summary "
        "GROUP BY merchant_category, country_code ORDER BY total_txn DESC LIMIT 20"
    ),
    # Fraud rate by date (default — for trend queries)
    "Fraud Rate": (
        "SELECT metric_date, country_code, "
        "ROUND(fraud_rate * 100, 4) AS fraud_rate_pct, "
        "ROUND(decline_rate * 100, 4) AS decline_rate_pct, "
        "ROUND(avg_fraud_score, 4) AS avg_fraud_score, "
        "fraud_txn, total_txn "
        "FROM cc_analytics.semantic_risk_metrics "
        "ORDER BY metric_date DESC, fraud_rate DESC LIMIT 36"
    ),
    # Delinquency buckets by country
    "Delinquency Rate": (
        "SELECT metric_date, country_code, "
        "ROUND(delinquency_1_30 * 100, 2) AS dpd_1_30_pct, "
        "ROUND(delinquency_31_60 * 100, 2) AS dpd_31_60_pct, "
        "ROUND(delinquency_61_90 * 100, 2) AS dpd_61_90_pct, "
        "ROUND(delinquency_91plus * 100, 2) AS dpd_91plus_pct "
        "FROM cc_analytics.semantic_risk_metrics "
        "ORDER BY metric_date DESC LIMIT 30"
    ),
    # Dispute rate by merchant category (default)
    "Dispute Rate": (
        "SELECT merchant_category, "
        "ROUND(SUM(is_fraud) / COUNT(*) * 100, 2) AS dispute_rate_pct, "
        "SUM(is_fraud) AS disputed_txn, "
        "COUNT(*) AS total_txn, "
        "ROUND(AVG(fraud_score), 4) AS avg_fraud_score "
        "FROM cc_analytics.semantic_transaction_summary "
        "GROUP BY merchant_category "
        "ORDER BY dispute_rate_pct DESC"
    ),
    # Utilization snapshot by customer segment
    "Account Utilization": (
        "SELECT customer_segment, country_code, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "COUNT(*) AS customer_count "
        "FROM cc_analytics.semantic_customer_360 "
        "GROUP BY customer_segment, country_code ORDER BY avg_utilization_pct DESC"
    ),
    # Payment status distribution
    "Payment Status": (
        "SELECT payment_status, country_code, customer_segment, "
        "COUNT(*) AS account_count, "
        "ROUND(SUM(amount_outstanding), 2) AS total_outstanding, "
        "ROUND(AVG(overdue_days), 1) AS avg_overdue_days "
        "FROM cc_analytics.semantic_payment_status "
        "GROUP BY payment_status, country_code, customer_segment "
        "ORDER BY account_count DESC LIMIT 20"
    ),
    # Portfolio KPIs by country
    "Portfolio KPIs": (
        "SELECT kpi_month, country_code, total_customers, active_customers, "
        "ROUND(customer_growth_pct * 100, 2) AS growth_pct, "
        "ROUND(churn_rate * 100, 2) AS churn_pct, "
        "ROUND(total_spend, 2) AS total_spend, "
        "ROUND(avg_utilization * 100, 2) AS avg_util_pct, "
        "ROUND(fraud_rate * 100, 4) AS fraud_rate_pct, "
        "ROUND(npl_rate * 100, 2) AS npl_pct, "
        "ROUND(est_interest_income, 2) AS interest_income "
        "FROM cc_analytics.semantic_portfolio_kpis "
        "ORDER BY kpi_month DESC, country_code LIMIT 30"
    ),
    # Customer profile snapshot
    "Customer Profile": (
        "SELECT customer_segment, country_code, "
        "COUNT(*) AS customer_count, "
        "ROUND(AVG(credit_score), 0) AS avg_credit_score, "
        "ROUND(AVG(current_balance), 2) AS avg_balance, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "SUM(is_overdue) AS overdue_count "
        "FROM cc_analytics.semantic_customer_360 "
        "GROUP BY customer_segment, country_code ORDER BY customer_count DESC"
    ),
}

# ── Dimension-aware SQL variants ─────────────────────────────────────────────
# Used when the user's message makes a specific grouping intent clear.
# Keys: (metric_name, dimension_name)  →  SQL string
METRIC_SQL_BY_DIMENSION: dict[tuple[str, str], str] = {

    # Fraud Rate × Geography — "which country has highest fraud", "fraud by country"
    ("Fraud Rate", "Geography"): (
        "SELECT country_code, "
        "ROUND(AVG(fraud_rate) * 100, 2) AS avg_fraud_rate_pct, "
        "ROUND(MAX(fraud_rate) * 100, 2) AS peak_fraud_rate_pct, "
        "ROUND(AVG(avg_fraud_score), 4) AS avg_fraud_score, "
        "SUM(fraud_txn) AS total_fraud_txn, "
        "SUM(total_txn) AS total_txn "
        "FROM cc_analytics.semantic_risk_metrics "
        "GROUP BY country_code "
        "ORDER BY avg_fraud_score DESC, avg_fraud_rate_pct DESC"
    ),

    # Fraud Rate × Merchant Category — "fraud by merchant", "which merchant has highest fraud"
    ("Fraud Rate", "Merchant Category"): (
        "SELECT merchant_category, country_code, "
        "COUNT(*) AS txn_count, "
        "SUM(is_fraud) AS fraud_txn, "
        "ROUND(AVG(fraud_score), 4) AS avg_fraud_score, "
        "ROUND(SUM(is_fraud) / COUNT(*) * 100, 2) AS fraud_rate_pct "
        "FROM cc_analytics.semantic_transaction_summary "
        "GROUP BY merchant_category, country_code "
        "ORDER BY avg_fraud_score DESC, fraud_rate_pct DESC LIMIT 20"
    ),

    # Fraud Rate × Segment
    ("Fraud Rate", "Segment"): (
        "SELECT customer_segment, country_code, "
        "ROUND(AVG(fraud_rate) * 100, 2) AS avg_fraud_rate_pct, "
        "ROUND(AVG(avg_fraud_score), 4) AS avg_fraud_score, "
        "SUM(fraud_txn) AS total_fraud_txn "
        "FROM cc_analytics.semantic_risk_metrics "
        "GROUP BY customer_segment, country_code "
        "ORDER BY avg_fraud_score DESC"
    ),

    # Delinquency Rate × Geography
    ("Delinquency Rate", "Geography"): (
        "SELECT country_code, "
        "ROUND(AVG(delinquency_1_30) * 100, 2) AS dpd_1_30_pct, "
        "ROUND(AVG(delinquency_31_60) * 100, 2) AS dpd_31_60_pct, "
        "ROUND(AVG(delinquency_61_90) * 100, 2) AS dpd_61_90_pct, "
        "ROUND(AVG(delinquency_91plus) * 100, 2) AS dpd_91plus_pct, "
        "SUM(high_risk_accounts) AS high_risk_accounts "
        "FROM cc_analytics.semantic_risk_metrics "
        "GROUP BY country_code "
        "ORDER BY dpd_91plus_pct DESC"
    ),

    # Delinquency Rate × Segment (also used for 'by product type', 'by card type')
    ("Delinquency Rate", "Segment"): (
        "SELECT customer_segment, country_code, "
        "ROUND(AVG(delinquency_1_30) * 100, 2) AS dpd_1_30_pct, "
        "ROUND(AVG(delinquency_31_60) * 100, 2) AS dpd_31_60_pct, "
        "ROUND(AVG(delinquency_61_90) * 100, 2) AS dpd_61_90_pct, "
        "ROUND(AVG(delinquency_91plus) * 100, 2) AS dpd_91plus_pct, "
        "SUM(high_risk_accounts) AS high_risk_accounts "
        "FROM cc_analytics.semantic_risk_metrics "
        "GROUP BY customer_segment, country_code "
        "ORDER BY dpd_91plus_pct DESC"
    ),

    # Delinquency Rate × Merchant Category — proxy via transaction_summary joined to risk metrics
    ("Delinquency Rate", "Merchant Category"): (
        "SELECT srm.customer_segment, srm.country_code, "
        "ROUND(AVG(srm.delinquency_1_30) * 100, 2) AS dpd_1_30_pct, "
        "ROUND(AVG(srm.delinquency_31_60) * 100, 2) AS dpd_31_60_pct, "
        "ROUND(AVG(srm.delinquency_61_90) * 100, 2) AS dpd_61_90_pct, "
        "ROUND(AVG(srm.delinquency_91plus) * 100, 2) AS dpd_91plus_pct, "
        "SUM(srm.high_risk_accounts) AS high_risk_accounts "
        "FROM cc_analytics.semantic_risk_metrics srm "
        "GROUP BY srm.customer_segment, srm.country_code "
        "ORDER BY dpd_91plus_pct DESC"
    ),

    # Delinquency Rate × Overdue Bucket
    ("Delinquency Rate", "Overdue Bucket"): (
        "SELECT "
        "  SUM(ROUND(delinquency_1_30 * total_txn, 0)) AS dpd_1_30_accounts, "
        "  SUM(ROUND(delinquency_31_60 * total_txn, 0)) AS dpd_31_60_accounts, "
        "  SUM(ROUND(delinquency_61_90 * total_txn, 0)) AS dpd_61_90_accounts, "
        "  SUM(ROUND(delinquency_91plus * total_txn, 0)) AS dpd_91plus_accounts, "
        "  SUM(high_risk_accounts) AS high_risk_accounts, "
        "  COUNT(DISTINCT country_code) AS countries "
        "FROM cc_analytics.semantic_risk_metrics"
    ),

    # Total Spend × Geography
    ("Total Spend", "Geography"): (
        "SELECT country_code, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "SUM(transaction_count) AS transaction_count, "
        "ROUND(AVG(avg_txn_amount), 2) AS avg_txn_amount "
        "FROM cc_analytics.semantic_spend_metrics "
        "GROUP BY country_code "
        "ORDER BY total_spend DESC"
    ),

    # Total Spend × Merchant Category
    ("Total Spend", "Merchant Category"): (
        "SELECT merchant_category, country_code, "
        "ROUND(SUM(amount), 2) AS total_spend, "
        "COUNT(*) AS txn_count, "
        "ROUND(AVG(amount), 2) AS avg_txn_amount "
        "FROM cc_analytics.semantic_transaction_summary "
        "WHERE transaction_type = 'PURCHASE' AND auth_status = 'APPROVED' "
        "GROUP BY merchant_category, country_code "
        "ORDER BY total_spend DESC LIMIT 20"
    ),

    # Total Spend × Segment
    ("Total Spend", "Segment"): (
        "SELECT customer_segment, country_code, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "COUNT(DISTINCT customer_id) AS customer_count, "
        "ROUND(AVG(avg_txn_amount), 2) AS avg_txn_amount "
        "FROM cc_analytics.semantic_spend_metrics "
        "GROUP BY customer_segment, country_code "
        "ORDER BY total_spend DESC"
    ),

    # Transaction Count × Geography
    ("Transaction Count", "Geography"): (
        "SELECT country_code, "
        "SUM(is_approved) AS approved_txn, "
        "SUM(is_declined) AS declined_txn, "
        "COUNT(*) AS total_txn, "
        "ROUND(SUM(is_declined) / COUNT(*) * 100, 2) AS decline_rate_pct "
        "FROM cc_analytics.semantic_transaction_summary "
        "GROUP BY country_code "
        "ORDER BY total_txn DESC"
    ),

    # Transaction Count × Merchant Category (same as default, already good)

    # Account Utilization × Geography
    ("Account Utilization", "Geography"): (
        "SELECT country_code, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "COUNT(*) AS customer_count, "
        "SUM(is_overdue) AS overdue_count "
        "FROM cc_analytics.semantic_customer_360 "
        "GROUP BY country_code "
        "ORDER BY avg_utilization_pct DESC"
    ),

    # Portfolio KPIs × Geography — "compare portfolio by country", "across countries"
    ("Portfolio KPIs", "Geography"): (
        "SELECT country_code, "
        "SUM(total_customers) AS total_customers, "
        "ROUND(AVG(customer_growth_pct) * 100, 2) AS avg_growth_pct, "
        "ROUND(AVG(churn_rate) * 100, 2) AS avg_churn_pct, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "ROUND(AVG(avg_utilization) * 100, 2) AS avg_utilization_pct, "
        "ROUND(AVG(fraud_rate) * 100, 4) AS avg_fraud_rate_pct, "
        "ROUND(AVG(npl_rate) * 100, 2) AS avg_npl_pct, "
        "ROUND(SUM(est_interest_income), 2) AS total_interest_income "
        "FROM cc_analytics.semantic_portfolio_kpis "
        "GROUP BY country_code "
        "ORDER BY total_spend DESC"
    ),

    # Portfolio KPIs × Legal Entity
    ("Portfolio KPIs", "Legal Entity"): (
        "SELECT legal_entity, country_code, "
        "SUM(total_customers) AS total_customers, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "ROUND(AVG(npl_rate) * 100, 2) AS avg_npl_pct, "
        "ROUND(SUM(est_interest_income), 2) AS total_interest_income "
        "FROM cc_analytics.semantic_portfolio_kpis "
        "GROUP BY legal_entity, country_code "
        "ORDER BY total_spend DESC"
    ),

    # Payment Status × Geography
    ("Payment Status", "Geography"): (
        "SELECT country_code, payment_status, "
        "COUNT(*) AS account_count, "
        "ROUND(SUM(amount_outstanding), 2) AS total_outstanding, "
        "ROUND(AVG(overdue_days), 1) AS avg_overdue_days "
        "FROM cc_analytics.semantic_payment_status "
        "GROUP BY country_code, payment_status "
        "ORDER BY account_count DESC LIMIT 20"
    ),

    # Payment Status × Segment
    ("Payment Status", "Segment"): (
        "SELECT customer_segment, payment_status, "
        "COUNT(*) AS account_count, "
        "ROUND(SUM(amount_outstanding), 2) AS total_outstanding, "
        "ROUND(AVG(overdue_days), 1) AS avg_overdue_days "
        "FROM cc_analytics.semantic_payment_status "
        "GROUP BY customer_segment, payment_status "
        "ORDER BY total_outstanding DESC LIMIT 20"
    ),

    # Customer Profile × Geography
    ("Customer Profile", "Geography"): (
        "SELECT country_code, customer_segment, "
        "COUNT(*) AS customer_count, "
        "ROUND(AVG(credit_score), 0) AS avg_credit_score, "
        "ROUND(AVG(current_balance), 2) AS avg_balance, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "SUM(is_overdue) AS overdue_count "
        "FROM cc_analytics.semantic_customer_360 "
        "GROUP BY country_code, customer_segment "
        "ORDER BY customer_count DESC"
    ),

    # Account Utilization × Segment
    ("Account Utilization", "Segment"): (
        "SELECT customer_segment, country_code, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "COUNT(*) AS customer_count, "
        "SUM(is_overdue) AS overdue_count "
        "FROM cc_analytics.semantic_customer_360 "
        "GROUP BY customer_segment, country_code "
        "ORDER BY avg_utilization_pct DESC"
    ),

    # Dispute Rate × Merchant Category (same as default canonical)
    ("Dispute Rate", "Merchant Category"): (
        "SELECT merchant_category, "
        "COUNT(*) AS total_txn, "
        "SUM(is_fraud) AS disputed_txn, "
        "ROUND(SUM(is_fraud) / COUNT(*) * 100, 2) AS dispute_rate_pct, "
        "ROUND(AVG(fraud_score), 4) AS avg_fraud_score "
        "FROM cc_analytics.semantic_transaction_summary "
        "GROUP BY merchant_category "
        "ORDER BY dispute_rate_pct DESC"
    ),

    # Dispute Rate × Geography
    ("Dispute Rate", "Geography"): (
        "SELECT country_code, "
        "COUNT(*) AS total_txn, "
        "SUM(is_fraud) AS disputed_txn, "
        "ROUND(SUM(is_fraud) / COUNT(*) * 100, 2) AS dispute_rate_pct, "
        "ROUND(AVG(fraud_score), 4) AS avg_fraud_score "
        "FROM cc_analytics.semantic_transaction_summary "
        "GROUP BY country_code "
        "ORDER BY dispute_rate_pct DESC"
    ),

    # Dispute Rate × Channel
    ("Dispute Rate", "Channel"): (
        "SELECT channel, "
        "COUNT(*) AS total_txn, "
        "SUM(is_fraud) AS disputed_txn, "
        "ROUND(SUM(is_fraud) / COUNT(*) * 100, 2) AS dispute_rate_pct, "
        "ROUND(AVG(fraud_score), 4) AS avg_fraud_score "
        "FROM cc_analytics.semantic_transaction_summary "
        "GROUP BY channel "
        "ORDER BY dispute_rate_pct DESC"
    ),

    # Dispute Rate × Segment
    ("Dispute Rate", "Segment"): (
        "SELECT srm.customer_segment, srm.country_code, "
        "ROUND(AVG(srm.fraud_rate) * 100, 2) AS dispute_rate_pct, "
        "ROUND(AVG(srm.avg_fraud_score), 4) AS avg_fraud_score, "
        "SUM(srm.fraud_txn) AS disputed_txn "
        "FROM cc_analytics.semantic_risk_metrics srm "
        "GROUP BY srm.customer_segment, srm.country_code "
        "ORDER BY dispute_rate_pct DESC"
    ),

}

# ---------------------------------------------------------------------------
# Live catalog — merged with DB metadata at import time
# ---------------------------------------------------------------------------
try:
    from app.semantic.db_loader import build_merged_catalog as _build_merged_catalog
    SEMANTIC_CATALOG: dict = _build_merged_catalog(_HARDCODED_CATALOG)
except Exception as _exc:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Failed to build merged catalog, using hardcoded fallback: %s", _exc
    )
    SEMANTIC_CATALOG = _HARDCODED_CATALOG
