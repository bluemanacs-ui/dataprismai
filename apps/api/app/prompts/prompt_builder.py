from app.prompts.persona_loader import load_persona_prompt


def build_chat_prompt(message: str, persona: str, semantic_context: dict | None = None) -> str:
    persona_text = load_persona_prompt(persona)
    semantic_context = semantic_context or {}

    metric = semantic_context.get("metric", "Revenue")
    dimensions = ", ".join(semantic_context.get("dimensions", ["Region", "Month"]))
    engine = semantic_context.get("engine", "StarRocks")

    return f"""
You are DataPrismAI, an enterprise GenBI insight assistant.

{persona_text}

Application rules:
- Be concise, useful, and business-relevant
- Do not expose hidden chain-of-thought
- Provide a reasoning summary, not private reasoning
- Stay grounded in the provided semantic context
- If assumptions are needed, state them briefly
- Do not invent unavailable data fields
- Output valid JSON only
- Do not wrap JSON in markdown fences

Semantic context:
- Metric: {metric}
- Dimensions: {dimensions}
- Engine: {engine}

User question:
{message}

Return JSON with exactly this shape:
{{
  "answer": "string",
  "insights": ["string", "string", "string"],
  "follow_ups": ["string", "string", "string"],
  "assumptions": ["string", "string"]
}}
""".strip()
