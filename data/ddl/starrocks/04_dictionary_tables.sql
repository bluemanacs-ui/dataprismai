-- =============================================================================
-- DataPrismAI — Data Dictionary Tables (StarRocks)
-- Database: cc_analytics
-- Tables:   dic_tables, dic_columns, dic_relationships
--
-- Run order: after 03_metadata_tables.sql
-- Run:  mysql -h 127.0.0.1 -P 9030 -u root < data/ddl/starrocks/04_dictionary_tables.sql
-- =============================================================================

USE cc_analytics;

-- ── dic_tables ────────────────────────────────────────────────────────────────
-- One row per logical table entry in the data dictionary.
CREATE TABLE IF NOT EXISTS cc_analytics.dic_tables (
    table_id          INT,
    table_name        VARCHAR(100),
    display_name      VARCHAR(200),
    layer             VARCHAR(50),    -- raw | conformed | semantic
    domain            VARCHAR(100),   -- customer | transaction | payment | risk | ...
    description       VARCHAR(1000),
    row_count_approx  BIGINT DEFAULT "0",
    owner             VARCHAR(100),
    refresh_cadence   VARCHAR(50),    -- daily | monthly | realtime
    is_active         TINYINT DEFAULT "1",
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
)
DUPLICATE KEY (table_id)
DISTRIBUTED BY HASH(table_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── dic_columns ──────────────────────────────────────────────────────────────
-- One row per column, keyed (column_id) to preserve display order.
CREATE TABLE IF NOT EXISTS cc_analytics.dic_columns (
    column_id       INT,
    table_name      VARCHAR(100),
    column_name     VARCHAR(100),
    display_name    VARCHAR(200),
    data_type       VARCHAR(50),
    description     VARCHAR(500),
    is_nullable     TINYINT DEFAULT "1",
    is_primary_key  TINYINT DEFAULT "0",
    is_pii          TINYINT DEFAULT "0",
    enum_values     VARCHAR(500),
    business_rule   VARCHAR(500),
    example_values  VARCHAR(500),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
)
DUPLICATE KEY (column_id)
DISTRIBUTED BY HASH(column_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");

-- ── dic_relationships ────────────────────────────────────────────────────────
-- FK / join relationships between tables (used to build ER model in UI).
CREATE TABLE IF NOT EXISTS cc_analytics.dic_relationships (
    rel_id            INT,
    from_table        VARCHAR(100),
    from_column       VARCHAR(100),
    to_table          VARCHAR(100),
    to_column         VARCHAR(100),
    relationship_type VARCHAR(50),    -- FK | join | derived
    description       VARCHAR(500),
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
)
DUPLICATE KEY (rel_id)
DISTRIBUTED BY HASH(rel_id) BUCKETS 4
PROPERTIES ("replication_num" = "1");
