from ollama import Client
from app.services.config_service import config_svc


def _client() -> Client:
    """Return an Ollama client using the current (possibly overridden) host."""
    return Client(host=config_svc.get("llm.ollama_host"))


def generate_with_ollama(prompt: str, temperature: float | None = None, model: str | None = None) -> str:
    effective_temp = temperature if temperature is not None else config_svc.get_float("llm.temperature", 0.2)
    effective_model = model or config_svc.get("llm.model")
    try:
        response = _client().generate(
            model=effective_model,
            prompt=prompt,
            stream=False,
            options={
                "temperature": effective_temp,
            },
        )
        return response["response"].strip()
    except Exception as exc:
        return (
            "DataPrismAI could not reach the local model runtime. "
            f"Ollama error: {exc}"
        )
