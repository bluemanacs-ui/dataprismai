# DataPrismAI Local Ecosystem (WSL2 + Docker)

This infra supports the design described in your second tech spec.

## Requirements

- Windows + WSL2 (Ubuntu)
- Docker Desktop (WSL2 backend)
- NVIDIA GPU + CUDA-for-WSL driver

## Quick validation in WSL

```bash
wsl --status
wsl --update
nvidia-smi
docker version
docker compose version
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

## Start stack

```bash
cd infra
docker compose up -d --build
```

## Services and ports

- Postgres: 5432
- Trino: 8080
- StarRocks FE: 9030, 8030
- StarRocks BE: 8040, 8060
- Ollama: 11434
- MinIO: 9000, 9001
- Redis: 6379
- API: 8000
- Web: 3001

## Data Generation and Loading

1. **Generate synthetic data**:

   ```bash
   cd ../data/synthetic
   pip install faker pandas pyarrow psycopg2-binary
   python generate_synthetic_data.py --output-dir ./raw --format csv
   ```

2. **Load semantic metadata**:

   ```bash
   python ../semantics/load_semantic_data.py
   ```

3. **Bootstrap StarRocks tables**:
   ```bash
   docker exec dataprismai-starrocks-fe /opt/starrocks/bootstrap.sh
   ```

## Postgres bootstrap entities (recommended)

- semantic_metric
- semantic_dimension
- semantic_entity
- semantic_join_path
- semantic_synonym
- lineage_edge
- data_product

## Next steps

1. Load synthetic data into Postgres raw tables
2. Create conformed dimensions and facts
3. Load data products into StarRocks
4. Configure Trino catalogs for data access
5. Test semantic resolution in DataPrismAI API
6. Add DataPrismAI semantic resolver to API service.
