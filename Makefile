.PHONY: api web infra-up infra-down

api:
	cd apps/api && . .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

infra-up:
	cd infra && docker compose up -d

infra-down:
	cd infra && docker compose down
