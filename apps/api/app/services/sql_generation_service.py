from app.prompts.sql_prompt_builder import build_sql_prompt
from app.schemas.sql import SQLGenerationResult
from app.services.llm_service import generate_with_ollama
from app.services.response_parser import parse_model_json


def generate_sql_from_question(message: str, persona: str, semantic_context: dict) -> SQLGenerationResult:
    prompt = build_sql_prompt(message, persona, semantic_context)
    raw_output = generate_with_ollama(prompt)

    try:
        parsed = parse_model_json(raw_output)

        sql = parsed.get("sql", "").strip()
        explanation = parsed.get("explanation", "").strip()
        assumptions = parsed.get("assumptions", [])

        if not sql:
            raise ValueError("Missing sql in model response")

        return SQLGenerationResult(
            sql=sql,
            explanation=explanation or "SQL generated from semantic context.",
            assumptions=assumptions if isinstance(assumptions, list) else [],
        )
    except Exception:
        metric = semantic_context["metric"].lower().replace(" ", "_")
        first_dimension = semantic_context["dimensions"][0].lower().replace(" ", "_")
        fallback_sql = (
            f"SELECT month, {first_dimension}, SUM({metric}) AS value\n"
            f"FROM semantic_model_table\n"
            f"GROUP BY month, {first_dimension}\n"
            f"ORDER BY month ASC;"
        )
        return SQLGenerationResult(
            sql=fallback_sql,
            explanation="Fallback SQL was generated because structured SQL parsing failed.",
            assumptions=[
                "Fallback SQL pattern was used.",
                "Semantic context dimensions were applied directly.",
            ],
        )
