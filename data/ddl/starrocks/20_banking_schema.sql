-- =============================================================================
-- DataPrismAI Banking Platform — Complete Schema
-- Database: cc_analytics (StarRocks)
-- Layers: raw_ → ddm_ → dp_ → semantic_ → mapping_ → audit_
-- Countries: SG (Singapore), MY (Malaysia), IN (India)
-- =============================================================================

USE cc_analytics;

-- =============================================================================
-- SECTION 0: DROP ALL EXISTING TABLES (clean slate)
-- =============================================================================
DROP TABLE IF EXISTS audit_pipeline_runs;
DROP TABLE IF EXISTS audit_data_profile;
DROP TABLE IF EXISTS audit_data_quality;
DROP TABLE IF EXISTS semantic_access_control;
DROP TABLE IF EXISTS semantic_dimension_mapping;
DROP TABLE IF EXISTS domain_grain_mapping;
DROP TABLE IF EXISTS semantic_metric_mapping;
DROP TABLE IF EXISTS domain_semantic_mapping;
DROP TABLE IF EXISTS intent_domain_mapping;
DROP TABLE IF EXISTS user_domain_mapping;
DROP TABLE IF EXISTS semantic_glossary_metrics;
DROP TABLE IF EXISTS semantic_portfolio_kpis;
DROP TABLE IF EXISTS semantic_risk_metrics;
DROP TABLE IF EXISTS semantic_payment_status;
DROP TABLE IF EXISTS semantic_spend_metrics;
DROP TABLE IF EXISTS semantic_transaction_summary;
DROP TABLE IF EXISTS semantic_customer_360;
DROP TABLE IF EXISTS dp_portfolio_kpis;
DROP TABLE IF EXISTS dp_risk_signals;
DROP TABLE IF EXISTS dp_payment_status;
DROP TABLE IF EXISTS dp_transaction_enriched;
DROP TABLE IF EXISTS dp_customer_spend_monthly;
DROP TABLE IF EXISTS dp_customer_balance_snapshot;
DROP TABLE IF EXISTS ddm_merchant;
DROP TABLE IF EXISTS ddm_statement;
DROP TABLE IF EXISTS ddm_payment;
DROP TABLE IF EXISTS ddm_transaction;
DROP TABLE IF EXISTS ddm_card;
DROP TABLE IF EXISTS ddm_account;
DROP TABLE IF EXISTS ddm_customer;
DROP TABLE IF EXISTS raw_merchant;
DROP TABLE IF EXISTS raw_statement;
DROP TABLE IF EXISTS raw_payment;
DROP TABLE IF EXISTS raw_transaction;
DROP TABLE IF EXISTS raw_card;
DROP TABLE IF EXISTS raw_account;
DROP TABLE IF EXISTS raw_customer;
-- Drop old cc_analytics tables
DROP TABLE IF EXISTS raw_customers;
DROP TABLE IF EXISTS raw_card_accounts;
DROP TABLE IF EXISTS raw_cards;
DROP TABLE IF EXISTS raw_transactions;
DROP TABLE IF EXISTS raw_payments;
DROP TABLE IF EXISTS raw_statements;
DROP TABLE IF EXISTS raw_merchants;
DROP TABLE IF EXISTS raw_fraud_alerts;
DROP TABLE IF EXISTS raw_disputes;
DROP TABLE IF EXISTS dp_account_health_monthly;
DROP TABLE IF EXISTS dp_customer_value_cohort;
DROP TABLE IF EXISTS dp_fraud_monitoring_hourly;
DROP TABLE IF EXISTS dp_rewards_profitability_monthly;
DROP TABLE IF EXISTS dp_spend_trend_daily;
DROP TABLE IF EXISTS query_audit_log;
DROP TABLE IF EXISTS semantic_dimensions;
DROP TABLE IF EXISTS semantic_joins;
DROP TABLE IF EXISTS semantic_metrics;

-- =============================================================================
-- SECTION 1: RAW LAYER — source-aligned, lightly cleaned
-- =============================================================================

CREATE TABLE raw_customer (
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    first_name          VARCHAR(50),
    last_name           VARCHAR(50),
    date_of_birth       DATE,
    gender              VARCHAR(10),
    email               VARCHAR(100),
    phone               VARCHAR(25),
    address_line1       VARCHAR(200),
    city                VARCHAR(80),
    state_province      VARCHAR(80),
    postal_code         VARCHAR(20),
    nationality         VARCHAR(50),
    id_type             VARCHAR(20),
    id_number           VARCHAR(40),
    customer_segment    VARCHAR(30),
    kyc_status          VARCHAR(20),
    risk_rating         VARCHAR(10),
    annual_income       DECIMAL(18,2),
    currency_code       VARCHAR(5),
    occupation          VARCHAR(100),
    acquisition_channel VARCHAR(30),
    credit_score        INT,
    is_deleted          TINYINT         DEFAULT '0',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(customer_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE raw_account (
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    account_type        VARCHAR(30),
    product_code        VARCHAR(30),
    currency_code       VARCHAR(5),
    current_balance     DECIMAL(18,2),
    available_balance   DECIMAL(18,2),
    credit_limit        DECIMAL(18,2),
    minimum_balance     DECIMAL(18,2),
    interest_rate       DECIMAL(8,4),
    account_status      VARCHAR(20),
    freeze_reason       VARCHAR(50),
    branch_code         VARCHAR(20),
    product_name        VARCHAR(100),
    open_date           DATE,
    close_date          DATE,
    last_activity_date  DATE,
    cycle_day           INT,
    is_deleted          TINYINT         DEFAULT '0',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(account_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE raw_card (
    card_id                 VARCHAR(20)     NOT NULL,
    account_id              VARCHAR(20)     NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(5)      NOT NULL,
    legal_entity            VARCHAR(20),
    card_type               VARCHAR(20),
    card_scheme             VARCHAR(20),
    card_number_hash        VARCHAR(64),
    card_tier               VARCHAR(20),
    issued_date             DATE,
    expiry_date             DATE,
    card_status             VARCHAR(20),
    is_primary_card         TINYINT         DEFAULT '1',
    daily_limit             DECIMAL(18,2),
    international_enabled   TINYINT         DEFAULT '1',
    contactless_enabled     TINYINT         DEFAULT '1',
    created_at              DATETIME,
    updated_at              DATETIME
) ENGINE = OLAP
DUPLICATE KEY(card_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE raw_transaction (
    transaction_id      VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    card_id             VARCHAR(20),
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    transaction_date    DATETIME,
    settlement_date     DATETIME,
    amount              DECIMAL(18,2),
    currency_code       VARCHAR(5),
    transaction_type    VARCHAR(20),
    channel             VARCHAR(20),
    merchant_id         VARCHAR(20),
    merchant_name       VARCHAR(100),
    merchant_category   VARCHAR(50),
    mcc_code            VARCHAR(10),
    auth_status         VARCHAR(20),
    decline_reason      VARCHAR(50),
    is_fraud            TINYINT         DEFAULT '0',
    fraud_score         DECIMAL(5,4),
    fraud_tier          VARCHAR(20),
    is_international    TINYINT         DEFAULT '0',
    is_recurring        TINYINT         DEFAULT '0',
    is_contactless      TINYINT         DEFAULT '0',
    reference_number    VARCHAR(30),
    description         VARCHAR(200),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(transaction_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

CREATE TABLE raw_payment (
    payment_id          VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    payment_date        DATETIME,
    due_date            DATE,
    statement_month     VARCHAR(7),
    minimum_due         DECIMAL(18,2),
    total_due           DECIMAL(18,2),
    payment_amount      DECIMAL(18,2),
    payment_method      VARCHAR(30),
    payment_channel     VARCHAR(30),
    payment_status      VARCHAR(20),
    overdue_days        INT             DEFAULT '0',
    late_fee            DECIMAL(10,2)   DEFAULT '0',
    reference_number    VARCHAR(30),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(payment_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE raw_statement (
    statement_id        VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    statement_date      DATE,
    statement_month     VARCHAR(7),
    opening_balance     DECIMAL(18,2),
    closing_balance     DECIMAL(18,2),
    total_spend         DECIMAL(18,2),
    total_credits       DECIMAL(18,2),
    total_fees          DECIMAL(18,2),
    minimum_due         DECIMAL(18,2),
    total_due           DECIMAL(18,2),
    due_date            DATE,
    payment_status      VARCHAR(20),
    credit_limit        DECIMAL(18,2),
    available_credit    DECIMAL(18,2),
    utilization_rate    DECIMAL(5,4),
    transaction_count   INT             DEFAULT '0',
    interest_charged    DECIMAL(10,2)   DEFAULT '0',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(statement_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE raw_merchant (
    merchant_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    merchant_name       VARCHAR(100),
    merchant_category   VARCHAR(50),
    mcc_code            VARCHAR(10),
    business_type       VARCHAR(50),
    address             VARCHAR(200),
    city                VARCHAR(80),
    is_online           TINYINT         DEFAULT '0',
    risk_tier           VARCHAR(20),
    fraud_rate          DECIMAL(5,4)    DEFAULT '0',
    decline_rate        DECIMAL(5,4)    DEFAULT '0',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(merchant_id)
DISTRIBUTED BY HASH(merchant_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 2: DDM LAYER — normalized domain model with derived fields
-- =============================================================================

CREATE TABLE ddm_customer (
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    first_name          VARCHAR(50),
    last_name           VARCHAR(50),
    date_of_birth       DATE,
    age                 INT,
    age_band            VARCHAR(20),
    gender              VARCHAR(10),
    email               VARCHAR(100),
    phone               VARCHAR(25),
    city                VARCHAR(80),
    nationality         VARCHAR(50),
    id_type             VARCHAR(20),
    id_number           VARCHAR(40),
    customer_segment    VARCHAR(30),
    kyc_status          VARCHAR(20),
    risk_rating         VARCHAR(10),
    annual_income       DECIMAL(18,2),
    income_band         VARCHAR(30),
    currency_code       VARCHAR(5),
    occupation          VARCHAR(100),
    acquisition_channel VARCHAR(30),
    credit_score        INT,
    credit_band         VARCHAR(20),
    is_deleted          TINYINT         DEFAULT '0',
    effective_from      DATE,
    effective_to        DATE,
    is_current          TINYINT         DEFAULT '1',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE ddm_account (
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    account_type        VARCHAR(30),
    product_code        VARCHAR(30),
    product_name        VARCHAR(100),
    currency_code       VARCHAR(5),
    current_balance     DECIMAL(18,2),
    available_balance   DECIMAL(18,2),
    credit_limit        DECIMAL(18,2),
    utilization_rate    DECIMAL(5,4),
    utilization_band    VARCHAR(20),
    interest_rate       DECIMAL(8,4),
    account_status      VARCHAR(20),
    open_date           DATE,
    close_date          DATE,
    account_age_days    INT,
    is_deleted          TINYINT         DEFAULT '0',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(account_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE ddm_card (
    card_id             VARCHAR(20)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    card_type           VARCHAR(20),
    card_scheme         VARCHAR(20),
    card_tier           VARCHAR(20),
    issued_date         DATE,
    expiry_date         DATE,
    card_status         VARCHAR(20),
    days_to_expiry      INT,
    is_primary_card     TINYINT         DEFAULT '1',
    daily_limit         DECIMAL(18,2),
    international_enabled TINYINT       DEFAULT '1',
    contactless_enabled   TINYINT       DEFAULT '1',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(card_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE ddm_transaction (
    transaction_id      VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    card_id             VARCHAR(20),
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    transaction_date    DATETIME,
    txn_year_month      VARCHAR(7),
    amount              DECIMAL(18,2),
    currency_code       VARCHAR(5),
    transaction_type    VARCHAR(20),
    channel             VARCHAR(20),
    merchant_id         VARCHAR(20),
    merchant_name       VARCHAR(100),
    merchant_category   VARCHAR(50),
    merchant_risk_tier  VARCHAR(20),
    mcc_code            VARCHAR(10),
    auth_status         VARCHAR(20),
    decline_reason      VARCHAR(50),
    is_fraud            TINYINT         DEFAULT '0',
    fraud_score         DECIMAL(5,4),
    fraud_tier          VARCHAR(20),
    is_suspicious       TINYINT         DEFAULT '0',
    is_international    TINYINT         DEFAULT '0',
    is_contactless      TINYINT         DEFAULT '0',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(transaction_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

CREATE TABLE ddm_payment (
    payment_id          VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    payment_date        DATETIME,
    due_date            DATE,
    statement_month     VARCHAR(7),
    minimum_due         DECIMAL(18,2),
    total_due           DECIMAL(18,2),
    payment_amount      DECIMAL(18,2),
    payment_ratio       DECIMAL(5,4),
    is_full_payment     TINYINT         DEFAULT '0',
    is_minimum_payment  TINYINT         DEFAULT '0',
    payment_method      VARCHAR(30),
    payment_channel     VARCHAR(30),
    payment_status      VARCHAR(20),
    overdue_days        INT             DEFAULT '0',
    overdue_bucket      VARCHAR(20),
    late_fee            DECIMAL(10,2)   DEFAULT '0',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(payment_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE ddm_statement (
    statement_id        VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    statement_month     VARCHAR(7),
    statement_date      DATE,
    opening_balance     DECIMAL(18,2),
    closing_balance     DECIMAL(18,2),
    total_spend         DECIMAL(18,2),
    total_credits       DECIMAL(18,2),
    total_fees          DECIMAL(18,2),
    minimum_due         DECIMAL(18,2),
    total_due           DECIMAL(18,2),
    due_date            DATE,
    payment_status      VARCHAR(20),
    credit_limit        DECIMAL(18,2),
    available_credit    DECIMAL(18,2),
    utilization_rate    DECIMAL(5,4),
    transaction_count   INT             DEFAULT '0',
    interest_charged    DECIMAL(10,2)   DEFAULT '0',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(statement_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE ddm_merchant (
    merchant_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    merchant_name       VARCHAR(100),
    merchant_category   VARCHAR(50),
    business_type       VARCHAR(50),
    mcc_code            VARCHAR(10),
    city                VARCHAR(80),
    is_online           TINYINT         DEFAULT '0',
    risk_tier           VARCHAR(20),
    fraud_rate          DECIMAL(5,4),
    decline_rate        DECIMAL(5,4),
    total_transaction_count BIGINT      DEFAULT '0',
    total_transaction_volume DECIMAL(18,2) DEFAULT '0',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(merchant_id)
DISTRIBUTED BY HASH(merchant_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 3: DATA PRODUCTS LAYER — domain-aligned aggregated tables
-- =============================================================================

CREATE TABLE dp_customer_balance_snapshot (
    snapshot_month      VARCHAR(7)      NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    total_accounts      INT,
    total_credit_limit  DECIMAL(18,2),
    total_balance       DECIMAL(18,2),
    total_available     DECIMAL(18,2),
    avg_utilization     DECIMAL(5,4),
    highest_util_account VARCHAR(20),
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(snapshot_month, customer_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE dp_customer_spend_monthly (
    spend_month         VARCHAR(7)      NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    customer_segment    VARCHAR(30),
    total_spend         DECIMAL(18,2),
    food_dining         DECIMAL(18,2),
    retail_shopping     DECIMAL(18,2),
    travel_transport    DECIMAL(18,2),
    healthcare          DECIMAL(18,2),
    entertainment       DECIMAL(18,2),
    utilities           DECIMAL(18,2),
    grocery             DECIMAL(18,2),
    hotel               DECIMAL(18,2),
    fuel                DECIMAL(18,2),
    other_spend         DECIMAL(18,2),
    transaction_count   INT,
    avg_txn_amount      DECIMAL(18,2),
    top_merchant        VARCHAR(100),
    top_category        VARCHAR(50),
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(spend_month, customer_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE dp_transaction_enriched (
    transaction_id      VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    transaction_date    DATETIME,
    txn_year_month      VARCHAR(7),
    amount              DECIMAL(18,2),
    currency_code       VARCHAR(5),
    transaction_type    VARCHAR(20),
    channel             VARCHAR(20),
    merchant_name       VARCHAR(100),
    merchant_category   VARCHAR(50),
    merchant_risk_tier  VARCHAR(20),
    auth_status         VARCHAR(20),
    decline_reason      VARCHAR(50),
    is_fraud            TINYINT         DEFAULT '0',
    fraud_score         DECIMAL(5,4),
    is_suspicious       TINYINT         DEFAULT '0',
    is_international    TINYINT         DEFAULT '0',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(transaction_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

CREATE TABLE dp_payment_status (
    as_of_date          DATE            NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    statement_month     VARCHAR(7),
    due_date            DATE,
    days_to_due         INT,
    minimum_due         DECIMAL(18,2),
    total_due           DECIMAL(18,2),
    amount_paid         DECIMAL(18,2),
    amount_outstanding  DECIMAL(18,2),
    payment_status      VARCHAR(20),
    overdue_days        INT             DEFAULT '0',
    overdue_bucket      VARCHAR(20),
    consecutive_late    INT             DEFAULT '0',
    late_fee            DECIMAL(10,2)   DEFAULT '0',
    interest_at_risk    DECIMAL(18,2)   DEFAULT '0',
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(as_of_date, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE dp_risk_signals (
    signal_date         DATE            NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    customer_segment    VARCHAR(30),
    total_txn           BIGINT,
    approved_txn        BIGINT,
    declined_txn        BIGINT,
    fraud_txn           BIGINT,
    suspicious_txn      BIGINT,
    total_amount        DECIMAL(18,2),
    fraud_amount        DECIMAL(18,2),
    fraud_rate          DECIMAL(8,6),
    decline_rate        DECIMAL(8,6),
    avg_fraud_score     DECIMAL(5,4),
    high_risk_accounts  INT,
    new_fraud_alerts    INT,
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(signal_date, country_code)
DISTRIBUTED BY HASH(country_code) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE dp_portfolio_kpis (
    kpi_month           VARCHAR(7)      NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    total_customers     INT,
    active_customers    INT,
    new_customers       INT,
    churned_customers   INT,
    customer_growth_pct DECIMAL(8,4),
    churn_rate          DECIMAL(8,4),
    total_accounts      INT,
    active_accounts     INT,
    total_credit_extended DECIMAL(18,2),
    total_outstanding   DECIMAL(18,2),
    total_spend         DECIMAL(18,2),
    spend_growth_pct    DECIMAL(8,4),
    avg_balance         DECIMAL(18,2),
    avg_utilization     DECIMAL(5,4),
    fraud_rate          DECIMAL(8,6),
    decline_rate        DECIMAL(8,6),
    delinquency_rate    DECIMAL(8,4),
    full_payment_rate   DECIMAL(8,4),
    npl_rate            DECIMAL(8,4),
    est_interest_income DECIMAL(18,2),
    currency_code       VARCHAR(5),
    fx_rate_to_usd      DECIMAL(12,6),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(kpi_month, country_code)
DISTRIBUTED BY HASH(country_code) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 4: SEMANTIC LAYER — chatbot/BI ready, denormalized
-- =============================================================================

CREATE TABLE semantic_customer_360 (
    as_of_date          DATE            NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    first_name          VARCHAR(50),
    last_name           VARCHAR(50),
    customer_segment    VARCHAR(30),
    risk_rating         VARCHAR(10),
    kyc_status          VARCHAR(20),
    age                 INT,
    age_band            VARCHAR(20),
    credit_score        INT,
    credit_band         VARCHAR(20),
    primary_account_id  VARCHAR(20),
    account_type        VARCHAR(30),
    current_balance     DECIMAL(18,2),
    available_balance   DECIMAL(18,2),
    credit_limit        DECIMAL(18,2),
    utilization_pct     DECIMAL(5,4),
    total_accounts      INT,
    mtd_spend           DECIMAL(18,2),
    last_month_spend    DECIMAL(18,2),
    spend_change_pct    DECIMAL(8,4),
    top_spend_category  VARCHAR(50),
    payment_status      VARCHAR(20),
    total_due           DECIMAL(18,2),
    days_to_due         INT,
    is_overdue          TINYINT         DEFAULT '0',
    consecutive_late    INT             DEFAULT '0',
    active_fraud_alerts INT             DEFAULT '0',
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(as_of_date, customer_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_transaction_summary (
    transaction_id      VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    transaction_date    DATETIME,
    txn_year_month      VARCHAR(7),
    amount              DECIMAL(18,2),
    currency_code       VARCHAR(5),
    transaction_type    VARCHAR(20),
    channel             VARCHAR(20),
    merchant_name       VARCHAR(100),
    merchant_category   VARCHAR(50),
    merchant_risk_tier  VARCHAR(20),
    auth_status         VARCHAR(20),
    decline_reason      VARCHAR(50),
    is_approved         TINYINT         DEFAULT '1',
    is_declined         TINYINT         DEFAULT '0',
    is_fraud            TINYINT         DEFAULT '0',
    fraud_score         DECIMAL(5,4),
    is_suspicious       TINYINT         DEFAULT '0',
    is_international    TINYINT         DEFAULT '0',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(transaction_id, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_spend_metrics (
    spend_month         VARCHAR(7)      NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    total_spend         DECIMAL(18,2),
    food_dining         DECIMAL(18,2),
    retail_shopping     DECIMAL(18,2),
    travel_transport    DECIMAL(18,2),
    healthcare          DECIMAL(18,2),
    entertainment       DECIMAL(18,2),
    utilities           DECIMAL(18,2),
    grocery             DECIMAL(18,2),
    hotel               DECIMAL(18,2),
    fuel                DECIMAL(18,2),
    other_spend         DECIMAL(18,2),
    transaction_count   INT,
    avg_txn_amount      DECIMAL(18,2),
    top_category        VARCHAR(50),
    top_merchant        VARCHAR(100),
    mom_spend_change_pct DECIMAL(8,4),
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(spend_month, customer_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_payment_status (
    as_of_date          DATE            NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    full_name           VARCHAR(100),
    customer_segment    VARCHAR(30),
    statement_month     VARCHAR(7),
    due_date            DATE,
    days_to_due         INT,
    minimum_due         DECIMAL(18,2),
    total_due           DECIMAL(18,2),
    amount_paid         DECIMAL(18,2),
    amount_outstanding  DECIMAL(18,2),
    payment_status      VARCHAR(20),
    overdue_days        INT             DEFAULT '0',
    overdue_bucket      VARCHAR(20),
    consecutive_late    INT             DEFAULT '0',
    late_fee            DECIMAL(10,2)   DEFAULT '0',
    interest_at_risk    DECIMAL(18,2)   DEFAULT '0',
    is_giro_enrolled    TINYINT         DEFAULT '0',
    preferred_method    VARCHAR(30),
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(as_of_date, account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_risk_metrics (
    metric_date         DATE            NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    customer_segment    VARCHAR(30),
    total_txn           BIGINT,
    approved_txn        BIGINT,
    declined_txn        BIGINT,
    fraud_txn           BIGINT,
    suspicious_txn      BIGINT,
    total_amount        DECIMAL(18,2),
    fraud_amount        DECIMAL(18,2),
    fraud_rate          DECIMAL(8,6),
    decline_rate        DECIMAL(8,6),
    avg_fraud_score     DECIMAL(5,4),
    delinquency_1_30    DECIMAL(8,4),
    delinquency_31_60   DECIMAL(8,4),
    delinquency_61_90   DECIMAL(8,4),
    delinquency_91plus  DECIMAL(8,4),
    high_risk_accounts  INT,
    currency_code       VARCHAR(5),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(metric_date, country_code)
DISTRIBUTED BY HASH(country_code) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_portfolio_kpis (
    kpi_month           VARCHAR(7)      NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    total_customers     INT,
    active_customers    INT,
    new_customers       INT,
    customer_growth_pct DECIMAL(8,4),
    churn_rate          DECIMAL(8,4),
    total_spend         DECIMAL(18,2),
    spend_growth_pct    DECIMAL(8,4),
    avg_balance         DECIMAL(18,2),
    avg_utilization     DECIMAL(5,4),
    fraud_rate          DECIMAL(8,6),
    decline_rate        DECIMAL(8,6),
    delinquency_rate    DECIMAL(8,4),
    full_payment_rate   DECIMAL(8,4),
    npl_rate            DECIMAL(8,4),
    est_interest_income DECIMAL(18,2),
    currency_code       VARCHAR(5),
    fx_rate_to_usd      DECIMAL(12,6),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(kpi_month, country_code)
DISTRIBUTED BY HASH(country_code) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_glossary_metrics (
    metric_id           VARCHAR(30)     NOT NULL,
    metric_name         VARCHAR(100),
    display_name        VARCHAR(150),
    definition          VARCHAR(500),
    formula             VARCHAR(500),
    grain               VARCHAR(50),
    source_table        VARCHAR(100),
    source_columns      VARCHAR(300),
    domain              VARCHAR(30),
    category            VARCHAR(30),
    is_active           TINYINT         DEFAULT '1'
) ENGINE = OLAP
UNIQUE KEY(metric_id)
DISTRIBUTED BY HASH(metric_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 5: MAPPING TABLES — chatbot routing & access control
-- =============================================================================

CREATE TABLE intent_domain_mapping (
    keyword             VARCHAR(100)    NOT NULL,
    domain              VARCHAR(30)     NOT NULL,
    weight              INT             DEFAULT '1',
    example_question    VARCHAR(300)
) ENGINE = OLAP
DUPLICATE KEY(keyword)
DISTRIBUTED BY HASH(keyword) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE domain_semantic_mapping (
    domain              VARCHAR(30)     NOT NULL,
    semantic_table      VARCHAR(100)    NOT NULL,
    priority            INT             DEFAULT '1',
    description         VARCHAR(200)
) ENGINE = OLAP
DUPLICATE KEY(domain)
DISTRIBUTED BY HASH(domain) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_metric_mapping (
    metric_name         VARCHAR(100)    NOT NULL,
    semantic_table      VARCHAR(100)    NOT NULL,
    value_column        VARCHAR(100),
    filter_column       VARCHAR(100),
    group_by_column     VARCHAR(100),
    aggregation         VARCHAR(20)
) ENGINE = OLAP
DUPLICATE KEY(metric_name)
DISTRIBUTED BY HASH(metric_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_dimension_mapping (
    dimension_name      VARCHAR(100)    NOT NULL,
    source_table        VARCHAR(100),
    source_column       VARCHAR(100),
    display_label       VARCHAR(150),
    dimension_type      VARCHAR(30),
    is_filterable       TINYINT         DEFAULT '1',
    is_groupable        TINYINT         DEFAULT '1'
) ENGINE = OLAP
DUPLICATE KEY(dimension_name)
DISTRIBUTED BY HASH(dimension_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE semantic_access_control (
    persona             VARCHAR(50)     NOT NULL,
    semantic_table      VARCHAR(100)    NOT NULL,
    can_access          TINYINT         DEFAULT '1',
    country_filter      VARCHAR(20),
    restricted_columns  VARCHAR(500),
    max_row_limit       INT             DEFAULT '1000',
    description         VARCHAR(200)
) ENGINE = OLAP
DUPLICATE KEY(persona, semantic_table)
DISTRIBUTED BY HASH(persona) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE user_domain_mapping (
    user_id             VARCHAR(20)     NOT NULL,
    domain              VARCHAR(30)     NOT NULL,
    country_code        VARCHAR(5),
    access_level        VARCHAR(20),
    granted_by          VARCHAR(50),
    granted_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(user_id, domain)
DISTRIBUTED BY HASH(user_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE domain_grain_mapping (
    domain              VARCHAR(30)     NOT NULL,
    default_grain       VARCHAR(30),
    default_lookback    VARCHAR(30),
    date_column         VARCHAR(100),
    description         VARCHAR(200)
) ENGINE = OLAP
DUPLICATE KEY(domain)
DISTRIBUTED BY HASH(domain) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 6: AUDIT TABLES — data quality & monitoring
-- =============================================================================

CREATE TABLE audit_data_quality (
    run_id              VARCHAR(50)     NOT NULL,
    run_date            DATE            NOT NULL,
    table_name          VARCHAR(100),
    check_type          VARCHAR(50),
    expected_value      VARCHAR(200),
    actual_value        VARCHAR(200),
    status              VARCHAR(20),
    row_count           BIGINT,
    null_count          BIGINT,
    duplicate_count     BIGINT,
    notes               VARCHAR(500),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(run_id, run_date)
DISTRIBUTED BY HASH(table_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE audit_data_profile (
    profile_date        DATE            NOT NULL,
    table_name          VARCHAR(100)    NOT NULL,
    column_name         VARCHAR(100)    NOT NULL,
    row_count           BIGINT,
    null_count          BIGINT,
    distinct_count      BIGINT,
    min_value           VARCHAR(100),
    max_value           VARCHAR(100),
    avg_value           DECIMAL(18,4),
    std_dev             DECIMAL(18,4),
    is_pii              TINYINT         DEFAULT '0',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(profile_date, table_name, column_name)
DISTRIBUTED BY HASH(table_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");

CREATE TABLE audit_pipeline_runs (
    run_id              VARCHAR(50)     NOT NULL,
    run_date            DATE            NOT NULL,
    pipeline_name       VARCHAR(100),
    source_layer        VARCHAR(20),
    target_table        VARCHAR(100),
    rows_read           BIGINT          DEFAULT '0',
    rows_inserted       BIGINT          DEFAULT '0',
    rows_updated        BIGINT          DEFAULT '0',
    rows_rejected       BIGINT          DEFAULT '0',
    start_time          DATETIME,
    end_time            DATETIME,
    duration_secs       INT,
    status              VARCHAR(20),
    error_message       VARCHAR(500),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(run_id, run_date)
DISTRIBUTED BY HASH(target_table) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- Chatbot query audit (replaces old query_audit_log)
CREATE TABLE audit_query_log (
    log_id              VARCHAR(50)     NOT NULL,
    log_date            DATE            NOT NULL,
    user_id             VARCHAR(30),
    persona             VARCHAR(50),
    country_code        VARCHAR(5),
    message             VARCHAR(1000),
    sql_generated       VARCHAR(4000),
    tables_accessed     VARCHAR(500),
    row_count           INT,
    latency_ms          INT,
    success             TINYINT         DEFAULT '1',
    error_message       VARCHAR(500),
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(log_id, log_date)
DISTRIBUTED BY HASH(user_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");
