-- =============================================================================
-- DataPrismAI Banking Platform
-- File: 12_banking_mapping.sql
-- Purpose: Persona/domain routing tables, metrics glossary, access control
-- These tables are used by the backend API for NL-to-SQL semantic routing
-- =============================================================================

-- =============================================================================
-- METRICS GLOSSARY — business definitions for LLM context injection
-- =============================================================================

DROP TABLE IF EXISTS semantic_glossary_metrics;
CREATE TABLE semantic_glossary_metrics (
    metric_id               INT             NOT NULL,
    metric_name             VARCHAR(100)    NOT NULL,    -- business name, e.g. "Fraud Rate"
    metric_definition       VARCHAR(500),               -- plain-English definition
    metric_formula          VARCHAR(300),               -- e.g. "fraud_transactions / total_transactions"
    grain                   VARCHAR(50),                -- DAY | MONTH | CUSTOMER | COUNTRY
    source_table            VARCHAR(100),               -- semantic table to query
    domain                  VARCHAR(30),                -- risk | spend | payments | customer | portfolio
    allowed_personas        VARCHAR(200),               -- comma-separated: analyst,cfo,fraud_analyst
    unit                    VARCHAR(20),                -- % | count | currency | ratio
    is_kpi                  TINYINT         DEFAULT 0,  -- 1 = executive KPI
    example_question        VARCHAR(300),
    display_format          VARCHAR(50)                 -- PERCENT | CURRENCY | INTEGER | DECIMAL
) DUPLICATE KEY(metric_id)
DISTRIBUTED BY HASH(metric_id) BUCKETS 2
PROPERTIES ("replication_num" = "1");

INSERT INTO semantic_glossary_metrics VALUES
(1,  'Fraud Rate',              'Percentage of transactions flagged as fraudulent out of total approved transactions.',
     'fraud_transactions / total_transactions * 100',
     'DAY,MONTH', 'semantic_risk_metrics', 'risk', 'analyst,fraud_analyst,cfo', '%', 1,
     'What is the fraud rate this month?', 'PERCENT'),
(2,  'Decline Rate',            'Percentage of card transactions declined by the authorisation system.',
     'declined_transactions / total_transactions * 100',
     'DAY,MONTH', 'semantic_risk_metrics', 'risk', 'analyst,fraud_analyst', '%', 1,
     'Show decline rate by country', 'PERCENT'),
(3,  'Total Spend',             'Sum of all approved transaction amounts in local currency for a given period.',
     'SUM(amount) WHERE status = APPROVED',
     'MONTH,CUSTOMER', 'semantic_spend_metrics', 'spend', 'analyst,cfo,end_user,retail_user', 'currency', 1,
     'How much did I spend last month?', 'CURRENCY'),
(4,  'Utilisation Rate',        'Percentage of credit limit currently used by the customer.',
     'outstanding_balance / credit_limit * 100',
     'DAY,CUSTOMER', 'semantic_customer_360', 'customer', 'analyst,cfo,end_user', '%', 0,
     'What is my credit utilisation?', 'PERCENT'),
(5,  'Total Due',               'Total outstanding balance due for payment by the next due date.',
     'total_due',
     'MONTH,CUSTOMER', 'semantic_payment_status', 'payments', 'analyst,cfo,end_user,retail_user', 'currency', 0,
     'What is my total due amount?', 'CURRENCY'),
(6,  'Days to Due',             'Number of calendar days until the next payment due date.',
     'DATEDIFF(due_date, CURRENT_DATE)',
     'DAY,CUSTOMER', 'semantic_payment_status', 'payments', 'end_user,retail_user', 'count', 0,
     'When is my next payment due?', 'INTEGER'),
(7,  'Delinquency Rate',        'Percentage of accounts with overdue balances older than 30 days.',
     'overdue_accounts / total_accounts * 100',
     'MONTH,COUNTRY', 'semantic_risk_metrics', 'risk', 'analyst,cfo,fraud_analyst', '%', 1,
     'What is the delinquency rate in SG?', 'PERCENT'),
(8,  'Customer Growth Rate',    'Percentage increase in active customers compared to prior month.',
     '(active_customers - prior_month_active) / prior_month_active * 100',
     'MONTH,COUNTRY', 'semantic_portfolio_kpis', 'portfolio', 'cfo,data_product_owner', '%', 1,
     'Show customer growth rate by country', 'PERCENT'),
(9,  'Avg Transaction Amount',  'Average value of approved transactions per customer per month.',
     'SUM(amount) / COUNT(transaction_id)',
     'MONTH,CUSTOMER', 'semantic_spend_metrics', 'spend', 'analyst,cfo', 'currency', 0,
     'What is the average transaction amount?', 'CURRENCY'),
(10, 'Full Payment Rate',       'Percentage of customers who paid the full statement balance.',
     'full_payment_customers / billed_customers * 100',
     'MONTH,COUNTRY', 'semantic_portfolio_kpis', 'portfolio', 'analyst,cfo,finance_user', '%', 1,
     'What is the full payment rate this month?', 'PERCENT'),
(11, 'Suspicious Transactions', 'Transactions with fraud_score > 0.7 or from blacklisted merchants.',
     'COUNT(*) WHERE is_suspicious = 1',
     'DAY,CUSTOMER', 'semantic_transaction_summary', 'risk', 'analyst,fraud_analyst', 'count', 0,
     'Show suspicious transactions this week', 'INTEGER'),
(12, 'Account Balance',        'Current available balance in the primary account.',
     'available_balance',
     'DAY,CUSTOMER', 'semantic_customer_360', 'customer', 'end_user,retail_user,analyst', 'currency', 0,
     'What is my current account balance?', 'CURRENCY'),
(13, 'Estimated Interest Income','Estimated interest revenue based on outstanding revolving balances.',
     'outstanding_balance * interest_rate / 12',
     'MONTH,COUNTRY', 'semantic_portfolio_kpis', 'portfolio', 'cfo,finance_user', 'currency', 1,
     'What is the estimated interest income for MY?', 'CURRENCY'),
(14, 'Spend by Category',       'Total spend broken down by merchant category group.',
     'SUM(amount) GROUP BY merchant_category_group',
     'MONTH,CUSTOMER', 'semantic_spend_metrics', 'spend', 'analyst,cfo,end_user', 'currency', 0,
     'Show my spend by category last month', 'CURRENCY'),
(15, 'Churn Rate',             'Percentage of previously active customers who had no transactions in the last 90 days.',
     'churned_customers / prior_active_customers * 100',
     'MONTH,COUNTRY', 'semantic_portfolio_kpis', 'portfolio', 'cfo,data_product_owner', '%', 1,
     'What is the customer churn rate in IN?', 'PERCENT');


-- =============================================================================
-- DOMAIN MAPPING — maps business domains to semantic tables
-- =============================================================================

DROP TABLE IF EXISTS domain_semantic_mapping;
CREATE TABLE domain_semantic_mapping (
    domain              VARCHAR(30)     NOT NULL,    -- risk | spend | customer | payments | portfolio | transactions
    semantic_table      VARCHAR(100)    NOT NULL,
    description         VARCHAR(200),
    primary_grain       VARCHAR(30),                -- what the table is primarily indexed by
    refresh_cadence     VARCHAR(20)                 -- DAILY | MONTHLY | REALTIME
) DUPLICATE KEY(domain, semantic_table)
DISTRIBUTED BY HASH(domain) BUCKETS 2
PROPERTIES ("replication_num" = "1");

INSERT INTO domain_semantic_mapping VALUES
('risk',          'semantic_risk_metrics',        'Aggregated fraud and risk KPIs by date/country/channel',  'date,country', 'DAILY'),
('risk',          'semantic_transaction_summary', 'Transaction-level data with fraud scores and risk flags',   'transaction',  'REALTIME'),
('spend',         'semantic_spend_metrics',       'Monthly spend rollup by customer and category',            'month,customer','DAILY'),
('spend',         'semantic_transaction_summary', 'Individual transaction details for spend analysis',        'transaction',  'REALTIME'),
('customer',      'semantic_customer_360',        'Complete customer view: balance, spend, payment health',   'customer',     'DAILY'),
('payments',      'semantic_payment_status',      'Payment due/overdue status per customer and account',      'customer',     'DAILY'),
('portfolio',     'semantic_portfolio_kpis',      'Executive-level KPIs by country: growth, revenue, risk',   'month,country','MONTHLY'),
('portfolio',     'semantic_risk_metrics',        'Risk KPIs aggregated at portfolio level',                  'date,country', 'DAILY'),
('transactions',  'semantic_transaction_summary', 'Detailed transaction log with enriched context',           'transaction',  'REALTIME'),
('transactions',  'semantic_spend_metrics',       'Aggregated transaction metrics by customer and month',     'month,customer','DAILY');


-- =============================================================================
-- INTENT → DOMAIN MAPPING — NL intent keywords to business domain
-- Used by backend to route chatbot query to the right semantic table(s)
-- =============================================================================

DROP TABLE IF EXISTS intent_domain_mapping;
CREATE TABLE intent_domain_mapping (
    intent_id           INT             NOT NULL,
    intent_keyword      VARCHAR(100)    NOT NULL,   -- lower-case NL phrase fragment
    domain              VARCHAR(30)     NOT NULL,
    secondary_domain    VARCHAR(30),               -- for cross-domain queries
    confidence          DECIMAL(3,2),              -- 0.50 to 1.00
    example_question    VARCHAR(300)
) DUPLICATE KEY(intent_id)
DISTRIBUTED BY HASH(intent_id) BUCKETS 2
PROPERTIES ("replication_num" = "1");

INSERT INTO intent_domain_mapping VALUES
(1,  'fraud',                   'risk',         NULL,           1.00, 'Show fraud transactions this week'),
(2,  'suspicious',              'risk',         NULL,           0.95, 'Show suspicious activity for customer'),
(3,  'decline',                 'risk',         NULL,           0.90, 'What is the decline rate by country?'),
(4,  'risk',                    'risk',         NULL,           0.90, 'Show high-risk customers in SG'),
(5,  'fraud rate',              'risk',         NULL,           1.00, 'What is the fraud rate this month?'),
(6,  'delinquency',             'risk',         'payments',     0.85, 'Show delinquency rate for MY'),
(7,  'alert',                   'risk',         NULL,           0.80, 'How many fraud alerts today?'),
(8,  'spend',                   'spend',        NULL,           1.00, 'How much did I spend last month?'),
(9,  'spending',                'spend',        NULL,           1.00, 'Show my spending by category'),
(10, 'category',                'spend',        NULL,           0.90, 'Show transactions by merchant category'),
(11, 'merchant',                'spend',        'transactions', 0.85, 'What are my top merchants?'),
(12, 'purchase',                'transactions', 'spend',        0.85, 'Show my purchases in April'),
(13, 'transaction',             'transactions', NULL,           1.00, 'Show recent transactions'),
(14, 'transfer',                'transactions', NULL,           0.95, 'Show transfers last week'),
(15, 'balance',                 'customer',     NULL,           1.00, 'What is my current balance?'),
(16, 'credit limit',            'customer',     NULL,           0.95, 'What is my credit limit?'),
(17, 'utilisation',             'customer',     NULL,           0.90, 'What is my credit utilisation?'),
(18, 'utilization',             'customer',     NULL,           0.90, 'What percent of my limit is used?'),
(19, 'account',                 'customer',     NULL,           0.80, 'Show my account details'),
(20, 'due',                     'payments',     NULL,           1.00, 'What is my due amount?'),
(21, 'payment',                 'payments',     NULL,           0.95, 'When is my next payment due?'),
(22, 'overdue',                 'payments',     'risk',         1.00, 'Show overdue accounts in IN'),
(23, 'late fee',                'payments',     NULL,           0.90, 'How much late fee was charged?'),
(24, 'statement',               'payments',     NULL,           0.85, 'Show my latest statement'),
(25, 'revenue',                 'portfolio',    NULL,           0.90, 'What is the estimated revenue for Q3?'),
(26, 'portfolio',               'portfolio',    NULL,           1.00, 'Show portfolio KPIs for IN'),
(27, 'kpi',                     'portfolio',    NULL,           0.95, 'Show key KPIs by country'),
(28, 'growth',                  'portfolio',    NULL,           0.90, 'What is the customer growth rate?'),
(29, 'churn',                   'portfolio',    NULL,           0.90, 'What is the churn rate in MY?'),
(30, 'interest income',         'portfolio',    NULL,           0.95, 'What is estimated interest income?'),
(31, 'how much',                'spend',        'customer',     0.75, 'How much did I spend?'),
(32, 'show me',                 'transactions', NULL,           0.60, 'Show me my recent activity'),
(33, 'compare',                 'portfolio',    'spend',        0.70, 'Compare spend across countries');


-- =============================================================================
-- PERSONA → SEMANTIC TABLE ACCESS CONTROL
-- Backend uses this to determine which tables a persona can query
-- and what country/row filters to apply
-- =============================================================================

DROP TABLE IF EXISTS semantic_access_control;
CREATE TABLE semantic_access_control (
    persona             VARCHAR(30)     NOT NULL,
    semantic_table      VARCHAR(100)    NOT NULL,
    domain              VARCHAR(30)     NOT NULL,
    -- Row-level security
    country_filter      VARCHAR(50),               -- comma-separated: SG,MY or ALL
    -- Column restrictions (for future column-level enforcement)
    restricted_columns  VARCHAR(300),              -- comma-separated columns to mask
    -- Access metadata
    can_export          TINYINT         DEFAULT 1,
    can_drill_down      TINYINT         DEFAULT 1,
    max_row_limit       INT             DEFAULT 10000,
    notes               VARCHAR(200)
) DUPLICATE KEY(persona, semantic_table)
DISTRIBUTED BY HASH(persona) BUCKETS 2
PROPERTIES ("replication_num" = "1");

INSERT INTO semantic_access_control VALUES
-- analyst: full access to risk and transactions domains, SG + MY
('analyst', 'semantic_risk_metrics',        'risk',         'SG,MY',    NULL,               1, 1, 50000, 'Fraud analyst default'),
('analyst', 'semantic_transaction_summary', 'transactions', 'SG,MY',    NULL,               1, 1, 50000, 'Transaction drill-down'),
('analyst', 'semantic_spend_metrics',       'spend',        'SG,MY',    NULL,               1, 1, 50000, 'Spend analysis'),
('analyst', 'semantic_customer_360',        'customer',     'SG,MY',    'annual_income',    1, 1, 10000, 'Customer view, income masked'),
('analyst', 'semantic_payment_status',      'payments',     'SG,MY',    NULL,               1, 1, 10000, 'Payment overdue tracking'),

-- fraud_analyst: risk and transactions only, SG + MY
('fraud_analyst', 'semantic_risk_metrics',        'risk',         'SG,MY',   NULL,  1, 1, 100000, 'Primary fraud monitoring table'),
('fraud_analyst', 'semantic_transaction_summary', 'transactions', 'SG,MY',   NULL,  1, 1, 100000, 'Transaction investigation'),
('fraud_analyst', 'semantic_customer_360',        'customer',     'SG,MY',   'annual_income,income_band', 0, 1, 5000, 'Customer context only'),

-- cfo: portfolio + payments + spend, all countries, no individual customer details
('cfo', 'semantic_portfolio_kpis',  'portfolio',  'ALL',   NULL,  1, 0, 1000,  'Executive portfolio view'),
('cfo', 'semantic_risk_metrics',    'risk',       'ALL',   NULL,  1, 0, 1000,  'Aggregated risk view'),
('cfo', 'semantic_spend_metrics',   'spend',      'ALL',   'customer_id', 1, 0, 1000, 'Aggregated spend, no PII'),
('cfo', 'semantic_payment_status',  'payments',   'ALL',   'customer_id,customer_name', 1, 0, 1000, 'Aggregated payment view'),

-- finance_user: payments and portfolio, all countries
('finance_user', 'semantic_portfolio_kpis', 'portfolio',  'ALL',  NULL,  1, 1, 5000, 'Finance team portfolio view'),
('finance_user', 'semantic_payment_status', 'payments',   'ALL',  NULL,  1, 1, 5000, 'Payment tracking'),
('finance_user', 'semantic_spend_metrics',  'spend',      'ALL',  NULL,  1, 1, 5000, 'Revenue-driving spend'),

-- retail_user (end customer): own data only, spend + customer + payments
('retail_user',  'semantic_customer_360',   'customer',   'OWN',  NULL,  0, 0, 10,  'Own account view only'),
('retail_user',  'semantic_spend_metrics',  'spend',      'OWN',  NULL,  0, 0, 12,  'Own spend history (12 months)'),
('retail_user',  'semantic_payment_status', 'payments',   'OWN',  NULL,  0, 0, 6,   'Own payment status'),

-- end_user (branch/call center): customer + spend + payments, SG only
('end_user', 'semantic_customer_360',   'customer',  'SG',  'annual_income', 1, 1, 100, 'Customer service view'),
('end_user', 'semantic_spend_metrics',  'spend',     'SG',  NULL,           1, 0, 100, 'Spend summary'),
('end_user', 'semantic_payment_status', 'payments',  'SG',  NULL,           1, 1, 100, 'Payment queries'),

-- data_product_owner: all tables, all countries, for data governance
('data_product_owner', 'semantic_risk_metrics',        'risk',         'ALL', NULL, 1, 1, 100000, 'Full access for DPO'),
('data_product_owner', 'semantic_transaction_summary', 'transactions', 'ALL', NULL, 1, 1, 100000, 'Full access for DPO'),
('data_product_owner', 'semantic_spend_metrics',       'spend',        'ALL', NULL, 1, 1, 100000, 'Full access for DPO'),
('data_product_owner', 'semantic_customer_360',        'customer',     'ALL', NULL, 1, 1, 100000, 'Full access for DPO'),
('data_product_owner', 'semantic_payment_status',      'payments',     'ALL', NULL, 1, 1, 100000, 'Full access for DPO'),
('data_product_owner', 'semantic_portfolio_kpis',      'portfolio',    'ALL', NULL, 1, 1, 100000, 'Full access for DPO'),

-- developer: all tables, all countries, for platform development
('developer', 'semantic_risk_metrics',        'risk',         'ALL', NULL, 1, 1, 100000, 'Dev access'),
('developer', 'semantic_transaction_summary', 'transactions', 'ALL', NULL, 1, 1, 100000, 'Dev access'),
('developer', 'semantic_spend_metrics',       'spend',        'ALL', NULL, 1, 1, 100000, 'Dev access'),
('developer', 'semantic_customer_360',        'customer',     'ALL', NULL, 1, 1, 100000, 'Dev access'),
('developer', 'semantic_payment_status',      'payments',     'ALL', NULL, 1, 1, 100000, 'Dev access'),
('developer', 'semantic_portfolio_kpis',      'portfolio',    'ALL', NULL, 1, 1, 100000, 'Dev access'),

-- architect: all tables, all countries, for schema/platform work
('architect', 'semantic_risk_metrics',        'risk',         'ALL', NULL, 1, 1, 100000, 'Architect access'),
('architect', 'semantic_transaction_summary', 'transactions', 'ALL', NULL, 1, 1, 100000, 'Architect access'),
('architect', 'semantic_spend_metrics',       'spend',        'ALL', NULL, 1, 1, 100000, 'Architect access'),
('architect', 'semantic_customer_360',        'customer',     'ALL', NULL, 1, 1, 100000, 'Architect access'),
('architect', 'semantic_payment_status',      'payments',     'ALL', NULL, 1, 1, 100000, 'Architect access'),
('architect', 'semantic_portfolio_kpis',      'portfolio',    'ALL', NULL, 1, 1, 100000, 'Architect access'),

-- admin: all tables, all countries
('admin', 'semantic_risk_metrics',        'risk',         'ALL', NULL, 1, 1, 1000000, 'Admin full access'),
('admin', 'semantic_transaction_summary', 'transactions', 'ALL', NULL, 1, 1, 1000000, 'Admin full access'),
('admin', 'semantic_spend_metrics',       'spend',        'ALL', NULL, 1, 1, 1000000, 'Admin full access'),
('admin', 'semantic_customer_360',        'customer',     'ALL', NULL, 1, 1, 1000000, 'Admin full access'),
('admin', 'semantic_payment_status',      'payments',     'ALL', NULL, 1, 1, 1000000, 'Admin full access'),
('admin', 'semantic_portfolio_kpis',      'portfolio',    'ALL', NULL, 1, 1, 1000000, 'Admin full access');


-- =============================================================================
-- USER DOMAIN MAPPING — user-level domain access (future: DB-backend auth)
-- =============================================================================

DROP TABLE IF EXISTS user_domain_mapping;
CREATE TABLE user_domain_mapping (
    user_id             VARCHAR(20)     NOT NULL,
    email               VARCHAR(100)    NOT NULL,
    role                VARCHAR(30)     NOT NULL,
    persona             VARCHAR(30),
    country_code        VARCHAR(2)      NOT NULL,
    legal_entity        VARCHAR(10),
    domain              VARCHAR(30)     NOT NULL,
    access_level        VARCHAR(20),               -- READ | READ_EXPORT | ADMIN
    granted_at          DATETIME,
    granted_by          VARCHAR(50),
    expires_at          DATETIME                   -- NULL = no expiry
) DUPLICATE KEY(user_id, country_code, domain)
DISTRIBUTED BY HASH(user_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

INSERT INTO user_domain_mapping VALUES
-- admin: all
('u1','admin@dataprismai.io','admin','analyst','SG','SG_BANK','risk','ADMIN','2025-01-01 00:00:00','system',NULL),
('u1','admin@dataprismai.io','admin','analyst','SG','SG_BANK','spend','ADMIN','2025-01-01 00:00:00','system',NULL),
('u1','admin@dataprismai.io','admin','analyst','SG','SG_BANK','customer','ADMIN','2025-01-01 00:00:00','system',NULL),
('u1','admin@dataprismai.io','admin','analyst','SG','SG_BANK','payments','ADMIN','2025-01-01 00:00:00','system',NULL),
('u1','admin@dataprismai.io','admin','analyst','SG','SG_BANK','portfolio','ADMIN','2025-01-01 00:00:00','system',NULL),
('u1','admin@dataprismai.io','admin','analyst','SG','SG_BANK','transactions','ADMIN','2025-01-01 00:00:00','system',NULL),
-- sarah (analyst/fraud): SG + MY, risk + transactions
('u2','sarah@dataprismai.io','analyst','analyst','SG','SG_BANK','risk','READ_EXPORT','2025-01-01 00:00:00','u1',NULL),
('u2','sarah@dataprismai.io','analyst','analyst','SG','SG_BANK','transactions','READ','2025-01-01 00:00:00','u1',NULL),
('u2','sarah@dataprismai.io','analyst','analyst','MY','MY_BANK','risk','READ_EXPORT','2025-01-01 00:00:00','u1',NULL),
('u2','sarah@dataprismai.io','analyst','analyst','MY','MY_BANK','transactions','READ','2025-01-01 00:00:00','u1',NULL),
-- priya (cfo): all countries, portfolio + payments + spend
('u4','priya@dataprismai.io','cfo','cfo','SG','SG_BANK','portfolio','READ_EXPORT','2025-01-01 00:00:00','u1',NULL),
('u4','priya@dataprismai.io','cfo','cfo','SG','SG_BANK','payments','READ_EXPORT','2025-01-01 00:00:00','u1',NULL),
('u4','priya@dataprismai.io','cfo','cfo','SG','SG_BANK','spend','READ_EXPORT','2025-01-01 00:00:00','u1',NULL),
('u4','priya@dataprismai.io','cfo','cfo','MY','MY_BANK','portfolio','READ_EXPORT','2025-01-01 00:00:00','u1',NULL),
('u4','priya@dataprismai.io','cfo','cfo','IN','IN_BANK','portfolio','READ_EXPORT','2025-01-01 00:00:00','u1',NULL),
-- mark (end_user): SG only, spend + customer
('u7','mark@dataprismai.io','end_user','end_user','SG','SG_BANK','spend','READ','2025-01-01 00:00:00','u1',NULL),
('u7','mark@dataprismai.io','end_user','end_user','SG','SG_BANK','customer','READ','2025-01-01 00:00:00','u1',NULL);


-- =============================================================================
-- SEMANTIC METRIC MAPPING — metric name → semantic table + filter column
-- =============================================================================

DROP TABLE IF EXISTS semantic_metric_mapping;
CREATE TABLE semantic_metric_mapping (
    metric_name         VARCHAR(100)    NOT NULL,
    semantic_table      VARCHAR(100)    NOT NULL,
    value_column        VARCHAR(100),              -- the column with the metric value
    filter_column       VARCHAR(100),              -- e.g. year_month, metric_date
    group_by_columns    VARCHAR(200),              -- suggested GROUP BY columns
    where_conditions    VARCHAR(300),              -- default WHERE clauses
    allowed_personas    VARCHAR(200)
) DUPLICATE KEY(metric_name, semantic_table)
DISTRIBUTED BY HASH(metric_name) BUCKETS 2
PROPERTIES ("replication_num" = "1");

INSERT INTO semantic_metric_mapping VALUES
('fraud_rate',          'semantic_risk_metrics',        'fraud_rate',           'metric_date',  'country_code,merchant_category',  'metric_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)', 'analyst,fraud_analyst,cfo,admin'),
('decline_rate',        'semantic_risk_metrics',        'decline_rate',         'metric_date',  'country_code,channel',            'metric_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)', 'analyst,fraud_analyst'),
('total_spend',         'semantic_spend_metrics',       'total_spend',          'year_month',   'customer_id,country_code',        NULL,                                              'analyst,cfo,end_user'),
('spending_by_category','semantic_spend_metrics',       'food_dining_spend,shopping_retail_spend,travel_transport_spend', 'year_month', 'customer_id', NULL, 'analyst,cfo,end_user'),
('balance',             'semantic_customer_360',        'current_balance',      NULL,           'customer_id,country_code',        NULL,                                              'end_user,retail_user,analyst'),
('credit_utilisation',  'semantic_customer_360',        'utilization_pct',      NULL,           'customer_id,country_code',        NULL,                                              'end_user,analyst'),
('total_due',           'semantic_payment_status',      'total_due',            'due_date',     'customer_id,country_code',        'payment_status != \'PAID\'',                     'end_user,retail_user,analyst'),
('overdue_accounts',    'semantic_payment_status',      'amount_still_owed',    'as_of_date',   'country_code,overdue_bucket',     'payment_status = \'OVERDUE\'',                    'analyst,cfo,fraud_analyst'),
('portfolio_kpis',      'semantic_portfolio_kpis',      '*',                    'kpi_month',    'country_code,legal_entity',       NULL,                                              'cfo,finance_user,data_product_owner'),
('suspicious_transactions', 'semantic_transaction_summary', 'COUNT(*)',         'transaction_date', 'country_code,merchant_category', 'is_suspicious = 1',                         'analyst,fraud_analyst');


-- =============================================================================
-- DOMAIN GRAIN MAPPING — default aggregation grain per domain
-- =============================================================================

DROP TABLE IF EXISTS domain_grain_mapping;
CREATE TABLE domain_grain_mapping (
    domain              VARCHAR(30)     NOT NULL,
    default_grain       VARCHAR(30)     NOT NULL,   -- DAILY | MONTHLY | CUSTOMER | TRANSACTION
    default_period      VARCHAR(20),               -- LAST_30_DAYS | CURRENT_MONTH | LAST_MONTH | YTD
    time_column         VARCHAR(100),              -- the date column to use for filtering
    id_column           VARCHAR(50),               -- the primary entity ID column
    notes               VARCHAR(200)
) DUPLICATE KEY(domain, default_grain)
DISTRIBUTED BY HASH(domain) BUCKETS 2
PROPERTIES ("replication_num" = "1");

INSERT INTO domain_grain_mapping VALUES
('risk',         'DAILY',       'LAST_30_DAYS',  'metric_date',       'country_code', 'Risk metrics are daily aggregations'),
('spend',        'MONTHLY',     'LAST_MONTH',    'year_month',        'customer_id',  'Spend is pre-aggregated monthly'),
('customer',     'CUSTOMER',    'AS_OF_TODAY',   'as_of_date',        'customer_id',  'Customer 360 is a current snapshot'),
('payments',     'CUSTOMER',    'CURRENT_CYCLE', 'as_of_date',        'customer_id',  'Payment status is current cycle'),
('portfolio',    'MONTHLY',     'CURRENT_MONTH', 'kpi_month',         'country_code', 'Portfolio KPIs are monthly'),
('transactions', 'TRANSACTION', 'LAST_30_DAYS',  'transaction_date',  'transaction_id','Individual transaction grain');
