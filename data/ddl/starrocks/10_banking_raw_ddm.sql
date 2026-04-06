-- =============================================================================
-- DataPrismAI Banking Platform
-- File: 10_banking_raw_ddm.sql
-- Layers: RAW (source-aligned) + DDM (domain data model, SCD-2)
-- Countries: SG (Singapore), MY (Malaysia), IN (India)
-- Legal Entities: SG_BANK, MY_BANK, IN_BANK
-- StarRocks syntax: DUPLICATE KEY (facts), UNIQUE KEY (dimensions)
-- =============================================================================

-- =============================================================================
-- RAW LAYER — minimal cleaning, source-aligned
-- =============================================================================

DROP TABLE IF EXISTS raw_customer;
CREATE TABLE raw_customer (
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(2)      NOT NULL,   -- SG | MY | IN
    legal_entity        VARCHAR(10),               -- SG_BANK | MY_BANK | IN_BANK
    first_name          VARCHAR(50),
    last_name           VARCHAR(50),
    date_of_birth       DATE,
    gender              VARCHAR(10),               -- M | F | OTHER
    email               VARCHAR(100),
    phone               VARCHAR(25),
    address             VARCHAR(255),
    city                VARCHAR(50),
    state_province      VARCHAR(50),
    postal_code         VARCHAR(15),
    nationality         VARCHAR(50),
    id_type             VARCHAR(20),               -- NRIC | PASSPORT | AADHAR | PAN | MYKAD
    id_number           VARCHAR(30),
    customer_segment    VARCHAR(20),               -- MASS | AFFLUENT | PRIORITY | PRIVATE
    kyc_status          VARCHAR(20),               -- VERIFIED | PENDING | EXPIRED | REJECTED
    risk_rating         VARCHAR(10),               -- LOW | MEDIUM | HIGH | CRITICAL
    annual_income       DECIMAL(20,2),
    currency_code       VARCHAR(3),               -- SGD | MYR | INR
    occupation          VARCHAR(50),
    acquisition_channel VARCHAR(30),              -- BRANCH | ONLINE | AGENT | REFERRAL
    source_system       VARCHAR(30),
    is_deleted          TINYINT         DEFAULT 0,
    created_at          DATETIME,
    updated_at          DATETIME
) DUPLICATE KEY(customer_id, country_code)
PARTITION BY RANGE(created_at)(
    PARTITION p2023 VALUES LESS THAN ("2024-01-01"),
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION p2026 VALUES LESS THAN ("2027-01-01")
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS raw_account;
CREATE TABLE raw_account (
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),
    account_type        VARCHAR(20),               -- SAVINGS | CURRENT | CREDIT | FIXED_DEPOSIT | LOAN
    account_subtype     VARCHAR(30),
    currency_code       VARCHAR(3),               -- SGD | MYR | INR | USD
    current_balance     DECIMAL(20,2),
    available_balance   DECIMAL(20,2),
    credit_limit        DECIMAL(20,2),
    minimum_balance     DECIMAL(20,2),
    interest_rate       DECIMAL(8,4),
    status              VARCHAR(20),               -- ACTIVE | DORMANT | CLOSED | FROZEN | SUSPENDED
    status_reason       VARCHAR(50),
    branch_code         VARCHAR(15),
    product_code        VARCHAR(20),
    product_name        VARCHAR(50),
    open_date           DATE,
    close_date          DATE,
    last_activity_date  DATE,
    source_system       VARCHAR(30),
    is_deleted          TINYINT         DEFAULT 0,
    created_at          DATETIME,
    updated_at          DATETIME
) DUPLICATE KEY(account_id, country_code)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS raw_card;
CREATE TABLE raw_card (
    card_id             VARCHAR(20)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),
    card_type           VARCHAR(20),               -- VISA | MASTERCARD | AMEX | UNIONPAY
    card_category       VARCHAR(20),               -- STANDARD | GOLD | PLATINUM | INFINITE | BUSINESS
    card_number_masked  VARCHAR(20),              -- e.g. ****1234
    credit_limit        DECIMAL(20,2),
    available_credit    DECIMAL(20,2),
    outstanding_balance DECIMAL(20,2),
    expiry_date         DATE,
    issue_date          DATE,
    status              VARCHAR(20),               -- ACTIVE | BLOCKED | EXPIRED | CANCELLED | HOTLISTED
    block_reason        VARCHAR(50),
    is_primary          TINYINT,
    reward_points       BIGINT,
    contactless_enabled TINYINT         DEFAULT 1,
    online_enabled      TINYINT         DEFAULT 1,
    intl_enabled        TINYINT         DEFAULT 0,
    source_system       VARCHAR(30),
    is_deleted          TINYINT         DEFAULT 0,
    created_at          DATETIME,
    updated_at          DATETIME
) DUPLICATE KEY(card_id, country_code)
DISTRIBUTED BY HASH(card_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS raw_transaction;
CREATE TABLE raw_transaction (
    transaction_id      VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    card_id             VARCHAR(20),
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),
    transaction_date    DATETIME        NOT NULL,
    posting_date        DATETIME,
    amount              DECIMAL(20,2)   NOT NULL,
    currency_code       VARCHAR(3),
    transaction_type    VARCHAR(20),               -- PURCHASE | REFUND | WITHDRAWAL | TRANSFER | FEE | INTEREST
    channel             VARCHAR(20),               -- POS | ONLINE | ATM | MOBILE | BRANCH | CONTACTLESS
    merchant_id         VARCHAR(20),
    merchant_name       VARCHAR(100),
    merchant_category   VARCHAR(50),               -- FOOD | RETAIL | TRAVEL | FUEL | HEALTHCARE | ENTERTAINMENT
    mcc_code            VARCHAR(6),               -- ISO 18245 merchant category code
    status              VARCHAR(20),               -- APPROVED | DECLINED | PENDING | REVERSED | CHARGEBACK
    decline_reason      VARCHAR(50),              -- INSUFFICIENT_FUNDS | CARD_BLOCKED | LIMIT_EXCEEDED | FRAUD_SUSPECT
    is_fraud            TINYINT         DEFAULT 0,
    fraud_score         DECIMAL(5,4),              -- 0.0000 to 1.0000
    fraud_rule_hit      VARCHAR(50),
    is_international    TINYINT         DEFAULT 0,
    is_contactless      TINYINT         DEFAULT 0,
    is_recurring        TINYINT         DEFAULT 0,
    reference_number    VARCHAR(30),
    description         VARCHAR(200),
    source_system       VARCHAR(30),
    created_at          DATETIME
) DUPLICATE KEY(transaction_id, country_code)
PARTITION BY RANGE(transaction_date)(
    PARTITION p2024q1 VALUES LESS THAN ("2024-04-01"),
    PARTITION p2024q2 VALUES LESS THAN ("2024-07-01"),
    PARTITION p2024q3 VALUES LESS THAN ("2024-10-01"),
    PARTITION p2024q4 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025q1 VALUES LESS THAN ("2025-04-01"),
    PARTITION p2025q2 VALUES LESS THAN ("2025-07-01"),
    PARTITION p2025q3 VALUES LESS THAN ("2025-10-01"),
    PARTITION p2025q4 VALUES LESS THAN ("2026-01-01"),
    PARTITION p2026q1 VALUES LESS THAN ("2026-07-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 16
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS raw_payment;
CREATE TABLE raw_payment (
    payment_id          VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),
    payment_date        DATETIME,
    due_date            DATE,
    statement_date      DATE,
    minimum_due         DECIMAL(20,2),
    total_due           DECIMAL(20,2),
    amount_paid         DECIMAL(20,2),
    payment_method      VARCHAR(20),               -- GIRO | TRANSFER | CASH | CHEQUE | ONLINE | UPI | PAYNOW
    payment_channel     VARCHAR(30),               -- MOBILE_APP | INTERNET_BANKING | ATM | BRANCH
    payment_status      VARCHAR(20),               -- PAID | PARTIAL | OVERDUE | PENDING | FAILED
    overdue_days        INT,
    late_fee            DECIMAL(20,2),
    reference_number    VARCHAR(30),
    source_system       VARCHAR(30),
    created_at          DATETIME
) DUPLICATE KEY(payment_id, country_code)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS raw_statement;
CREATE TABLE raw_statement (
    statement_id        VARCHAR(30)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),
    statement_date      DATE            NOT NULL,
    due_date            DATE,
    opening_balance     DECIMAL(20,2),
    closing_balance     DECIMAL(20,2),
    total_credits       DECIMAL(20,2),
    total_debits        DECIMAL(20,2),
    minimum_due         DECIMAL(20,2),
    total_due           DECIMAL(20,2),
    interest_charged    DECIMAL(20,2),
    late_fee            DECIMAL(20,2),
    reward_points_earned   BIGINT,
    reward_points_redeemed BIGINT,
    transaction_count   INT,
    source_system       VARCHAR(30),
    created_at          DATETIME
) DUPLICATE KEY(statement_id, country_code)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS raw_merchant;
CREATE TABLE raw_merchant (
    merchant_id         VARCHAR(20)     NOT NULL,
    merchant_name       VARCHAR(100),
    merchant_name_clean VARCHAR(100),
    merchant_category   VARCHAR(50),
    mcc_code            VARCHAR(6),
    country_code        VARCHAR(2),
    city                VARCHAR(50),
    address             VARCHAR(255),
    is_online           TINYINT         DEFAULT 0,
    risk_tier           VARCHAR(10),               -- LOW | MEDIUM | HIGH | CRITICAL
    is_blacklisted      TINYINT         DEFAULT 0,
    blacklist_reason    VARCHAR(100),
    blacklist_date      DATE,
    source_system       VARCHAR(30),
    created_at          DATETIME,
    updated_at          DATETIME
) DUPLICATE KEY(merchant_id)
DISTRIBUTED BY HASH(merchant_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");


-- =============================================================================
-- DDM LAYER — normalized domain model, SCD-2 for customer/account/card
-- =============================================================================

DROP TABLE IF EXISTS ddm_customer;
CREATE TABLE ddm_customer (
    customer_key        BIGINT          NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),               -- SG_BANK | MY_BANK | IN_BANK
    full_name           VARCHAR(100),
    date_of_birth       DATE,
    age                 INT,
    age_band            VARCHAR(15),               -- <25 | 25-35 | 35-50 | 50-65 | >65
    gender              VARCHAR(10),
    email               VARCHAR(100),
    phone               VARCHAR(25),
    city                VARCHAR(50),
    nationality         VARCHAR(50),
    id_type             VARCHAR(20),
    id_number_masked    VARCHAR(30),              -- masked for security
    customer_segment    VARCHAR(20),               -- MASS | AFFLUENT | PRIORITY | PRIVATE
    kyc_status          VARCHAR(20),
    kyc_expiry_date     DATE,
    risk_rating         VARCHAR(10),
    annual_income       DECIMAL(20,2),
    income_band         VARCHAR(20),               -- <50K | 50K-150K | 150K-500K | >500K (local currency)
    occupation          VARCHAR(50),
    tenure_months       INT,
    acquisition_channel VARCHAR(30),
    relationship_manager VARCHAR(50),
    is_active           TINYINT         DEFAULT 1,
    -- SCD-2 fields
    effective_from      DATETIME,
    effective_to        DATETIME,                  -- NULL means current
    is_current          TINYINT         DEFAULT 1,
    dw_created_at       DATETIME,
    dw_updated_at       DATETIME
) UNIQUE KEY(customer_key, country_code)
DISTRIBUTED BY HASH(customer_key) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS ddm_account;
CREATE TABLE ddm_account (
    account_key         BIGINT          NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_key        BIGINT,
    customer_id         VARCHAR(20),
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),
    account_type        VARCHAR(20),
    account_subtype     VARCHAR(30),
    currency_code       VARCHAR(3),
    current_balance     DECIMAL(20,2),
    available_balance   DECIMAL(20,2),
    credit_limit        DECIMAL(20,2),
    utilization_pct     DECIMAL(8,4),             -- outstanding / credit_limit
    interest_rate       DECIMAL(8,4),
    status              VARCHAR(20),
    status_reason       VARCHAR(50),
    branch_code         VARCHAR(15),
    product_code        VARCHAR(20),
    product_name        VARCHAR(50),
    open_date           DATE,
    tenure_months       INT,
    last_activity_date  DATE,
    days_since_activity INT,
    is_active           TINYINT         DEFAULT 1,
    -- SCD-2
    effective_from      DATETIME,
    effective_to        DATETIME,
    is_current          TINYINT         DEFAULT 1,
    dw_created_at       DATETIME
) UNIQUE KEY(account_key, country_code)
DISTRIBUTED BY HASH(account_key) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS ddm_card;
CREATE TABLE ddm_card (
    card_key            BIGINT          NOT NULL,
    card_id             VARCHAR(20)     NOT NULL,
    account_key         BIGINT,
    customer_key        BIGINT,
    country_code        VARCHAR(2)      NOT NULL,
    card_type           VARCHAR(20),
    card_category       VARCHAR(20),
    card_number_masked  VARCHAR(20),
    credit_limit        DECIMAL(20,2),
    available_credit    DECIMAL(20,2),
    outstanding_balance DECIMAL(20,2),
    utilization_pct     DECIMAL(8,4),
    min_payment_due     DECIMAL(20,2),
    expiry_date         DATE,
    days_to_expiry      INT,
    status              VARCHAR(20),
    is_primary          TINYINT,
    is_expired          TINYINT,
    is_blocked          TINYINT,
    reward_points       BIGINT,
    contactless_enabled TINYINT,
    online_enabled      TINYINT,
    intl_enabled        TINYINT,
    dw_created_at       DATETIME
) UNIQUE KEY(card_key, country_code)
DISTRIBUTED BY HASH(card_key) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS ddm_transaction;
CREATE TABLE ddm_transaction (
    transaction_key     BIGINT          NOT NULL,
    transaction_id      VARCHAR(30)     NOT NULL,
    account_key         BIGINT,
    card_key            BIGINT,
    customer_key        BIGINT,
    merchant_key        BIGINT,
    country_code        VARCHAR(2)      NOT NULL,
    transaction_date    DATETIME        NOT NULL,
    posting_date        DATETIME,
    year_month          VARCHAR(7),               -- YYYY-MM for easy aggregation
    year_quarter        VARCHAR(7),               -- YYYY-QN
    amount_local        DECIMAL(20,2),
    amount_usd          DECIMAL(20,2),            -- standardized to USD
    currency_code       VARCHAR(3),
    fx_rate             DECIMAL(12,6),
    transaction_type    VARCHAR(20),
    channel             VARCHAR(20),
    merchant_category   VARCHAR(50),
    merchant_category_group VARCHAR(30),         -- FOOD_DINING | SHOPPING | TRAVEL | SERVICES | UTILITIES
    mcc_code            VARCHAR(6),
    status              VARCHAR(20),
    decline_reason      VARCHAR(50),
    is_fraud            TINYINT         DEFAULT 0,
    fraud_score         DECIMAL(5,4),
    fraud_tier          VARCHAR(10),              -- LOW (<0.3) | MEDIUM (0.3-0.7) | HIGH (>0.7)
    is_international    TINYINT         DEFAULT 0,
    is_contactless      TINYINT         DEFAULT 0,
    is_recurring        TINYINT         DEFAULT 0,
    dw_created_at       DATETIME
) DUPLICATE KEY(transaction_key, country_code)
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
DISTRIBUTED BY HASH(customer_key) BUCKETS 16
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS ddm_payment;
CREATE TABLE ddm_payment (
    payment_key         BIGINT          NOT NULL,
    payment_id          VARCHAR(30)     NOT NULL,
    account_key         BIGINT,
    customer_key        BIGINT,
    country_code        VARCHAR(2)      NOT NULL,
    payment_date        DATETIME,
    due_date            DATE,
    statement_date      DATE,
    days_before_due     INT,                       -- negative = paid late
    is_early            TINYINT,
    is_on_time          TINYINT,
    is_late             TINYINT,
    minimum_due         DECIMAL(20,2),
    total_due           DECIMAL(20,2),
    amount_paid         DECIMAL(20,2),
    payment_ratio       DECIMAL(8,4),             -- amount_paid / total_due
    is_full_payment     TINYINT,
    is_minimum_only     TINYINT,
    is_partial          TINYINT,
    payment_method      VARCHAR(20),
    payment_status      VARCHAR(20),
    overdue_days        INT,
    late_fee            DECIMAL(20,2),
    dw_created_at       DATETIME
) DUPLICATE KEY(payment_key, country_code)
DISTRIBUTED BY HASH(account_key) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS ddm_statement;
CREATE TABLE ddm_statement (
    statement_key           BIGINT          NOT NULL,
    statement_id            VARCHAR(30)     NOT NULL,
    account_key             BIGINT,
    customer_key            BIGINT,
    country_code            VARCHAR(2)      NOT NULL,
    statement_year_month    VARCHAR(7),            -- YYYY-MM
    statement_date          DATE,
    due_date                DATE,
    payment_date            DATE,
    days_to_due             INT,
    opening_balance         DECIMAL(20,2),
    closing_balance         DECIMAL(20,2),
    total_spend             DECIMAL(20,2),
    total_credits           DECIMAL(20,2),
    minimum_due             DECIMAL(20,2),
    total_due               DECIMAL(20,2),
    interest_charged        DECIMAL(20,2),
    late_fee                DECIMAL(20,2),
    reward_points_earned    BIGINT,
    reward_points_redeemed  BIGINT,
    transaction_count       INT,
    is_paid                 TINYINT,
    is_overdue              TINYINT,
    days_overdue            INT,
    dw_created_at           DATETIME
) DUPLICATE KEY(statement_key, country_code)
DISTRIBUTED BY HASH(account_key) BUCKETS 8
PROPERTIES ("replication_num" = "1");


DROP TABLE IF EXISTS ddm_merchant;
CREATE TABLE ddm_merchant (
    merchant_key        BIGINT          NOT NULL,
    merchant_id         VARCHAR(20)     NOT NULL,
    merchant_name       VARCHAR(100),
    merchant_name_clean VARCHAR(100),
    merchant_category   VARCHAR(50),
    merchant_category_group VARCHAR(30),
    mcc_code            VARCHAR(6),
    country_code        VARCHAR(2),
    city                VARCHAR(50),
    is_online           TINYINT,
    risk_tier           VARCHAR(10),
    is_blacklisted      TINYINT,
    total_transaction_count  BIGINT,
    total_transaction_volume DECIMAL(20,2),
    avg_transaction_amount   DECIMAL(20,2),
    fraud_rate               DECIMAL(5,4),
    decline_rate             DECIMAL(5,4),
    dw_created_at            DATETIME
) UNIQUE KEY(merchant_key)
DISTRIBUTED BY HASH(merchant_key) BUCKETS 4
PROPERTIES ("replication_num" = "1");
