#!/usr/bin/env python3
"""
Load semantic metadata into Postgres database.

This script loads the semantic metadata CSV files into the dataprismai database.
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import json

def load_semantic_data(db_config):
    """Load semantic metadata from CSV files"""

    # Connect to database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Load metrics
        metrics_df = pd.read_csv('/home/acs1980/workspace/dataprismai/data/semantics/metrics/metrics.csv')
        metrics_data = []
        for _, row in metrics_df.iterrows():
            metrics_data.append((
                row['metric_name'],
                row['business_name'],
                row['definition'],
                row['grain'],
                row['owner'],
                row['default_engine'],
                row['sql_expression'],
                row['status']
            ))

        # Use ON CONFLICT DO NOTHING to allow repeated runs without failing on duplicates
        execute_values(cursor,
            "INSERT INTO semantic_metric (metric_name, business_name, definition, grain, owner, default_engine, sql_expression, status) VALUES %s ON CONFLICT (metric_name) DO NOTHING",
            metrics_data)

        # Load dimensions
        dimensions_df = pd.read_csv('/home/acs1980/workspace/dataprismai/data/semantics/dimensions/dimensions.csv')
        dimensions_data = []
        for _, row in dimensions_df.iterrows():
            dimensions_data.append((
                row['dimension_name'],
                row['business_name'],
                row['definition'],
                row['domain'],
                row['allowed_values_jsonb']
            ))

        execute_values(cursor,
            "INSERT INTO semantic_dimension (dimension_name, business_name, definition, domain, allowed_values_jsonb) VALUES %s ON CONFLICT (dimension_name) DO NOTHING",
            dimensions_data)

        # Load joins
        joins_df = pd.read_csv('/home/acs1980/workspace/dataprismai/data/semantics/joins/joins.csv')
        joins_data = []
        for _, row in joins_df.iterrows():
            joins_data.append((
                row['left_entity'],
                row['right_entity'],
                row['join_sql'],
                row['join_type'],
                row['approved_flag']
            ))

        execute_values(cursor,
            "INSERT INTO semantic_join_path (left_entity, right_entity, join_sql, join_type, approved_flag) VALUES %s",
            joins_data)

        # Load some sample synonyms
        synonyms_data = [
            ('spend', 'metric', 'total_spend'),
            ('transactions', 'metric', 'txn_count'),
            ('balance', 'metric', 'ending_balance'),
            ('utilization', 'metric', 'utilization_rate'),
            ('fraud', 'metric', 'fraud_flagged_amount'),
            ('location', 'dimension', 'geography'),
            ('category', 'dimension', 'merchant_category'),
            ('product', 'dimension', 'product'),
            ('segment', 'dimension', 'segment')
        ]

        execute_values(cursor,
            "INSERT INTO semantic_synonym (synonym, target_type, target_name) VALUES %s ON CONFLICT (synonym) DO NOTHING",
            synonyms_data)

        # Load sample data products
        products_data = [
            ('dp_spend_trend_daily', 'finance', 'daily', 'StarRocks', 'daily', 24),
            ('dp_account_health_monthly', 'finance', 'monthly', 'StarRocks', 'monthly', 24),
            ('dp_fraud_monitoring_hourly', 'fraud', 'hourly', 'StarRocks', 'hourly', 1),
            ('dp_rewards_profitability_monthly', 'rewards', 'monthly', 'StarRocks', 'monthly', 24),
            ('dp_customer_value_cohort', 'analytics', 'cohort', 'StarRocks', 'monthly', 24)
        ]

        execute_values(cursor,
            "INSERT INTO data_product (product_name, owner, grain, engine, refresh_policy, sla_minutes) VALUES %s ON CONFLICT (product_name) DO NOTHING",
            products_data)

        conn.commit()
        print("Semantic metadata loaded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error loading semantic data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'dataprismai',
        'user': 'dataprismai',
        'password': 'dataprismai'
    }

    load_semantic_data(db_config)
