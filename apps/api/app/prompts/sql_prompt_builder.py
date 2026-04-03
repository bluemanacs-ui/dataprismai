def build_sql_prompt(message: str, persona: str, semantic_context: dict) -> str:
    metric = semantic_context.get("metric", "Revenue")
    dimensions = ", ".join(semantic_context.get("dimensions", ["Region", "Month"]))
    engine = semantic_context.get("engine", "StarRocks")
    domain = semantic_context.get("domain", "Sales")
    definition = semantic_context.get("definition", "No definition available.")

    return f"""
You are DataPrismAI, an enterprise GenBI SQL generation assistant.

Rules:
- Generate SQL only
- Output valid JSON only
- Do not wrap JSON in markdown fences
- Only generate read-only SELECT SQL
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE
- Use semantic context faithfully
- Prefer simple, explainable SQL
- Use snake_case column naming when needed
- Assume a semantic table name of semantic_model_table unless otherwise specified

Semantic context:
- Domain: {domain}
- Metric: {metric}
- Definition: {definition}
- Dimensions: {dimensions}
- Engine: {engine}

User question:
{message}

Return JSON exactly like:
{{
  "sql": "string",
  "explanation": "string",
  "assumptions": ["string", "string"]
}}
""".strip()
