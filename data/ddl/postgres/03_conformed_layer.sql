-- Conformed layer tables for credit card data

CREATE SCHEMA IF NOT EXISTS conformed;

-- Conformed dimensions
CREATE TABLE conformed.dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE,
    customer_segment VARCHAR(50),
    age_band VARCHAR(20),
    income_band VARCHAR(50),
    geography_key INTEGER,
    risk_segment_id VARCHAR(50),
    open_date DATE,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_card_account (
    account_key SERIAL PRIMARY KEY,
    account_id VARCHAR(50) UNIQUE,
    customer_key INTEGER REFERENCES conformed.dim_customer(customer_key),
    product_key INTEGER,
    credit_limit DECIMAL(12,2),
    apr DECIMAL(5,4),
    cycle_day INTEGER,
    open_date DATE,
    close_date DATE,
    status VARCHAR(20),
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_card (
    card_key SERIAL PRIMARY KEY,
    card_id VARCHAR(50) UNIQUE,
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    card_number_hash VARCHAR(64),
    expiration_date DATE,
    issued_date DATE,
    status VARCHAR(20),
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_merchant (
    merchant_key SERIAL PRIMARY KEY,
    merchant_id VARCHAR(50) UNIQUE,
    merchant_name VARCHAR(255),
    merchant_category_key INTEGER,
    geography_key INTEGER,
    online_offline_flag VARCHAR(10),
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_merchant_category (
    merchant_category_key SERIAL PRIMARY KEY,
    merchant_category_code VARCHAR(10) UNIQUE,
    category_name VARCHAR(100),
    category_description TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_geography (
    geography_key SERIAL PRIMARY KEY,
    country VARCHAR(50),
    state VARCHAR(50),
    city VARCHAR(100),
    zip_code VARCHAR(20),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_channel (
    channel_key SERIAL PRIMARY KEY,
    channel_name VARCHAR(50) UNIQUE,
    channel_description TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_device (
    device_key SERIAL PRIMARY KEY,
    device_type VARCHAR(50) UNIQUE,
    device_description TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_risk_segment (
    risk_segment_key SERIAL PRIMARY KEY,
    risk_segment_id VARCHAR(50) UNIQUE,
    segment_name VARCHAR(100),
    min_score INTEGER,
    max_score INTEGER,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE,
    product_name VARCHAR(100),
    product_type VARCHAR(50),
    annual_fee DECIMAL(8,2),
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT true
);

CREATE TABLE conformed.dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(10),
    month_name VARCHAR(10),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT false
);

-- Conformed facts
CREATE TABLE conformed.fact_card_transaction (
    transaction_key SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE,
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    card_key INTEGER REFERENCES conformed.dim_card(card_key),
    merchant_key INTEGER REFERENCES conformed.dim_merchant(merchant_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    channel_key INTEGER REFERENCES conformed.dim_channel(channel_key),
    device_key INTEGER REFERENCES conformed.dim_device(device_key),
    amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    auth_status VARCHAR(20),
    settlement_status VARCHAR(20),
    interchange_fee DECIMAL(8,2),
    fraud_score DECIMAL(5,4),
    dispute_flag BOOLEAN DEFAULT false
);

CREATE TABLE conformed.fact_authorization (
    auth_key SERIAL PRIMARY KEY,
    auth_id VARCHAR(50) UNIQUE,
    transaction_key INTEGER REFERENCES conformed.fact_card_transaction(transaction_key),
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    merchant_key INTEGER REFERENCES conformed.dim_merchant(merchant_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    response_code VARCHAR(10)
);

CREATE TABLE conformed.fact_settlement (
    settlement_key SERIAL PRIMARY KEY,
    settlement_id VARCHAR(50) UNIQUE,
    transaction_key INTEGER REFERENCES conformed.fact_card_transaction(transaction_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    amount DECIMAL(12,2),
    interchange_fee DECIMAL(8,2)
);

CREATE TABLE conformed.fact_statement_snapshot (
    statement_key SERIAL PRIMARY KEY,
    statement_id VARCHAR(50) UNIQUE,
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    ending_balance DECIMAL(12,2),
    minimum_due DECIMAL(12,2),
    payment_due_date_key INTEGER REFERENCES conformed.dim_date(date_key),
    delinquency_bucket VARCHAR(20),
    revolving_flag BOOLEAN,
    utilization_rate DECIMAL(5,4)
);

CREATE TABLE conformed.fact_payment (
    payment_key SERIAL PRIMARY KEY,
    payment_id VARCHAR(50) UNIQUE,
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    amount DECIMAL(12,2),
    payment_type VARCHAR(50),
    autopay_flag BOOLEAN DEFAULT false
);

CREATE TABLE conformed.fact_fee (
    fee_key SERIAL PRIMARY KEY,
    fee_id VARCHAR(50) UNIQUE,
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    fee_type VARCHAR(50),
    amount DECIMAL(8,2)
);

CREATE TABLE conformed.fact_dispute (
    dispute_key SERIAL PRIMARY KEY,
    dispute_id VARCHAR(50) UNIQUE,
    transaction_key INTEGER REFERENCES conformed.fact_card_transaction(transaction_key),
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    dispute_reason VARCHAR(255),
    amount DECIMAL(12,2),
    status VARCHAR(20)
);

CREATE TABLE conformed.fact_fraud_alert (
    alert_key SERIAL PRIMARY KEY,
    alert_id VARCHAR(50) UNIQUE,
    transaction_key INTEGER REFERENCES conformed.fact_card_transaction(transaction_key),
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    fraud_score DECIMAL(5,4),
    alert_type VARCHAR(50),
    confirmed_fraud BOOLEAN DEFAULT false
);

CREATE TABLE conformed.fact_rewards_event (
    event_key SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE,
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    event_type VARCHAR(50),
    points_earned INTEGER,
    points_redeemed INTEGER
);

CREATE TABLE conformed.fact_delinquency_snapshot (
    snapshot_key SERIAL PRIMARY KEY,
    snapshot_id VARCHAR(50) UNIQUE,
    account_key INTEGER REFERENCES conformed.dim_card_account(account_key),
    date_key INTEGER REFERENCES conformed.dim_date(date_key),
    days_past_due INTEGER,
    delinquency_bucket VARCHAR(20),
    chargeoff_flag BOOLEAN DEFAULT false
);
