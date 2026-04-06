-- Semantic metadata tables for DataPrismAI

CREATE TABLE semantic_metric (
    metric_id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) UNIQUE NOT NULL,
    business_name VARCHAR(255),
    definition TEXT,
    grain VARCHAR(255),
    owner VARCHAR(255),
    default_engine VARCHAR(255),
    sql_expression TEXT,
    status VARCHAR(50) DEFAULT 'active'
);

CREATE TABLE semantic_dimension (
    dimension_id SERIAL PRIMARY KEY,
    dimension_name VARCHAR(255) UNIQUE NOT NULL,
    business_name VARCHAR(255),
    definition TEXT,
    domain VARCHAR(255),
    allowed_values_jsonb JSONB
);

CREATE TABLE semantic_entity (
    entity_id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(255),
    natural_key VARCHAR(255),
    surrogate_key VARCHAR(255)
);

CREATE TABLE semantic_join_path (
    join_path_id SERIAL PRIMARY KEY,
    left_entity VARCHAR(255),
    right_entity VARCHAR(255),
    join_sql TEXT,
    join_type VARCHAR(50),
    approved_flag BOOLEAN DEFAULT true
);

CREATE TABLE semantic_synonym (
    synonym VARCHAR(255) PRIMARY KEY,
    target_type VARCHAR(50),
    target_name VARCHAR(255)
);

CREATE TABLE lineage_edge (
    source_object VARCHAR(255),
    target_object VARCHAR(255),
    relation_type VARCHAR(50),
    PRIMARY KEY (source_object, target_object, relation_type)
);

CREATE TABLE data_product (
    product_name VARCHAR(255) PRIMARY KEY,
    owner VARCHAR(255),
    grain VARCHAR(255),
    engine VARCHAR(255),
    refresh_policy VARCHAR(255),
    sla_minutes INTEGER
);

-- Indexes for performance
CREATE INDEX idx_semantic_metric_name ON semantic_metric(metric_name);
CREATE INDEX idx_semantic_dimension_name ON semantic_dimension(dimension_name);
CREATE INDEX idx_semantic_entity_name ON semantic_entity(entity_name);
CREATE INDEX idx_semantic_synonym_target ON semantic_synonym(target_name);
CREATE INDEX idx_lineage_source ON lineage_edge(source_object);
CREATE INDEX idx_lineage_target ON lineage_edge(target_object);
