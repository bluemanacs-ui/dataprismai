import os


class Settings:
    app_name: str = os.getenv("APP_NAME", "DataPrismAI API")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    use_vanna: bool = os.getenv("USE_VANNA", "false").lower() == "true"
    vanna_model: str = os.getenv("VANNA_MODEL", "qwen2.5:7b")


settings = Settings()
