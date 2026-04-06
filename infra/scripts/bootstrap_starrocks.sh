#!/bin/bash
# StarRocks bootstrap script

set -e

echo "Waiting for StarRocks FE to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8030/api/health | grep -qi "ok"; then
    echo "StarRocks FE healthy"
    break
  fi
  echo "Waiting for FE health... ($i/30)"
  sleep 5
done

if ! curl -s http://localhost:8030/api/health | grep -qi "ok"; then
  echo "StarRocks FE did not become healthy"
  exit 1
fi

DDL_FILE=/tmp/01_data_products.sql
if [ ! -f "$DDL_FILE" ]; then
  echo "DDL file not found: $DDL_FILE"
  exit 1
fi

echo "Creating database and data product tables..."

mysql -h 127.0.0.1 -P 9030 -u root -e "CREATE DATABASE IF NOT EXISTS cc_analytics;"
mysql -h 127.0.0.1 -P 9030 -u root -D cc_analytics -e "source $DDL_FILE"

echo "StarRocks bootstrap complete!"
