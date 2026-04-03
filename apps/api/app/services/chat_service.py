from app.prompts.prompt_builder import build_chat_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.llm_service import generate_with_ollama


def _default_semantic_context(persona: str) -> dict:
    return {
        "metric": "Revenue",
        "dimensions": ["Region", "Month"],
        "engine": "StarRocks",
        "persona": persona,
    }


def _extract_followups(message: str, persona: str) -> list[str]:
    persona = (persona or "analyst").lower()

    if persona == "cfo":
        return [
            "Show margin trend",
            "Highlight business risks",
            "Compare quarterly variance",
        ]
    if persona == "manager":
        return [
            "Analyze South region",
            "Compare by segment",
            "Show recommended actions",
        ]
    if persona == "product":
        return [
            "Break down by acquisition channel",
            "Compare retention by region",
            "Suggest product experiments",
        ]
    if persona == "engineer":
        return [
            "Inspect semantic mapping",
            "Show SQL plan",
            "Review data assumptions",
        ]
    return [
        "Compare by segment",
        "Analyze South region",
        "Show monthly contribution",
    ]


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    semantic_context = _default_semantic_context(persona)
    prompt = build_chat_prompt(message, persona, semantic_context)
    llm_answer = generate_with_ollama(prompt)

    return ChatQueryResponse(
        answer=llm_answer,
        actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
        follow_ups=_extract_followups(message, persona),
        chart_title="Revenue Trend by Region",
        chart_type="line",
        sql=(
            "SELECT month, region, SUM(revenue) AS revenue\n"
            "FROM sales\n"
            "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
            "GROUP BY month, region\n"
            "ORDER BY month ASC;"
        ),
        insights=[
            "Revenue is up over the selected period.",
            "West region appears strongest.",
            "South region may require investigation.",
        ],
        semantic_context={
            "metric": semantic_context["metric"],
            "dimensions": semantic_context["dimensions"],
            "engine": semantic_context["engine"],
            "persona": persona,
            "prompt_template_loaded": f"Persona: {persona.capitalize()}",
        },
    )
