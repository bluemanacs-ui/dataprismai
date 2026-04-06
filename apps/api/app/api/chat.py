# =============================================================================
# DataPrismAI — /chat API Router
# =============================================================================
# Exposes the primary natural-language analytics endpoint.
#
# POST /chat/query  — accepts a user message + persona + thread_id and returns
#                     a full ChatQueryResponse: answer, insights, SQL, chart,
#                     KPIs, follow-ups, and reasoning steps.
#
# The route delegates to the compiled LangGraph (graph_runtime.py) which runs
# the full 13-node agentic pipeline.
# =============================================================================
import uuid
import random
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.graph_runtime import compiled_graph
from app.graph_nodes.recommendation_node import (
    _METRIC_FOLLOW_UPS,
    _METRIC_INSIGHT_RECS,
    _PERSONA_DEFAULTS,
    _DEFAULT_PERSONA,
)
from app.services.llm_service import generate_with_ollama
from app.semantic.catalog import _HARDCODED_CATALOG
from app.core.config import settings as app_settings

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest) -> ChatQueryResponse:
    thread_id = payload.thread_id or str(uuid.uuid4())
    workspace_id = payload.workspace_id or payload.workspace or "default"

    initial_state = {
        "thread_id": thread_id,
        "user_id": payload.user_id,
        "workspace_id": workspace_id,
        "persona": payload.persona,
        "user_message": payload.message,
        "time_range": payload.time_range,
    }

    final_state = compiled_graph.invoke(initial_state)

    qr = final_state.get("query_result") or {}
    sc = final_state.get("semantic_context") or {}
    vc = final_state.get("visualization_config") or {}

    # Build legacy chart_config for backwards-compatible clients
    chart_config: dict = {}
    chart_recommendations: list = []
    if vc:
        chart_config = vc.get("payload") or {}
        chart_recommendations = [
            r.get("payload") or r
            for r in (final_state.get("visualization_recommendations") or [])
        ]

    return ChatQueryResponse(
        answer=final_state.get("answer") or "",
        thread_id=thread_id,
        report_id=final_state.get("report_id"),
        intent_type=final_state.get("intent_type") or "metric_query",
        response_mode=final_state.get("response_mode") or "metric",
        literal_table_name=final_state.get("literal_table_name") or "",
        insights=final_state.get("insights") or [],
        bottlenecks=final_state.get("bottlenecks") or [],
        highlight_actions=final_state.get("highlight_actions") or [],
        kpi_metrics=final_state.get("kpi_metrics") or [],
        insight_recommendations=final_state.get("insight_recommendations") or [],
        follow_ups=final_state.get("follow_ups") or [],
        assumptions=final_state.get("assumptions") or [],
        actions=[],
        chart_title=vc.get("title") or "",
        chart_type=vc.get("visualization_type") or "",
        chart_config=chart_config,
        chart_recommendations=chart_recommendations,
        visualization_config=vc or None,
        visualization_recommendations=final_state.get("visualization_recommendations"),
        sql=final_state.get("generated_sql") or "",
        sql_explanation=final_state.get("sql_explanation") or "",
        sql_validation_issues=final_state.get("sql_validation_issues") or [],
        result_columns=qr.get("columns") or [],
        result_rows=qr.get("rows") or [],
        result_row_count=qr.get("row_count") or 0,
        result_engine=final_state.get("target_engine") or "",
        result_execution_time_ms=qr.get("execution_time_ms") or 0,
        semantic_context=sc,
        reasoning_steps=final_state.get("reasoning_steps") or [],
        model_used=app_settings.ollama_model,
        raw_model_output=None,
    )


# ── Suggestions refresh endpoint ─────────────────────────────────────────────

class SuggestionsRequest(BaseModel):
    persona: str = "analyst"
    metric: str = ""
    answer_snippet: str = ""
    exclude_recs: List[str] = []
    exclude_fus: List[str] = []


class SuggestionsResponse(BaseModel):
    insight_recommendations: List[str]
    follow_ups: List[str]


_SUGGESTIONS_PROMPT = """\
You are a data analytics assistant helping a {persona} explore a credit card banking analytics platform.

STRICT CONSTRAINT — only suggest questions that use the metrics and dimensions listed below.
Do NOT invent metrics, tables, or fields that are not in this list.

Available metrics (use ONLY these):
{available_metrics}

Available dimensions (use ONLY these):
{available_dimensions}

Context for this response:
- Matched metric: {metric}
- Response summary: {answer_snippet}

Already shown to this user (do NOT repeat any of these):
{shown_items}

Generate EXACTLY 3 insight recommendations and EXACTLY 3 follow-up questions.
- Insight recommendations: short analytical observations about the available data worth investigating.
- Follow-up questions: concise natural-language queries the user can ask next, using only the available metrics/dimensions above.

Respond in this EXACT format with no extra text:
INSIGHT_RECS:
1. <recommendation>
2. <recommendation>
3. <recommendation>
FOLLOW_UPS:
1. <question>
2. <question>
3. <question>"""


# Pre-build catalog constraint strings once at import time
_CATALOG_METRICS = "\n".join(
    f"- {m['name']}: dimensions [{', '.join(m['dimensions'])}]"
    for m in _HARDCODED_CATALOG["metrics"]
)
_CATALOG_DIMENSIONS = ", ".join(d["name"] for d in _HARDCODED_CATALOG["dimensions"])


def _parse_llm_suggestions(text: str) -> tuple[list[str], list[str]]:
    """Parse INSIGHT_RECS / FOLLOW_UPS sections from LLM output."""
    recs: list[str] = []
    fus: list[str] = []
    in_recs = in_fus = False
    for line in text.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("INSIGHT_RECS"):
            in_recs, in_fus = True, False
        elif upper.startswith("FOLLOW_UPS"):
            in_recs, in_fus = False, True
        elif stripped and stripped[0].isdigit() and ". " in stripped:
            item = stripped.split(". ", 1)[1].strip()
            if in_recs:
                recs.append(item)
            elif in_fus:
                fus.append(item)
    return recs[:3], fus[:3]


def _static_fallback(
    persona: str,
    metric: str,
    exclude_recs: list[str],
    exclude_fus: list[str],
) -> tuple[list[str], list[str]]:
    """Return shuffled suggestions from the static pool, excluding already-shown items."""
    persona_defaults = _PERSONA_DEFAULTS.get(persona) or _PERSONA_DEFAULTS[_DEFAULT_PERSONA]

    if metric and metric in _METRIC_INSIGHT_RECS:
        seen: set[str] = set()
        rec_pool: list[str] = []
        for r in _METRIC_INSIGHT_RECS[metric] + persona_defaults["insight_recs"]:
            if r not in seen:
                seen.add(r)
                rec_pool.append(r)
    else:
        rec_pool = list(persona_defaults["insight_recs"])

    if metric and metric in _METRIC_FOLLOW_UPS:
        seen_fu: set[str] = set()
        fu_pool: list[str] = []
        for q in _METRIC_FOLLOW_UPS[metric] + persona_defaults["follow_ups"]:
            if q not in seen_fu:
                seen_fu.add(q)
                fu_pool.append(q)
    else:
        fu_pool = list(persona_defaults["follow_ups"])

    exclude_recs_set = set(exclude_recs)
    exclude_fus_set = set(exclude_fus)
    fresh_recs = [r for r in rec_pool if r not in exclude_recs_set] or list(rec_pool)
    fresh_fus = [q for q in fu_pool if q not in exclude_fus_set] or list(fu_pool)
    random.shuffle(fresh_recs)
    random.shuffle(fresh_fus)
    return fresh_recs[:3], fresh_fus[:3]


@router.post("/suggestions", response_model=SuggestionsResponse)
def refresh_suggestions(payload: SuggestionsRequest) -> SuggestionsResponse:
    """Use the LLM to generate fresh insight recommendations and follow-ups."""
    persona = payload.persona.lower()
    metric = payload.metric or ""
    answer_snippet = (payload.answer_snippet or "")[:400]  # trim to keep prompt compact

    shown_items = "\n".join(
        f"- {item}" for item in (payload.exclude_recs + payload.exclude_fus)
    ) or "(none yet)"

    prompt = _SUGGESTIONS_PROMPT.format(
        persona=persona,
        available_metrics=_CATALOG_METRICS,
        available_dimensions=_CATALOG_DIMENSIONS,
        metric=metric or "general analytics",
        answer_snippet=answer_snippet or "No summary available.",
        shown_items=shown_items,
    )

    raw = generate_with_ollama(prompt, temperature=0.7)
    recs, fus = _parse_llm_suggestions(raw)

    # Fallback to static pool if LLM returned malformed output
    if not recs or not fus:
        recs, fus = _static_fallback(persona, metric, payload.exclude_recs, payload.exclude_fus)

    return SuggestionsResponse(
        insight_recommendations=recs,
        follow_ups=fus,
    )
