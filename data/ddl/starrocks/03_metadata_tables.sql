-- StarRocks metadata + audit tables
-- All semantic catalog data, join paths, and query audit live here.
-- Uses DUPLICATE KEY for append-friendly bulk loads and single-replica dev config.

CREATE DATABASE IF NOT EXISTS cc_analytics;

-- ── Semantic metrics catalog ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cc_analytics.semantic_metrics (
    metric_name    VARCHAR(100),
    business_name  VARCHAR(200),
    definition     VARCHAR(1000),
    grain          VARCHAR(50),
    owner          VARCHAR(100),
    default_engine VARCHAR(50),
    sql_expression VARCHAR(500),
    status         VARCHAR(20) DEFAULT 'active',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
)
DUPLICATE KEY (metric_name)
DISTRIBUTED BY HASH(metric_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── Semantic dimensions catalog ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cc_analytics.semantic_dimensions (
    dimension_name  VARCHAR(100),
    business_name   VARCHAR(200),
    definition      VARCHAR(1000),
    domain          VARCHAR(100),
    allowed_values  VARCHAR(2000),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
)
DUPLICATE KEY (dimension_name)
DISTRIBUTED BY HASH(dimension_name) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── Semantic join paths ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cc_analytics.semantic_joins (
    left_entity    VARCHAR(100),
    right_entity   VARCHAR(100),
    join_sql       VARCHAR(500),
    join_type      VARCHAR(20),
    approved_flag  TINYINT DEFAULT "1",
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
)
DUPLICATE KEY (left_entity, right_entity)
DISTRIBUTED BY HASH(left_entity) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── Query audit log ──────────────────────────────────────────────────────────
-- High write throughput via append-only DUPLICATE KEY distribution.
CREATE TABLE IF NOT EXISTS cc_analytics.query_audit_log (
    log_id           BIGINT,
    thread_id        VARCHAR(100),
    user_id          VARCHAR(100),
    user_message     VARCHAR(2000),
    generated_sql    VARCHAR(4000),
    engine           VARCHAR(50),
    row_count        INT DEFAULT "0",
    execution_time_ms INT DEFAULT "0",
    status           VARCHAR(20) DEFAULT 'success',
    error_message    VARCHAR(500),
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
)
DUPLICATE KEY (log_id)
DISTRIBUTED BY HASH(log_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");
