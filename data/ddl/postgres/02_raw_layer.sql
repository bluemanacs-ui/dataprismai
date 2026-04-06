-- Raw layer tables for credit card data

CREATE SCHEMA IF NOT EXISTS raw;

-- Raw customer data
CREATE TABLE raw.customers (
    customer_id VARCHAR(50) PRIMARY KEY,
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
    ssn_last4 VARCHAR(4),
    income_band VARCHAR(50),
    customer_segment VARCHAR(50),
    credit_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw card accounts
CREATE TABLE raw.card_accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    product_id VARCHAR(50),
    credit_limit DECIMAL(12,2),
    apr DECIMAL(5,4),
    cycle_day INTEGER,
    open_date DATE,
    close_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw cards
CREATE TABLE raw.cards (
    card_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    card_number_hash VARCHAR(64),
    expiration_date DATE,
    cvv_hash VARCHAR(64),
    issued_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw merchants
CREATE TABLE raw.merchants (
    merchant_id VARCHAR(50) PRIMARY KEY,
    merchant_name VARCHAR(255),
    merchant_category_code VARCHAR(10),
    address_line1 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    online_offline_flag VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw transactions
CREATE TABLE raw.transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    card_id VARCHAR(50),
    merchant_id VARCHAR(50),
    transaction_date TIMESTAMP,
    amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    auth_status VARCHAR(20),
    settlement_status VARCHAR(20),
    interchange_fee DECIMAL(8,2),
    fraud_score DECIMAL(5,4),
    dispute_flag BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw authorizations
CREATE TABLE raw.authorizations (
    auth_id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(50),
    account_id VARCHAR(50),
    merchant_id VARCHAR(50),
    auth_date TIMESTAMP,
    amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    response_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw settlements
CREATE TABLE raw.settlements (
    settlement_id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(50),
    settlement_date TIMESTAMP,
    amount DECIMAL(12,2),
    interchange_fee DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw statements
CREATE TABLE raw.statements (
    statement_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    statement_date DATE,
    ending_balance DECIMAL(12,2),
    minimum_due DECIMAL(12,2),
    payment_due_date DATE,
    delinquency_bucket VARCHAR(20),
    revolving_flag BOOLEAN,
    utilization_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw payments
CREATE TABLE raw.payments (
    payment_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    payment_date DATE,
    amount DECIMAL(12,2),
    payment_type VARCHAR(50),
    autopay_flag BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw fees
CREATE TABLE raw.fees (
    fee_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    fee_date DATE,
    fee_type VARCHAR(50),
    amount DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw disputes
CREATE TABLE raw.disputes (
    dispute_id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(50),
    account_id VARCHAR(50),
    dispute_date DATE,
    dispute_reason VARCHAR(255),
    amount DECIMAL(12,2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw fraud alerts
CREATE TABLE raw.fraud_alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(50),
    account_id VARCHAR(50),
    alert_date TIMESTAMP,
    fraud_score DECIMAL(5,4),
    alert_type VARCHAR(50),
    confirmed_fraud BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw rewards events
CREATE TABLE raw.rewards_events (
    event_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    event_date DATE,
    event_type VARCHAR(50),
    points_earned INTEGER,
    points_redeemed INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw delinquency snapshots
CREATE TABLE raw.delinquency_snapshots (
    snapshot_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    snapshot_date DATE,
    days_past_due INTEGER,
    delinquency_bucket VARCHAR(20),
    chargeoff_flag BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
