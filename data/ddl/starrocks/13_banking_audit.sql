-- =============================================================================
-- DataPrismAI Banking Platform
-- File: 13_banking_audit.sql
-- Purpose: Data quality, data profiling, and pipeline run tracking
-- =============================================================================

-- audit_data_quality: per-table per-run quality checks
DROP TABLE IF EXISTS audit_data_quality;
CREATE TABLE audit_data_quality (
    check_id            BIGINT          NOT NULL,
    check_timestamp     DATETIME        NOT NULL,
    table_name          VARCHAR(100)    NOT NULL,
    layer               VARCHAR(20),               -- RAW | DDM | DP | SEMANTIC
    country_code        VARCHAR(2),
    check_type          VARCHAR(50),               -- ROW_COUNT | NULL_RATE | DUPLICATE | FRESHNESS | SCHEMA | REFERENTIAL
    check_name          VARCHAR(100),              -- e.g. "customer_id NOT NULL"
    expected_value      VARCHAR(100),              -- threshold or expected
    actual_value        VARCHAR(100),              -- observed value
    status              VARCHAR(20),               -- PASS | FAIL | WARNING
    severity            VARCHAR(10),               -- INFO | LOW | MEDIUM | HIGH | CRITICAL
    row_count           BIGINT,
    null_count          BIGINT,
    null_rate           DECIMAL(5,4),
    duplicate_count     BIGINT,
    min_value           VARCHAR(100),
    max_value           VARCHAR(100),
    notes               VARCHAR(300),
    pipeline_run_id     VARCHAR(50)
) DUPLICATE KEY(check_id, check_timestamp)
PARTITION BY RANGE(check_timestamp)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(table_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");


-- audit_data_profile: column-level statistical profiling, run weekly
DROP TABLE IF EXISTS audit_data_profile;
CREATE TABLE audit_data_profile (
    profile_id          BIGINT          NOT NULL,
    profile_date        DATE            NOT NULL,
    table_name          VARCHAR(100)    NOT NULL,
    layer               VARCHAR(20),
    country_code        VARCHAR(2),
    column_name         VARCHAR(100)    NOT NULL,
    data_type           VARCHAR(30),
    total_rows          BIGINT,
    non_null_count      BIGINT,
    null_count          BIGINT,
    null_rate           DECIMAL(5,4),
    distinct_count      BIGINT,
    distinct_rate       DECIMAL(5,4),
    min_value           VARCHAR(200),
    max_value           VARCHAR(200),
    avg_value           DECIMAL(20,4),
    stddev_value        DECIMAL(20,4),
    min_length          INT,
    max_length          INT,
    avg_length          DECIMAL(8,2),
    top_value_1         VARCHAR(100),
    top_value_1_count   BIGINT,
    top_value_2         VARCHAR(100),
    top_value_2_count   BIGINT,
    top_value_3         VARCHAR(100),
    top_value_3_count   BIGINT,
    is_pii              TINYINT         DEFAULT 0,  -- 1 = contains PII (masked in reports)
    pipeline_run_id     VARCHAR(50)
) DUPLICATE KEY(profile_id, profile_date)
PARTITION BY RANGE(profile_date)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(table_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");


-- audit_pipeline_runs: ETL/ELT job tracking for all data layers
DROP TABLE IF EXISTS audit_pipeline_runs;
CREATE TABLE audit_pipeline_runs (
    run_id              VARCHAR(50)     NOT NULL,
    pipeline_name       VARCHAR(100)    NOT NULL,   -- e.g. raw_to_ddm_customer, ddm_to_semantic_spend
    source_layer        VARCHAR(20),               -- RAW | DDM | DP | SEMANTIC
    target_layer        VARCHAR(20),
    source_table        VARCHAR(100),
    target_table        VARCHAR(100),
    country_code        VARCHAR(2),
    start_time          DATETIME        NOT NULL,
    end_time            DATETIME,
    duration_seconds    INT,
    status              VARCHAR(20),               -- RUNNING | SUCCESS | FAILED | PARTIAL | SKIPPED
    rows_read           BIGINT,
    rows_inserted       BIGINT,
    rows_updated        BIGINT,
    rows_deleted        BIGINT,
    rows_rejected       BIGINT,
    error_message       VARCHAR(500),
    error_code          VARCHAR(50),
    retry_count         INT             DEFAULT 0,
    triggered_by        VARCHAR(50),               -- SCHEDULER | MANUAL | API | EVENT
    dag_run_id          VARCHAR(100),              -- Airflow/Prefect run reference
    git_commit          VARCHAR(40)
) DUPLICATE KEY(run_id)
DISTRIBUTED BY HASH(pipeline_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");


-- audit_user_activity: chatbot query audit log for compliance
DROP TABLE IF EXISTS audit_user_activity;
CREATE TABLE audit_user_activity (
    activity_id         BIGINT          NOT NULL,
    activity_timestamp  DATETIME        NOT NULL,
    user_id             VARCHAR(20),
    user_email          VARCHAR(100),
    user_role           VARCHAR(30),
    persona             VARCHAR(30),
    country_code        VARCHAR(2),
    session_id          VARCHAR(50),
    thread_id           VARCHAR(50),
    activity_type       VARCHAR(30),               -- LOGIN | LOGOUT | QUERY | EXPORT | VIEW
    query_text          VARCHAR(1000),             -- user's NL query (masked if PII detected)
    tables_accessed     VARCHAR(300),             -- comma-separated semantic tables queried
    domains_accessed    VARCHAR(100),             -- comma-separated domains
    sql_generated       VARCHAR(2000),            -- generated SQL (truncated)
    rows_returned       INT,
    execution_time_ms   INT,
    status              VARCHAR(20),               -- SUCCESS | DENIED | ERROR
    deny_reason         VARCHAR(100),             -- if DENIED: which access control rule triggered
    ip_address          VARCHAR(45),              -- IPv4 or IPv6
    user_agent          VARCHAR(200)
) DUPLICATE KEY(activity_id, activity_timestamp)
PARTITION BY RANGE(activity_timestamp)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(user_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");


-- audit_access_denied: dedicated log for access control violations
DROP TABLE IF EXISTS audit_access_denied;
CREATE TABLE audit_access_denied (
    denial_id           BIGINT          NOT NULL,
    denial_timestamp    DATETIME        NOT NULL,
    user_id             VARCHAR(20),
    user_email          VARCHAR(100),
    user_role           VARCHAR(30),
    persona             VARCHAR(30),
    requested_table     VARCHAR(100),
    requested_domain    VARCHAR(30),
    requested_country   VARCHAR(2),
    deny_reason         VARCHAR(200),              -- e.g. "Country SG not in user.country_codes [IN]"
    query_text          VARCHAR(1000),
    ip_address          VARCHAR(45),
    session_id          VARCHAR(50)
) DUPLICATE KEY(denial_id, denial_timestamp)
PARTITION BY RANGE(denial_timestamp)(
    PARTITION p2024 VALUES LESS THAN ("2025-01-01"),
    PARTITION p2025 VALUES LESS THAN ("2026-01-01"),
    PARTITION pfuture VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(user_id) BUCKETS 2
PROPERTIES ("replication_num" = "1");
