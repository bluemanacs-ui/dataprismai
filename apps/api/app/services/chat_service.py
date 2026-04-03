from app.prompts.prompt_builder import build_chat_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.llm_service import generate_with_ollama
from app.services.response_parser import parse_model_json
from app.services.semantic_service import resolve_semantic_context
from app.services.sql_generation_service import generate_sql_from_question
from app.services.sql_validator_service import validate_sql


def _fallback_response(raw_output: str, persona: str, semantic_context: dict) -> ChatQueryResponse:
    sql_result = generate_sql_from_question("fallback", persona, semantic_context)
    is_valid, sql_issues, validated_sql = validate_sql(sql_result.sql)

    return ChatQueryResponse(
        answer=raw_output or "DataPrismAI could not generate a structured response.",
        insights=[
            "Structured parsing failed.",
            "The local model returned unstructured output.",
            "Fallback response has been used.",
        ],
        follow_ups=[
            "Compare by segment",
            "Analyze regional variation",
            "Show time-based breakdown",
        ],
        assumptions=[
            f"Metric inferred as {semantic_context['metric']}.",
            "No real query execution has happened yet.",
        ],
        actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
        chart_title=f"{semantic_context['metric']} Trend",
        chart_type="line",
        sql=validated_sql,
        sql_explanation=sql_result.explanation,
        sql_validation_issues=sql_issues,
        semantic_context={
            "metric": semantic_context["metric"],
            "dimensions": semantic_context["dimensions"],
            "engine": semantic_context["engine"],
            "domain": semantic_context["domain"],
            "definition": semantic_context["definition"],
            "persona": persona,
            "prompt_template_loaded": f"Persona: {persona.capitalize()}",
        },
        raw_model_output=raw_output,
    )


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    semantic_context = resolve_semantic_context(message, persona)

    prompt = build_chat_prompt(message, persona, semantic_context)
    raw_output = generate_with_ollama(prompt)

    sql_result = generate_sql_from_question(message, persona, semantic_context)
    _, sql_issues, validated_sql = validate_sql(sql_result.sql)

    try:
        parsed = parse_model_json(raw_output)

        answer = parsed.get("answer", "").strip()
        insights = parsed.get("insights", [])
        follow_ups = parsed.get("follow_ups", [])
        assumptions = parsed.get("assumptions", [])

        if not answer:
            raise ValueError("Missing answer in parsed response")

        merged_assumptions = assumptions[:5] if isinstance(assumptions, list) else []
        merged_assumptions.extend(sql_result.assumptions[:2])

        return ChatQueryResponse(
            answer=answer,
            insights=insights[:5] if isinstance(insights, list) else [],
            follow_ups=follow_ups[:5] if isinstance(follow_ups, list) else [],
            assumptions=merged_assumptions[:5],
            actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
            chart_title=f"{semantic_context['metric']} Trend",
            chart_type="line",
            sql=validated_sql,
            sql_explanation=sql_result.explanation,
            sql_validation_issues=sql_issues,
            semantic_context={
                "metric": semantic_context["metric"],
                "dimensions": semantic_context["dimensions"],
                "engine": semantic_context["engine"],
                "domain": semantic_context["domain"],
                "definition": semantic_context["definition"],
                "persona": persona,
                "prompt_template_loaded": f"Persona: {persona.capitalize()}",
            },
            raw_model_output=raw_output,
        )
    except Exception:
        return _fallback_response(raw_output, persona, semantic_context)
