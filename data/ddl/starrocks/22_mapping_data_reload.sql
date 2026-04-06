-- =============================================================================
-- 22_mapping_data_reload.sql
-- Truncate and reload all chatbot routing / access-control mapping tables
-- with business-valid data aligned to the banking analytics semantic layer.
-- =============================================================================

USE cc_analytics;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. domain_semantic_mapping
--    Tells the chatbot which semantic tables belong to each domain.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE domain_semantic_mapping;

INSERT INTO domain_semantic_mapping (domain, semantic_table, priority, description) VALUES
('customer',     'semantic_customer_360',         1, 'Primary customer 360 snapshot with balances, limits, payment and risk indicators'),
('transactions', 'semantic_transaction_summary',  1, 'Transaction-level summary for search, drilldown, approval and decline analysis'),
('spend',        'semantic_spend_metrics',        1, 'Customer spend metrics by day, month, category and country'),
('payments',     'semantic_payment_status',       1, 'Payment due, minimum due, billed amount and payment completion status'),
('risk',         'semantic_risk_metrics',         1, 'Fraud, suspicious activity, declines and risk monitoring metrics'),
('portfolio',    'semantic_portfolio_kpis',       1, 'Finance and portfolio KPIs by country, product and reporting period'),
('customer',     'semantic_payment_status',       2, 'Secondary source for customer billing and due amount context'),
('risk',         'semantic_transaction_summary',  2, 'Secondary source for transaction-level risk investigation'),
('portfolio',    'semantic_customer_360',         2, 'Secondary source for customer-level portfolio and exposure analysis');

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. user_domain_mapping
--    Maps users (by user_id) to domains they are authorised to access,
--    with country scope and access level.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE user_domain_mapping;

INSERT INTO user_domain_mapping (user_id, domain, country_code, access_level, granted_by, granted_at) VALUES
-- u1 = Acs Admin — full access all domains all countries
('u1', 'customer',     'ALL', 'admin', 'system', '2024-01-01 00:00:00'),
('u1', 'transactions', 'ALL', 'admin', 'system', '2024-01-01 00:00:00'),
('u1', 'spend',        'ALL', 'admin', 'system', '2024-01-01 00:00:00'),
('u1', 'payments',     'ALL', 'admin', 'system', '2024-01-01 00:00:00'),
('u1', 'risk',         'ALL', 'admin', 'system', '2024-01-01 00:00:00'),
('u1', 'portfolio',    'ALL', 'admin', 'system', '2024-01-01 00:00:00'),
-- u2 = Sarah Lee — analyst, SG scope, customer/transactions/spend/risk
('u2', 'customer',     'SG',  'read',  'u1',     '2024-01-15 08:00:00'),
('u2', 'transactions', 'SG',  'read',  'u1',     '2024-01-15 08:00:00'),
('u2', 'spend',        'SG',  'read',  'u1',     '2024-01-15 08:00:00'),
('u2', 'risk',         'SG',  'read',  'u1',     '2024-01-15 08:00:00'),
-- u3 = David Chen — developer, all countries, read for customer/transactions
('u3', 'customer',     'ALL', 'read',  'u1',     '2024-01-15 08:00:00'),
('u3', 'transactions', 'ALL', 'read',  'u1',     '2024-01-15 08:00:00'),
('u3', 'spend',        'ALL', 'read',  'u1',     '2024-01-15 08:00:00'),
-- u4 = Priya Kapoor — CFO, all countries, portfolio/spend/customer
('u4', 'portfolio',    'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
('u4', 'spend',        'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
('u4', 'customer',     'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
-- u5 = James Okafor — data product owner, full domain access, all countries
('u5', 'customer',     'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
('u5', 'transactions', 'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
('u5', 'spend',        'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
('u5', 'payments',     'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
('u5', 'risk',         'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
('u5', 'portfolio',    'ALL', 'read',  'u1',     '2024-02-01 09:00:00'),
-- u6 = Elena Sousa — architect, all countries, read all
('u6', 'customer',     'ALL', 'read',  'u1',     '2024-01-15 08:00:00'),
('u6', 'transactions', 'ALL', 'read',  'u1',     '2024-01-15 08:00:00'),
('u6', 'spend',        'ALL', 'read',  'u1',     '2024-01-15 08:00:00'),
('u6', 'portfolio',    'ALL', 'read',  'u1',     '2024-01-15 08:00:00'),
-- u7 = Mark Williams — end user, MY scope, retail domains
('u7', 'customer',     'MY',  'read',  'u1',     '2024-03-01 09:00:00'),
('u7', 'transactions', 'MY',  'read',  'u1',     '2024-03-01 09:00:00'),
('u7', 'spend',        'MY',  'read',  'u1',     '2024-03-01 09:00:00'),
('u7', 'payments',     'MY',  'read',  'u1',     '2024-03-01 09:00:00');

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. intent_domain_mapping
--    Maps user natural-language keywords to a routing domain.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE intent_domain_mapping;

INSERT INTO intent_domain_mapping (keyword, domain, weight, example_question) VALUES
('customer',      'customer',     10, 'Show me customers with high credit utilization'),
('balance',       'customer',     10, 'What is the current balance for account ACC001?'),
('credit limit',  'customer',      9, 'Which customers have credit limits above 10000?'),
('utilization',   'customer',      9, 'Show credit utilization ratio by customer segment'),
('profile',       'customer',      8, 'Give me a 360 view of customer CUST_000001'),
('account',       'customer',      7, 'List all active accounts in Singapore'),
('available',     'customer',      6, 'How much available credit does customer CUST_000001 have?'),
('segment',       'customer',      6, 'How many customers are in the premium segment?'),
('transaction',   'transactions', 10, 'Show all transactions from the last 7 days'),
('merchant',      'transactions',  8, 'Which merchants have the highest transaction volume this month?'),
('approved',      'transactions',  7, 'How many transactions were approved last week?'),
('declined',      'transactions',  7, 'Show declined transactions in Singapore for last 30 days'),
('refund',        'transactions',  6, 'List refunded transactions in Q1 2025'),
('spend',         'spend',        10, 'What is total spend by merchant category this month?'),
('usage',         'spend',         8, 'Show card usage trends for Malaysian customers'),
('category',      'spend',         7, 'Break down spend by merchant category for last quarter'),
('international', 'spend',         7, 'Show international spend for Singapore customers this year'),
('average',       'spend',         6, 'What is the average transaction size per customer in India?'),
('payment',       'payments',     10, 'Which accounts have overdue payments this month?'),
('due',           'payments',      9, 'What payments are due in the next 7 days?'),
('bill',          'payments',      8, 'Show billed amount for account ACC001 last statement'),
('overdue',       'payments',      9, 'List accounts with more than 30 days past due'),
('minimum',       'payments',      7, 'Which customers have only paid the minimum due amount?'),
('statement',     'payments',      6, 'Show statement history for customer CUST_000001'),
('fraud',         'risk',         10, 'Show suspicious transactions in the last 30 days'),
('suspicious',    'risk',          9, 'Flag suspicious transactions in Malaysia last 7 days'),
('decline rate',  'risk',          9, 'What is the transaction decline rate by country this week?'),
('risk',          'risk',          9, 'Which accounts have the highest fraud score today?'),
('anomaly',       'risk',          7, 'Are there anomalies in transaction patterns this week?'),
('flagged',       'risk',          8, 'Show all flagged accounts for SG region'),
('portfolio',     'portfolio',    10, 'Give me portfolio KPIs for Singapore in Q1 2025'),
('revenue',       'portfolio',     9, 'What is total revenue by country for this quarter?'),
('kpi',           'portfolio',     9, 'Show active customer count and outstanding balance by country'),
('outstanding',   'portfolio',     8, 'What is total outstanding balance across all countries?'),
('active',        'portfolio',     6, 'How many active customers do we have in India?'),
('loss',          'portfolio',     7, 'Show net credit loss for Malaysia year to date');

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. domain_grain_mapping
--    Defines the default query grain and time scope per domain.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE domain_grain_mapping;

INSERT INTO domain_grain_mapping (domain, default_grain, default_lookback, date_column, description) VALUES
('customer',     'customer_account_snapshot', '1_day',     'snapshot_date',     'One row per customer-account snapshot, representing current state'),
('transactions', 'transaction',               '7_days',    'transaction_date',  'One row per transaction event, supports drilldown and search'),
('spend',        'customer_month',            '3_months',  'reporting_month',   'One row per customer per reporting month with aggregated spend'),
('payments',     'account_billing_cycle',     '3_months',  'statement_date',    'One row per account per billing cycle with due and paid amounts'),
('risk',         'account_day',               '30_days',   'risk_date',         'Risk monitoring at account-day granularity, refreshed daily'),
('portfolio',    'country_month',             '12_months', 'reporting_month',   'Portfolio KPIs aggregated by country and product per reporting month');

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. semantic_metric_mapping
--    Maps metric names to semantic tables with column-level routing metadata.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE semantic_metric_mapping;

INSERT INTO semantic_metric_mapping (metric_name, semantic_table, value_column, filter_column, group_by_column, aggregation) VALUES
('current_balance',       'semantic_customer_360',        'current_balance',          'country_code',      'customer_id',       'latest'),
('available_credit',      'semantic_customer_360',        'available_credit',         'country_code',      'customer_id',       'latest'),
('credit_limit',          'semantic_customer_360',        'credit_limit',             'country_code',      'segment',           'avg'),
('utilization_ratio',     'semantic_customer_360',        'utilization_ratio',        'country_code',      'segment',           'avg'),
('total_spend',           'semantic_spend_metrics',       'total_spend',              'reporting_month',   'merchant_category', 'sum'),
('avg_ticket_size',       'semantic_spend_metrics',       'avg_ticket_size',          'reporting_month',   'customer_id',       'avg'),
('international_spend',   'semantic_spend_metrics',       'international_spend_pct',  'reporting_month',   'country_code',      'avg'),
('spend_transaction_count','semantic_spend_metrics',      'transaction_count',        'reporting_month',   'country_code',      'sum'),
('transaction_amount',    'semantic_transaction_summary', 'transaction_amount',       'transaction_date',  'merchant_category', 'sum'),
('transaction_count',     'semantic_transaction_summary', 'transaction_id',           'transaction_date',  'transaction_status','count'),
('approved_count',        'semantic_transaction_summary', 'transaction_id',           'transaction_status','country_code',      'count'),
('declined_count',        'semantic_transaction_summary', 'transaction_id',           'transaction_status','country_code',      'count'),
('payment_due_amount',    'semantic_payment_status',      'payment_due_amount',       'statement_date',    'account_id',        'sum'),
('minimum_due',           'semantic_payment_status',      'minimum_due',              'due_date',          'country_code',      'sum'),
('days_past_due',         'semantic_payment_status',      'days_past_due',            'due_date',          'country_code',      'max'),
('paid_amount',           'semantic_payment_status',      'paid_amount',              'statement_date',    'country_code',      'sum'),
('fraud_score',           'semantic_risk_metrics',        'fraud_score',              'risk_date',         'country_code',      'avg'),
('decline_rate',          'semantic_risk_metrics',        'decline_rate',             'risk_date',         'country_code',      'avg'),
('suspicious_txn_count',  'semantic_risk_metrics',        'suspicious_txn_count',     'risk_date',         'country_code',      'sum'),
('total_outstanding',     'semantic_portfolio_kpis',      'total_outstanding',        'reporting_month',   'country_code',      'sum'),
('active_customers',      'semantic_portfolio_kpis',      'active_customers',         'reporting_month',   'country_code',      'sum'),
('active_accounts',       'semantic_portfolio_kpis',      'active_accounts',          'reporting_month',   'country_code',      'sum'),
('net_credit_loss',       'semantic_portfolio_kpis',      'net_credit_loss',          'reporting_month',   'country_code',      'sum'),
('total_revenue',         'semantic_portfolio_kpis',      'total_revenue',            'reporting_month',   'country_code',      'sum');

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. semantic_dimension_mapping
--    Maps dimension names to their source table, column, and display metadata.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE semantic_dimension_mapping;

INSERT INTO semantic_dimension_mapping (dimension_name, source_table, source_column, display_label, dimension_type, is_filterable, is_groupable) VALUES
-- Customer 360 dimensions
('customer_id',          'semantic_customer_360',        'customer_id',         'Customer ID',               'key',         1, 1),
('account_id',           'semantic_customer_360',        'account_id',          'Account ID',                'key',         1, 0),
('customer_country',     'semantic_customer_360',        'country_code',        'Customer Country',          'categorical', 1, 1),
('customer_segment',     'semantic_customer_360',        'segment',             'Customer Segment',          'categorical', 1, 1),
('snapshot_date',        'semantic_customer_360',        'snapshot_date',       'Snapshot Date',             'date',        1, 1),
('risk_band',            'semantic_customer_360',        'customer_risk_band',  'Risk Band',                 'categorical', 1, 1),
-- Transaction dimensions
('transaction_id',       'semantic_transaction_summary', 'transaction_id',      'Transaction ID',            'key',         1, 0),
('transaction_date',     'semantic_transaction_summary', 'transaction_date',    'Transaction Date',          'date',        1, 1),
('merchant_name',        'semantic_transaction_summary', 'merchant_name',       'Merchant',                  'categorical', 1, 1),
('merchant_category',    'semantic_transaction_summary', 'merchant_category',   'Merchant Category',         'categorical', 1, 1),
('transaction_status',   'semantic_transaction_summary', 'transaction_status',  'Transaction Status',        'categorical', 1, 1),
('transaction_type',     'semantic_transaction_summary', 'transaction_type',    'Transaction Type',          'categorical', 1, 1),
('transaction_country',  'semantic_transaction_summary', 'country_code',        'Transaction Country',       'categorical', 1, 1),
-- Spend dimensions
('reporting_month',      'semantic_spend_metrics',       'reporting_month',     'Reporting Month',           'date',        1, 1),
('spend_country',        'semantic_spend_metrics',       'country_code',        'Spend Country',             'categorical', 1, 1),
('spend_category',       'semantic_spend_metrics',       'merchant_category',   'Spend Category',            'categorical', 1, 1),
-- Payment dimensions
('statement_date',       'semantic_payment_status',      'statement_date',      'Statement Date',            'date',        1, 1),
('due_date',             'semantic_payment_status',      'due_date',            'Payment Due Date',          'date',        1, 0),
('payment_status',       'semantic_payment_status',      'payment_status',      'Payment Status',            'categorical', 1, 1),
('payment_country',      'semantic_payment_status',      'country_code',        'Payment Country',           'categorical', 1, 1),
-- Risk dimensions
('risk_date',            'semantic_risk_metrics',        'risk_date',           'Risk Date',                 'date',        1, 1),
('is_suspicious',        'semantic_risk_metrics',        'is_suspicious',       'Suspicious Flag',           'boolean',     1, 1),
('risk_country',         'semantic_risk_metrics',        'country_code',        'Risk Country',              'categorical', 1, 1),
-- Portfolio dimensions
('portfolio_country',    'semantic_portfolio_kpis',      'country_code',        'Portfolio Country',         'categorical', 1, 1),
('portfolio_month',      'semantic_portfolio_kpis',      'reporting_month',     'Portfolio Reporting Month', 'date',        1, 1),
('product_type',         'semantic_portfolio_kpis',      'product_type',        'Product Type',              'categorical', 1, 1);

-- ─────────────────────────────────────────────────────────────────────────────
-- 7. semantic_access_control
--    Defines per-persona access rules for each semantic table.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE semantic_access_control;

INSERT INTO semantic_access_control (persona, semantic_table, can_access, country_filter, restricted_columns, max_row_limit, description) VALUES
-- fraud_analyst: risk + transactions + customer lookup only
('fraud_analyst', 'semantic_risk_metrics',        1, 'user_country_scope', 'none',                              5000,  'Full risk metrics read within analyst country scope'),
('fraud_analyst', 'semantic_transaction_summary', 1, 'user_country_scope', 'national_id,email,phone',           10000, 'Transaction access with PII columns masked'),
('fraud_analyst', 'semantic_customer_360',        1, 'user_country_scope', 'national_id,email,phone',           1000,  'Customer lookup with sensitive PII masked'),
('fraud_analyst', 'semantic_spend_metrics',       0, 'none',               'none',                              0,     'Spend metrics outside fraud analyst scope'),
('fraud_analyst', 'semantic_payment_status',      0, 'none',               'none',                              0,     'Payment status outside fraud analyst scope'),
('fraud_analyst', 'semantic_portfolio_kpis',      0, 'none',               'none',                              0,     'Portfolio KPIs outside fraud analyst scope'),
-- regional_risk_user: risk + transactions + customer + portfolio overview across regions
('regional_risk_user', 'semantic_risk_metrics',        1, 'user_country_scope', 'none',                              10000, 'Full risk metrics read across all assigned regions'),
('regional_risk_user', 'semantic_transaction_summary', 1, 'user_country_scope', 'national_id,email,phone',           20000, 'Transaction access with PII masking across regions'),
('regional_risk_user', 'semantic_customer_360',        1, 'user_country_scope', 'national_id,email,phone',           5000,  'Customer 360 with PII masking, multi-region scope'),
('regional_risk_user', 'semantic_portfolio_kpis',      1, 'user_country_scope', 'none',                              1000,  'Portfolio KPI overview for regional reporting'),
('regional_risk_user', 'semantic_spend_metrics',       0, 'none',               'none',                              0,     'Spend metrics outside regional risk scope'),
('regional_risk_user', 'semantic_payment_status',      0, 'none',               'none',                              0,     'Payment data outside regional risk scope'),
-- retail_user: customer + transactions + spend + payments for own country
('retail_user', 'semantic_customer_360',        1, 'user_country_scope', 'national_id',                          500,   'Customer view scoped to own country, national_id masked'),
('retail_user', 'semantic_transaction_summary', 1, 'user_country_scope', 'national_id,email,phone',              5000,  'Transaction access for own country with PII masking'),
('retail_user', 'semantic_spend_metrics',       1, 'user_country_scope', 'none',                                 2000,  'Spend metrics for own country, standard access'),
('retail_user', 'semantic_payment_status',      1, 'user_country_scope', 'none',                                 2000,  'Payment status for own country, standard access'),
('retail_user', 'semantic_risk_metrics',        0, 'none',               'none',                                 0,     'Risk and fraud data restricted from retail staff'),
('retail_user', 'semantic_portfolio_kpis',      0, 'none',               'none',                                 0,     'Portfolio KPIs restricted from retail staff'),
-- finance_user: portfolio + spend aggregates + customer summary
('finance_user', 'semantic_portfolio_kpis',      1, 'user_country_scope', 'none',                                1000,  'Portfolio KPIs for finance reporting, own country'),
('finance_user', 'semantic_spend_metrics',       1, 'user_country_scope', 'customer_id,account_id',              5000,  'Spend aggregates, individual identifiers masked'),
('finance_user', 'semantic_customer_360',        1, 'user_country_scope', 'national_id,email,phone,account_id',  1000,  'Customer aggregated view only, all PII masked'),
('finance_user', 'semantic_risk_metrics',        0, 'none',               'none',                                0,     'Risk data restricted from finance users'),
('finance_user', 'semantic_transaction_summary', 0, 'none',               'none',                                0,     'Transaction detail restricted from finance users'),
('finance_user', 'semantic_payment_status',      0, 'none',               'none',                                0,     'Payment detail restricted from finance users'),
-- regional_finance_user: portfolio + spend aggregates across all regions
('regional_finance_user', 'semantic_portfolio_kpis',      1, 'user_country_scope', 'none',                              5000,  'Full portfolio KPI access across all assigned regions'),
('regional_finance_user', 'semantic_spend_metrics',       1, 'user_country_scope', 'customer_id,account_id',            10000, 'Regional spend aggregates, individual identifiers masked'),
('regional_finance_user', 'semantic_customer_360',        1, 'user_country_scope', 'national_id,email,phone',            2000,  'Customer 360 aggregated view across regions'),
('regional_finance_user', 'semantic_risk_metrics',        0, 'none',               'none',                              0,     'Risk data outside regional finance scope'),
('regional_finance_user', 'semantic_transaction_summary', 0, 'none',               'none',                              0,     'Transaction detail outside regional finance scope'),
('regional_finance_user', 'semantic_payment_status',      0, 'none',               'none',                              0,     'Payment status outside regional finance scope');

-- ─────────────────────────────────────────────────────────────────────────────
-- 8. semantic_glossary_metrics
--    Business glossary — grounding definitions used by the chatbot response layer.
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE semantic_glossary_metrics;

INSERT INTO semantic_glossary_metrics (metric_id, metric_name, display_name, definition, formula, grain, source_table, source_columns, domain, category, is_active) VALUES
('met_001', 'total_spend',          'Total Spend',
  'Total value of approved purchase transactions excluding refunds and reversals',
  'SUM(transaction_amount) WHERE transaction_status = approved',
  'customer_month', 'semantic_spend_metrics', 'total_spend', 'spend', 'volume', 1),

('met_002', 'current_balance',      'Current Balance',
  'Outstanding balance on the customer account as of the latest snapshot date',
  'latest(current_balance)',
  'customer_account_snapshot', 'semantic_customer_360', 'current_balance', 'customer', 'exposure', 1),

('met_003', 'available_credit',     'Available Credit',
  'Remaining available credit calculated as credit limit minus outstanding balance',
  'credit_limit - current_balance',
  'customer_account_snapshot', 'semantic_customer_360', 'credit_limit,current_balance', 'customer', 'exposure', 1),

('met_004', 'utilization_ratio',    'Credit Utilization',
  'Percentage of the assigned credit limit currently in use',
  'current_balance / credit_limit',
  'customer_account_snapshot', 'semantic_customer_360', 'current_balance,credit_limit', 'customer', 'behavior', 1),

('met_005', 'payment_due_amount',   'Payment Due',
  'Total amount due for the current active billing cycle',
  'SUM(payment_due_amount)',
  'account_billing_cycle', 'semantic_payment_status', 'payment_due_amount', 'payments', 'debt', 1),

('met_006', 'minimum_due',          'Minimum Payment Due',
  'Minimum contractual payment required to keep the account in good standing',
  'MIN(minimum_due)',
  'account_billing_cycle', 'semantic_payment_status', 'minimum_due', 'payments', 'debt', 1),

('met_007', 'days_past_due',        'Days Past Due',
  'Number of calendar days a payment has remained overdue from the statement due date',
  'DATEDIFF(CURRENT_DATE, due_date) WHERE paid_amount < minimum_due',
  'account_billing_cycle', 'semantic_payment_status', 'days_past_due,due_date', 'payments', 'risk', 1),

('met_008', 'fraud_score',          'Fraud Score',
  'Model-driven score estimating the probability of fraudulent activity on the account',
  'MODEL_SCORE(fraud_model, account_features)',
  'account_day', 'semantic_risk_metrics', 'fraud_score', 'risk', 'fraud', 1),

('met_009', 'decline_rate',         'Transaction Decline Rate',
  'Ratio of declined transactions to total attempted transactions in the period',
  'declined_count / attempted_count',
  'account_day', 'semantic_risk_metrics', 'decline_rate,declined_count', 'risk', 'performance', 1),

('met_010', 'suspicious_txn_count', 'Suspicious Transactions',
  'Count of transactions flagged as suspicious by rule-based or model thresholds',
  'COUNT(transaction_id) WHERE is_suspicious = 1',
  'account_day', 'semantic_risk_metrics', 'suspicious_txn_count', 'risk', 'fraud', 1),

('met_011', 'transaction_count',    'Transaction Count',
  'Total count of transactions within the selected scope and time filter',
  'COUNT(transaction_id)',
  'transaction', 'semantic_transaction_summary', 'transaction_id', 'transactions', 'volume', 1),

('met_012', 'avg_ticket_size',      'Average Transaction Value',
  'Average value of approved purchase transactions per card or customer',
  'SUM(transaction_amount) / COUNT(transaction_id)',
  'customer_month', 'semantic_spend_metrics', 'avg_ticket_size,total_spend', 'spend', 'behavior', 1),

('met_013', 'total_outstanding',    'Total Outstanding Balance',
  'Aggregated outstanding credit card balance across the filtered portfolio scope',
  'SUM(total_outstanding)',
  'country_month', 'semantic_portfolio_kpis', 'total_outstanding', 'portfolio', 'exposure', 1),

('met_014', 'active_customers',     'Active Customers',
  'Count of customers with at least one approved transaction in the reporting period',
  'COUNT(DISTINCT customer_id) WHERE is_active = 1',
  'country_month', 'semantic_portfolio_kpis', 'active_customers', 'portfolio', 'volume', 1),

('met_015', 'active_accounts',      'Active Accounts',
  'Count of accounts with at least one approved transaction in the reporting period',
  'COUNT(DISTINCT account_id) WHERE is_active = 1',
  'country_month', 'semantic_portfolio_kpis', 'active_accounts', 'portfolio', 'volume', 1),

('met_016', 'international_spend',  'International Spend',
  'Spend where the merchant country code differs from the customer home country',
  'SUM(transaction_amount) WHERE merchant_country != customer_country_code',
  'customer_month', 'semantic_spend_metrics', 'international_spend_pct', 'spend', 'behavior', 1),

('met_017', 'net_credit_loss',      'Net Credit Loss',
  'Total credit loss after recoveries in the reporting period, used for provisioning and P&L',
  'SUM(write_off_amount) - SUM(recovery_amount)',
  'country_month', 'semantic_portfolio_kpis', 'net_credit_loss', 'portfolio', 'risk', 1),

('met_018', 'revenue_per_customer', 'Revenue Per Customer',
  'Average revenue generated per active customer in the portfolio reporting period',
  'total_revenue / active_customers',
  'country_month', 'semantic_portfolio_kpis', 'total_revenue,active_customers', 'portfolio', 'profitability', 1),

('met_019', 'category_spend_share', 'Category Spend Share',
  'Proportion of total spend attributed to a specific merchant category',
  'category_spend / total_spend',
  'customer_month', 'semantic_spend_metrics', 'total_spend,merchant_category', 'spend', 'behavior', 1);
