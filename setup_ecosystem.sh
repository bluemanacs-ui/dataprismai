#!/bin/bash
# Complete DataPrismAI ecosystem setup script

set -e

echo "=== DataPrismAI Local Ecosystem Setup ==="

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker Desktop with WSL2 support."
    exit 1
fi

if ! command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU not detected. Please ensure you have an NVIDIA GPU with proper drivers."
    exit 1
fi

echo "Prerequisites OK."

# Start Docker services
echo "Starting Docker services..."
cd infra
docker compose up -d

echo "Waiting for services to be ready..."
sleep 60

# Check service health
echo "Checking service health..."
docker compose ps

# Install Python dependencies if needed
echo "Installing Python dependencies..."
pip install faker pandas pyarrow psycopg2-binary mysql-connector-python || true

cd ../data/synthetic

# Wait for StarRocks FE to be healthy before loading data
echo "Waiting for StarRocks FE to be healthy..."
MAX_ATTEMPTS=30
SLEEP_SECONDS=10
for ((i=1;i<=MAX_ATTEMPTS;i++)); do
    python3 - <<END
import sys
import mysql.connector
try:
    conn = mysql.connector.connect(host='localhost', port=9030, user='root', password='', connection_timeout=3)
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
END
    if [ $? -eq 0 ]; then
        echo "StarRocks FE is healthy!"
        break
    else
        echo "Attempt $i/$MAX_ATTEMPTS: StarRocks FE not ready yet. Waiting $SLEEP_SECONDS seconds..."
        sleep $SLEEP_SECONDS
    fi
    if [ $i -eq $MAX_ATTEMPTS ]; then
        echo "StarRocks FE did not become healthy in time. Exiting."
        exit 1
    fi
done

# Generate and load all synthetic data into StarRocks (all layers: raw, ddm, dp, semantic)
# Skip if data already exists (idempotent — avoids reloading after laptop restart)
echo "Checking if StarRocks data already exists..."
ROW_COUNT=$(mysql -h 127.0.0.1 -P 9030 -u root --batch --skip-column-names \
  -e "SELECT COUNT(*) FROM cc_analytics.raw_customer" 2>/dev/null || echo "0")

if [ "$ROW_COUNT" -gt "0" ] 2>/dev/null; then
    echo "Data already loaded ($ROW_COUNT customers found). Skipping DDL and data load."
else
    echo "No data found. Creating schema and loading synthetic data..."

    # Create all StarRocks tables in order (DDL first, then data)
    DDL_DIR="/home/acs1980/workspace/dataprismai/data/ddl/starrocks"

    echo "Creating raw CC tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/00_raw_cc_tables.sql" 2>/dev/null || true

    echo "Creating data product tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/01_data_products.sql" 2>/dev/null || true

    echo "Creating metadata tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/03_metadata_tables.sql" 2>/dev/null || true

    echo "Creating data dictionary tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/04_dictionary_tables.sql" 2>/dev/null || true

    echo "Seeding data dictionary..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/05_dictionary_seed.sql" 2>/dev/null || true

    echo "Creating banking raw and DDM tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/10_banking_raw_ddm.sql" 2>/dev/null || true

    echo "Creating banking data product and semantic tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/11_banking_dp_semantic.sql" 2>/dev/null || true

    echo "Creating banking mapping tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/12_banking_mapping.sql" 2>/dev/null || true

    echo "Creating banking audit tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/13_banking_audit.sql" 2>/dev/null || true

    echo "Creating banking deposits and loans tables..."
    mysql -h 127.0.0.1 -P 9030 -u root cc_analytics < "$DDL_DIR/30_banking_deposits_loans.sql" 2>/dev/null || true

    echo "Generating and loading synthetic data..."
    python gen_load.py

    # Load semantic metadata into Postgres (metadata only)
    echo "Loading semantic metadata into Postgres..."
    python ../semantics/load_semantic_data.py
fi

echo "=== Setup Complete! ==="
echo ""
echo "Services running:"
echo "- PostgreSQL: localhost:5432"
echo "- Trino: localhost:8080"
echo "- StarRocks: localhost:9030"
echo "- Ollama: localhost:11434"
echo "- MinIO: localhost:9000"
echo "- API: localhost:8000"
echo "- Web: localhost:3001"
echo ""
echo "Next steps:"
echo "1. Verify Trino UI: http://localhost:8080"
echo "2. Verify StarRocks UI: http://localhost:9030"
echo "3. Test Ollama: curl http://localhost:11434/api/tags"
echo "4. Load data into conformed layer and StarRocks data products"
echo "5. Test DataPrismAI semantic queries"
