# =============================================================================
# DataPrismAI — Prompt Builder
# =============================================================================
# Constructs the system prompt for the LLM from persona text + semantic context.
#
# HOW TO CUSTOMISE THE LLM PROMPT:
#   • Change tone / rules  →  edit this file
#   • Change persona       →  edit apps/api/app/prompts/personas/<name>.txt
#   • Change output schema →  update the JSON shape here AND in schemas/chat.py
# =============================================================================
from app.prompts.persona_loader import load_persona_prompt
from app.services.config_service import config_svc


def build_chat_prompt(message: str, persona: str, semantic_context: dict | None = None) -> str:
    persona_text = load_persona_prompt(persona)
    semantic_context = semantic_context or {}

    metric = semantic_context.get("metric", "Revenue")
    dimensions = ", ".join(semantic_context.get("dimensions", ["Region", "Month"]))
    engine = semantic_context.get("engine", "StarRocks")
    domain = semantic_context.get("domain") or config_svc.get("business.domain_label", "Sales")
    definition = semantic_context.get("definition", "No definition available.")

    identity = config_svc.get("prompt.app_identity", "You are DataPrismAI, an enterprise GenBI insight assistant.")
    biz_context = config_svc.get("business.extra_context", "").strip()
    biz_block = f"\nBusiness context: {biz_context}" if biz_context else ""
    extra_rules = config_svc.get("prompt.insight_extra_rules", "").strip()
    extra_rules_block = ("\n" + "\n".join(f"- {r.strip()}" for r in extra_rules.splitlines() if r.strip())) if extra_rules else ""

    return f"""
{identity}

{persona_text}

Application rules:
- Be concise, useful, and business-relevant
- Do not expose hidden chain-of-thought
- Provide a reasoning summary, not private reasoning
- Stay grounded in the provided semantic context
- If assumptions are needed, state them briefly
- Do not invent unavailable fields or metrics
- Output valid JSON only
- Do not wrap JSON in markdown fences{extra_rules_block}{biz_block}

Semantic context:
- Domain: {domain}
- Metric: {metric}
- Metric definition: {definition}
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
