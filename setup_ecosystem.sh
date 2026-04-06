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

# Generate synthetic data
echo "Generating synthetic data..."
cd ../data/synthetic

# Install Python dependencies if needed
pip install faker pandas pyarrow psycopg2-binary mysql-connector-python || true


# Generate data
python generate_synthetic_data.py --output-dir ./raw --format csv

# Wait for StarRocks FE to be healthy before loading data (Python-based check)
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

# Load synthetic data into StarRocks (business data)
echo "Loading synthetic data into StarRocks..."
python load_to_starrocks.py

# Load semantic metadata into Postgres (metadata only)
echo "Loading semantic metadata into Postgres..."
python ../semantics/load_semantic_data.py

# Bootstrap StarRocks
echo "Bootstrapping StarRocks..."
docker exec dataprismai-starrocks-fe /opt/starrocks/bootstrap.sh

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
