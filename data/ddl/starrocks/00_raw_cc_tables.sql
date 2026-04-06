-- StarRocks raw tables for credit card data (cc_analytics database)
-- All business data resides in StarRocks

CREATE DATABASE IF NOT EXISTS cc_analytics;

-- Raw customer data
CREATE TABLE IF NOT EXISTS cc_analytics.raw_customers (
    customer_id VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    date_of_birth DATE,
    ssn_last4 INT,
    income_band VARCHAR(50),
    customer_segment VARCHAR(50),
    credit_score INT,
    created_at DATETIME
)
DUPLICATE KEY (customer_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- Raw card accounts
CREATE TABLE IF NOT EXISTS cc_analytics.raw_card_accounts (
    account_id VARCHAR(50),
    customer_id VARCHAR(50),
    product_id VARCHAR(50),
    credit_limit DECIMAL(12,2),
    apr DECIMAL(5,4),
    cycle_day INT,
    open_date DATE,
    close_date DATE,
    status VARCHAR(20),
    created_at DATETIME
)
DUPLICATE KEY (account_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- Raw cards
CREATE TABLE IF NOT EXISTS cc_analytics.raw_cards (
    card_id VARCHAR(50),
    account_id VARCHAR(50),
    card_number_hash VARCHAR(255),
    expiration_date DATE,
    cvv_hash VARCHAR(100),
    issued_date DATE,
    status VARCHAR(20),
    created_at DATETIME
)
DUPLICATE KEY (card_id)
DISTRIBUTED BY HASH(card_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- Raw merchants
CREATE TABLE IF NOT EXISTS cc_analytics.raw_merchants (
    merchant_id VARCHAR(50),
    merchant_name VARCHAR(255),
    merchant_category_code VARCHAR(10),
    address_line1 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    online_offline_flag VARCHAR(10),
    created_at DATETIME
)
DUPLICATE KEY (merchant_id)
DISTRIBUTED BY HASH(merchant_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- Raw transactions - main fact table
CREATE TABLE IF NOT EXISTS cc_analytics.raw_transactions (
    transaction_id VARCHAR(50),
    account_id VARCHAR(50),
    card_id VARCHAR(50),
    merchant_id VARCHAR(50),
    transaction_date DATETIME,
    amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    auth_status VARCHAR(20),
    settlement_status VARCHAR(20),
    interchange_fee DECIMAL(10,4),
    fraud_score DECIMAL(5,4),
    dispute_flag TINYINT DEFAULT "0",
    created_at DATETIME
)
DUPLICATE KEY (transaction_id)
DISTRIBUTED BY HASH(transaction_id) BUCKETS 16
PROPERTIES ("replication_num" = "1");

-- Raw statements (account snapshots)
CREATE TABLE IF NOT EXISTS cc_analytics.raw_statements (
    statement_id VARCHAR(50),
    account_id VARCHAR(50),
    statement_date DATE,
    ending_balance DECIMAL(12,2),
    minimum_due DECIMAL(12,2),
    payment_due_date DATE,
    delinquency_bucket VARCHAR(20),
    revolving_flag TINYINT DEFAULT "0",
    utilization_rate DECIMAL(5,4),
    created_at DATETIME
)
DUPLICATE KEY (statement_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- Raw payments
CREATE TABLE IF NOT EXISTS cc_analytics.raw_payments (
    payment_id VARCHAR(50),
    account_id VARCHAR(50),
    payment_date DATE,
    amount DECIMAL(12,2),
    payment_type VARCHAR(50),
    autopay_flag TINYINT DEFAULT "0",
    created_at DATETIME
)
DUPLICATE KEY (payment_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- Raw disputes
CREATE TABLE IF NOT EXISTS cc_analytics.raw_disputes (
    dispute_id VARCHAR(50),
    transaction_id VARCHAR(50),
    account_id VARCHAR(50),
    dispute_date DATETIME,
    dispute_reason VARCHAR(100),
    amount DECIMAL(12,2),
    status VARCHAR(20),
    created_at DATETIME
)
DUPLICATE KEY (dispute_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");

-- Raw fraud alerts
CREATE TABLE IF NOT EXISTS cc_analytics.raw_fraud_alerts (
    alert_id VARCHAR(50),
    transaction_id VARCHAR(50),
    account_id VARCHAR(50),
    alert_date DATETIME,
    fraud_score DECIMAL(5,4),
    alert_type VARCHAR(50),
    confirmed_fraud TINYINT DEFAULT "0",
    created_at DATETIME
)
DUPLICATE KEY (alert_id)
DISTRIBUTED BY HASH(account_id) BUCKETS 8
PROPERTIES ("replication_num" = "1");
