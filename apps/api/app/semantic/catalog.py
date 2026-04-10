_HARDCODED_CATALOG: dict = {
    "metrics": [
        {
            "name": "Total Spend",
            "keywords": ["total spend", "spend", "transaction amount", "purchase amount", "spending", "expenditure", "volume", "sales", "how much spent", "category spend"],
            "dimensions": ["Month", "Geography", "Merchant Category", "Segment", "Channel"],
            "engine": "starrocks",
            "domain": "spend",
            "definition": "Sum of all purchase transaction amounts (approved, transaction_type=PURCHASE).",
            "source_table": "cc_analytics.dp_customer_spend_monthly",
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
            "source_table": "cc_analytics.semantic_deposit_portfolio",
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
            "source_table": "cc_analytics.dp_transaction_enriched",
        },
        {
            "name": "Dispute Rate",
            "keywords": ["dispute", "disputes", "dispute rate", "chargeback", "chargebacks", "contested", "disputed transaction", "fraud dispute", "claim"],
            "dimensions": ["Merchant Category", "Geography", "Channel", "Segment", "Date"],
            "engine": "starrocks",
            "domain": "risk",
            "definition": "Ratio of disputed (fraudulent or contested) transactions to total transactions, by merchant or geography.",
            "source_table": "cc_analytics.dp_transaction_enriched",
        },
        {
            "name": "Deposit Portfolio",
            "keywords": ["deposit", "savings", "fixed deposit", "fd", "current account", "savings balance", "fd balance", "deposit balance", "term deposit", "maturity", "interest earned", "salary credit", "casa"],
            "dimensions": ["Month", "Segment", "Geography", "Deposit Category", "FD Tenor"],
            "engine": "starrocks",
            "domain": "deposits",
            "definition": "Customer-level deposit portfolio snapshot covering savings, current, and fixed deposit balances with interest metrics.",
            "source_table": "cc_analytics.semantic_deposit_portfolio",
        },
        {
            "name": "Loan Portfolio",
            "keywords": ["loan", "loans", "outstanding loan", "emi", "personal loan", "home loan", "auto loan", "education loan", "business loan", "npa", "non-performing", "dpd", "overdue loan", "repayment", "loan outstanding", "debt"],
            "dimensions": ["Month", "Segment", "Geography", "Loan Type", "DPD Bucket", "Loan Status"],
            "engine": "starrocks",
            "domain": "loans",
            "definition": "Customer-level loan portfolio covering outstanding balances, EMI, DPD, NPA classification by loan type.",
            "source_table": "cc_analytics.semantic_loan_portfolio",
        },
        {
            "name": "Customer Product Mix",
            "keywords": ["product mix", "product holdings", "cross-sell", "wallet share", "products held", "how many products", "product count", "has loan", "has deposit", "has credit card", "product penetration", "multi-product", "customer holdings"],
            "dimensions": ["Segment", "Geography", "Age Band", "Product Domain"],
            "engine": "starrocks",
            "domain": "cross_product",
            "definition": "Per-customer snapshot of all product holdings across CC, deposits, and loans with wallet share score.",
            "source_table": "cc_analytics.semantic_customer_product_mix",
        },
    ],
    "dimensions": [
        {"name": "Date", "keywords": ["date", "day", "period", "today", "yesterday", "last 7 days", "last 30 days"]},
        {"name": "Month", "keywords": ["month", "monthly", "billing cycle", "per month", "year-month"]},
        {"name": "Geography", "keywords": ["country", "country code", "country_code", "singapore", "malaysia", "india", "per country", "by country", "each country", "region", "location", "geography"]},
        {"name": "Merchant Category", "keywords": ["mcc", "merchant category", "merchant type", "merchant", "by merchant", "per merchant", "food", "retail", "travel", "grocery"]},
        {"name": "Channel", "keywords": ["channel", "online", "in-store", "atm", "mobile", "e-commerce", "pos", "contactless", "by channel"]},
        {"name": "Segment", "keywords": ["segment", "customer segment", "mass", "affluent", "premium", "tier", "by segment", "per segment", "product type", "product category", "card product", "card type", "account type", "by product", "by account", "card tier"]},
        {"name": "Overdue Bucket", "keywords": ["overdue bucket", "1-30", "31-60", "61-90", "91+", "dpd", "days past due", "delinquency bucket"]},
        {"name": "Age Band", "keywords": ["age band", "age group", "25-34", "35-44", "45-54", "55+", "young", "senior", "by age"]},
        {"name": "Payment Method", "keywords": ["payment method", "giro", "paynow", "upi", "fpxpay", "bank transfer", "online banking"]},
        {"name": "Legal Entity", "keywords": ["legal entity", "sg_bank", "my_bank", "in_bank", "entity", "subsidiary", "by entity"]},
        {"name": "Deposit Category", "keywords": ["deposit type", "savings", "current", "term deposit", "fixed deposit", "fd", "casa", "deposit category"]},
        {"name": "FD Tenor", "keywords": ["fd tenor", "3 month", "6 month", "12 month", "24 month", "36 month", "tenor", "maturity period"]},
        {"name": "Loan Type", "keywords": ["loan type", "personal loan", "home loan", "auto loan", "education loan", "business loan", "renovation loan", "secured", "unsecured"]},
        {"name": "Loan Status", "keywords": ["loan status", "performing", "watchlist", "sub-standard", "doubtful", "npa", "closed loan"]},
        {"name": "DPD Bucket", "keywords": ["dpd", "days past due", "1-30 dpd", "31-60 dpd", "61-90 dpd", "91+", "npa bucket", "overdue loan"]},
        {"name": "Balance Band", "keywords": ["balance band", "balance tier", "low balance", "high balance", "account balance range"]},
        {"name": "Product Domain", "keywords": ["product domain", "credit card", "deposits", "loans", "all products", "banking product"]},
    ],
}

# Canonical SQL per metric — directly executable against StarRocks cc_analytics
METRIC_CANONICAL_SQL = {
    # Monthly spend trend across all countries (using dp_customer_spend_monthly)
    "Total Spend": (
        "SELECT year_month AS spend_month, country_code, "
        "SUM(transaction_count) AS transaction_count, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "ROUND(AVG(avg_transaction_amount), 2) AS avg_txn_amount "
        "FROM cc_analytics.dp_customer_spend_monthly "
        "GROUP BY year_month, country_code "
        "ORDER BY spend_month ASC, total_spend DESC LIMIT 36"
    ),
    # Transaction count by merchant category
    "Transaction Count": (
        "SELECT merchant_category, country_code, "
        "SUM(IF(status='approved', 1, 0)) AS approved_txn, "
        "SUM(IF(status='declined', 1, 0)) AS declined_txn, "
        "COUNT(*) AS total_txn "
        "FROM cc_analytics.dp_transaction_enriched "
        "GROUP BY merchant_category, country_code ORDER BY total_txn DESC LIMIT 20"
    ),
    # Fraud rate by date (default — for trend queries)
    "Fraud Rate": (
        "SELECT metric_date, country_code, "
        "ROUND(fraud_rate * 100, 4) AS fraud_rate_pct, "
        "ROUND(decline_rate * 100, 4) AS decline_rate_pct, "
        "ROUND(avg_fraud_score, 4) AS avg_fraud_score, "
        "fraud_transactions, total_transactions "
        "FROM cc_analytics.semantic_risk_metrics "
        "ORDER BY metric_date DESC, fraud_rate DESC LIMIT 36"
    ),
    # Delinquency buckets by country
    "Delinquency Rate": (
        "SELECT metric_date, country_code, "
        "ROUND(delinquency_rate_1_30 * 100, 2) AS dpd_1_30_pct, "
        "ROUND(delinquency_rate_31_60 * 100, 2) AS dpd_31_60_pct, "
        "ROUND(delinquency_rate_61_90 * 100, 2) AS dpd_61_90_pct, "
        "ROUND(delinquency_rate_91_plus * 100, 2) AS dpd_91plus_pct "
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
        "FROM cc_analytics.dp_transaction_enriched "
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
        "ROUND(SUM(amount_still_owed), 2) AS total_outstanding, "
        "ROUND(AVG(overdue_days), 1) AS avg_overdue_days "
        "FROM cc_analytics.semantic_payment_status "
        "GROUP BY payment_status, country_code, customer_segment "
        "ORDER BY account_count DESC LIMIT 20"
    ),
    # Portfolio KPIs from deposit portfolio (semantic_portfolio_kpis is empty)
    "Portfolio KPIs": (
        "SELECT snapshot_month AS kpi_month, country_code, customer_segment, "
        "COUNT(DISTINCT customer_id) AS total_customers, "
        "ROUND(SUM(total_deposit_balance), 2) AS total_deposit_balance, "
        "ROUND(SUM(savings_balance), 2) AS savings_balance, "
        "ROUND(SUM(total_fd_balance), 2) AS fd_balance, "
        "ROUND(AVG(fd_avg_rate) * 100, 2) AS avg_fd_rate_pct, "
        "ROUND(SUM(avg_monthly_credit), 2) AS total_monthly_credit "
        "FROM cc_analytics.semantic_deposit_portfolio "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_deposit_portfolio) "
        "GROUP BY snapshot_month, country_code, customer_segment "
        "ORDER BY total_deposit_balance DESC LIMIT 30"
    ),
    # Customer profile snapshot
    "Customer Profile": (
        "SELECT customer_segment, country_code, "
        "COUNT(*) AS customer_count, "
        "ROUND(AVG(current_balance), 2) AS avg_balance, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "ROUND(AVG(spend_last_30d), 2) AS avg_spend_last_30d, "
        "SUM(is_overdue) AS overdue_count "
        "FROM cc_analytics.semantic_customer_360 "
        "GROUP BY customer_segment, country_code ORDER BY customer_count DESC"
    ),
    # Deposit portfolio by customer segment
    "Deposit Portfolio": (
        "SELECT snapshot_month, country_code, customer_segment, "
        "COUNT(DISTINCT customer_id) AS customer_count, "
        "ROUND(SUM(total_deposit_balance), 2) AS total_deposit_balance, "
        "ROUND(SUM(savings_balance), 2) AS savings_balance, "
        "ROUND(SUM(total_fd_balance), 2) AS fd_balance, "
        "ROUND(AVG(fd_avg_rate) * 100, 2) AS avg_fd_rate_pct, "
        "SUM(fd_count) AS total_fd_accounts, "
        "ROUND(SUM(fd_maturing_next_30d), 2) AS fd_maturing_30d "
        "FROM cc_analytics.semantic_deposit_portfolio "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_deposit_portfolio) "
        "GROUP BY snapshot_month, country_code, customer_segment "
        "ORDER BY total_deposit_balance DESC"
    ),
    # Loan portfolio by customer segment
    "Loan Portfolio": (
        "SELECT snapshot_month, country_code, customer_segment, "
        "COUNT(DISTINCT customer_id) AS borrower_count, "
        "ROUND(SUM(total_loan_outstanding), 2) AS total_outstanding, "
        "ROUND(SUM(personal_loan_outstanding), 2) AS personal_loan_outstanding, "
        "ROUND(SUM(home_loan_outstanding), 2) AS home_loan_outstanding, "
        "ROUND(SUM(auto_loan_outstanding), 2) AS auto_loan_outstanding, "
        "ROUND(SUM(total_monthly_emi), 2) AS total_emi, "
        "SUM(is_npa) AS npa_count, "
        "ROUND(AVG(loan_to_income_ratio), 4) AS avg_lti "
        "FROM cc_analytics.semantic_loan_portfolio "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_loan_portfolio) "
        "GROUP BY snapshot_month, country_code, customer_segment "
        "ORDER BY total_outstanding DESC"
    ),
    # Product mix by segment
    "Customer Product Mix": (
        "SELECT customer_segment, country_code, "
        "COUNT(DISTINCT customer_id) AS customer_count, "
        "SUM(has_credit_card) AS cc_holders, "
        "SUM(has_savings + has_current + has_fd) AS deposit_holders, "
        "SUM(has_loan) AS loan_holders, "
        "ROUND(AVG(total_product_count), 2) AS avg_products, "
        "ROUND(AVG(wallet_share_score), 4) AS avg_wallet_share, "
        "ROUND(SUM(total_asset_balance), 2) AS total_assets "
        "FROM cc_analytics.semantic_customer_product_mix "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_customer_product_mix) "
        "GROUP BY customer_segment, country_code "
        "ORDER BY customer_count DESC"
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
        "SUM(fraud_transactions) AS total_fraud_txn, "
        "SUM(total_transactions) AS total_txn "
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
        "FROM cc_analytics.dp_transaction_enriched "
        "GROUP BY merchant_category, country_code "
        "ORDER BY avg_fraud_score DESC, fraud_rate_pct DESC LIMIT 20"
    ),

    # Fraud Rate × Segment
    ("Fraud Rate", "Segment"): (
        "SELECT customer_segment, country_code, "
        "ROUND(AVG(fraud_rate) * 100, 2) AS avg_fraud_rate_pct, "
        "ROUND(AVG(avg_fraud_score), 4) AS avg_fraud_score, "
        "SUM(fraud_transactions) AS total_fraud_txn "
        "FROM cc_analytics.semantic_risk_metrics "
        "GROUP BY customer_segment, country_code "
        "ORDER BY avg_fraud_score DESC"
    ),

    # Delinquency Rate × Geography
    ("Delinquency Rate", "Geography"): (
        "SELECT country_code, "
        "ROUND(AVG(delinquency_rate_1_30) * 100, 2) AS dpd_1_30_pct, "
        "ROUND(AVG(delinquency_rate_31_60) * 100, 2) AS dpd_31_60_pct, "
        "ROUND(AVG(delinquency_rate_61_90) * 100, 2) AS dpd_61_90_pct, "
        "ROUND(AVG(delinquency_rate_91_plus) * 100, 2) AS dpd_91plus_pct, "
        "SUM(high_risk_transactions) AS high_risk_accounts "
        "FROM cc_analytics.semantic_risk_metrics "
        "GROUP BY country_code "
        "ORDER BY dpd_91plus_pct DESC"
    ),

    # Delinquency Rate × Segment (also used for 'by product type', 'by card type')
    ("Delinquency Rate", "Segment"): (
        "SELECT customer_segment, country_code, "
        "ROUND(AVG(delinquency_rate_1_30) * 100, 2) AS dpd_1_30_pct, "
        "ROUND(AVG(delinquency_rate_31_60) * 100, 2) AS dpd_31_60_pct, "
        "ROUND(AVG(delinquency_rate_61_90) * 100, 2) AS dpd_61_90_pct, "
        "ROUND(AVG(delinquency_rate_91_plus) * 100, 2) AS dpd_91plus_pct, "
        "SUM(high_risk_transactions) AS high_risk_accounts "
        "FROM cc_analytics.semantic_risk_metrics "
        "GROUP BY customer_segment, country_code "
        "ORDER BY dpd_91plus_pct DESC"
    ),

    # Delinquency Rate × Merchant Category — proxy via transaction_summary joined to risk metrics
    ("Delinquency Rate", "Merchant Category"): (
        "SELECT srm.customer_segment, srm.country_code, "
        "ROUND(AVG(srm.delinquency_rate_1_30) * 100, 2) AS dpd_1_30_pct, "
        "ROUND(AVG(srm.delinquency_rate_31_60) * 100, 2) AS dpd_31_60_pct, "
        "ROUND(AVG(srm.delinquency_rate_61_90) * 100, 2) AS dpd_61_90_pct, "
        "ROUND(AVG(srm.delinquency_rate_91_plus) * 100, 2) AS dpd_91plus_pct, "
        "SUM(srm.high_risk_transactions) AS high_risk_accounts "
        "FROM cc_analytics.semantic_risk_metrics srm "
        "GROUP BY srm.customer_segment, srm.country_code "
        "ORDER BY dpd_91plus_pct DESC"
    ),

    # Delinquency Rate × Overdue Bucket
    ("Delinquency Rate", "Overdue Bucket"): (
        "SELECT "
        "  SUM(ROUND(delinquency_rate_1_30 * total_transactions, 0)) AS dpd_1_30_accounts, "
        "  SUM(ROUND(delinquency_rate_31_60 * total_transactions, 0)) AS dpd_31_60_accounts, "
        "  SUM(ROUND(delinquency_rate_61_90 * total_transactions, 0)) AS dpd_61_90_accounts, "
        "  SUM(ROUND(delinquency_rate_91_plus * total_transactions, 0)) AS dpd_91plus_accounts, "
        "  SUM(high_risk_transactions) AS high_risk_accounts, "
        "  COUNT(DISTINCT country_code) AS countries "
        "FROM cc_analytics.semantic_risk_metrics"
    ),

    # Total Spend × Geography
    ("Total Spend", "Geography"): (
        "SELECT country_code, "
        "SUM(transaction_count) AS transaction_count, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "ROUND(AVG(avg_transaction_amount), 2) AS avg_txn_amount "
        "FROM cc_analytics.dp_customer_spend_monthly "
        "GROUP BY country_code "
        "ORDER BY total_spend DESC"
    ),

    # Total Spend × Merchant Category — use dp_customer_spend_monthly
    ("Total Spend", "Merchant Category"): (
        "SELECT merchant_category, country_code, "
        "SUM(transaction_count) AS txn_count, "
        "ROUND(SUM(total_spend), 2) AS total_spend, "
        "ROUND(AVG(avg_transaction_amount), 2) AS avg_txn_amount "
        "FROM cc_analytics.dp_customer_spend_monthly "
        "GROUP BY merchant_category, country_code "
        "ORDER BY total_spend DESC"
    ),

    # Total Spend × Segment — use semantic_deposit_portfolio (has customer_segment and spend data)
    ("Total Spend", "Segment"): (
        "SELECT customer_segment, country_code, "
        "COUNT(DISTINCT customer_id) AS customer_count, "
        "ROUND(SUM(total_deposit_balance), 2) AS total_balance, "
        "ROUND(SUM(avg_monthly_credit), 2) AS monthly_credit_volume, "
        "ROUND(SUM(avg_monthly_debit), 2) AS monthly_debit_volume "
        "FROM cc_analytics.semantic_deposit_portfolio "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_deposit_portfolio) "
        "GROUP BY customer_segment, country_code "
        "ORDER BY total_balance DESC"
    ),

    # Transaction Count × Geography
    ("Transaction Count", "Geography"): (
        "SELECT country_code, "
        "SUM(IF(status='approved', 1, 0)) AS approved_txn, "
        "SUM(IF(status='declined', 1, 0)) AS declined_txn, "
        "COUNT(*) AS total_txn, "
        "ROUND(SUM(IF(status='declined', 1, 0)) / COUNT(*) * 100, 2) AS decline_rate_pct "
        "FROM cc_analytics.dp_transaction_enriched "
        "GROUP BY country_code "
        "ORDER BY total_txn DESC"
    ),

    # Transaction Count × Merchant Category (same as default, already good)

    # Account Utilization × Geography
    ("Account Utilization", "Geography"): (
        "SELECT country_code, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "COUNT(*) AS customer_count, "
        "SUM(is_overdue) AS overdue_count, "
        "ROUND(AVG(spend_last_30d), 2) AS avg_spend_last_30d "
        "FROM cc_analytics.semantic_customer_360 "
        "GROUP BY country_code "
        "ORDER BY avg_utilization_pct DESC"
    ),

    # Portfolio KPIs × Geography — from deposit portfolio by country
    ("Portfolio KPIs", "Geography"): (
        "SELECT country_code, "
        "COUNT(DISTINCT customer_id) AS total_customers, "
        "ROUND(SUM(total_deposit_balance), 2) AS total_deposit_balance, "
        "ROUND(SUM(savings_balance), 2) AS savings_balance, "
        "ROUND(SUM(total_fd_balance), 2) AS fd_balance, "
        "ROUND(AVG(fd_avg_rate) * 100, 2) AS avg_fd_rate_pct "
        "FROM cc_analytics.semantic_deposit_portfolio "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_deposit_portfolio) "
        "GROUP BY country_code "
        "ORDER BY total_deposit_balance DESC"
    ),

    # Portfolio KPIs × Legal Entity — from deposit portfolio by entity
    ("Portfolio KPIs", "Legal Entity"): (
        "SELECT legal_entity, country_code, "
        "COUNT(DISTINCT customer_id) AS total_customers, "
        "ROUND(SUM(total_deposit_balance), 2) AS total_deposit_balance, "
        "ROUND(SUM(avg_monthly_credit), 2) AS monthly_credit_inflow "
        "FROM cc_analytics.semantic_deposit_portfolio "
        "GROUP BY legal_entity, country_code "
        "ORDER BY total_deposit_balance DESC"
    ),

    # Payment Status × Geography
    ("Payment Status", "Geography"): (
        "SELECT country_code, payment_status, "
        "COUNT(*) AS account_count, "
        "ROUND(SUM(amount_still_owed), 2) AS total_outstanding, "
        "ROUND(AVG(overdue_days), 1) AS avg_overdue_days "
        "FROM cc_analytics.semantic_payment_status "
        "GROUP BY country_code, payment_status "
        "ORDER BY account_count DESC LIMIT 20"
    ),

    # Payment Status × Segment
    ("Payment Status", "Segment"): (
        "SELECT customer_segment, payment_status, "
        "COUNT(*) AS account_count, "
        "ROUND(SUM(amount_still_owed), 2) AS total_outstanding, "
        "ROUND(AVG(overdue_days), 1) AS avg_overdue_days "
        "FROM cc_analytics.semantic_payment_status "
        "GROUP BY customer_segment, payment_status "
        "ORDER BY total_outstanding DESC LIMIT 20"
    ),

    # Customer Profile × Geography
    ("Customer Profile", "Geography"): (
        "SELECT country_code, customer_segment, "
        "COUNT(*) AS customer_count, "
        "ROUND(AVG(current_balance), 2) AS avg_balance, "
        "ROUND(AVG(utilization_pct) * 100, 2) AS avg_utilization_pct, "
        "ROUND(AVG(spend_last_30d), 2) AS avg_spend_last_30d, "
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
        "SUM(is_overdue) AS overdue_count, "
        "ROUND(AVG(spend_last_30d), 2) AS avg_spend_last_30d "
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
        "FROM cc_analytics.dp_transaction_enriched "
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
        "FROM cc_analytics.dp_transaction_enriched "
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
        "FROM cc_analytics.dp_transaction_enriched "
        "GROUP BY channel "
        "ORDER BY dispute_rate_pct DESC"
    ),

    # Dispute Rate × Segment
    ("Dispute Rate", "Segment"): (
        "SELECT srm.customer_segment, srm.country_code, "
        "ROUND(AVG(srm.fraud_rate) * 100, 2) AS dispute_rate_pct, "
        "ROUND(AVG(srm.avg_fraud_score), 4) AS avg_fraud_score, "
        "SUM(srm.fraud_transactions) AS disputed_txn "
        "FROM cc_analytics.semantic_risk_metrics srm "
        "GROUP BY srm.customer_segment, srm.country_code "
        "ORDER BY dispute_rate_pct DESC"
    ),

    # Deposit Portfolio × Geography
    ("Deposit Portfolio", "Geography"): (
        "SELECT country_code, "
        "ROUND(SUM(total_deposit_balance), 2) AS total_deposit_balance, "
        "ROUND(SUM(savings_balance), 2) AS savings_balance, "
        "ROUND(SUM(total_fd_balance), 2) AS fd_balance, "
        "ROUND(AVG(fd_avg_rate) * 100, 2) AS avg_fd_rate_pct, "
        "SUM(fd_count) AS total_fd_accounts "
        "FROM cc_analytics.semantic_deposit_portfolio "
        "GROUP BY country_code ORDER BY total_deposit_balance DESC"
    ),

    # Deposit Portfolio × Deposit Category — CASA vs FD breakdown
    ("Deposit Portfolio", "Deposit Category"): (
        "SELECT country_code, customer_segment, "
        "ROUND(SUM(savings_balance + current_balance), 2) AS casa_balance, "
        "ROUND(SUM(total_fd_balance), 2) AS fd_balance, "
        "SUM(fd_count) AS fd_accounts, "
        "ROUND(SUM(fd_maturing_next_30d), 2) AS fd_maturing_30d "
        "FROM cc_analytics.semantic_deposit_portfolio "
        "GROUP BY country_code, customer_segment "
        "ORDER BY fd_balance DESC"
    ),

    # Loan Portfolio × Geography
    ("Loan Portfolio", "Geography"): (
        "SELECT country_code, "
        "COUNT(DISTINCT customer_id) AS borrower_count, "
        "ROUND(SUM(total_loan_outstanding), 2) AS total_outstanding, "
        "ROUND(SUM(total_monthly_emi), 2) AS total_emi, "
        "SUM(is_npa) AS npa_count, "
        "ROUND(SUM(total_overdue_amount), 2) AS total_overdue_amount, "
        "ROUND(AVG(loan_to_income_ratio), 4) AS avg_lti "
        "FROM cc_analytics.semantic_loan_portfolio "
        "GROUP BY country_code ORDER BY total_outstanding DESC"
    ),

    # Loan Portfolio × Loan Type
    ("Loan Portfolio", "Loan Type"): (
        "SELECT country_code, customer_segment, "
        "ROUND(SUM(personal_loan_outstanding), 2) AS personal_loan, "
        "ROUND(SUM(home_loan_outstanding), 2) AS home_loan, "
        "ROUND(SUM(auto_loan_outstanding), 2) AS auto_loan, "
        "COUNT(DISTINCT CASE WHEN personal_loan_id IS NOT NULL THEN customer_id END) AS personal_borrowers, "
        "COUNT(DISTINCT CASE WHEN home_loan_id IS NOT NULL THEN customer_id END) AS home_borrowers, "
        "COUNT(DISTINCT CASE WHEN auto_loan_id IS NOT NULL THEN customer_id END) AS auto_borrowers "
        "FROM cc_analytics.semantic_loan_portfolio "
        "GROUP BY country_code, customer_segment "
        "ORDER BY personal_loan DESC"
    ),

    # Loan Portfolio × DPD Bucket
    ("Loan Portfolio", "DPD Bucket"): (
        "SELECT overdue_bucket, country_code, "
        "COUNT(*) AS loan_count, "
        "ROUND(SUM(total_loan_outstanding), 2) AS total_outstanding, "
        "SUM(is_npa) AS npa_count, "
        "ROUND(SUM(total_overdue_amount), 2) AS overdue_amount "
        "FROM cc_analytics.semantic_loan_portfolio "
        "GROUP BY overdue_bucket, country_code "
        "ORDER BY FIELD(overdue_bucket, 'CURRENT', '1-30 DPD', '31-60 DPD', '61-90 DPD', '91-180 DPD', 'NPA')"
    ),

    # Customer Product Mix × Geography
    ("Customer Product Mix", "Geography"): (
        "SELECT country_code, customer_segment, "
        "COUNT(DISTINCT customer_id) AS customer_count, "
        "ROUND(AVG(total_product_count), 2) AS avg_products, "
        "ROUND(AVG(wallet_share_score), 4) AS avg_wallet_share, "
        "SUM(has_credit_card) AS cc_holders, "
        "SUM(has_fd) AS fd_holders, "
        "SUM(has_loan) AS loan_holders "
        "FROM cc_analytics.semantic_customer_product_mix "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_customer_product_mix) "
        "GROUP BY country_code, customer_segment "
        "ORDER BY customer_count DESC"
    ),

    # Customer Product Mix × Age Band
    ("Customer Product Mix", "Age Band"): (
        "SELECT age_band, customer_segment, country_code, "
        "COUNT(DISTINCT customer_id) AS customer_count, "
        "ROUND(AVG(total_product_count), 2) AS avg_products, "
        "ROUND(AVG(wallet_share_score), 4) AS avg_wallet_share, "
        "SUM(has_credit_card) AS cc_holders, "
        "SUM(has_fd) AS fd_holders, "
        "SUM(has_loan) AS loan_holders "
        "FROM cc_analytics.semantic_customer_product_mix "
        "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_customer_product_mix) "
        "GROUP BY age_band, customer_segment, country_code "
        "ORDER BY customer_count DESC"
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
