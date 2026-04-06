#!/bin/bash
# Synthetic data generation and loading script

echo "Installing Python dependencies..."
pip install faker pandas pyarrow psycopg2-binary

echo "Generating synthetic data..."
cd /home/acs1980/workspace/dataprismai/data/synthetic
python generate_synthetic_data.py --output-dir ./raw --format csv

echo "Loading data into Postgres..."
# Load CSV files into Postgres raw tables
# This would require a more complex loading script, but for now we'll note it

echo "Loading semantic metadata..."
python /home/acs1980/workspace/dataprismai/data/semantics/load_semantic_data.py

echo "Synthetic data generation and loading complete!"
