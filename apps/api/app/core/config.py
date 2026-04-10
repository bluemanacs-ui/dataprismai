# =============================================================================
# DataPrismAI — Application Settings
# =============================================================================
# All settings are read from environment variables.  Defaults work for local
# development with the standard docker-compose stack.
#
# To change a setting:
#   1. Edit apps/api/.env  (local dev)
#   2. Set the corresponding environment variable in your deployment target.
#
# Full list of available variables — see apps/api/.env.example.
# =============================================================================

import os
from dotenv import load_dotenv

# Load .env before reading any os.getenv() defaults so that the values
# in apps/api/.env take effect even when config.py is imported before
# main.py calls load_dotenv().
load_dotenv()

class Settings:
    # ── Application ─────────────────────────────────────────────────────────
    app_name: str = os.getenv("APP_NAME", "DataPrismAI API")

    # ── LLM / Ollama ────────────────────────────────────────────────────────
    # Supported models (comma-separated list shown in /model endpoint)
    #   e.g.  OLLAMA_AVAILABLE_MODELS=qwen2.5:7b,qwen2.5:32b
    ollama_host:             str = os.getenv("OLLAMA_HOST",             "http://localhost:11434")
    ollama_model:            str = os.getenv("OLLAMA_MODEL",            "qwen2.5:32b")
    ollama_general_model:    str = os.getenv("OLLAMA_GENERAL_MODEL",    "qwen2.5:7b")
    ollama_available_models: str = os.getenv("OLLAMA_AVAILABLE_MODELS", "qwen2.5:7b,qwen2.5:32b")

    # ── Vanna SQL ────────────────────────────────────────────────────────────
    use_vanna:   bool = os.getenv("USE_VANNA", "false").lower() == "true"
    vanna_model: str  = os.getenv("VANNA_MODEL", "qwen2.5:32b")

    # ── StarRocks ────────────────────────────────────────────────────────────
    starrocks_host:     str = os.getenv("STARROCKS_HOST",     "localhost")
    starrocks_port:     int = int(os.getenv("STARROCKS_PORT", "9030"))
    starrocks_user:     str = os.getenv("STARROCKS_USER",     "root")
    starrocks_password: str = os.getenv("STARROCKS_PASSWORD", "")
    starrocks_database: str = os.getenv("STARROCKS_DATABASE", "cc_analytics")

    # ── Postgres (operational store) ─────────────────────────────────────────
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://dataprismai:dataprismai@localhost:5432/dataprismai",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins.
    @property
    def allowed_origins(self) -> list[str]:
        raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
        return [o.strip() for o in raw.split(",") if o.strip()]

    # ── Optional integrations ────────────────────────────────────────────────
    superset_url: str = os.getenv("SUPERSET_URL", "http://localhost:8088")


settings = Settings()
