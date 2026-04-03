.PHONY: api web infra-up infra-down

api:
docker-compose.yml cd apps/api && . .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

web:
docker-compose.yml cd apps/web && npm run dev

infra-up:
docker-compose.yml cd infra && docker compose up -d

infra-down:
docker-compose.yml cd infra && docker compose down
