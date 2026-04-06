from app.prompts.prompt_builder import build_chat_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chart_service import build_chart_recommendations
from app.services.llm_service import generate_with_ollama
from app.services.query_executor_service import execute_query
from app.services.response_parser import parse_model_json
from app.services.semantic_service import resolve_semantic_context
from app.services.sql_generation_service import generate_sql_from_question
from app.services.sql_validator_service import validate_sql


def _build_insight_recommendations(semantic_context: dict) -> list[str]:
    metric = semantic_context.get("metric", "Revenue")
    dimensions = semantic_context.get("dimensions", [])

    recommendations = [
        f"Analyze {metric} trend by region",
        f"Compare {metric} by segment",
        f"Show {metric} evolution by month",
    ]

    if "product" in [d.lower() for d in dimensions]:
        recommendations.append(f"Break down {metric} by product")

    return recommendations[:4]


def _build_response(
    answer: str,
    insights: list[str],
    follow_ups: list[str],
    assumptions: list[str],
    persona: str,
    semantic_context: dict,
    raw_output: str | None,
    message_for_sql: str,
) -> ChatQueryResponse:
    sql_result = generate_sql_from_question(message_for_sql, persona, semantic_context)
    _, sql_issues, validated_sql = validate_sql(sql_result.sql)
    execution_result = execute_query(semantic_context["engine"], validated_sql, semantic_context)
    primary_chart, chart_recommendations = build_chart_recommendations(
        result_columns=execution_result.columns,
        result_rows=execution_result.rows,
        semantic_context=semantic_context,
    )

    merged_assumptions = assumptions[:5]
    merged_assumptions.extend(sql_result.assumptions[:2])

    return ChatQueryResponse(
        answer=answer,
        insights=insights[:5],
        insight_recommendations=_build_insight_recommendations(semantic_context),
        follow_ups=follow_ups[:5],
        assumptions=merged_assumptions[:5],
        actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
        chart_title=primary_chart.title,
        chart_type=primary_chart.chart_type,
        chart_config=primary_chart.model_dump(),
        chart_recommendations=[rec.model_dump() for rec in chart_recommendations],
        sql=validated_sql,
        sql_explanation=sql_result.explanation,
        sql_validation_issues=sql_issues,
        result_columns=execution_result.columns,
        result_rows=execution_result.rows,
        result_row_count=execution_result.row_count,
        result_engine=execution_result.engine,
        result_execution_time_ms=execution_result.execution_time_ms,
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


def _fallback_response(raw_output: str, persona: str, semantic_context: dict) -> ChatQueryResponse:
    return _build_response(
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
            "Mock query execution was used.",
        ],
        persona=persona,
        semantic_context=semantic_context,
        raw_output=raw_output,
        message_for_sql="fallback",
    )


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    semantic_context = resolve_semantic_context(message, persona)

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

        return _build_response(
            answer=answer,
            insights=insights if isinstance(insights, list) else [],
            follow_ups=follow_ups if isinstance(follow_ups, list) else [],
            assumptions=assumptions if isinstance(assumptions, list) else [],
            persona=persona,
            semantic_context=semantic_context,
            raw_output=raw_output,
            message_for_sql=message,
        )
    except Exception:
        return _fallback_response(raw_output, persona, semantic_context)
