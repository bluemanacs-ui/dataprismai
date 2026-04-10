-- =============================================================================
-- DataPrismAI — Data Dictionary Seed Data (StarRocks)
-- Database: cc_analytics
--
-- Populates dic_tables, dic_columns, dic_relationships with the banking domain
-- definitions used by the /dictionary API.
--
-- Run AFTER 04_dictionary_tables.sql:
--   mysql -h 127.0.0.1 -P 9030 -u root < data/ddl/starrocks/05_dictionary_seed.sql
-- =============================================================================

USE cc_analytics;

-- Clear before reload (idempotent)
DELETE FROM dic_tables;
DELETE FROM dic_columns;
DELETE FROM dic_relationships;

-- ── dic_tables (all 38 tables across 6 layers) ──────────────────────────────
INSERT INTO dic_tables (table_id, table_name, display_name, layer, domain, description, owner, refresh_cadence, is_active) VALUES
  -- Semantic Layer
  (1,  'semantic_customer_360',        'Customer 360',             'semantic','customer',   'Full customer profile with balances, spend, payment status and risk flags',                 'data-team','daily',    1),
  (2,  'semantic_transaction_summary', 'Transaction Summary',      'semantic','transaction','Enriched transaction ledger with fraud, channel, merchant and customer attributes',        'data-team','daily',    1),
  (3,  'semantic_spend_metrics',       'Spend Metrics',            'semantic','spend',      'Monthly per-customer spend by category with MoM change',                                   'data-team','monthly',  1),
  (4,  'semantic_payment_status',      'Payment Status',           'semantic','payment',    'Account-level payment behavior, overdue buckets, and late-fee exposure',                   'data-team','daily',    1),
  (5,  'semantic_risk_metrics',        'Risk Metrics',             'semantic','risk',       'Daily fraud rates, decline rates, and delinquency bands by country/segment',               'risk-team','daily',    1),
  (6,  'semantic_portfolio_kpis',      'Portfolio KPIs',           'semantic','portfolio',  'Monthly portfolio roll-up: customers, spend growth, utilization, fraud rate, NPL rate',   'data-team','monthly',  1),
  (7,  'semantic_glossary_metrics',    'Glossary Metrics',         'semantic','catalog',    'Semantic metric definitions, SQL expressions, and grain metadata',                         'data-team','on-demand',1),
  -- Data Products (DP)
  (11, 'dp_customer_balance_snapshot', 'Customer Balance Snapshot','dp',      'customer',   'Monthly snapshot: total credit, outstanding balance, and utilization per customer',        'data-team','monthly',  1),
  (12, 'dp_customer_spend_monthly',    'Customer Monthly Spend',   'dp',      'spend',      'Monthly per-customer spend across 11 merchant categories with totals',                     'data-team','monthly',  1),
  (13, 'dp_transaction_enriched',      'Enriched Transactions',    'dp',      'transaction','Transaction ledger enriched with customer/merchant context, fraud scoring, and segment',   'data-team','daily',    1),
  (14, 'dp_payment_status',            'Payment Status',           'dp',      'payment',    'Daily account-level payment status with overdue buckets, late fees, interest at risk',     'data-team','daily',    1),
  (15, 'dp_risk_signals',              'Risk Signals',             'dp',      'risk',       'Daily aggregated fraud/decline/delinquency risk signals by country and segment',           'risk-team','daily',    1),
  (16, 'dp_portfolio_kpis',            'Portfolio KPIs',           'dp',      'portfolio',  'Monthly portfolio health KPIs: customers, spend, utilization, fraud, NPL, churn',         'data-team','monthly',  1),
  -- Domain Data Model (DDM)
  (21, 'ddm_customer',                 'DDM Customer',             'ddm',     'customer',   'Conformed customer dimension: demographics, KYC, risk, income band, credit band',          'data-eng', 'daily',    1),
  (22, 'ddm_account',                  'DDM Account',              'ddm',     'account',    'Conformed account dimension: balance, credit limit, utilization band, product info',       'data-eng', 'daily',    1),
  (23, 'ddm_card',                     'DDM Card',                 'ddm',     'card',       'Conformed card dimension: card type, expiry, status, linked account and customer',        'data-eng', 'daily',    1),
  (24, 'ddm_transaction',              'DDM Transaction',          'ddm',     'transaction','Conformed transaction fact: enriched with segment, fraud tier, merchant risk tier',        'data-eng', 'realtime', 1),
  (25, 'ddm_payment',                  'DDM Payment',              'ddm',     'payment',    'Conformed payment fact: method, amount, overdue days, linked statement',                   'data-eng', 'daily',    1),
  (26, 'ddm_statement',                'DDM Statement',            'ddm',     'statement',  'Conformed monthly statement: closing balance, spend, minimum due, payment status',        'data-eng', 'monthly',  1),
  (27, 'ddm_merchant',                 'DDM Merchant',             'ddm',     'merchant',   'Conformed merchant dimension: MCC, risk tier, historical fraud/decline rates',            'data-eng', 'daily',    1),
  -- Raw Layer
  (31, 'raw_customer',                 'Raw Customers',            'raw',     'customer',   'Source customer master — demographics, KYC, risk rating, credit score',                   'data-eng', 'daily',    1),
  (32, 'raw_account',                  'Raw Accounts',             'raw',     'account',    'Credit card accounts — balance, credit limit, interest rate, status',                     'data-eng', 'daily',    1),
  (33, 'raw_card',                     'Raw Cards',                'raw',     'card',       'Physical card records — card type, expiry, linked account',                               'data-eng', 'daily',    1),
  (34, 'raw_transaction',              'Raw Transactions',         'raw',     'transaction','Source transaction ledger with auth status, fraud score and channel',                     'data-eng', 'realtime', 1),
  (35, 'raw_payment',                  'Raw Payments',             'raw',     'payment',    'Payment records — amount paid, method, overdue days',                                     'data-eng', 'daily',    1),
  (36, 'raw_statement',                'Raw Statements',           'raw',     'statement',  'Monthly statements — closing balance, total spend, minimum due, payment status',          'data-eng', 'monthly',  1),
  (37, 'raw_merchant',                 'Raw Merchants',            'raw',     'merchant',   'Merchant master — category, MCC, risk tier, fraud/decline rate',                          'data-eng', 'daily',    1),
  -- Audit
  (41, 'audit_data_quality',           'Data Quality Audit',       'audit',   'ops',        'Row-level data quality check results per table and rule',                                  'data-eng', 'daily',    1),
  (42, 'audit_data_profile',           'Data Profile Audit',       'audit',   'ops',        'Column-level profile statistics: null%, distinct count, min, max',                        'data-eng', 'daily',    1),
  (43, 'audit_pipeline_runs',          'Pipeline Run Audit',       'audit',   'ops',        'ETL pipeline execution log: status, rows loaded, duration, errors',                       'data-eng', 'realtime', 1),
  (44, 'audit_query_log',              'Query Audit Log',          'audit',   'ops',        'GenBI query audit: SQL generated, engine used, row count, execution time',                'platform', 'realtime', 1),
  -- Config & Mapping
  (51, 'intent_domain_mapping',        'Intent→Domain Mapping',    'config',  'routing',    'Maps LLM-detected intent keywords to business domains for query routing',                  'platform', 'on-demand',1),
  (52, 'domain_semantic_mapping',      'Domain→Semantic Mapping',  'config',  'routing',    'Maps business domains to semantic table names for SQL generation',                         'platform', 'on-demand',1),
  (53, 'semantic_metric_mapping',      'Metric Mapping',           'config',  'catalog',    'Maps metric names to SQL expressions and source tables',                                   'platform', 'on-demand',1),
  (54, 'semantic_dimension_mapping',   'Dimension Mapping',        'config',  'catalog',    'Allowed dimension breakdowns per metric/domain',                                           'platform', 'on-demand',1),
  (55, 'semantic_access_control',      'Semantic Access Control',  'config',  'security',   'Row-level access: which domains/tables a persona/role may query',                          'platform', 'on-demand',1),
  (56, 'user_domain_mapping',          'User→Domain Mapping',      'config',  'security',   'Maps user IDs to allowed business domains and country codes',                              'platform', 'on-demand',1),
  (57, 'domain_grain_mapping',         'Domain Grain Mapping',     'config',  'catalog',    'Default query grain (daily/monthly/all-time) for each business domain',                    'platform', 'on-demand',1);

-- ── dic_columns ──────────────────────────────────────────────────────────────
-- semantic_customer_360
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (101,'semantic_customer_360','as_of_date',          'As-of Date',        'DATE',    'Snapshot date',                              0,0,0,NULL),
  (102,'semantic_customer_360','customer_id',         'Customer ID',       'VARCHAR', 'Unique customer identifier',                 0,1,1,NULL),
  (103,'semantic_customer_360','country_code',        'Country',           'VARCHAR', 'SG / MY / IN',                               0,0,0,'SG,MY,IN'),
  (104,'semantic_customer_360','legal_entity',        'Legal Entity',      'VARCHAR', 'SG_BANK / MY_BANK / IN_BANK',                0,0,0,'SG_BANK,MY_BANK,IN_BANK'),
  (105,'semantic_customer_360','full_name',           'Full Name',         'VARCHAR', 'Customer full name',                         1,0,1,NULL),
  (106,'semantic_customer_360','customer_segment',    'Segment',           'VARCHAR', 'Customer segment',                           0,0,0,'mass,affluent,premium'),
  (107,'semantic_customer_360','risk_rating',         'Risk Rating',       'VARCHAR', 'Risk classification',                        0,0,0,'low,medium,high'),
  (108,'semantic_customer_360','kyc_status',          'KYC Status',        'VARCHAR', 'KYC verification status',                    0,0,0,'verified,pending,enhanced_dd'),
  (109,'semantic_customer_360','credit_score',        'Credit Score',      'INT',     'Numeric credit score',                       1,0,0,NULL),
  (110,'semantic_customer_360','credit_band',         'Credit Band',       'VARCHAR', 'Credit quality band',                        1,0,0,'poor,fair,good,very_good,excellent'),
  (111,'semantic_customer_360','current_balance',     'Current Balance',   'DECIMAL', 'Current outstanding balance',                1,0,0,NULL),
  (112,'semantic_customer_360','credit_limit',        'Credit Limit',      'DECIMAL', 'Approved credit limit',                      1,0,0,NULL),
  (113,'semantic_customer_360','utilization_pct',     'Utilization %',     'DECIMAL', 'Balance / credit limit ratio',               1,0,0,NULL),
  (114,'semantic_customer_360','mtd_spend',           'MTD Spend',         'DECIMAL', 'Month-to-date spend',                        1,0,0,NULL),
  (115,'semantic_customer_360','payment_status',      'Payment Status',    'VARCHAR', 'Latest payment status',                      1,0,0,'paid_full,paid_partial,paid_minimum,overdue,pending'),
  (116,'semantic_customer_360','is_overdue',          'Is Overdue',        'BOOLEAN', 'True if account is overdue',                 0,0,0,NULL),
  (117,'semantic_customer_360','active_fraud_alerts', 'Active Fraud Alerts','INT',    'Number of open fraud alerts',                0,0,0,NULL),
  (118,'semantic_customer_360','currency_code',       'Currency',          'VARCHAR', 'Account currency',                           0,0,0,NULL);

-- semantic_transaction_summary
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (201,'semantic_transaction_summary','transaction_id',      'Transaction ID',  'VARCHAR','Unique transaction identifier',      0,1,0,NULL),
  (202,'semantic_transaction_summary','account_id',          'Account ID',      'VARCHAR','Associated account',                 0,0,0,NULL),
  (203,'semantic_transaction_summary','customer_id',         'Customer ID',     'VARCHAR','Account owner',                      0,0,1,NULL),
  (204,'semantic_transaction_summary','country_code',        'Country',         'VARCHAR','SG / MY / IN',                       0,0,0,'SG,MY,IN'),
  (205,'semantic_transaction_summary','transaction_date',    'Transaction Date','DATE',   'Date of transaction',                0,0,0,NULL),
  (206,'semantic_transaction_summary','amount',              'Amount',          'DECIMAL','Transaction value',                  0,0,0,NULL),
  (207,'semantic_transaction_summary','transaction_type',    'Type',            'VARCHAR','purchase or declined',               0,0,0,'purchase,declined'),
  (208,'semantic_transaction_summary','channel',             'Channel',         'VARCHAR','Purchase channel',                   1,0,0,'online,pos,contactless,mobile,atm'),
  (209,'semantic_transaction_summary','merchant_name',       'Merchant',        'VARCHAR','Merchant name',                      1,0,0,NULL),
  (210,'semantic_transaction_summary','merchant_category',   'Category',        'VARCHAR','Merchant category',                  1,0,0,NULL),
  (211,'semantic_transaction_summary','auth_status',         'Auth Status',     'VARCHAR','approved or declined',               0,0,0,'approved,declined'),
  (212,'semantic_transaction_summary','is_fraud',            'Is Fraud',        'BOOLEAN','Confirmed fraud flag',               0,0,0,NULL),
  (213,'semantic_transaction_summary','fraud_score',         'Fraud Score',     'DECIMAL','ML fraud probability 0-1',           1,0,0,NULL),
  (214,'semantic_transaction_summary','is_international',    'International',   'BOOLEAN','Cross-border transaction flag',      0,0,0,NULL);

-- semantic_spend_metrics
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (301,'semantic_spend_metrics','spend_month',         'Spend Month',    'VARCHAR','YYYY-MM month key',                           0,1,0,NULL),
  (302,'semantic_spend_metrics','customer_id',         'Customer ID',    'VARCHAR','Customer identifier',                         0,1,1,NULL),
  (303,'semantic_spend_metrics','country_code',        'Country',        'VARCHAR','SG / MY / IN',                                0,0,0,'SG,MY,IN'),
  (304,'semantic_spend_metrics','customer_segment',    'Segment',        'VARCHAR','mass,affluent,premium',                       0,0,0,'mass,affluent,premium'),
  (305,'semantic_spend_metrics','total_spend',         'Total Spend',    'DECIMAL','Total spend in month',                        0,0,0,NULL),
  (306,'semantic_spend_metrics','food_dining',         'Food & Dining',  'DECIMAL','Spend at food/restaurant merchants',           1,0,0,NULL),
  (307,'semantic_spend_metrics','retail_shopping',     'Retail Shopping','DECIMAL','Retail merchant spend',                       1,0,0,NULL),
  (308,'semantic_spend_metrics','travel_transport',    'Travel & Transport','DECIMAL','Travel and transport spend',                1,0,0,NULL),
  (309,'semantic_spend_metrics','top_category',        'Top Category',   'VARCHAR','Highest-spend category for month',            1,0,0,NULL),
  (310,'semantic_spend_metrics','transaction_count',   'Txn Count',      'INT',   'Number of transactions in month',              0,0,0,NULL),
  (311,'semantic_spend_metrics','mom_spend_change_pct','MoM Change %',   'DECIMAL','Month-over-month spend % change',             1,0,0,NULL);

-- semantic_payment_status
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (401,'semantic_payment_status','as_of_date',          'As-of Date',      'DATE',   'Snapshot date',                              0,0,0,NULL),
  (402,'semantic_payment_status','account_id',          'Account ID',      'VARCHAR','Account identifier',                         0,1,0,NULL),
  (403,'semantic_payment_status','customer_id',         'Customer ID',     'VARCHAR','Customer identifier',                        0,0,1,NULL),
  (404,'semantic_payment_status','payment_status',      'Payment Status',  'VARCHAR','paid_full,paid_partial,paid_minimum,overdue,pending',0,0,0,'paid_full,paid_partial,paid_minimum,overdue,pending'),
  (405,'semantic_payment_status','overdue_days',        'Overdue Days',    'INT',    'Days past due date',                         0,0,0,NULL),
  (406,'semantic_payment_status','overdue_bucket',      'Overdue Bucket',  'VARCHAR','current,1-30 days,31-60 days',               1,0,0,NULL),
  (407,'semantic_payment_status','consecutive_late',    'Consecutive Late','INT',    'Consecutive months with late payment',        0,0,0,NULL),
  (408,'semantic_payment_status','total_due',           'Total Due',       'DECIMAL','Total amount due',                           0,0,0,NULL),
  (409,'semantic_payment_status','amount_paid',         'Amount Paid',     'DECIMAL','Amount actually paid',                       1,0,0,NULL),
  (410,'semantic_payment_status','late_fee',            'Late Fee',        'DECIMAL','Late fee assessed',                          1,0,0,NULL),
  (411,'semantic_payment_status','interest_at_risk',    'Interest at Risk','DECIMAL','Interest income at risk from late accounts',  1,0,0,NULL);

-- semantic_risk_metrics
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (501,'semantic_risk_metrics','metric_date',        'Metric Date',     'DATE',   'Date of risk snapshot',                        0,1,0,NULL),
  (502,'semantic_risk_metrics','country_code',       'Country',         'VARCHAR','SG / MY / IN',                                 0,1,0,'SG,MY,IN'),
  (503,'semantic_risk_metrics','customer_segment',   'Segment',         'VARCHAR','mass,affluent,premium',                        0,1,0,'mass,affluent,premium'),
  (504,'semantic_risk_metrics','fraud_rate',         'Fraud Rate',      'DECIMAL','Fraud transactions / total transactions',      0,0,0,NULL),
  (505,'semantic_risk_metrics','decline_rate',       'Decline Rate',    'DECIMAL','Declined transactions / total transactions',   0,0,0,NULL),
  (506,'semantic_risk_metrics','fraud_amount',       'Fraud Amount',    'DECIMAL','Total value of fraud transactions',            0,0,0,NULL),
  (507,'semantic_risk_metrics','delinquency_1_30',   'Delinquency 1-30d','INT',  'Accounts 1-30 days past due',                  0,0,0,NULL),
  (508,'semantic_risk_metrics','delinquency_31_60',  'Delinquency 31-60d','INT', 'Accounts 31-60 days past due',                 0,0,0,NULL),
  (509,'semantic_risk_metrics','high_risk_accounts', 'High Risk Accounts','INT', 'Count of high-risk rated accounts',             0,0,0,NULL);

-- semantic_portfolio_kpis
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (601,'semantic_portfolio_kpis','kpi_month',          'KPI Month',       'VARCHAR','YYYY-MM month key',                           0,1,0,NULL),
  (602,'semantic_portfolio_kpis','country_code',       'Country',         'VARCHAR','SG / MY / IN',                                0,1,0,'SG,MY,IN'),
  (603,'semantic_portfolio_kpis','total_customers',    'Total Customers', 'INT',    'Total active customers',                      0,0,0,NULL),
  (604,'semantic_portfolio_kpis','total_spend',        'Total Spend',     'DECIMAL','Portfolio total spend',                       0,0,0,NULL),
  (605,'semantic_portfolio_kpis','spend_growth_pct',   'Spend Growth %',  'DECIMAL','YoY spend growth',                            1,0,0,NULL),
  (606,'semantic_portfolio_kpis','avg_utilization',    'Avg Utilization', 'DECIMAL','Average credit utilization across portfolio',  1,0,0,NULL),
  (607,'semantic_portfolio_kpis','fraud_rate',         'Fraud Rate',      'DECIMAL','Portfolio-level fraud rate',                  1,0,0,NULL),
  (608,'semantic_portfolio_kpis','delinquency_rate',   'Delinquency Rate','DECIMAL','% accounts with overdue payments',            1,0,0,NULL),
  (609,'semantic_portfolio_kpis','npl_rate',           'NPL Rate',        'DECIMAL','Non-performing loan rate',                    1,0,0,NULL),
  (610,'semantic_portfolio_kpis','est_interest_income','Est. Interest Income','DECIMAL','Estimated interest income',               1,0,0,NULL);

-- raw_customer
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (701,'raw_customer','customer_id',      'Customer ID',  'VARCHAR','Unique customer ID',             0,1,1,NULL),
  (702,'raw_customer','country_code',     'Country',      'VARCHAR','SG/MY/IN',                       0,0,0,'SG,MY,IN'),
  (703,'raw_customer','first_name',       'First Name',   'VARCHAR','Customer first name',            0,0,1,NULL),
  (704,'raw_customer','last_name',        'Last Name',    'VARCHAR','Customer last name',             0,0,1,NULL),
  (705,'raw_customer','email',            'Email',        'VARCHAR','Customer email address',         1,0,1,NULL),
  (706,'raw_customer','phone',            'Phone',        'VARCHAR','Contact phone number',           1,0,1,NULL),
  (707,'raw_customer','customer_segment', 'Segment',      'VARCHAR','mass,affluent,premium',          0,0,0,'mass,affluent,premium'),
  (708,'raw_customer','credit_score',     'Credit Score', 'INT',    'Credit score',                   1,0,0,NULL),
  (709,'raw_customer','kyc_status',       'KYC Status',   'VARCHAR','verified,pending,enhanced_dd',   0,0,0,'verified,pending,enhanced_dd'),
  (710,'raw_customer','risk_rating',      'Risk Rating',  'VARCHAR','low,medium,high',                0,0,0,'low,medium,high');

-- raw_transaction
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (801,'raw_transaction','transaction_id',    'Transaction ID', 'VARCHAR','Unique transaction ID',              0,1,0,NULL),
  (802,'raw_transaction','account_id',        'Account ID',     'VARCHAR','Account identifier',                0,0,0,NULL),
  (803,'raw_transaction','customer_id',       'Customer ID',    'VARCHAR','Customer identifier',               0,0,1,NULL),
  (804,'raw_transaction','transaction_date',  'Date',           'DATE',   'Transaction date',                  0,0,0,NULL),
  (805,'raw_transaction','amount',            'Amount',         'DECIMAL','Transaction amount',                0,0,0,NULL),
  (806,'raw_transaction','merchant_category', 'Category',       'VARCHAR','Merchant category',                 1,0,0,NULL),
  (807,'raw_transaction','auth_status',       'Auth Status',    'VARCHAR','approved,declined',                 0,0,0,'approved,declined'),
  (808,'raw_transaction','is_fraud',          'Is Fraud',       'BOOLEAN','Fraud flag',                        0,0,0,NULL),
  (809,'raw_transaction','channel',           'Channel',        'VARCHAR','online,pos,contactless,mobile,atm', 1,0,0,'online,pos,contactless,mobile,atm');

-- raw_account
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (901,'raw_account','account_id',      'Account ID',   'VARCHAR','Unique account ID',            0,1,0,NULL),
  (902,'raw_account','customer_id',     'Customer ID',  'VARCHAR','Account owner',                0,0,1,NULL),
  (903,'raw_account','current_balance', 'Balance',      'DECIMAL','Current outstanding balance',  1,0,0,NULL),
  (904,'raw_account','credit_limit',    'Credit Limit', 'DECIMAL','Approved credit limit',        1,0,0,NULL),
  (905,'raw_account','account_status',  'Status',       'VARCHAR','Account status',               0,0,0,NULL),
  (906,'raw_account','open_date',       'Open Date',    'DATE',   'Account open date',            1,0,0,NULL);

-- raw_statement
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (1001,'raw_statement','statement_id',    'Statement ID',    'VARCHAR','Unique statement ID',                 0,1,0,NULL),
  (1002,'raw_statement','account_id',      'Account ID',      'VARCHAR','Account identifier',                  0,0,0,NULL),
  (1003,'raw_statement','statement_month', 'Statement Month', 'VARCHAR','YYYY-MM',                             0,0,0,NULL),
  (1004,'raw_statement','closing_balance', 'Closing Balance', 'DECIMAL','End-of-month balance',               0,0,0,NULL),
  (1005,'raw_statement','total_spend',     'Total Spend',     'DECIMAL','Month spend',                         0,0,0,NULL),
  (1006,'raw_statement','total_due',       'Total Due',       'DECIMAL','Amount due',                          0,0,0,NULL),
  (1007,'raw_statement','payment_status',  'Payment Status',  'VARCHAR','paid_full,paid_partial,paid_minimum,overdue,pending',1,0,0,'paid_full,paid_partial,paid_minimum,overdue,pending');

-- raw_payment
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (1101,'raw_payment','payment_id',     'Payment ID',    'VARCHAR','Unique payment ID',    0,1,0,NULL),
  (1102,'raw_payment','account_id',     'Account ID',    'VARCHAR','Account identifier',   0,0,0,NULL),
  (1103,'raw_payment','payment_date',   'Payment Date',  'DATE',   'Date payment received',0,0,0,NULL),
  (1104,'raw_payment','payment_amount', 'Amount Paid',   'DECIMAL','Payment amount',       0,0,0,NULL),
  (1105,'raw_payment','payment_method', 'Method',        'VARCHAR','Payment method',       1,0,0,NULL),
  (1106,'raw_payment','overdue_days',   'Overdue Days',  'INT',    'Days past due',        0,0,0,NULL);

-- raw_merchant
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (1201,'raw_merchant','merchant_id',       'Merchant ID',   'VARCHAR','Unique merchant ID',                        0,1,0,NULL),
  (1202,'raw_merchant','merchant_name',     'Merchant Name', 'VARCHAR','Merchant name',                             0,0,0,NULL),
  (1203,'raw_merchant','merchant_category', 'Category',      'VARCHAR','Merchant category code description',        1,0,0,NULL),
  (1204,'raw_merchant','risk_tier',         'Risk Tier',     'VARCHAR','low,medium',                                1,0,0,'low,medium'),
  (1205,'raw_merchant','fraud_rate',        'Fraud Rate',    'DECIMAL','Historical fraud rate at merchant',         1,0,0,NULL),
  (1206,'raw_merchant','decline_rate',      'Decline Rate',  'DECIMAL','Historical decline rate at merchant',       1,0,0,NULL);

-- ── dic_relationships ────────────────────────────────────────────────────────
INSERT INTO dic_relationships (rel_id, from_table, from_column, to_table, to_column, relationship_type, description) VALUES
  (1, 'semantic_customer_360',       'customer_id',       'semantic_spend_metrics',       'customer_id', 'join', 'Customer 360 ← → Spend Metrics on customer_id'),
  (2, 'semantic_customer_360',       'customer_id',       'semantic_payment_status',      'customer_id', 'join', 'Customer 360 ← → Payment Status on customer_id'),
  (3, 'semantic_customer_360',       'primary_account_id','semantic_payment_status',      'account_id',  'join', 'Customer 360 ← → Payment Status on account_id'),
  (4, 'semantic_transaction_summary','country_code',      'semantic_risk_metrics',        'country_code','join', 'Transactions ← → Risk Metrics on country_code'),
  (5, 'semantic_portfolio_kpis',     'country_code',      'semantic_risk_metrics',        'country_code','join', 'Portfolio KPIs ← → Risk Metrics on country_code'),
  (6, 'raw_account',                 'customer_id',       'raw_customer',                 'customer_id', 'FK',   'Account → Customer (owner)'),
  (7, 'raw_transaction',             'account_id',        'raw_account',                  'account_id',  'FK',   'Transaction → Account'),
  (8, 'raw_transaction',             'merchant_id',       'raw_merchant',                 'merchant_id', 'FK',   'Transaction → Merchant'),
  (9, 'raw_statement',               'account_id',        'raw_account',                  'account_id',  'FK',   'Statement → Account'),
  (10,'raw_payment',                 'account_id',        'raw_account',                  'account_id',  'FK',   'Payment → Account');

-- ── Data Products (DP) dic_columns ────────────────────────────────────────────
-- dp_customer_balance_snapshot
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (2101,'dp_customer_balance_snapshot','snapshot_month',    'Snapshot Month',  'VARCHAR','YYYY-MM month key',                                 0,1,0,NULL),
  (2102,'dp_customer_balance_snapshot','customer_id',       'Customer ID',     'VARCHAR','Customer identifier',                               0,1,1,NULL),
  (2103,'dp_customer_balance_snapshot','country_code',      'Country',         'VARCHAR','SG/MY/IN',                                          0,0,0,'SG,MY,IN'),
  (2104,'dp_customer_balance_snapshot','legal_entity',      'Legal Entity',    'VARCHAR','SG_BANK/MY_BANK/IN_BANK',                           0,0,0,NULL),
  (2105,'dp_customer_balance_snapshot','customer_segment',  'Segment',         'VARCHAR','mass,affluent,premium',                             0,0,0,'mass,affluent,premium'),
  (2106,'dp_customer_balance_snapshot','total_accounts',    'Total Accounts',  'INT',    'Number of active accounts',                         0,0,0,NULL),
  (2107,'dp_customer_balance_snapshot','total_credit_limit','Total Credit',    'DECIMAL','Sum of credit limits across all accounts',           1,0,0,NULL),
  (2108,'dp_customer_balance_snapshot','total_balance',     'Total Balance',   'DECIMAL','Total outstanding balance',                         1,0,0,NULL),
  (2109,'dp_customer_balance_snapshot','total_available',   'Total Available', 'DECIMAL','Total available credit',                            1,0,0,NULL),
  (2110,'dp_customer_balance_snapshot','avg_utilization',   'Avg Utilization', 'DECIMAL','Average utilization ratio across accounts',         1,0,0,NULL),
  (2111,'dp_customer_balance_snapshot','currency_code',     'Currency',        'VARCHAR','Account base currency',                             0,0,0,NULL);

-- dp_customer_spend_monthly
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (2201,'dp_customer_spend_monthly','spend_month',        'Spend Month',     'VARCHAR','YYYY-MM month key',                                 0,1,0,NULL),
  (2202,'dp_customer_spend_monthly','customer_id',        'Customer ID',     'VARCHAR','Customer identifier',                               0,1,1,NULL),
  (2203,'dp_customer_spend_monthly','country_code',       'Country',         'VARCHAR','SG/MY/IN',                                          0,0,0,'SG,MY,IN'),
  (2204,'dp_customer_spend_monthly','customer_segment',   'Segment',         'VARCHAR','mass,affluent,premium',                             0,0,0,'mass,affluent,premium'),
  (2205,'dp_customer_spend_monthly','total_spend',        'Total Spend',     'DECIMAL','Total monthly spend',                               0,0,0,NULL),
  (2206,'dp_customer_spend_monthly','food_dining',        'Food & Dining',   'DECIMAL','Spend at food/restaurant merchants',                1,0,0,NULL),
  (2207,'dp_customer_spend_monthly','retail_shopping',    'Retail Shopping', 'DECIMAL','Retail merchant spend',                             1,0,0,NULL),
  (2208,'dp_customer_spend_monthly','travel_transport',   'Travel & Transport','DECIMAL','Travel and transport spend',                      1,0,0,NULL),
  (2209,'dp_customer_spend_monthly','transaction_count',  'Txn Count',       'INT',    'Number of transactions in month',                   0,0,0,NULL),
  (2210,'dp_customer_spend_monthly','avg_txn_amount',     'Avg Txn Amount',  'DECIMAL','Average transaction value for the month',           1,0,0,NULL),
  (2211,'dp_customer_spend_monthly','top_category',       'Top Category',    'VARCHAR','Highest-spend merchant category',                   1,0,0,NULL),
  (2212,'dp_customer_spend_monthly','currency_code',      'Currency',        'VARCHAR','Account base currency',                             0,0,0,NULL);

-- dp_transaction_enriched
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (2301,'dp_transaction_enriched','transaction_id',      'Transaction ID',  'VARCHAR','Unique transaction identifier',                     0,1,0,NULL),
  (2302,'dp_transaction_enriched','account_id',          'Account ID',      'VARCHAR','Associated account',                                0,0,0,NULL),
  (2303,'dp_transaction_enriched','customer_id',         'Customer ID',     'VARCHAR','Account owner',                                     0,0,1,NULL),
  (2304,'dp_transaction_enriched','country_code',        'Country',         'VARCHAR','SG/MY/IN',                                          0,0,0,'SG,MY,IN'),
  (2305,'dp_transaction_enriched','transaction_date',    'Date',            'DATE',   'Transaction date',                                  0,0,0,NULL),
  (2306,'dp_transaction_enriched','amount',              'Amount',          'DECIMAL','Transaction value',                                 0,0,0,NULL),
  (2307,'dp_transaction_enriched','merchant_name',       'Merchant',        'VARCHAR','Merchant name',                                     1,0,0,NULL),
  (2308,'dp_transaction_enriched','merchant_category',   'Category',        'VARCHAR','Merchant category',                                 1,0,0,NULL),
  (2309,'dp_transaction_enriched','customer_segment',    'Segment',         'VARCHAR','mass,affluent,premium',                             0,0,0,'mass,affluent,premium'),
  (2310,'dp_transaction_enriched','auth_status',         'Auth Status',     'VARCHAR','approved,declined',                                0,0,0,'approved,declined'),
  (2311,'dp_transaction_enriched','is_fraud',            'Is Fraud',        'BOOLEAN','Confirmed fraud flag',                              0,0,0,NULL),
  (2312,'dp_transaction_enriched','fraud_score',         'Fraud Score',     'DECIMAL','ML fraud probability 0-1',                          1,0,0,NULL);

-- dp_payment_status
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (2401,'dp_payment_status','as_of_date',          'As-of Date',      'DATE',   'Payment snapshot date',                             0,1,0,NULL),
  (2402,'dp_payment_status','account_id',          'Account ID',      'VARCHAR','Account identifier',                                0,1,0,NULL),
  (2403,'dp_payment_status','customer_id',         'Customer ID',     'VARCHAR','Customer identifier',                               0,0,1,NULL),
  (2404,'dp_payment_status','payment_status',      'Payment Status',  'VARCHAR','paid_full,paid_partial,paid_minimum,overdue,pending',0,0,0,'paid_full,paid_partial,paid_minimum,overdue,pending'),
  (2405,'dp_payment_status','overdue_days',        'Overdue Days',    'INT',    'Days past due date',                                0,0,0,NULL),
  (2406,'dp_payment_status','overdue_bucket',      'Overdue Bucket',  'VARCHAR','current,1-30 days,31-60 days,61-90 days,90+ days',  1,0,0,NULL),
  (2407,'dp_payment_status','consecutive_late',    'Consecutive Late','INT',    'Consecutive months with late payment',               0,0,0,NULL),
  (2408,'dp_payment_status','total_due',           'Total Due',       'DECIMAL','Total amount due',                                  0,0,0,NULL),
  (2409,'dp_payment_status','amount_paid',         'Amount Paid',     'DECIMAL','Amount actually paid',                              1,0,0,NULL),
  (2410,'dp_payment_status','late_fee',            'Late Fee',        'DECIMAL','Late fee assessed',                                 1,0,0,NULL),
  (2411,'dp_payment_status','interest_at_risk',    'Interest at Risk','DECIMAL','Interest income at risk from late accounts',         1,0,0,NULL);

-- dp_risk_signals
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (2501,'dp_risk_signals','signal_date',       'Signal Date',      'DATE',   'Date of daily risk snapshot',                       0,1,0,NULL),
  (2502,'dp_risk_signals','country_code',      'Country',          'VARCHAR','SG/MY/IN',                                          0,1,0,'SG,MY,IN'),
  (2503,'dp_risk_signals','customer_segment',  'Segment',          'VARCHAR','mass,affluent,premium',                             0,1,0,'mass,affluent,premium'),
  (2504,'dp_risk_signals','total_txn',         'Total Txns',       'INT',    'Total transaction count',                           0,0,0,NULL),
  (2505,'dp_risk_signals','fraud_txn',         'Fraud Txns',       'INT',    'Confirmed fraud transaction count',                 0,0,0,NULL),
  (2506,'dp_risk_signals','fraud_rate',        'Fraud Rate',       'DECIMAL','Fraud transactions / total transactions',           0,0,0,NULL),
  (2507,'dp_risk_signals','decline_rate',      'Decline Rate',     'DECIMAL','Declined transactions / total transactions',        0,0,0,NULL),
  (2508,'dp_risk_signals','avg_fraud_score',   'Avg Fraud Score',  'DECIMAL','Average ML fraud score for the day',                1,0,0,NULL),
  (2509,'dp_risk_signals','high_risk_accounts','High Risk Accts',  'INT',    'Count of currently high-risk accounts',             0,0,0,NULL);

-- dp_portfolio_kpis
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (2601,'dp_portfolio_kpis','kpi_month',          'KPI Month',       'VARCHAR','YYYY-MM month key',                                 0,1,0,NULL),
  (2602,'dp_portfolio_kpis','country_code',       'Country',         'VARCHAR','SG/MY/IN',                                          0,1,0,'SG,MY,IN'),
  (2603,'dp_portfolio_kpis','total_customers',    'Total Customers', 'INT',    'Total customers in portfolio',                      0,0,0,NULL),
  (2604,'dp_portfolio_kpis','active_customers',   'Active Customers','INT',    'Customers with at least one transaction this month', 0,0,0,NULL),
  (2605,'dp_portfolio_kpis','new_customers',      'New Customers',   'INT',    'Customers acquired this month',                     0,0,0,NULL),
  (2606,'dp_portfolio_kpis','churn_rate',         'Churn Rate',      'DECIMAL','% customers lost vs prior month',                   1,0,0,NULL),
  (2607,'dp_portfolio_kpis','total_spend',        'Total Spend',     'DECIMAL','Portfolio total spend for the month',               0,0,0,NULL),
  (2608,'dp_portfolio_kpis','spend_growth_pct',   'Spend Growth %',  'DECIMAL','Month-over-month spend growth',                     1,0,0,NULL),
  (2609,'dp_portfolio_kpis','avg_utilization',    'Avg Utilization', 'DECIMAL','Average credit utilization across portfolio',       1,0,0,NULL),
  (2610,'dp_portfolio_kpis','fraud_rate',         'Fraud Rate',      'DECIMAL','Portfolio-level fraud rate',                        1,0,0,NULL),
  (2611,'dp_portfolio_kpis','delinquency_rate',   'Delinquency Rate','DECIMAL','% accounts with overdue payments',                  1,0,0,NULL),
  (2612,'dp_portfolio_kpis','npl_rate',           'NPL Rate',        'DECIMAL','Non-performing loan rate',                          1,0,0,NULL),
  (2613,'dp_portfolio_kpis','est_interest_income','Est. Interest Income','DECIMAL','Estimated interest income for the month',       1,0,0,NULL);

-- ── Domain Data Model (DDM) dic_columns ──────────────────────────────────────
-- ddm_customer
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (3101,'ddm_customer','customer_id',        'Customer ID',   'VARCHAR','Unique customer identifier',                         0,1,1,NULL),
  (3102,'ddm_customer','country_code',       'Country',       'VARCHAR','SG/MY/IN',                                           0,0,0,'SG,MY,IN'),
  (3103,'ddm_customer','legal_entity',       'Legal Entity',  'VARCHAR','SG_BANK/MY_BANK/IN_BANK',                            0,0,0,NULL),
  (3104,'ddm_customer','full_name',          'Full Name',     'VARCHAR','Customer full name (derived)',                       1,0,1,NULL),
  (3105,'ddm_customer','customer_segment',   'Segment',       'VARCHAR','mass,affluent,premium',                              0,0,0,'mass,affluent,premium'),
  (3106,'ddm_customer','kyc_status',         'KYC Status',    'VARCHAR','verified,pending,enhanced_dd',                       0,0,0,'verified,pending,enhanced_dd'),
  (3107,'ddm_customer','risk_rating',        'Risk Rating',   'VARCHAR','low,medium,high',                                    0,0,0,'low,medium,high'),
  (3108,'ddm_customer','credit_score',       'Credit Score',  'INT',    'Numeric credit bureau score',                        1,0,0,NULL),
  (3109,'ddm_customer','credit_band',        'Credit Band',   'VARCHAR','poor,fair,good,very_good,excellent',                 1,0,0,'poor,fair,good,very_good,excellent'),
  (3110,'ddm_customer','income_band',        'Income Band',   'VARCHAR','low,lower_middle,upper_middle,high',                 1,0,0,NULL),
  (3111,'ddm_customer','age_band',           'Age Band',      'VARCHAR','18-25,26-35,36-45,46-55,56+',                        1,0,0,NULL),
  (3112,'ddm_customer','is_current',         'Is Current',    'BOOLEAN','True = active/non-deleted record (SCD2)',            0,0,0,NULL);

-- ddm_account
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (3201,'ddm_account','account_id',        'Account ID',    'VARCHAR','Unique account identifier',                          0,1,0,NULL),
  (3202,'ddm_account','customer_id',       'Customer ID',   'VARCHAR','Account owner',                                      0,0,1,NULL),
  (3203,'ddm_account','country_code',      'Country',       'VARCHAR','SG/MY/IN',                                           0,0,0,'SG,MY,IN'),
  (3204,'ddm_account','account_type',      'Account Type',  'VARCHAR','Credit card account type',                           0,0,0,NULL),
  (3205,'ddm_account','current_balance',   'Balance',       'DECIMAL','Current outstanding balance',                        1,0,0,NULL),
  (3206,'ddm_account','credit_limit',      'Credit Limit',  'DECIMAL','Approved credit limit',                              1,0,0,NULL),
  (3207,'ddm_account','utilization_rate',  'Utilization',   'DECIMAL','Balance / credit limit ratio',                       1,0,0,NULL),
  (3208,'ddm_account','utilization_band',  'Util Band',     'VARCHAR','low,medium,high,critical',                           1,0,0,'low,medium,high,critical'),
  (3209,'ddm_account','account_status',    'Status',        'VARCHAR','open,closed,frozen,defaulted',                       0,0,0,'open,closed,frozen,defaulted'),
  (3210,'ddm_account','account_age_days',  'Account Age',   'INT',    'Days since account open date',                       1,0,0,NULL);

-- ddm_transaction
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (3301,'ddm_transaction','transaction_id',      'Transaction ID',  'VARCHAR','Unique transaction identifier',               0,1,0,NULL),
  (3302,'ddm_transaction','account_id',          'Account ID',      'VARCHAR','Associated account',                          0,0,0,NULL),
  (3303,'ddm_transaction','customer_id',         'Customer ID',     'VARCHAR','Account owner',                               0,0,1,NULL),
  (3304,'ddm_transaction','country_code',        'Country',         'VARCHAR','SG/MY/IN',                                    0,0,0,'SG,MY,IN'),
  (3305,'ddm_transaction','transaction_date',    'Date',            'DATE',   'Transaction date',                            0,0,0,NULL),
  (3306,'ddm_transaction','amount',              'Amount',          'DECIMAL','Transaction value',                           0,0,0,NULL),
  (3307,'ddm_transaction','merchant_category',   'Category',        'VARCHAR','Merchant category description',               1,0,0,NULL),
  (3308,'ddm_transaction','merchant_risk_tier',  'Merchant Risk',   'VARCHAR','low,medium,high',                             1,0,0,'low,medium,high'),
  (3309,'ddm_transaction','auth_status',         'Auth Status',     'VARCHAR','approved,declined',                          0,0,0,'approved,declined'),
  (3310,'ddm_transaction','is_fraud',            'Is Fraud',        'BOOLEAN','Confirmed fraud flag',                        0,0,0,NULL),
  (3311,'ddm_transaction','fraud_tier',          'Fraud Tier',      'VARCHAR','low,medium,high,critical',                    1,0,0,'low,medium,high,critical'),
  (3312,'ddm_transaction','channel',             'Channel',         'VARCHAR','online,pos,contactless,mobile,atm',           1,0,0,'online,pos,contactless,mobile,atm');

-- ── Audit dic_columns ─────────────────────────────────────────────────────────
INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (4101,'audit_pipeline_runs','run_id',         'Run ID',         'VARCHAR','Unique pipeline run identifier',                 0,1,0,NULL),
  (4102,'audit_pipeline_runs','pipeline_name',  'Pipeline',       'VARCHAR','ETL pipeline or job name',                       0,0,0,NULL),
  (4103,'audit_pipeline_runs','start_time',     'Start Time',     'DATETIME','Run start timestamp',                           0,0,0,NULL),
  (4104,'audit_pipeline_runs','end_time',       'End Time',       'DATETIME','Run end timestamp',                             1,0,0,NULL),
  (4105,'audit_pipeline_runs','status',         'Status',         'VARCHAR','success,failed,running',                         0,0,0,'success,failed,running'),
  (4106,'audit_pipeline_runs','rows_loaded',    'Rows Loaded',    'BIGINT', 'Number of rows successfully loaded',             1,0,0,NULL),
  (4107,'audit_pipeline_runs','error_message',  'Error Message',  'VARCHAR','Error detail if status=failed',                  1,0,0,NULL);

INSERT INTO dic_columns (column_id, table_name, column_name, display_name, data_type, description, is_nullable, is_primary_key, is_pii, enum_values) VALUES
  (4201,'audit_query_log','query_id',       'Query ID',       'VARCHAR','Unique query log entry',                            0,1,0,NULL),
  (4202,'audit_query_log','user_id',        'User ID',        'VARCHAR','User who ran the query',                            0,0,0,NULL),
  (4203,'audit_query_log','question',       'Natural Language','VARCHAR','Original NL question from user',                   0,0,0,NULL),
  (4204,'audit_query_log','sql_generated',  'SQL',            'TEXT',   'Generated SQL sent to execution engine',            1,0,0,NULL),
  (4205,'audit_query_log','engine',         'Engine',         'VARCHAR','starrocks,trino,mock',                              0,0,0,'starrocks,trino,mock'),
  (4206,'audit_query_log','row_count',      'Rows Returned',  'INT',    'Number of rows in result',                          1,0,0,NULL),
  (4207,'audit_query_log','execution_ms',   'Execution Time', 'INT',    'Query execution time in milliseconds',              1,0,0,NULL),
  (4208,'audit_query_log','created_at',     'Timestamp',      'DATETIME','When the query was logged',                       0,0,0,NULL);

-- ── Extended dic_relationships ────────────────────────────────────────────────
INSERT INTO dic_relationships (rel_id, from_table, from_column, to_table, to_column, relationship_type, description) VALUES
  -- DDM layer FK chain
  (11,'ddm_account',     'customer_id',  'ddm_customer',  'customer_id', 'FK', 'DDM Account → DDM Customer (owner)'),
  (12,'ddm_transaction', 'account_id',   'ddm_account',   'account_id',  'FK', 'DDM Transaction → DDM Account'),
  (13,'ddm_transaction', 'merchant_id',  'ddm_merchant',  'merchant_id', 'FK', 'DDM Transaction → DDM Merchant'),
  (14,'ddm_card',        'account_id',   'ddm_account',   'account_id',  'FK', 'DDM Card → DDM Account'),
  (15,'ddm_payment',     'account_id',   'ddm_account',   'account_id',  'FK', 'DDM Payment → DDM Account'),
  (16,'ddm_statement',   'account_id',   'ddm_account',   'account_id',  'FK', 'DDM Statement → DDM Account'),
  -- DP → DDM upstream joins
  (17,'dp_customer_balance_snapshot','customer_id','ddm_customer','customer_id','join','DP Balance Snapshot → DDM Customer'),
  (18,'dp_customer_spend_monthly',   'customer_id','ddm_customer','customer_id','join','DP Spend Monthly → DDM Customer'),
  (19,'dp_transaction_enriched',     'account_id', 'ddm_account', 'account_id', 'join','DP Enriched Txns → DDM Account'),
  (20,'dp_payment_status',           'account_id', 'ddm_account', 'account_id', 'join','DP Payment Status → DDM Account'),
  -- DP cross-joins
  (21,'dp_customer_balance_snapshot','customer_id','dp_customer_spend_monthly',  'customer_id','join','Balance Snapshot ↔ Spend Monthly'),
  (22,'dp_customer_spend_monthly',   'customer_id','dp_payment_status',          'customer_id','join','Spend Monthly ↔ Payment Status'),
  -- Semantic → DP / DDM
  (23,'semantic_customer_360',       'customer_id','dp_customer_balance_snapshot','customer_id','join','Customer 360 ← Balance Snapshot'),
  (24,'semantic_customer_360',       'customer_id','dp_customer_spend_monthly',   'customer_id','join','Customer 360 ← Spend Monthly'),
  (25,'semantic_transaction_summary','account_id', 'dp_transaction_enriched',    'account_id', 'join','Txn Summary ← Enriched Txns'),
  (26,'semantic_portfolio_kpis',     'kpi_month',  'dp_portfolio_kpis',          'kpi_month',  'join','Semantic Portfolio KPIs ← DP KPIs'),
  (27,'semantic_risk_metrics',       'metric_date','dp_risk_signals',            'signal_date','join','Risk Metrics ← Risk Signals');

