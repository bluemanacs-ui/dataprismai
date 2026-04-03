from app.prompts.prompt_builder import build_chat_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.llm_service import generate_with_ollama
from app.services.response_parser import parse_model_json


def _default_semantic_context(persona: str) -> dict:
    return {
        "metric": "Revenue",
        "dimensions": ["Region", "Month"],
        "engine": "StarRocks",
        "persona": persona,
    }


def _fallback_response(raw_output: str, persona: str, semantic_context: dict) -> ChatQueryResponse:
    return ChatQueryResponse(
        answer=raw_output or "DataPrismAI could not generate a structured response.",
        insights=[
            "Structured parsing failed.",
            "The local model returned unstructured output.",
            "Fallback response has been used.",
        ],
        follow_ups=[
            "Compare by segment",
            "Analyze South region",
            "Show monthly contribution",
        ],
        assumptions=[
            "Default semantic context was used.",
            "No real query execution has happened yet.",
        ],
        actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
        chart_title="Revenue Trend by Region",
        chart_type="line",
        sql=(
            "SELECT month, region, SUM(revenue) AS revenue\n"
            "FROM sales\n"
            "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
            "GROUP BY month, region\n"
            "ORDER BY month ASC;"
        ),
        semantic_context={
            "metric": semantic_context["metric"],
            "dimensions": semantic_context["dimensions"],
            "engine": semantic_context["engine"],
            "persona": persona,
            "prompt_template_loaded": f"Persona: {persona.capitalize()}",
        },
        raw_model_output=raw_output,
    )


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    semantic_context = _default_semantic_context(persona)
    prompt = build_chat_prompt(message, persona, semantic_context)
    raw_output = generate_with_ollama(prompt)

    try:
        parsed = parse_model_json(raw_output)

        answer = parsed.get("answer", "").strip()
        insights = parsed.get("insights", [])
        follow_ups = parsed.get("follow_ups", [])
        assumptions = parsed.get("assumptions", [])

        if not answer:
            raise ValueError("Missing answer in parsed response")

        return ChatQueryResponse(
            answer=answer,
            insights=insights[:5] if isinstance(insights, list) else [],
            follow_ups=follow_ups[:5] if isinstance(follow_ups, list) else [],
            assumptions=assumptions[:5] if isinstance(assumptions, list) else [],
            actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
            chart_title="Revenue Trend by Region",
            chart_type="line",
            sql=(
                "SELECT month, region, SUM(revenue) AS revenue\n"
                "FROM sales\n"
                "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
                "GROUP BY month, region\n"
                "ORDER BY month ASC;"
            ),
            semantic_context={
                "metric": semantic_context["metric"],
                "dimensions": semantic_context["dimensions"],
                "engine": semantic_context["engine"],
                "persona": persona,
                "prompt_template_loaded": f"Persona: {persona.capitalize()}",
            },
            raw_model_output=raw_output,
        )
    except Exception:
        return _fallback_response(raw_output, persona, semantic_context)
