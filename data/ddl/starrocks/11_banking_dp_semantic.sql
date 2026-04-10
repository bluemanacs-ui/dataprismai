-- =============================================================================
-- DataPrismAI Banking Platform
-- File: 11_banking_dp_semantic.sql
-- Layers: DATA PRODUCTS (aggregated) + SEMANTIC (chatbot/BI-ready)
-- Countries: SG, MY, IN
-- Purpose: Pre-joined, business-friendly tables for NL-to-SQL queries
-- =============================================================================

-- =============================================================================
-- DATA PRODUCT LAYER — derived aggregations, refreshed daily/monthly
-- =============================================================================

-- dp_customer_balance_snapshot: daily balance snapshot per account per customer
DROP TABLE IF EXISTS dp_customer_balance_snapshot;
CREATE TABLE dp_customer_balance_snapshot (
    snapshot_date           DATE            NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    account_id              VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    customer_segment        VARCHAR(20),
    account_type            VARCHAR(20),
    currency_code           VARCHAR(3),
    current_balance         DECIMAL(20,2),
    available_balance       DECIMAL(20,2),
    credit_limit            DECIMAL(20,2),
    utilization_pct         DECIMAL(8,4),
    outstanding_balance     DECIMAL(20,2),
    min_payment_due         DECIMAL(20,2),
    is_overdue              TINYINT,
    overdue_days            INT,
    account_status          VARCHAR(20),
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(snapshot_date, customer_id, account_id, country_code)
PARTITION BY RANGE(snapshot_date)(
    PARTITION p2024q1 VALUES LESS THAN ("2024-04-01"),
    PARTITION p2024q2 VALUES LESS THAN ("2024-07-01"),
    PARTITION p2024q3 VALUES LESS THAN ("2024-10-01"),
    PARTITION p2024q4 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025q1 VALUES LESS THAN ("2025-04-01"),
    PARTITION p2025q2 VALUES LESS THAN ("2025-07-01"),
    PARTITION p2025q3 VALUES LESS THAN ("2025-10-01"),
    PARTITION p2025q4 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


-- dp_customer_spend_monthly: monthly spend rollup by category per customer
DROP TABLE IF EXISTS dp_customer_spend_monthly;
CREATE TABLE dp_customer_spend_monthly (
    year_month              VARCHAR(7)      NOT NULL,   -- YYYY-MM
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    merchant_category       VARCHAR(50),
    merchant_category_group VARCHAR(30),
    total_spend             DECIMAL(20,2),
    transaction_count       INT,
    avg_transaction_amount  DECIMAL(20,2),
    max_single_transaction  DECIMAL(20,2),
    unique_merchants        INT,
    currency_code           VARCHAR(3),
    channel_online_pct      DECIMAL(5,4),            -- % of transactions online
    channel_intl_pct        DECIMAL(5,4),            -- % international
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(year_month, customer_id, country_code, legal_entity)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


-- dp_transaction_enriched: individual transactions with full merchant/customer context
DROP TABLE IF EXISTS dp_transaction_enriched;
CREATE TABLE dp_transaction_enriched (
    transaction_id          VARCHAR(30)     NOT NULL,
    transaction_date        DATETIME        NOT NULL,
    year_month              VARCHAR(7),
    customer_id             VARCHAR(20)     NOT NULL,
    account_id              VARCHAR(20)     NOT NULL,
    card_id                 VARCHAR(20),
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    customer_segment        VARCHAR(20),
    risk_rating             VARCHAR(10),
    full_name               VARCHAR(100),
    amount_local            DECIMAL(20,2),
    currency_code           VARCHAR(3),
    transaction_type        VARCHAR(20),
    channel                 VARCHAR(20),
    merchant_id             VARCHAR(20),
    merchant_name           VARCHAR(100),
    merchant_category       VARCHAR(50),
    merchant_category_group VARCHAR(30),
    mcc_code                VARCHAR(6),
    merchant_risk_tier      VARCHAR(10),
    status                  VARCHAR(20),
    decline_reason          VARCHAR(50),
    is_fraud                TINYINT,
    fraud_score             DECIMAL(5,4),
    fraud_tier          VARCHAR(15),
    is_international        TINYINT,
    is_contactless          TINYINT,
    is_recurring            TINYINT,
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(transaction_id, transaction_date)
PARTITION BY RANGE(transaction_date)(
    PARTITION p2024q1 VALUES LESS THAN ("2024-04-01"),
    PARTITION p2024q2 VALUES LESS THAN ("2024-07-01"),
    PARTITION p2024q3 VALUES LESS THAN ("2024-10-01"),
    PARTITION p2024q4 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025q1 VALUES LESS THAN ("2025-04-01"),
    PARTITION p2025q2 VALUES LESS THAN ("2025-07-01"),
    PARTITION p2025q3 VALUES LESS THAN ("2025-10-01"),
    PARTITION p2025q4 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 16
PROPERTIES ("replication_num" = "1");


-- dp_payment_status: payment tracking with due date intelligence
DROP TABLE IF EXISTS dp_payment_status;
CREATE TABLE dp_payment_status (
    as_of_date              DATE            NOT NULL,
    account_id              VARCHAR(20)     NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    statement_year_month    VARCHAR(7),
    statement_date          DATE,
    due_date                DATE,
    days_to_due             INT,            -- negative = overdue
    minimum_due             DECIMAL(20,2),
    total_due               DECIMAL(20,2),
    amount_paid             DECIMAL(20,2),
    amount_outstanding      DECIMAL(20,2),  -- total_due - amount_paid
    payment_status          VARCHAR(20),    -- PAID | PARTIAL | OVERDUE | DUE_SOON | UPCOMING
    overdue_days            INT,
    overdue_bucket          VARCHAR(15),    -- 0 | 1-30 | 31-60 | 61-90 | 90+
    late_fee                DECIMAL(20,2),
    interest_at_risk        DECIMAL(20,2),  -- estimated interest if not paid
    payment_method          VARCHAR(20),
    is_giro_enabled         TINYINT,
    consecutive_late_months INT,
    customer_segment        VARCHAR(20),
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(as_of_date, account_id, customer_id)
PARTITION BY RANGE(as_of_date)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


-- dp_risk_signals: fraud and risk indicators per customer, refreshed daily
DROP TABLE IF EXISTS dp_risk_signals;
CREATE TABLE dp_risk_signals (
    signal_date             DATE            NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    risk_rating             VARCHAR(10),
    -- Fraud signals (rolling 30-day)
    fraud_transaction_count     INT,
    fraud_transaction_amount    DECIMAL(20,2),
    fraud_rate_30d              DECIMAL(5,4),
    fraud_score_avg_30d         DECIMAL(5,4),
    fraud_score_max_30d         DECIMAL(5,4),
    high_risk_merchant_count    INT,
    blacklisted_merchant_count  INT,
    -- Card signals
    card_decline_count_30d      INT,
    card_decline_rate_30d       DECIMAL(5,4),
    intl_transaction_count_30d  INT,
    intl_transaction_amount_30d DECIMAL(20,2),
    -- Velocity signals
    transaction_count_24h       INT,
    transaction_amount_24h      DECIMAL(20,2),
    unique_merchants_24h        INT,
    unique_countries_24h        INT,
    -- Delinquency signals
    overdue_accounts_count      INT,
    max_overdue_days            INT,
    total_overdue_amount        DECIMAL(20,2),
    -- Risk score composite
    composite_risk_score        DECIMAL(5,4),   -- 0.0-1.0 combined model score
    risk_tier                   VARCHAR(10),    -- LOW | MEDIUM | HIGH | CRITICAL
    alert_triggered             TINYINT,
    alert_type                  VARCHAR(50),
    dw_refreshed_at             DATETIME
) DUPLICATE KEY(signal_date, customer_id, country_code)
PARTITION BY RANGE(signal_date)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


-- dp_portfolio_kpis: business-level KPIs, refreshed monthly for exec reporting
DROP TABLE IF EXISTS dp_portfolio_kpis;
CREATE TABLE dp_portfolio_kpis (
    kpi_year_month          VARCHAR(7)      NOT NULL,   -- YYYY-MM
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    customer_segment        VARCHAR(20),
    account_type            VARCHAR(20),
    -- Volume KPIs
    total_customers         BIGINT,
    active_customers        BIGINT,
    new_customers           BIGINT,
    churned_customers       BIGINT,
    total_accounts          BIGINT,
    active_accounts         BIGINT,
    total_cards             BIGINT,
    active_cards            BIGINT,
    -- Financial KPIs
    total_outstanding_balance   DECIMAL(20,2),
    total_credit_limit          DECIMAL(20,2),
    avg_utilization_pct         DECIMAL(8,4),
    total_transaction_volume    DECIMAL(20,2),
    total_transaction_count     BIGINT,
    avg_transaction_amount      DECIMAL(20,2),
    -- Risk KPIs
    fraud_rate                  DECIMAL(5,4),
    decline_rate                DECIMAL(5,4),
    delinquency_rate            DECIMAL(5,4),
    overdue_amount              DECIMAL(20,2),
    -- Payments KPIs
    payment_count               BIGINT,
    full_payment_rate           DECIMAL(5,4),
    late_payment_rate           DECIMAL(5,4),
    total_late_fee_collected    DECIMAL(20,2),
    -- Revenue proxy
    estimated_interest_income   DECIMAL(20,2),
    estimated_fee_income        DECIMAL(20,2),
    dw_refreshed_at             DATETIME
) DUPLICATE KEY(kpi_year_month, country_code, legal_entity, customer_segment)
DISTRIBUTED BY HASH(country_code) BUCKETS 4
PROPERTIES ("replication_num" = "1");


-- =============================================================================
-- SEMANTIC LAYER — chatbot/BI-ready: flat, denormalized, business-named columns
-- Persona routing: backend uses semantic_access_control to pick tables
-- =============================================================================

-- semantic_customer_360: complete customer view for "What is my balance?" queries
DROP TABLE IF EXISTS semantic_customer_360;
CREATE TABLE semantic_customer_360 (
    customer_id                 VARCHAR(20)     NOT NULL,
    country_code                VARCHAR(2)      NOT NULL,
    legal_entity                VARCHAR(10),
    full_name                   VARCHAR(100),
    customer_segment            VARCHAR(20),
    risk_rating                 VARCHAR(10),
    kyc_status                  VARCHAR(20),
    age                         INT,
    age_band                    VARCHAR(15),
    income_band                 VARCHAR(20),
    tenure_months               INT,
    -- Account summary (primary account)
    primary_account_id          VARCHAR(20),
    primary_account_type        VARCHAR(20),
    current_balance             DECIMAL(20,2),
    available_balance           DECIMAL(20,2),
    credit_limit                DECIMAL(20,2),
    utilization_pct             DECIMAL(8,4),
    -- Card summary
    active_card_count           INT,
    total_credit_limit_cards    DECIMAL(20,2),
    total_outstanding_cards     DECIMAL(20,2),
    max_card_utilization_pct    DECIMAL(8,4),
    -- Recent activity (last 30 days)
    spend_last_30d              DECIMAL(20,2),
    transaction_count_last_30d  INT,
    top_spend_category          VARCHAR(50),
    -- Payment health
    payment_status              VARCHAR(20),
    total_due                   DECIMAL(20,2),
    days_to_due                 INT,
    consecutive_late_months     INT,
    is_overdue                  TINYINT,
    as_of_date                  DATE,
    dw_refreshed_at             DATETIME
) DUPLICATE KEY(customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


-- semantic_transaction_summary: transaction-level analytics for fraud/ops queries
DROP TABLE IF EXISTS semantic_transaction_summary;
CREATE TABLE semantic_transaction_summary (
    transaction_id          VARCHAR(30)     NOT NULL,
    transaction_date        DATETIME        NOT NULL,
    year_month              VARCHAR(7),
    customer_id             VARCHAR(20)     NOT NULL,
    customer_name           VARCHAR(100),
    customer_segment        VARCHAR(20),
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    account_id              VARCHAR(20),
    card_last4              VARCHAR(4),
    amount                  DECIMAL(20,2),
    currency_code           VARCHAR(3),
    transaction_type        VARCHAR(20),
    channel                 VARCHAR(20),
    merchant_name           VARCHAR(100),
    merchant_category       VARCHAR(50),
    merchant_category_group VARCHAR(30),
    merchant_risk_tier      VARCHAR(10),
    transaction_status      VARCHAR(20),
    decline_reason          VARCHAR(50),
    is_fraud                TINYINT,
    fraud_score             DECIMAL(5,4),
    fraud_tier          VARCHAR(15),
    is_international        TINYINT,
    is_suspicious           TINYINT,        -- derived: fraud_score > 0.7 or high-risk merchant
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(transaction_id, country_code)
PARTITION BY RANGE(transaction_date)(
    PARTITION p2024h1 VALUES LESS THAN ("2024-07-01"),
    PARTITION p2024h2 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025h1 VALUES LESS THAN ("2025-07-01"),
    PARTITION p2025h2 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 16
PROPERTIES ("replication_num" = "1");


-- semantic_spend_metrics: spend analytics for "How much did I spend?" queries
DROP TABLE IF EXISTS semantic_spend_metrics;
CREATE TABLE semantic_spend_metrics (
    year_month              VARCHAR(7)      NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    customer_segment        VARCHAR(20),
    -- Spend by category (pre-pivoted for fast lookup)
    total_spend             DECIMAL(20,2),
    food_dining_spend       DECIMAL(20,2),
    shopping_retail_spend   DECIMAL(20,2),
    travel_transport_spend  DECIMAL(20,2),
    healthcare_spend        DECIMAL(20,2),
    entertainment_spend     DECIMAL(20,2),
    utilities_spend         DECIMAL(20,2),
    other_spend             DECIMAL(20,2),
    -- Counts
    total_transactions      INT,
    unique_merchants        INT,
    -- Channel breakdown
    online_spend_pct        DECIMAL(5,4),
    offline_spend_pct       DECIMAL(5,4),
    international_spend     DECIMAL(20,2),
    -- Month-over-month deltas
    spend_mom_change_pct    DECIMAL(8,4),   -- vs prior month
    spend_yoy_change_pct    DECIMAL(8,4),   -- vs same month last year
    top_merchant            VARCHAR(100),
    top_category            VARCHAR(50),
    currency_code           VARCHAR(3),
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(year_month, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


-- semantic_payment_status: payment due/overdue for "What is my due amount?" queries
DROP TABLE IF EXISTS semantic_payment_status;
CREATE TABLE semantic_payment_status (
    as_of_date              DATE            NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    customer_name           VARCHAR(100),
    customer_segment        VARCHAR(20),
    account_id              VARCHAR(20),
    account_type            VARCHAR(20),
    statement_month         VARCHAR(7),
    due_date                DATE,
    days_to_due             INT,            -- negative = already overdue
    minimum_due             DECIMAL(20,2),
    total_due               DECIMAL(20,2),
    amount_paid             DECIMAL(20,2),
    amount_still_owed       DECIMAL(20,2),
    payment_status          VARCHAR(20),    -- PAID | PARTIAL | OVERDUE | DUE_SOON (≤5 days) | UPCOMING
    overdue_days            INT,
    overdue_bucket          VARCHAR(15),    -- CURRENT | 1-30 | 31-60 | 61-90 | 91+
    late_fee_applied        DECIMAL(20,2),
    is_giro_enabled         TINYINT,
    preferred_payment_method VARCHAR(20),
    consecutive_late_months INT,
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(as_of_date, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


-- semantic_risk_metrics: risk/fraud dashboard for analyst and fraud_analyst persona
DROP TABLE IF EXISTS semantic_risk_metrics;
CREATE TABLE semantic_risk_metrics (
    metric_date             DATE            NOT NULL,
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    customer_segment        VARCHAR(20),   -- NULL = all segments
    merchant_category       VARCHAR(50),   -- NULL = all categories
    channel                 VARCHAR(20),   -- NULL = all channels
    -- Transaction metrics
    total_transactions          BIGINT,
    approved_transactions       BIGINT,
    declined_transactions       BIGINT,
    decline_rate                DECIMAL(5,4),
    -- Fraud metrics
    fraud_transactions          BIGINT,
    fraud_amount                DECIMAL(20,2),
    fraud_rate                  DECIMAL(5,4),
    avg_fraud_score             DECIMAL(5,4),
    high_risk_transactions      BIGINT,
    -- Alerts
    active_fraud_alerts         INT,
    new_alerts_today            INT,
    resolved_alerts_today       INT,
    -- Delinquency
    overdue_customers           BIGINT,
    overdue_amount              DECIMAL(20,2),
    delinquency_rate_1_30       DECIMAL(5,4),    -- 1-30 day bucket
    delinquency_rate_31_60      DECIMAL(5,4),
    delinquency_rate_61_90      DECIMAL(5,4),
    delinquency_rate_91_plus    DECIMAL(5,4),
    -- Top risky merchants
    top_fraud_merchant          VARCHAR(100),
    top_fraud_merchant_amount   DECIMAL(20,2),
    dw_refreshed_at             DATETIME
) DUPLICATE KEY(metric_date, country_code, legal_entity, customer_segment, merchant_category)
PARTITION BY RANGE(metric_date)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(country_code) BUCKETS 4
PROPERTIES ("replication_num" = "1");


-- semantic_portfolio_kpis: executive KPI view for CFO persona
DROP TABLE IF EXISTS semantic_portfolio_kpis;
CREATE TABLE semantic_portfolio_kpis (
    kpi_month               VARCHAR(7)      NOT NULL,   -- YYYY-MM
    country_code            VARCHAR(2)      NOT NULL,
    legal_entity            VARCHAR(10),
    -- Customer KPIs
    total_customers         BIGINT,
    active_customers        BIGINT,
    customer_growth_pct     DECIMAL(8,4),
    churn_rate              DECIMAL(5,4),
    -- Revenue KPIs
    total_spend_volume      DECIMAL(20,2),
    spend_growth_pct        DECIMAL(8,4),
    avg_spend_per_customer  DECIMAL(20,2),
    estimated_interest_income DECIMAL(20,2),
    estimated_fee_income    DECIMAL(20,2),
    -- Risk KPIs
    fraud_rate              DECIMAL(5,4),
    delinquency_rate        DECIMAL(5,4),
    npl_rate                DECIMAL(5,4),   -- non-performing loan rate
    -- Efficiency KPIs
    avg_utilization_pct     DECIMAL(8,4),
    full_payment_rate       DECIMAL(5,4),
    approval_rate           DECIMAL(5,4),
    -- Country context
    currency_code           VARCHAR(3),
    fx_rate_to_usd          DECIMAL(12,6),
    dw_refreshed_at         DATETIME
) DUPLICATE KEY(kpi_month, country_code)
DISTRIBUTED BY HASH(country_code) BUCKETS 4
PROPERTIES ("replication_num" = "1");
