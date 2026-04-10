-- =============================================================================
-- DataPrismAI Banking Platform — Deposit & Loan Extensions
-- File: 30_banking_deposits_loans.sql
-- Layers: RAW | DDM | DP | SEMANTIC
-- New domains: Deposits (Savings/Current/FD), Loans (Personal/Home/Auto/Business)
-- Run AFTER: 20_banking_schema.sql
-- =============================================================================

USE cc_analytics;

-- =============================================================================
-- SECTION 1: DROP & (RE)CREATE — RAW ADDITIONS
-- =============================================================================

DROP TABLE IF EXISTS raw_deposit_account;
DROP TABLE IF EXISTS raw_deposit_transaction;
DROP TABLE IF EXISTS raw_loan;
DROP TABLE IF EXISTS raw_loan_repayment;
DROP TABLE IF EXISTS ddm_deposit_account;
DROP TABLE IF EXISTS ddm_loan;
DROP TABLE IF EXISTS ddm_loan_repayment;
DROP TABLE IF EXISTS dp_deposit_portfolio;
DROP TABLE IF EXISTS dp_loan_portfolio;
DROP TABLE IF EXISTS semantic_deposit_portfolio;
DROP TABLE IF EXISTS semantic_loan_portfolio;
DROP TABLE IF EXISTS semantic_customer_product_mix;

-- ── raw_deposit_account ──────────────────────────────────────────────────────
-- Deposit product master: Savings, Current, Fixed Deposit
-- One row per deposit account, links to raw_account via account_id
CREATE TABLE raw_deposit_account (
    deposit_id          VARCHAR(20)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    deposit_type        VARCHAR(30),    -- SAVINGS | SAVINGS_PLUS | CURRENT | CURRENT_PLUS | FIXED_DEPOSIT
    deposit_category    VARCHAR(20),    -- SAVINGS | CURRENT | TERM_DEPOSIT
    product_code        VARCHAR(30),
    product_name        VARCHAR(100),
    currency_code       VARCHAR(5),
    current_balance     DECIMAL(20,2),
    minimum_balance     DECIMAL(20,2),
    interest_rate       DECIMAL(8,4),  -- annual rate e.g. 0.0350 = 3.50%
    interest_frequency  VARCHAR(20),   -- MONTHLY | QUARTERLY | HALF_YEARLY | ANNUALLY
    interest_earned_ytd DECIMAL(20,2),
    -- Fixed Deposit specific
    tenor_months        INT,           -- 0=demand, 1/3/6/12/24/36 for FD
    deposit_amount      DECIMAL(20,2), -- original placed amount (FD)
    maturity_date       DATE,
    maturity_amount     DECIMAL(20,2),
    auto_renewal        TINYINT        DEFAULT '0',
    auto_renewal_tenor  INT,
    -- Savings / Current specific
    avg_monthly_balance DECIMAL(20,2),
    has_salary_credit   TINYINT        DEFAULT '0',
    salary_credit_amount DECIMAL(20,2),
    sweep_enabled       TINYINT        DEFAULT '0',
    sweep_linked_account VARCHAR(20),
    -- Account state
    status              VARCHAR(20),   -- ACTIVE | DORMANT | CLOSED | FROZEN | MATURING
    open_date           DATE,
    close_date          DATE,
    last_debit_date     DATE,
    last_credit_date    DATE,
    branch_code         VARCHAR(20),
    source_system       VARCHAR(30)    DEFAULT 'CBS',
    is_deleted          TINYINT        DEFAULT '0',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(deposit_id, account_id, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── raw_deposit_transaction ──────────────────────────────────────────────────
-- Debit / credit transactions on deposit accounts (ATM, UPI, salary, transfers, etc.)
CREATE TABLE raw_deposit_transaction (
    txn_id              VARCHAR(30)     NOT NULL,
    deposit_id          VARCHAR(20)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    txn_date            DATETIME        NOT NULL,
    value_date          DATETIME,
    amount              DECIMAL(20,2)   NOT NULL,
    txn_direction       VARCHAR(10),    -- CREDIT | DEBIT
    txn_type            VARCHAR(30),    -- SALARY_CREDIT | TRANSFER_IN | TRANSFER_OUT | ATM_WITHDRAWAL | UPI_PAYMENT | NEFT | IMPS | PAYNOW | FPS | INTEREST_CREDIT | STANDING_ORDER | CASH_DEPOSIT | UTILITY_PAYMENT | FD_ROLLOVER | FD_MATURITY | FEE_DEBIT | GIRO | CHEQUE
    txn_category        VARCHAR(30),    -- SALARY | TRANSFER | CASH | INVESTMENT | UTILITY | LOAN_EMI | INTEREST | FEE
    channel             VARCHAR(20),    -- MOBILE | INTERNET | ATM | BRANCH | STANDING_ORDER | INTER_BANK | SYSTEM
    description         VARCHAR(200),
    beneficiary_name    VARCHAR(100),
    beneficiary_account VARCHAR(30),
    reference_number    VARCHAR(30),
    balance_after       DECIMAL(20,2),
    status              VARCHAR(20),    -- COMPLETED | PENDING | FAILED | REVERSED
    source_system       VARCHAR(30)     DEFAULT 'CBS',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(txn_id, deposit_id)
PARTITION BY RANGE(txn_date)(
    PARTITION p2024q1 VALUES LESS THAN ("2024-04-01"),
    PARTITION p2024q2 VALUES LESS THAN ("2024-07-01"),
    PARTITION p2024q3 VALUES LESS THAN ("2024-10-01"),
    PARTITION p2024q4 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025q1 VALUES LESS THAN ("2025-04-01"),
    PARTITION p2025q2 VALUES LESS THAN ("2025-07-01"),
    PARTITION p2025q3 VALUES LESS THAN ("2025-10-01"),
    PARTITION p2025q4 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture  VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- ── raw_loan ─────────────────────────────────────────────────────────────────
-- Loan master record (Personal / Home / Auto / Business / Education)
CREATE TABLE raw_loan (
    loan_id             VARCHAR(20)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    loan_type           VARCHAR(30),   -- PERSONAL | HOME | AUTO | BUSINESS | EDUCATION | RENOVATION
    loan_category       VARCHAR(20),   -- SECURED | UNSECURED
    loan_purpose        VARCHAR(100),
    product_code        VARCHAR(30),
    product_name        VARCHAR(100),
    currency_code       VARCHAR(5),
    -- Original terms
    loan_amount         DECIMAL(20,2)  NOT NULL,
    disbursement_date   DATE,
    loan_term_months    INT,
    interest_type       VARCHAR(10),   -- FIXED | FLOATING
    annual_interest_rate DECIMAL(8,4),
    emi_amount          DECIMAL(20,2),
    total_interest_payable DECIMAL(20,2),
    -- Current position
    outstanding_principal DECIMAL(20,2),
    outstanding_balance DECIMAL(20,2), -- principal + accrued interest
    accrued_interest    DECIMAL(20,2),
    total_paid          DECIMAL(20,2),
    last_payment_date   DATE,
    next_due_date       DATE,
    payments_made       INT,
    payments_remaining  INT,
    -- Overdue / NPA
    overdue_amount      DECIMAL(20,2)  DEFAULT '0',
    overdue_days        INT            DEFAULT '0',
    dpd_bucket          VARCHAR(15),   -- CURRENT | DPD_1_30 | DPD_31_60 | DPD_61_90 | DPD_90_PLUS
    npa_flag            TINYINT        DEFAULT '0',
    npa_date            DATE,
    restructured_flag   TINYINT        DEFAULT '0',
    restructure_date    DATE,
    written_off_flag    TINYINT        DEFAULT '0',
    -- Collateral (secured loans)
    collateral_type     VARCHAR(30),   -- PROPERTY | VEHICLE | FIXED_DEPOSIT | NONE
    collateral_description VARCHAR(200),
    collateral_value    DECIMAL(20,2),
    ltv_ratio           DECIMAL(8,4),
    -- Status
    loan_status         VARCHAR(20),   -- ACTIVE | CLOSED | NPA | PENDING_DISBURSAL | RESTRUCTURED
    branch_code         VARCHAR(20),
    sourced_by          VARCHAR(50),   -- BRANCH | ONLINE | AGENT | REFERRAL | TOP_UP
    source_system       VARCHAR(30)    DEFAULT 'LOS',
    is_deleted          TINYINT        DEFAULT '0',
    created_at          DATETIME,
    updated_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(loan_id, account_id, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── raw_loan_repayment ───────────────────────────────────────────────────────
-- Monthly EMI repayment schedule + actual payment record
CREATE TABLE raw_loan_repayment (
    repayment_id        VARCHAR(30)     NOT NULL,
    loan_id             VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    installment_number  INT             NOT NULL,
    due_date            DATE            NOT NULL,
    payment_date        DATE,
    -- Amounts due
    principal_due       DECIMAL(20,2),
    interest_due        DECIMAL(20,2),
    emi_due             DECIMAL(20,2),  -- principal + interest
    penalty_charges     DECIMAL(20,2)  DEFAULT '0',
    -- Amounts paid
    amount_paid         DECIMAL(20,2)  DEFAULT '0',
    principal_paid      DECIMAL(20,2)  DEFAULT '0',
    interest_paid       DECIMAL(20,2)  DEFAULT '0',
    -- Residual
    outstanding_principal DECIMAL(20,2),
    overdue_days        INT            DEFAULT '0',
    cumulative_overdue  DECIMAL(20,2)  DEFAULT '0',
    -- Payment details
    payment_status      VARCHAR(20),   -- PAID | PARTIAL | OVERDUE | FUTURE | WAIVED
    payment_method      VARCHAR(30),   -- GIRO | UPI | NEFT | STANDING_ORDER | MANUAL | CHEQUE
    payment_channel     VARCHAR(30),   -- MOBILE | INTERNET | BRANCH | AUTO_DEBIT
    reference_number    VARCHAR(30),
    source_system       VARCHAR(30)    DEFAULT 'LOS',
    created_at          DATETIME
) ENGINE = OLAP
DUPLICATE KEY(repayment_id, loan_id, customer_id, country_code)
PARTITION BY RANGE(due_date)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(loan_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 2: DDM LAYER — CONFORMED DOMAIN MODEL
-- =============================================================================

-- ── ddm_deposit_account ──────────────────────────────────────────────────────
CREATE TABLE ddm_deposit_account (
    deposit_key         BIGINT          NOT NULL,
    deposit_id          VARCHAR(20)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    customer_segment    VARCHAR(30),
    deposit_type        VARCHAR(30),
    deposit_category    VARCHAR(20),    -- SAVINGS | CURRENT | TERM_DEPOSIT
    product_name        VARCHAR(100),
    currency_code       VARCHAR(5),
    current_balance     DECIMAL(20,2),
    deposit_amount      DECIMAL(20,2),
    interest_rate       DECIMAL(8,4),
    interest_earned_ytd DECIMAL(20,2),
    tenor_months        INT,
    balance_band        VARCHAR(20),    -- <10K | 10K–50K | 50K–200K | 200K+
    is_fd               TINYINT        DEFAULT '0',
    is_term_maturing_30d TINYINT       DEFAULT '0',
    has_salary_credit   TINYINT        DEFAULT '0',
    tenure_months       INT,           -- months since open_date
    status              VARCHAR(20),
    open_date           DATE,
    maturity_date       DATE,
    last_debit_date     DATE,
    last_credit_date    DATE,
    dw_refreshed_at     DATETIME
) ENGINE = OLAP
DUPLICATE KEY(deposit_key, deposit_id, account_id, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── ddm_loan ──────────────────────────────────────────────────────────────────
CREATE TABLE ddm_loan (
    loan_key            BIGINT          NOT NULL,
    loan_id             VARCHAR(20)     NOT NULL,
    account_id          VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    customer_segment    VARCHAR(30),
    loan_type           VARCHAR(30),
    loan_category       VARCHAR(20),   -- SECURED | UNSECURED
    currency_code       VARCHAR(5),
    loan_amount         DECIMAL(20,2),
    outstanding_balance DECIMAL(20,2),
    interest_rate       DECIMAL(8,4),
    emi_amount          DECIMAL(20,2),
    loan_term_months    INT,
    months_remaining    INT,
    disbursement_date   DATE,
    maturity_date       DATE,
    loan_status         VARCHAR(20),
    dpd_bucket          VARCHAR(15),
    overdue_days        INT,
    npa_flag            TINYINT,
    ltv_ratio           DECIMAL(8,4),
    loan_to_income_ratio DECIMAL(8,4),
    dw_refreshed_at     DATETIME
) ENGINE = OLAP
DUPLICATE KEY(loan_key, loan_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── ddm_loan_repayment ────────────────────────────────────────────────────────
CREATE TABLE ddm_loan_repayment (
    repayment_key       BIGINT          NOT NULL,
    repayment_id        VARCHAR(30)     NOT NULL,
    loan_id             VARCHAR(20)     NOT NULL,
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    customer_segment    VARCHAR(30),
    loan_type           VARCHAR(30),
    installment_number  INT,
    due_date            DATE,
    payment_date        DATE,
    emi_due             DECIMAL(20,2),
    amount_paid         DECIMAL(20,2),
    outstanding_principal DECIMAL(20,2),
    overdue_days        INT,
    payment_status      VARCHAR(20),
    is_late             TINYINT,
    delay_days          INT,
    dw_refreshed_at     DATETIME
) ENGINE = OLAP
DUPLICATE KEY(repayment_key, repayment_id, loan_id, customer_id, country_code)
PARTITION BY RANGE(due_date)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 3: DATA PRODUCTS LAYER
-- =============================================================================

-- ── dp_deposit_portfolio ──────────────────────────────────────────────────────
-- Monthly deposit portfolio snapshot per customer
CREATE TABLE dp_deposit_portfolio (
    snapshot_month      VARCHAR(7)      NOT NULL,  -- YYYY-MM
    customer_id         VARCHAR(20)     NOT NULL,
    country_code        VARCHAR(5)      NOT NULL,
    legal_entity        VARCHAR(20),
    customer_segment    VARCHAR(30),
    currency_code       VARCHAR(5),
    -- Savings
    savings_balance           DECIMAL(20,2),
    savings_account_count     INT,
    savings_interest_rate     DECIMAL(8,4),
    savings_interest_earned   DECIMAL(20,2),
    -- Current
    current_balance           DECIMAL(20,2),
    current_account_count     INT,
    -- Fixed Deposits
    fd_balance                DECIMAL(20,2),
    fd_count                  INT,
    fd_avg_rate               DECIMAL(8,4),
    fd_maturing_next_30d      DECIMAL(20,2),
    fd_maturing_next_90d      DECIMAL(20,2),
    -- Totals
    total_deposit_balance     DECIMAL(20,2),
    total_deposit_accounts    INT,
    total_interest_earned_ytd DECIMAL(20,2),
    -- Behavior
    avg_monthly_credits       DECIMAL(20,2),
    avg_monthly_debits        DECIMAL(20,2),
    monthly_credit_count      INT,
    monthly_debit_count       INT,
    has_salary_credit         TINYINT,
    salary_credit_amount      DECIMAL(20,2),
    -- Month over month
    deposit_balance_mom_change DECIMAL(20,2),
    deposit_balance_mom_pct   DECIMAL(8,4),
    dw_refreshed_at           DATETIME
) ENGINE = OLAP
DUPLICATE KEY(snapshot_month, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── dp_loan_portfolio ─────────────────────────────────────────────────────────
-- Monthly loan portfolio snapshot per customer
CREATE TABLE dp_loan_portfolio (
    snapshot_month          VARCHAR(7)      NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(5)      NOT NULL,
    legal_entity            VARCHAR(20),
    customer_segment        VARCHAR(30),
    currency_code           VARCHAR(5),
    annual_income           DECIMAL(20,2),
    -- By loan type
    personal_loan_outstanding  DECIMAL(20,2),
    personal_loan_count        INT,
    personal_loan_emi          DECIMAL(20,2),
    home_loan_outstanding      DECIMAL(20,2),
    home_loan_count            INT,
    home_loan_emi              DECIMAL(20,2),
    auto_loan_outstanding      DECIMAL(20,2),
    auto_loan_count            INT,
    auto_loan_emi              DECIMAL(20,2),
    business_loan_outstanding  DECIMAL(20,2),
    business_loan_count        INT,
    business_loan_emi          DECIMAL(20,2),
    education_loan_outstanding DECIMAL(20,2),
    education_loan_count       INT,
    -- Aggregates
    total_loan_outstanding     DECIMAL(20,2),
    total_loan_count           INT,
    total_monthly_emi          DECIMAL(20,2),
    -- Risk indicators
    max_overdue_days           INT,
    overdue_loan_count         INT,
    is_npa                     TINYINT,
    npa_amount                 DECIMAL(20,2),
    dpd_bucket                 VARCHAR(15),
    -- Ratios
    debt_to_income_ratio       DECIMAL(8,4),
    debt_service_ratio         DECIMAL(8,4), -- total_emi / (annual_income/12)
    dw_refreshed_at            DATETIME
) ENGINE = OLAP
DUPLICATE KEY(snapshot_month, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- =============================================================================
-- SECTION 4: SEMANTIC LAYER
-- =============================================================================

-- ── semantic_deposit_portfolio ───────────────────────────────────────────────
-- Query target for: "What is my savings balance?", "Show FD portfolio", "Deposits by segment"
CREATE TABLE semantic_deposit_portfolio (
    snapshot_month          VARCHAR(7)      NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(5)      NOT NULL,
    legal_entity            VARCHAR(20),
    customer_name           VARCHAR(100),
    customer_segment        VARCHAR(30),
    risk_rating             VARCHAR(10),
    currency_code           VARCHAR(5),
    -- Savings
    savings_account_id      VARCHAR(20),
    savings_balance         DECIMAL(20,2),
    savings_interest_rate   DECIMAL(8,4),
    savings_interest_ytd    DECIMAL(20,2),
    -- Current
    current_account_id      VARCHAR(20),
    current_balance         DECIMAL(20,2),
    -- Fixed Deposit
    fd_count                INT,
    total_fd_balance        DECIMAL(20,2),
    fd_avg_rate             DECIMAL(8,4),
    fd_maturing_next_30d    DECIMAL(20,2),
    -- Portfolio totals
    total_deposit_balance   DECIMAL(20,2),
    deposit_mom_change_pct  DECIMAL(8,4),
    -- Behavior
    has_salary_credit       TINYINT,
    avg_monthly_credit      DECIMAL(20,2),
    avg_monthly_debit       DECIMAL(20,2),
    dw_refreshed_at         DATETIME
) ENGINE = OLAP
UNIQUE KEY(snapshot_month, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── semantic_loan_portfolio ───────────────────────────────────────────────────
-- Query target for: "Show my loan EMI", "Which customers have home loans?", "NPA analysis"
CREATE TABLE semantic_loan_portfolio (
    snapshot_month              VARCHAR(7)      NOT NULL,
    customer_id                 VARCHAR(20)     NOT NULL,
    country_code                VARCHAR(5)      NOT NULL,
    legal_entity                VARCHAR(20),
    customer_name               VARCHAR(100),
    customer_segment            VARCHAR(30),
    risk_rating                 VARCHAR(10),
    kyc_status                  VARCHAR(20),
    currency_code               VARCHAR(5),
    annual_income               DECIMAL(20,2),
    -- Personal loan
    personal_loan_id            VARCHAR(20),
    personal_loan_disbursed     DECIMAL(20,2),
    personal_loan_outstanding   DECIMAL(20,2),
    personal_loan_rate          DECIMAL(8,4),
    personal_loan_emi           DECIMAL(20,2),
    personal_loan_term_months   INT,
    personal_loan_months_remaining INT,
    personal_loan_status        VARCHAR(20),
    personal_loan_overdue_days  INT,
    -- Home loan
    home_loan_id                VARCHAR(20),
    home_loan_disbursed         DECIMAL(20,2),
    home_loan_outstanding       DECIMAL(20,2),
    home_loan_rate              DECIMAL(8,4),
    home_loan_emi               DECIMAL(20,2),
    home_loan_ltv               DECIMAL(8,4),
    home_loan_status            VARCHAR(20),
    -- Auto loan
    auto_loan_id                VARCHAR(20),
    auto_loan_disbursed         DECIMAL(20,2),
    auto_loan_outstanding       DECIMAL(20,2),
    auto_loan_rate              DECIMAL(8,4),
    auto_loan_emi               DECIMAL(20,2),
    auto_loan_status            VARCHAR(20),
    -- Portfolio totals
    total_loan_outstanding      DECIMAL(20,2),
    total_loan_count            INT,
    total_monthly_emi           DECIMAL(20,2),
    -- Delinquency
    max_overdue_days            INT,
    overdue_bucket              VARCHAR(15),    -- CURRENT|DPD_1_30|DPD_31_60|DPD_61_90|DPD_90_PLUS
    is_npa                      TINYINT,
    total_overdue_amount        DECIMAL(20,2),
    -- Ratios
    loan_to_income_ratio        DECIMAL(8,4),
    debt_service_ratio          DECIMAL(8,4),
    dw_refreshed_at             DATETIME
) ENGINE = OLAP
UNIQUE KEY(snapshot_month, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── semantic_customer_product_mix ────────────────────────────────────────────
-- Cross-sell / C360 view: product holdings + demographics for all personas
CREATE TABLE semantic_customer_product_mix (
    snapshot_month          VARCHAR(7)      NOT NULL,
    customer_id             VARCHAR(20)     NOT NULL,
    country_code            VARCHAR(5)      NOT NULL,
    legal_entity            VARCHAR(20),
    customer_name           VARCHAR(100),
    date_of_birth           DATE,
    age                     INT,
    age_band                VARCHAR(20),
    gender                  VARCHAR(10),
    city                    VARCHAR(80),
    customer_segment        VARCHAR(30),
    risk_rating             VARCHAR(10),
    kyc_status              VARCHAR(20),
    occupation              VARCHAR(100),
    annual_income           DECIMAL(20,2),
    income_band             VARCHAR(30),
    tenure_months           INT,
    currency_code           VARCHAR(5),
    -- Product flags
    total_product_count     INT,
    has_credit_card         TINYINT,
    has_savings             TINYINT,
    has_current             TINYINT,
    has_fd                  TINYINT,
    has_loan                TINYINT,
    has_personal_loan       TINYINT,
    has_home_loan           TINYINT,
    has_auto_loan           TINYINT,
    -- Financials summary
    total_asset_balance     DECIMAL(20,2),
    total_liability_balance DECIMAL(20,2),
    net_balance             DECIMAL(20,2),
    cc_outstanding          DECIMAL(20,2),
    cc_credit_limit         DECIMAL(20,2),
    cc_utilization_pct      DECIMAL(8,4),
    cc_spend_last_month     DECIMAL(20,2),
    total_deposit_balance   DECIMAL(20,2),
    total_loan_outstanding  DECIMAL(20,2),
    total_monthly_emi       DECIMAL(20,2),
    -- Health
    payment_status          VARCHAR(20),    -- CC payment status
    consecutive_late_months INT,
    is_overdue              TINYINT,
    wallet_share_score      DECIMAL(8,4),
    dw_refreshed_at         DATETIME
) ENGINE = OLAP
UNIQUE KEY(snapshot_month, customer_id, country_code)
DISTRIBUTED BY HASH(customer_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");
