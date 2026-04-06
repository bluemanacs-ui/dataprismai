-- =============================================================================
-- DataPrismAI Banking Platform
-- File: 15_banking_sample_queries.sql
-- Purpose: Annotated NL-to-SQL examples for chatbot testing and LLM few-shot
-- These queries target ONLY the semantic layer (chatbot-ready tables)
-- =============================================================================
-- USAGE: Load into semantic_glossary_metrics or use as LLM few-shot examples
-- TABLE REFERENCE: All queries use semantic_* tables only
-- PERSONA ROUTING: Backend maps user message → domain → tables via 12_banking_mapping.sql
-- =============================================================================


-- =============================================================================
-- CATEGORY: SPEND ANALYTICS (domain: spend)
-- Persona: end_user, retail_user, analyst, cfo
-- Routed from: semantic_spend_metrics
-- =============================================================================

-- Q: "How much did I spend last month?"
-- Persona: end_user | Country: SG | customer_id injected by backend from session
SELECT
    year_month,
    total_spend,
    transaction_count,
    top_category,
    top_merchant
FROM semantic_spend_metrics
WHERE customer_id   = :customer_id
  AND country_code  = :country_code
  AND year_month    = DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 MONTH), '%Y-%m');


-- Q: "Show my spending by category for February 2025"
-- Persona: end_user | cross-category breakdown
SELECT
    year_month,
    food_dining_spend        AS food_and_dining,
    shopping_retail_spend    AS shopping,
    travel_transport_spend   AS travel,
    healthcare_spend         AS healthcare,
    entertainment_spend      AS entertainment,
    utilities_spend          AS utilities,
    other_spend              AS other,
    total_spend
FROM semantic_spend_metrics
WHERE customer_id   = :customer_id
  AND country_code  = :country_code
  AND year_month    = '2025-02'
ORDER BY total_spend DESC;


-- Q: "Show total spend by country for the last 3 months" (CFO view)
-- Persona: cfo | aggregated, no customer PII
SELECT
    year_month,
    country_code,
    SUM(total_spend)            AS portfolio_spend,
    SUM(transaction_count)      AS total_transactions,
    AVG(avg_transaction_amount) AS avg_ticket_size
FROM semantic_spend_metrics
WHERE year_month >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 3 MONTH), '%Y-%m')
  AND country_code IN (:country_codes)    -- injected from user.country_codes
GROUP BY year_month, country_code
ORDER BY year_month DESC, portfolio_spend DESC;


-- Q: "What is the month-over-month spend change for SG customers?"
-- Persona: analyst | trend analysis
SELECT
    year_month,
    country_code,
    SUM(total_spend)            AS total_spend,
    AVG(spend_mom_change_pct)   AS avg_mom_change_pct,
    SUM(transaction_count)      AS transactions
FROM semantic_spend_metrics
WHERE country_code = 'SG'
  AND year_month   >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 6 MONTH), '%Y-%m')
GROUP BY year_month, country_code
ORDER BY year_month DESC;


-- =============================================================================
-- CATEGORY: PAYMENT STATUS (domain: payments)
-- Persona: end_user, retail_user, analyst
-- Routed from: semantic_payment_status
-- =============================================================================

-- Q: "What is my total due amount?"
-- Persona: end_user | single customer view
SELECT
    customer_name,
    account_id,
    statement_month,
    due_date,
    days_to_due,
    minimum_due,
    total_due,
    amount_paid,
    amount_still_owed,
    payment_status,
    overdue_days,
    late_fee_applied,
    preferred_payment_method
FROM semantic_payment_status
WHERE customer_id   = :customer_id
  AND country_code  = :country_code
  AND as_of_date    = CURRENT_DATE;


-- Q: "Show overdue accounts in Singapore sorted by overdue days"
-- Persona: analyst | operational view
SELECT
    customer_id,
    customer_name,
    customer_segment,
    account_id,
    total_due,
    amount_still_owed,
    overdue_days,
    overdue_bucket,
    late_fee_applied,
    consecutive_late_months
FROM semantic_payment_status
WHERE country_code      = 'SG'
  AND payment_status    = 'OVERDUE'
  AND as_of_date        = CURRENT_DATE
ORDER BY overdue_days DESC
LIMIT 50;


-- Q: "Show overdue distribution by bucket for all countries"
-- Persona: cfo, finance_user | portfolio delinquency view
SELECT
    country_code,
    overdue_bucket,
    COUNT(*)                        AS account_count,
    SUM(amount_still_owed)          AS total_overdue_amount,
    AVG(consecutive_late_months)    AS avg_consecutive_late_months
FROM semantic_payment_status
WHERE payment_status = 'OVERDUE'
  AND as_of_date     = CURRENT_DATE
  AND country_code   IN (:country_codes)
GROUP BY country_code, overdue_bucket
ORDER BY country_code,
    CASE overdue_bucket
        WHEN '1-30'  THEN 1
        WHEN '31-60' THEN 2
        WHEN '61-90' THEN 3
        WHEN '91+'   THEN 4
        ELSE 0
    END;


-- Q: "When is my next payment due and how much?"
-- Persona: end_user | single customer reminder
SELECT
    due_date,
    days_to_due,
    CASE
        WHEN days_to_due < 0  THEN CONCAT('OVERDUE by ', ABS(days_to_due), ' days')
        WHEN days_to_due = 0  THEN 'Due TODAY'
        WHEN days_to_due <= 5 THEN CONCAT('Due in ', days_to_due, ' days — pay soon')
        ELSE CONCAT('Due in ', days_to_due, ' days')
    END                             AS due_status_message,
    minimum_due,
    total_due,
    amount_still_owed,
    preferred_payment_method,
    is_giro_enabled
FROM semantic_payment_status
WHERE customer_id   = :customer_id
  AND country_code  = :country_code
  AND as_of_date    = CURRENT_DATE;


-- =============================================================================
-- CATEGORY: CUSTOMER ACCOUNT (domain: customer)
-- Persona: end_user, analyst, retail_user
-- Routed from: semantic_customer_360
-- =============================================================================

-- Q: "What is my current account balance?"
-- Persona: end_user
SELECT
    full_name,
    customer_segment,
    primary_account_type,
    current_balance,
    available_balance,
    credit_limit,
    ROUND(utilization_pct * 100, 1)     AS utilization_pct,
    active_card_count,
    total_outstanding_cards,
    country_code
FROM semantic_customer_360
WHERE customer_id   = :customer_id
  AND country_code  = :country_code;


-- Q: "Show high-utilisation customers in SG (>80%)"
-- Persona: analyst | credit risk flag
SELECT
    customer_id,
    full_name,
    customer_segment,
    risk_rating,
    credit_limit,
    ROUND(utilization_pct * 100, 2)     AS utilization_pct,
    total_outstanding_cards,
    payment_status,
    is_overdue,
    consecutive_late_months
FROM semantic_customer_360
WHERE country_code      = 'SG'
  AND utilization_pct   > 0.80
  AND as_of_date        = CURRENT_DATE
ORDER BY utilization_pct DESC
LIMIT 100;


-- Q: "Show customer breakdown by segment and country"
-- Persona: cfo, analyst
SELECT
    country_code,
    customer_segment,
    COUNT(*)                            AS customer_count,
    AVG(credit_limit)                   AS avg_credit_limit,
    AVG(utilization_pct)                AS avg_utilization,
    SUM(CASE WHEN is_overdue=1 THEN 1 ELSE 0 END) AS overdue_count
FROM semantic_customer_360
WHERE country_code  IN (:country_codes)
GROUP BY country_code, customer_segment
ORDER BY country_code, customer_count DESC;


-- =============================================================================
-- CATEGORY: RISK & FRAUD (domain: risk)
-- Persona: analyst, fraud_analyst
-- Routed from: semantic_risk_metrics + semantic_transaction_summary
-- =============================================================================

-- Q: "Show suspicious transactions this week"
-- Persona: analyst, fraud_analyst | transaction-level investigation
SELECT
    transaction_id,
    transaction_date,
    customer_id,
    customer_name,
    customer_segment,
    amount,
    currency_code,
    merchant_name,
    merchant_category,
    merchant_risk_tier,
    channel,
    is_fraud,
    fraud_score,
    fraud_tier,
    transaction_status,
    decline_reason,
    is_international,
    country_code
FROM semantic_transaction_summary
WHERE is_suspicious     = 1
  AND transaction_date  >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND country_code      IN (:country_codes)
ORDER BY fraud_score DESC, transaction_date DESC
LIMIT 200;


-- Q: "What is the fraud rate this month by country?"
-- Persona: analyst, cfo | executive fraud summary
SELECT
    country_code,
    SUM(fraud_transactions)                         AS total_fraud_txns,
    SUM(fraud_amount)                               AS total_fraud_amount,
    AVG(fraud_rate)                                 AS avg_fraud_rate,
    SUM(active_fraud_alerts)                        AS open_alerts
FROM semantic_risk_metrics
WHERE metric_date   >= DATE_FORMAT(NOW(), '%Y-%m-01')   -- first day of current month
  AND country_code  IN (:country_codes)
GROUP BY country_code
ORDER BY avg_fraud_rate DESC;


-- Q: "Show decline rate by country for the last 30 days"
-- Persona: analyst, fraud_analyst | authorisation quality monitoring
SELECT
    country_code,
    SUM(total_transactions)         AS total_txns,
    SUM(declined_transactions)      AS declined_txns,
    ROUND(SUM(declined_transactions) / SUM(total_transactions) * 100, 4) AS decline_rate_pct,
    AVG(fraud_rate)                 AS avg_fraud_rate
FROM semantic_risk_metrics
WHERE metric_date   >= DATE_SUB(NOW(), INTERVAL 30 DAY)
  AND country_code  IN (:country_codes)
  AND customer_segment IS NULL    -- use aggregated (not segment-split) rows
  AND merchant_category IS NULL
  AND channel IS NULL
GROUP BY country_code
ORDER BY decline_rate_pct DESC;


-- Q: "Show delinquency rate trend for MY over last 6 months"
-- Persona: analyst, cfo
SELECT
    DATE_FORMAT(metric_date, '%Y-%m')   AS year_month,
    AVG(delinquency_rate_1_30)          AS rate_1_30_days,
    AVG(delinquency_rate_31_60)         AS rate_31_60_days,
    AVG(delinquency_rate_61_90)         AS rate_61_90_days,
    AVG(delinquency_rate_91_plus)       AS rate_91_plus_days,
    SUM(overdue_customers)              AS total_overdue_customers,
    SUM(overdue_amount)                 AS total_overdue_amount
FROM semantic_risk_metrics
WHERE country_code      = 'MY'
  AND metric_date       >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
  AND customer_segment  IS NULL
  AND merchant_category IS NULL
  AND channel           IS NULL
GROUP BY year_month
ORDER BY year_month DESC;


-- =============================================================================
-- CATEGORY: PORTFOLIO KPIs (domain: portfolio)
-- Persona: cfo, finance_user, data_product_owner
-- Routed from: semantic_portfolio_kpis
-- =============================================================================

-- Q: "Show key KPIs for all countries for February 2025"
-- Persona: cfo
SELECT
    kpi_month,
    country_code,
    total_customers,
    active_customers,
    ROUND(customer_growth_pct * 100, 2)         AS customer_growth_pct,
    ROUND(churn_rate * 100, 2)                  AS churn_rate_pct,
    total_spend_volume,
    ROUND(spend_growth_pct * 100, 2)            AS spend_growth_pct,
    ROUND(fraud_rate * 100, 4)                  AS fraud_rate_pct,
    ROUND(delinquency_rate * 100, 4)            AS delinquency_rate_pct,
    ROUND(full_payment_rate * 100, 2)           AS full_payment_rate_pct,
    estimated_interest_income,
    estimated_fee_income
FROM semantic_portfolio_kpis
WHERE kpi_month     = '2025-02'
  AND country_code  IN (:country_codes)
ORDER BY country_code;


-- Q: "Compare portfolio performance year-over-year for IN"
-- Persona: cfo, data_product_owner
SELECT
    kpi_month,
    total_customers,
    active_customers,
    total_spend_volume,
    ROUND(fraud_rate * 100, 4)          AS fraud_rate_pct,
    ROUND(full_payment_rate * 100, 2)   AS full_payment_rate_pct,
    estimated_interest_income,
    currency_code
FROM semantic_portfolio_kpis
WHERE country_code  = 'IN'
  AND kpi_month     IN (
    DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 MONTH), '%Y-%m'),
    DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 13 MONTH), '%Y-%m')  -- same month last year
  )
ORDER BY kpi_month;


-- Q: "What is the estimated interest income for Q1 2025 across all countries?"
-- Persona: cfo, finance_user
SELECT
    country_code,
    currency_code,
    SUM(estimated_interest_income)  AS q1_interest_income,
    SUM(estimated_fee_income)       AS q1_fee_income,
    SUM(total_spend_volume)         AS q1_spend_volume,
    AVG(fraud_rate)                 AS avg_fraud_rate
FROM semantic_portfolio_kpis
WHERE kpi_month     IN ('2025-01', '2025-02', '2025-03')
  AND country_code  IN (:country_codes)
GROUP BY country_code, currency_code
ORDER BY q1_interest_income DESC;
