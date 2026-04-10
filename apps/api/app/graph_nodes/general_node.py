"""General-purpose LLM node — no data context, no guardrails, pure model Q&A."""
from app.services.llm_service import generate_with_ollama
from app.core.config import settings


_SYSTEM_PREAMBLE = (
    "You are a helpful, knowledgeable assistant. "
    "Answer the user's question clearly and concisely. "
    "You can help with any topic — coding, writing, reasoning, general knowledge, math, etc. "
    "Use markdown formatting: **bold** for key terms, numbered/bullet lists where helpful, "
    "code blocks for code snippets. Keep responses focused and well-structured."
)


def general_node(state: dict) -> dict:
    """Bypass the entire analytics pipeline and answer via raw LLM."""
    message = state.get("user_message") or ""
    model = settings.ollama_general_model
    prompt = f"{_SYSTEM_PREAMBLE}\n\nUser: {message}\n\nAssistant:"
    answer = generate_with_ollama(prompt, temperature=0.7, model=model)
    return {
        "answer": answer,
        "intent_type": "general",
        "response_mode": "general",
        "reasoning_steps": [],
        "answer_llm_used": True,
        "model_used": model,
    }
