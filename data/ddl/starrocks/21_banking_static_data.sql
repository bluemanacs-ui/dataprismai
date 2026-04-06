-- =============================================================================
-- DataPrismAI Banking Platform — Static Reference Data
-- File: 21_banking_static_data.sql
-- Purpose: Seed INSERT data for all mapping/routing tables
-- =============================================================================

USE cc_analytics;

-- =============================================================================
-- semantic_glossary_metrics
-- =============================================================================
INSERT INTO semantic_glossary_metrics VALUES
('total_spend',      'Total Spend',          'Total Spend',              'Sum of all purchase transactions in the period.',                                      'SUM(amount) WHERE transaction_type=PURCHASE AND auth_status=APPROVED',                           'MONTHLY',   'semantic_spend_metrics',      'total_spend',           'spend',      'SPEND',     1),
('current_balance',  'Current Balance',      'Current Account Balance',  'Outstanding balance owed on the credit account as of today.',                          'closing_balance from latest statement',                                                          'SNAPSHOT',  'semantic_customer_360',       'current_balance',       'customer',   'BALANCE',   1),
('available_credit', 'Available Credit',     'Available Credit',         'Credit limit minus current outstanding balance.',                                       'credit_limit - current_balance',                                                                 'SNAPSHOT',  'semantic_customer_360',       'available_balance',     'customer',   'BALANCE',   1),
('utilization_rate', 'Credit Utilization',   'Credit Utilization Rate',  'Percentage of credit limit currently used.',                                           'current_balance / credit_limit',                                                                 'SNAPSHOT',  'semantic_customer_360',       'utilization_pct',       'customer',   'BALANCE',   1),
('payment_due',      'Payment Due',          'Total Due Amount',         'Total amount due at next statement due date.',                                          'total_due from semantic_payment_status WHERE payment_status != PAID',                             'SNAPSHOT',  'semantic_payment_status',     'total_due',             'payments',   'PAYMENT',   1),
('minimum_due',      'Minimum Due',          'Minimum Payment Due',      'Minimum payment required to avoid late fee and maintain account in good standing.',     'minimum_due from latest statement',                                                              'SNAPSHOT',  'semantic_payment_status',     'minimum_due',           'payments',   'PAYMENT',   1),
('overdue_days',     'Overdue Days',         'Days Past Due',            'Number of calendar days since payment was due and not received.',                       'DATEDIFF(today, due_date) WHERE payment_status=OVERDUE',                                         'SNAPSHOT',  'semantic_payment_status',     'overdue_days',          'payments',   'PAYMENT',   1),
('fraud_rate',       'Fraud Rate',           'Transaction Fraud Rate',   'Percentage of transactions confirmed as fraudulent by count or amount.',                'COUNT(is_fraud=1) / COUNT(*)',                                                                   'DAILY',     'semantic_risk_metrics',       'fraud_rate',            'risk',       'RISK',      1),
('decline_rate',     'Decline Rate',         'Authorization Decline Rate','Percentage of transaction authorization attempts that were declined.',                  'COUNT(auth_status=DECLINED) / COUNT(*)',                                                         'DAILY',     'semantic_risk_metrics',       'decline_rate',          'risk',       'RISK',      1),
('fraud_score_avg',  'Avg Fraud Score',      'Average Fraud Score',      'Average machine-learning fraud propensity score across transactions (0–1 scale).',      'AVG(fraud_score)',                                                                               'DAILY',     'semantic_risk_metrics',       'avg_fraud_score',       'risk',       'RISK',      1),
('txn_count',        'Transaction Count',    'Transaction Count',        'Number of transactions processed in the period.',                                       'COUNT(transaction_id)',                                                                          'MONTHLY',   'semantic_spend_metrics',      'transaction_count',     'transactions','SPEND',    1),
('avg_txn_amount',   'Avg Transaction',      'Average Transaction Size',  'Average ticket size per transaction.',                                                 'SUM(amount) / COUNT(transaction_id)',                                                            'MONTHLY',   'semantic_spend_metrics',      'avg_txn_amount',        'spend',      'SPEND',     1),
('delinquency_rate', 'Delinquency Rate',     'Delinquency Rate',         'Percentage of accounts with overdue payments (1+ days past due).',                     'COUNT(overdue_days>0) / COUNT(account_id)',                                                      'MONTHLY',   'semantic_risk_metrics',       'delinquency_1_30',      'risk',       'RISK',      1),
('full_payment_rate','Full Payment Rate',    'Full Payment Rate',        'Percentage of accounts that paid total due in full.',                                   'COUNT(payment_amount >= total_due) / COUNT(account_id)',                                         'MONTHLY',   'semantic_portfolio_kpis',     'full_payment_rate',     'payments',   'PAYMENT',   1),
('customer_growth',  'Customer Growth',      'Customer Growth Rate',     'Month-over-month percentage change in total active customers.',                         '(active_customers_this_month - active_customers_last_month) / active_customers_last_month',       'MONTHLY',   'semantic_portfolio_kpis',     'customer_growth_pct',   'portfolio',  'PORTFOLIO', 1),
('churn_rate',       'Churn Rate',           'Customer Churn Rate',      'Percentage of customers who closed or became dormant in the period.',                   'churned_customers / total_customers',                                                            'MONTHLY',   'semantic_portfolio_kpis',     'churn_rate',            'portfolio',  'PORTFOLIO', 1),
('npl_rate',         'NPL Rate',             'Non-Performing Loan Rate', 'Percentage of outstanding balance that is 90+ days overdue.',                          'SUM(balance WHERE overdue_days>90) / SUM(total_outstanding)',                                    'MONTHLY',   'semantic_portfolio_kpis',     'npl_rate',              'risk',       'RISK',      1),
('interest_income',  'Interest Income',      'Estimated Interest Income','Estimated interest income from revolving balances at current APR.',                     'SUM(closing_balance * interest_rate / 12) WHERE revolving=true',                                'MONTHLY',   'semantic_portfolio_kpis',     'est_interest_income',   'portfolio',  'PORTFOLIO', 1),
('top_category',     'Top Spend Category',   'Top Merchant Category',    'Merchant category accounting for the highest spend share in the period.',               'MAX(category_spend)',                                                                            'MONTHLY',   'semantic_spend_metrics',      'top_category',          'spend',      'SPEND',     1);

-- =============================================================================
-- intent_domain_mapping — NL keyword → domain routing
-- =============================================================================
INSERT INTO intent_domain_mapping VALUES
-- SPEND domain
('spend',               'spend',        10, 'How much did I spend last month?'),
('spent',               'spend',        10, 'How much did I spend on food?'),
('purchase',            'spend',         9, 'Show my purchases this week'),
('shopping',            'spend',         8, 'What did I buy at retail stores?'),
('transaction',         'transactions',  9, 'Show me my latest transactions'),
('transactions',        'transactions', 10, 'List all transactions this month'),
('payments made',       'spend',         7, 'Show payments I made to merchants'),
('merchant',            'transactions',  7, 'What merchants did I use?'),
('category',            'spend',         8, 'Show spending by category'),
('food',                'spend',         7, 'How much on food?'),
('travel',              'spend',         7, 'Show travel spending'),
('groceries',           'spend',         7, 'What did I spend on groceries?'),
('entertainment',       'spend',         6, 'How much on entertainment?'),
-- PAYMENTS domain
('due',                 'payments',     10, 'What is my due amount?'),
('payment due',         'payments',     10, 'When is my next payment due?'),
('outstanding',         'payments',      9, 'What is my outstanding balance?'),
('overdue',             'payments',      9, 'Are any of my payments overdue?'),
('minimum payment',     'payments',      9, 'What is my minimum payment?'),
('bill',                'payments',      8, 'Show my bill'),
('statement',           'payments',      8, 'Show my latest statement'),
('payment',             'payments',      9, 'Did I make my payment?'),
('late fee',            'payments',      8, 'Show any late fees'),
('giro',                'payments',      7, 'Is my GIRO enrolled?'),
('autopay',             'payments',      7, 'Check my autopay status'),
-- CUSTOMER domain
('balance',             'customer',      9, 'What is my current balance?'),
('credit limit',        'customer',      9, 'What is my credit limit?'),
('available credit',    'customer',      9, 'How much available credit do I have?'),
('utilization',         'customer',      8, 'What is my credit utilization?'),
('account',             'customer',      7, 'Show my account details'),
('profile',             'customer',      8, 'Show my customer profile'),
('segment',             'customer',      7, 'What segment am I in?'),
('kyc',                 'customer',      6, 'What is my KYC status?'),
-- RISK domain
('fraud',               'risk',         10, 'Show suspicious transactions'),
('suspicious',          'risk',          9, 'Any suspicious activity?'),
('decline',             'risk',          9, 'Why was my transaction declined?'),
('declined',            'risk',          9, 'Show declined transactions'),
('fraud rate',          'risk',          9, 'What is the fraud rate?'),
('decline rate',        'risk',          9, 'Show decline rate by country'),
('fraud score',         'risk',          8, 'Show high fraud score transactions'),
('alert',               'risk',          8, 'Show fraud alerts'),
('blocked',             'risk',          7, 'Why is my card blocked?'),
('high risk',           'risk',          8, 'Show high risk customers'),
-- PORTFOLIO domain
('portfolio',           'portfolio',    10, 'Show portfolio KPIs'),
('kpi',                 'portfolio',     9, 'Show key KPIs'),
('growth',              'portfolio',     8, 'Show customer growth rate'),
('churn',               'portfolio',     8, 'What is the churn rate?'),
('npl',                 'portfolio',     9, 'What is the NPL rate?'),
('delinquency',         'portfolio',     9, 'Show delinquency rates'),
('interest income',     'portfolio',     8, 'Estimate interest income');

-- =============================================================================
-- domain_semantic_mapping — domain → semantic table
-- =============================================================================
INSERT INTO domain_semantic_mapping VALUES
('customer',      'semantic_customer_360',         1, 'Customer profile, balance, account snapshot'),
('transactions',  'semantic_transaction_summary',  1, 'All transaction events with enrichments'),
('spend',         'semantic_spend_metrics',         1, 'Monthly spend aggregation by customer and category'),
('payments',      'semantic_payment_status',        1, 'Current payment status and due amounts per account'),
('risk',          'semantic_risk_metrics',           1, 'Daily fraud and decline rate aggregations'),
('portfolio',     'semantic_portfolio_kpis',        1, 'Monthly portfolio-level executive KPIs'),
('risk',          'semantic_transaction_summary',   2, 'Transaction-level fraud and decline detail'),
('customer',      'semantic_spend_metrics',         2, 'Customer spend history'),
('payments',      'semantic_customer_360',          2, 'Quick balance and payment status check');

-- =============================================================================
-- semantic_metric_mapping — metric → column
-- =============================================================================
INSERT INTO semantic_metric_mapping VALUES
('total_spend',       'semantic_spend_metrics',        'total_spend',         'spend_month',   'customer_id',       'SUM'),
('fraud_rate',        'semantic_risk_metrics',          'fraud_rate',          'metric_date',   'country_code',      'AVG'),
('decline_rate',      'semantic_risk_metrics',          'decline_rate',        'metric_date',   'country_code',      'AVG'),
('payment_due',       'semantic_payment_status',        'total_due',           'as_of_date',    'customer_id',       'SUM'),
('minimum_due',       'semantic_payment_status',        'minimum_due',         'as_of_date',    'customer_id',       'SUM'),
('current_balance',   'semantic_customer_360',          'current_balance',     'as_of_date',    'customer_id',       'MAX'),
('available_credit',  'semantic_customer_360',          'available_balance',   'as_of_date',    'customer_id',       'MAX'),
('utilization_rate',  'semantic_customer_360',          'utilization_pct',     'as_of_date',    'customer_id',       'MAX'),
('txn_count',         'semantic_spend_metrics',         'transaction_count',   'spend_month',   'customer_id',       'SUM'),
('delinquency_rate',  'semantic_risk_metrics',          'delinquency_1_30',    'metric_date',   'country_code',      'AVG');

-- =============================================================================
-- semantic_dimension_mapping
-- =============================================================================
INSERT INTO semantic_dimension_mapping VALUES
('country',           'semantic_customer_360', 'country_code',       'Country',              'CATEGORICAL', 1, 1),
('customer_segment',  'semantic_customer_360', 'customer_segment',   'Customer Segment',     'CATEGORICAL', 1, 1),
('month',             'semantic_spend_metrics','spend_month',        'Month (YYYY-MM)',       'DATE',        1, 1),
('merchant_category', 'semantic_transaction_summary','merchant_category','Merchant Category', 'CATEGORICAL', 1, 1),
('payment_status',    'semantic_payment_status','payment_status',    'Payment Status',        'CATEGORICAL', 1, 1),
('risk_rating',       'semantic_customer_360', 'risk_rating',        'Risk Rating',          'CATEGORICAL', 1, 1),
('overdue_bucket',    'semantic_payment_status','overdue_bucket',    'Overdue Bucket',        'CATEGORICAL', 1, 1),
('channel',           'semantic_transaction_summary','channel',      'Transaction Channel',   'CATEGORICAL', 1, 1),
('transaction_type',  'semantic_transaction_summary','transaction_type','Transaction Type',   'CATEGORICAL', 1, 1),
('age_band',          'semantic_customer_360', 'age_band',           'Customer Age Band',     'CATEGORICAL', 1, 1);

-- =============================================================================
-- domain_grain_mapping — domain → time grain
-- =============================================================================
INSERT INTO domain_grain_mapping VALUES
('customer',      'SNAPSHOT',    'AS_OF_TODAY',    'as_of_date',    'Customer 360 snapshot — latest record per customer'),
('transactions',  'EVENT',       'LAST_30_DAYS',   'transaction_date','Transaction event log — default last 30 days'),
('spend',         'MONTHLY',     'LAST_3_MONTHS',  'spend_month',   'Monthly spend aggregation — default last 3 months'),
('payments',      'SNAPSHOT',    'CURRENT_DUE',    'as_of_date',    'Payment status snapshot — current statement due'),
('risk',          'DAILY',       'LAST_30_DAYS',   'metric_date',   'Risk metrics — daily aggregation, default last 30 days'),
('portfolio',     'MONTHLY',     'LAST_12_MONTHS', 'kpi_month',     'Portfolio KPIs — monthly, default last 12 months');

-- =============================================================================
-- semantic_access_control — persona → table access with country rules
-- =============================================================================
INSERT INTO semantic_access_control VALUES
-- fraud_analyst: risk tables for SG + MY, read-only, no PII
('fraud_analyst',  'semantic_transaction_summary',  1, 'SG,MY',  'id_number,email,phone,address_line1',  2000, 'Fraud analyst — SG+MY transactions, no PII'),
('fraud_analyst',  'semantic_risk_metrics',           1, 'SG,MY',  NULL,                                   500,  'Fraud analyst — risk KPIs for SG+MY'),
('fraud_analyst',  'semantic_customer_360',           1, 'SG,MY',  'id_number,email,phone,annual_income',  500,  'Fraud analyst — customer context, limited PII'),
('fraud_analyst',  'semantic_spend_metrics',          0, 'ALL',    NULL,                                   0,    'Fraud analyst — no spend access'),
('fraud_analyst',  'semantic_payment_status',         0, 'ALL',    NULL,                                   0,    'Fraud analyst — no payment access'),
('fraud_analyst',  'semantic_portfolio_kpis',         0, 'ALL',    NULL,                                   0,    'Fraud analyst — no portfolio access'),
-- retail_user: own data only (row-level = OWN customer_id)
('retail_user',    'semantic_customer_360',           1, 'OWN',    'annual_income,credit_score,id_number', 10,   'Retail — own profile only'),
('retail_user',    'semantic_spend_metrics',          1, 'OWN',    NULL,                                   50,   'Retail — own spend history'),
('retail_user',    'semantic_payment_status',         1, 'OWN',    NULL,                                   10,   'Retail — own payment status'),
('retail_user',    'semantic_transaction_summary',    1, 'OWN',    'fraud_score',                         200,   'Retail — own transactions'),
('retail_user',    'semantic_risk_metrics',            0, 'ALL',    NULL,                                   0,    'Retail — no risk metrics'),
('retail_user',    'semantic_portfolio_kpis',          0, 'ALL',    NULL,                                   0,    'Retail — no portfolio access'),
-- finance_user: aggregated views only, all countries, no row-level PII
('finance_user',   'semantic_portfolio_kpis',         1, 'ALL',    NULL,                                   200,  'Finance — full portfolio KPIs'),
('finance_user',   'semantic_spend_metrics',          1, 'ALL',    'email,phone,id_number',               1000,  'Finance — aggregated spend'),
('finance_user',   'semantic_payment_status',         1, 'ALL',    'email,phone,id_number',               1000,  'Finance — payment status aggregates'),
('finance_user',   'semantic_risk_metrics',            1, 'ALL',    NULL,                                  500,   'Finance — risk KPIs'),
('finance_user',   'semantic_customer_360',            1, 'ALL',    'id_number,phone,email,address_line1', 500,   'Finance — aggregated customer view'),
('finance_user',   'semantic_transaction_summary',    1, 'ALL',    'id_number,phone,email',              2000,   'Finance — transaction summaries'),
-- analyst: full access, all countries, minimal PII restrictions
('analyst',        'semantic_customer_360',           1, 'ALL',    'id_number',                          2000,  'Analyst — full customer view, no govt ID'),
('analyst',        'semantic_transaction_summary',    1, 'ALL',    NULL,                                 5000,  'Analyst — full transaction access'),
('analyst',        'semantic_spend_metrics',          1, 'ALL',    NULL,                                 2000,  'Analyst — full spend access'),
('analyst',        'semantic_payment_status',         1, 'ALL',    NULL,                                 2000,  'Analyst — full payment access'),
('analyst',        'semantic_risk_metrics',            1, 'ALL',    NULL,                                 1000,  'Analyst — full risk access'),
('analyst',        'semantic_portfolio_kpis',         1, 'ALL',    NULL,                                  500,  'Analyst — full portfolio access'),
-- admin: unrestricted access
('admin',          'semantic_customer_360',           1, 'ALL',    NULL,                                 10000, 'Admin — unrestricted'),
('admin',          'semantic_transaction_summary',    1, 'ALL',    NULL,                                 10000, 'Admin — unrestricted'),
('admin',          'semantic_spend_metrics',          1, 'ALL',    NULL,                                 10000, 'Admin — unrestricted'),
('admin',          'semantic_payment_status',         1, 'ALL',    NULL,                                 10000, 'Admin — unrestricted'),
('admin',          'semantic_risk_metrics',            1, 'ALL',    NULL,                                 10000, 'Admin — unrestricted'),
('admin',          'semantic_portfolio_kpis',         1, 'ALL',    NULL,                                 10000, 'Admin — unrestricted');

-- =============================================================================
-- user_domain_mapping — specific user grants
-- =============================================================================
INSERT INTO user_domain_mapping VALUES
('u1', 'customer',     'ALL', 'FULL',  'system', NOW()),
('u1', 'transactions', 'ALL', 'FULL',  'system', NOW()),
('u1', 'spend',        'ALL', 'FULL',  'system', NOW()),
('u1', 'payments',     'ALL', 'FULL',  'system', NOW()),
('u1', 'risk',         'ALL', 'FULL',  'system', NOW()),
('u1', 'portfolio',    'ALL', 'FULL',  'system', NOW()),
('u2', 'risk',         'SG',  'READ',  'admin',  NOW()),
('u2', 'transactions', 'SG',  'READ',  'admin',  NOW()),
('u2', 'risk',         'MY',  'READ',  'admin',  NOW()),
('u3', 'portfolio',    'ALL', 'FULL',  'admin',  NOW()),
('u3', 'spend',        'ALL', 'READ',  'admin',  NOW()),
('u4', 'customer',     'SG',  'READ',  'admin',  NOW()),
('u4', 'spend',        'SG',  'READ',  'admin',  NOW()),
('u4', 'payments',     'SG',  'READ',  'admin',  NOW());
