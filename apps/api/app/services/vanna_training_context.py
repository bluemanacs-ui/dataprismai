def build_training_context(semantic_context: dict) -> dict:
    metric = semantic_context.get("metric", "Total Spend")
    dimensions = semantic_context.get("dimensions", ["Geography", "Month"])
    domain = semantic_context.get("domain", "deposit_banking")
    definition = semantic_context.get("definition", "cc_analytics deposit banking platform.")

    ddl = """
-- Database: cc_analytics (StarRocks / MySQL-compatible)
-- Countries: SG, MY, IN | Year: 2025 | Deposit & loan banking analytics

CREATE TABLE cc_analytics.semantic_customer_360 (
    customer_id VARCHAR(20), country_code VARCHAR(2), legal_entity VARCHAR(10),
    full_name VARCHAR(100), customer_segment VARCHAR(20), risk_rating VARCHAR(10),
    kyc_status VARCHAR(20), age INT, age_band VARCHAR(15), income_band VARCHAR(20),
    tenure_months INT, primary_account_id VARCHAR(20), primary_account_type VARCHAR(20),
    current_balance DECIMAL(20,2), available_balance DECIMAL(20,2),
    credit_limit DECIMAL(20,2), utilization_pct DECIMAL(8,4),
    active_card_count INT, spend_last_30d DECIMAL(20,2),
    transaction_count_last_30d INT, top_spend_category VARCHAR(50),
    payment_status VARCHAR(20), total_due DECIMAL(20,2), days_to_due INT,
    consecutive_late_months INT, is_overdue TINYINT, as_of_date DATE
);

CREATE TABLE cc_analytics.semantic_deposit_portfolio (
    snapshot_month VARCHAR(7), customer_id VARCHAR(20), country_code VARCHAR(5),
    legal_entity VARCHAR(20), customer_name VARCHAR(100), customer_segment VARCHAR(30),
    risk_rating VARCHAR(10), currency_code VARCHAR(5),
    savings_account_id VARCHAR(20), savings_balance DECIMAL(20,2),
    savings_interest_rate DECIMAL(8,4), savings_interest_ytd DECIMAL(20,2),
    current_account_id VARCHAR(20), current_balance DECIMAL(20,2),
    fd_count INT, total_fd_balance DECIMAL(20,2), fd_avg_rate DECIMAL(8,4),
    fd_maturing_next_30d DECIMAL(20,2), total_deposit_balance DECIMAL(20,2),
    deposit_mom_change_pct DECIMAL(8,4), has_salary_credit TINYINT,
    avg_monthly_credit DECIMAL(20,2), avg_monthly_debit DECIMAL(20,2)
);

CREATE TABLE cc_analytics.semantic_loan_portfolio (
    snapshot_month VARCHAR(7), customer_id VARCHAR(20), country_code VARCHAR(5),
    legal_entity VARCHAR(20), customer_name VARCHAR(100), customer_segment VARCHAR(30),
    risk_rating VARCHAR(10), currency_code VARCHAR(5), annual_income DECIMAL(20,2),
    personal_loan_id VARCHAR(20), personal_loan_disbursed DECIMAL(20,2),
    personal_loan_outstanding DECIMAL(20,2), personal_loan_rate DECIMAL(8,4),
    personal_loan_emi DECIMAL(20,2), personal_loan_status VARCHAR(20),
    home_loan_id VARCHAR(20), home_loan_outstanding DECIMAL(20,2),
    home_loan_rate DECIMAL(8,4), home_loan_emi DECIMAL(20,2), home_loan_ltv DECIMAL(8,4),
    auto_loan_id VARCHAR(20), auto_loan_outstanding DECIMAL(20,2),
    auto_loan_rate DECIMAL(8,4), auto_loan_emi DECIMAL(20,2),
    total_loan_outstanding DECIMAL(20,2), total_loan_count INT, total_monthly_emi DECIMAL(20,2),
    max_overdue_days INT, overdue_bucket VARCHAR(15), is_npa TINYINT,
    total_overdue_amount DECIMAL(20,2), loan_to_income_ratio DECIMAL(8,4),
    debt_service_ratio DECIMAL(8,4)
);

CREATE TABLE cc_analytics.semantic_payment_status (
    as_of_date DATE, customer_id VARCHAR(20), country_code VARCHAR(2),
    legal_entity VARCHAR(10), customer_name VARCHAR(100), customer_segment VARCHAR(20),
    account_id VARCHAR(20), account_type VARCHAR(20), statement_month VARCHAR(7),
    due_date DATE, days_to_due INT, minimum_due DECIMAL(20,2), total_due DECIMAL(20,2),
    amount_paid DECIMAL(20,2), amount_still_owed DECIMAL(20,2),
    payment_status VARCHAR(20), overdue_days INT, overdue_bucket VARCHAR(15),
    late_fee_applied DECIMAL(20,2), is_giro_enabled TINYINT,
    preferred_payment_method VARCHAR(20), consecutive_late_months INT
);

CREATE TABLE cc_analytics.semantic_spend_metrics (
    year_month VARCHAR(7), customer_id VARCHAR(20), country_code VARCHAR(2),
    legal_entity VARCHAR(10), customer_segment VARCHAR(20),
    total_spend DECIMAL(20,2), food_dining_spend DECIMAL(20,2),
    shopping_retail_spend DECIMAL(20,2), travel_transport_spend DECIMAL(20,2),
    healthcare_spend DECIMAL(20,2), entertainment_spend DECIMAL(20,2),
    utilities_spend DECIMAL(20,2), other_spend DECIMAL(20,2),
    total_transactions INT, unique_merchants INT,
    online_spend_pct DECIMAL(5,4), international_spend DECIMAL(20,2),
    spend_mom_change_pct DECIMAL(8,4), top_merchant VARCHAR(100), top_category VARCHAR(50),
    currency_code VARCHAR(3)
);

CREATE TABLE cc_analytics.semantic_portfolio_kpis (
    kpi_month VARCHAR(7), country_code VARCHAR(2), legal_entity VARCHAR(10),
    total_customers BIGINT, active_customers BIGINT, customer_growth_pct DECIMAL(8,4),
    churn_rate DECIMAL(5,4), total_spend_volume DECIMAL(20,2),
    spend_growth_pct DECIMAL(8,4), avg_spend_per_customer DECIMAL(20,2),
    estimated_interest_income DECIMAL(20,2), estimated_fee_income DECIMAL(20,2),
    fraud_rate DECIMAL(5,4), delinquency_rate DECIMAL(5,4), npl_rate DECIMAL(5,4),
    avg_utilization_pct DECIMAL(8,4), full_payment_rate DECIMAL(5,4),
    approval_rate DECIMAL(5,4), currency_code VARCHAR(3)
);

CREATE TABLE cc_analytics.raw_deposit_transaction (
    txn_id VARCHAR(20), deposit_id VARCHAR(20), account_id VARCHAR(20),
    customer_id VARCHAR(20), country_code VARCHAR(2), legal_entity VARCHAR(10),
    txn_date DATE, value_date DATE, amount DECIMAL(20,2),
    txn_direction VARCHAR(6), txn_type VARCHAR(30), txn_category VARCHAR(30),
    channel VARCHAR(20), description VARCHAR(200), beneficiary_name VARCHAR(100),
    balance_after DECIMAL(20,2), status VARCHAR(20)
);

CREATE TABLE cc_analytics.raw_deposit_account (
    deposit_id VARCHAR(20), account_id VARCHAR(20), customer_id VARCHAR(20),
    country_code VARCHAR(2), legal_entity VARCHAR(10), deposit_type VARCHAR(20),
    currency_code VARCHAR(3), current_balance DECIMAL(20,2),
    interest_rate DECIMAL(8,4), interest_earned_ytd DECIMAL(20,2),
    tenor_months INT, maturity_date DATE, avg_monthly_balance DECIMAL(20,2),
    has_salary_credit TINYINT, status VARCHAR(20)
);

CREATE TABLE cc_analytics.raw_loan (
    loan_id VARCHAR(20), customer_id VARCHAR(20), country_code VARCHAR(2),
    legal_entity VARCHAR(10), loan_type VARCHAR(20), currency_code VARCHAR(3),
    principal_amount DECIMAL(20,2), outstanding_balance DECIMAL(20,2),
    interest_rate DECIMAL(8,4), tenor_months INT, disbursement_date DATE,
    maturity_date DATE, status VARCHAR(20), monthly_installment DECIMAL(20,2),
    npl_flag TINYINT, past_due_days INT
);

CREATE TABLE cc_analytics.raw_loan_repayment (
    repayment_id VARCHAR(20), loan_id VARCHAR(20), customer_id VARCHAR(20),
    country_code VARCHAR(2), payment_date DATE, due_date DATE,
    payment_amount DECIMAL(20,2), scheduled_amount DECIMAL(20,2),
    payment_status VARCHAR(20), days_late INT, penalty_fee DECIMAL(20,2)
);
""".strip()

    documentation = f"""
Database: cc_analytics (StarRocks / MySQL-compatible)
Domain: {domain}
Metric: {metric}
Definition: {definition}
Supported dimensions: {", ".join(dimensions)}

Rules:
- Always prefix tables: cc_analytics.<table_name>
- Use DATE_FORMAT(col, '%Y-%m') for monthly grouping; NOT date_trunc
- country_code values: SG, MY, IN
- legal_entity values: SG_BANK, MY_BANK, IN_BANK
- txn_direction in raw_deposit_transaction: CREDIT or DEBIT
- deposit_type in raw_deposit_account: SAVINGS, CURRENT, FIXED_DEPOSIT
- payment_status in semantic_payment_status: paid_full, paid_partial, paid_minimum, overdue, missed
- Use semantic_* tables for analytics; raw_* for transaction-level detail
- For overdue/delinquency use loan tables (raw_loan, raw_loan_repayment, semantic_loan_portfolio)
- No credit card tables exist; deposit banking only
""".strip()

    examples = [
        {
            "question": "How many customers do we have by country?",
            "sql": (
                "SELECT country_code, COUNT(*) AS customer_count "
                "FROM cc_analytics.semantic_customer_360 "
                "GROUP BY country_code ORDER BY customer_count DESC"
            ),
        },
        {
            "question": "Show total deposit balance by segment",
            "sql": (
                "SELECT customer_segment, country_code, "
                "ROUND(SUM(total_deposit_balance), 2) AS total_deposit_balance, "
                "COUNT(DISTINCT customer_id) AS customer_count "
                "FROM cc_analytics.semantic_deposit_portfolio "
                "WHERE snapshot_month = (SELECT MAX(snapshot_month) FROM cc_analytics.semantic_deposit_portfolio) "
                "GROUP BY customer_segment, country_code ORDER BY total_deposit_balance DESC"
            ),
        },
        {
            "question": "Show monthly transaction volume trend",
            "sql": (
                "SELECT DATE_FORMAT(txn_date, '%Y-%m') AS month, country_code, "
                "COUNT(*) AS txn_count, ROUND(SUM(amount), 2) AS total_amount "
                "FROM cc_analytics.raw_deposit_transaction "
                "GROUP BY DATE_FORMAT(txn_date, '%Y-%m'), country_code "
                "ORDER BY month ASC"
            ),
        },
        {
            "question": "Show NPL rate and overdue loans by country",
            "sql": (
                "SELECT country_code, customer_segment, "
                "SUM(is_npa) AS npa_count, COUNT(*) AS total_borrowers, "
                "ROUND(SUM(total_overdue_amount), 2) AS total_overdue_amount, "
                "ROUND(100.0 * SUM(is_npa) / COUNT(*), 2) AS npl_rate_pct "
                "FROM cc_analytics.semantic_loan_portfolio "
                "GROUP BY country_code, customer_segment ORDER BY npl_rate_pct DESC"
            ),
        },
        {
            "question": "Show payment status distribution",
            "sql": (
                "SELECT payment_status, country_code, COUNT(*) AS account_count, "
                "ROUND(SUM(amount_still_owed), 2) AS total_outstanding "
                "FROM cc_analytics.semantic_payment_status "
                "GROUP BY payment_status, country_code ORDER BY account_count DESC"
            ),
        },
        {
            "question": "Top spending customers this month",
            "sql": (
                "SELECT customer_id, country_code, customer_segment, "
                "ROUND(SUM(total_spend), 0) AS total_spend, SUM(total_transactions) AS txn_count "
                "FROM cc_analytics.semantic_spend_metrics "
                "WHERE year_month = (SELECT MAX(year_month) FROM cc_analytics.semantic_spend_metrics) "
                "GROUP BY customer_id, country_code, customer_segment "
                "ORDER BY total_spend DESC LIMIT 20"
            ),
        },
    ]

    return {
        "ddl": ddl,
        "documentation": documentation,
        "examples": examples,
    }
