from ollama import Client
from app.core.config import settings


client = Client(host=settings.ollama_host)


def generate_with_ollama(prompt: str, temperature: float = 0.2) -> str:
    try:
        response = client.generate(
            model=settings.ollama_model,
            prompt=prompt,
            stream=False,
            options={
                "temperature": temperature,
            },
        )
        return response["response"].strip()
    except Exception as exc:
        return (
            "DataPrismAI could not reach the local model runtime. "
            f"Ollama error: {exc}"
        )
