-- StarRocks data products DDL

-- dp_spend_trend_daily
CREATE TABLE dp_spend_trend_daily (
    date_key INT,
    geography_key INT,
    merchant_category_key INT,
    product_key INT,
    gross_spend DECIMAL(20,2),
    txn_count BIGINT,
    avg_ticket DECIMAL(10,2),
    fraud_flagged_amount DECIMAL(20,2),
    dispute_amount DECIMAL(20,2)
)
DUPLICATE KEY (date_key, geography_key, merchant_category_key, product_key)
DISTRIBUTED BY HASH(date_key) BUCKETS 8
PROPERTIES (
    "replication_num" = "1"
);

-- dp_account_health_monthly
CREATE TABLE dp_account_health_monthly (
    month_key INT,
    account_key INT,
    segment_key INT,
    ending_balance DECIMAL(20,2),
    utilization_rate DECIMAL(5,4),
    payment_rate DECIMAL(5,4),
    min_due_ratio DECIMAL(5,4),
    delinquency_bucket VARCHAR(20),
    chargeoff_risk_score DECIMAL(5,4)
)
DUPLICATE KEY (month_key, account_key, segment_key)
DISTRIBUTED BY HASH(account_key) BUCKETS 8
PROPERTIES (
    "replication_num" = "1"
);

-- dp_fraud_monitoring_hourly
CREATE TABLE dp_fraud_monitoring_hourly (
    hour_key BIGINT,
    merchant_category_key INT,
    channel_key INT,
    region_key INT,
    flagged_txn_count BIGINT,
    flagged_amount DECIMAL(20,2),
    avg_fraud_score DECIMAL(5,4),
    confirmed_fraud_count BIGINT
)
DUPLICATE KEY (hour_key, merchant_category_key, channel_key, region_key)
DISTRIBUTED BY HASH(hour_key) BUCKETS 8
PROPERTIES (
    "replication_num" = "1"
);

-- dp_rewards_profitability_monthly
CREATE TABLE dp_rewards_profitability_monthly (
    month_key INT,
    product_key INT,
    segment_key INT,
    total_spend DECIMAL(20,2),
    interchange_revenue DECIMAL(20,2),
    annual_fee_revenue DECIMAL(20,2),
    rewards_cost DECIMAL(20,2),
    net_profitability DECIMAL(20,2)
)
DUPLICATE KEY (month_key, product_key, segment_key)
DISTRIBUTED BY HASH(product_key) BUCKETS 8
PROPERTIES (
    "replication_num" = "1"
);

-- dp_customer_value_cohort
CREATE TABLE dp_customer_value_cohort (
    cohort_month_key INT,
    customer_segment_key INT,
    product_key INT,
    active_accounts BIGINT,
    retained_accounts BIGINT,
    avg_spend DECIMAL(15,2),
    avg_balance DECIMAL(15,2),
    delinquency_rate DECIMAL(5,4)
)
DUPLICATE KEY (cohort_month_key, customer_segment_key, product_key)
DISTRIBUTED BY HASH(cohort_month_key) BUCKETS 8
PROPERTIES (
    "replication_num" = "1"
);
