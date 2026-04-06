# =============================================================================
# DataPrismAI — LangGraph Agentic Pipeline
# =============================================================================
# Defines AgentState (the shared TypedDict that flows through all nodes) and
# compiles the 13-node directed graph.
#
# Node execution order (simplified):
#   guardrail → entity_resolver → planner
#     ├─ fast_path ──────────────────────►  vanna_sql → sql_validator
#     └─ full_path → persona → semantic_resolver → vanna_sql → sql_validator
#   → query_router → query_executor → result_evaluator
#     ├─ retry ──────────────────────────► vanna_sql (max 1 retry)
#     └─ proceed → visualization → insight → recommendation → response → persist
#
# HOW TO ADD A NEW NODE:
#   1. Create apps/api/app/graph_nodes/<name>_node.py  (returns partial AgentState)
#   2. Import and add it with graph.add_node("<name>", <name>_node)
#   3. Wire edges / conditional edges below
#   4. Add any new state keys to AgentState
# =============================================================================
from langgraph.graph import StateGraph, END
from langgraph.graph.state import START
from app.graph_nodes.guardrail_node import guardrail_node
from app.graph_nodes.entity_resolver_node import entity_resolver_node
from app.graph_nodes.planner_node import planner_node
from app.graph_nodes.persona_node import persona_node
from app.graph_nodes.semantic_resolver_node import semantic_resolver_node
from app.graph_nodes.vanna_sql_node import vanna_sql_node
from app.graph_nodes.sql_validator_node import sql_validator_node
from app.graph_nodes.query_router_node import query_router_node
from app.graph_nodes.query_executor_node import query_executor_node
from app.graph_nodes.result_evaluator_node import result_evaluator_node
from app.graph_nodes.visualization_node import visualization_node
from app.graph_nodes.insight_node import insight_node
from app.graph_nodes.recommendation_node import recommendation_node
from app.graph_nodes.response_node import response_node
from app.graph_nodes.persist_node import persist_node

from typing import TypedDict, Optional

class AgentState(TypedDict, total=False):
    thread_id: str
    user_id: str
    workspace_id: str
    persona: str
    user_message: str
    time_range: str          # L7D | L1M | LQ | L1Y | ALL (default ALL)
    # intent classification (set by planner_node)
    intent: str              # legacy alias — same value as intent_type
    intent_type: str         # preview_data | schema_query | metric_query | insight_query | explanation | report
    response_mode: str       # table | schema | metric | insight
    literal_table_name: str  # explicit table name extracted from the user message (if any)
    entity_filter: dict      # {col, val} for entity ID lookups e.g. {col: customer_id, val: CUST_001}
    # conversational entity memory (set by entity_resolver_node)
    original_message: str      # raw user text before pronoun rewriting
    resolved_entity: dict      # entity that was used to rewrite a pronoun follow-up
    last_entity: dict          # most-recently known entity for this thread
    guardrail_blocked: bool
    semantic_context: dict
    generated_sql: str
    sql_explanation: str
    sql_assumptions: list[str]
    sql_validation_issues: list[str]
    target_engine: str
    query_result: dict
    visualization_config: dict
    visualization_recommendations: list[dict]
    answer: str
    insights: list[str]
    bottlenecks: list[str]
    highlight_actions: list[str]
    kpi_metrics: list[dict]
    insight_recommendations: list[str]
    follow_ups: list[str]
    assumptions: list[str]
    reasoning_steps: list[str]
    report_id: str
    error: str
    _needs_retry: bool
    _retry_count: int
    prior_context: list


def _after_guardrail(state: AgentState) -> str:
    """Skip data pipeline if guardrail blocked the query."""
    if state.get("guardrail_blocked"):
        return "blocked"
    return "proceed"


def _after_planner(state: AgentState) -> str:
    """Route preview/schema directly to SQL generation, bypassing persona + semantic resolver."""
    if state.get("intent_type") in ("preview_data", "schema_query"):
        return "fast_path"
    return "full_path"


def _should_retry(state: AgentState) -> str:
    """Conditional edge: retry SQL generation once if result_evaluator flags it."""
    if state.get("_needs_retry") and (state.get("_retry_count", 0) or 0) < 1:
        return "retry"
    return "continue"


graph = StateGraph(AgentState)
graph.add_node("guardrail", guardrail_node)
graph.add_node("entity_resolver", entity_resolver_node)
graph.add_node("planner", planner_node)
graph.add_node("persona", persona_node)
graph.add_node("semantic_resolver", semantic_resolver_node)
graph.add_node("vanna_sql", vanna_sql_node)
graph.add_node("sql_validator", sql_validator_node)
graph.add_node("query_router", query_router_node)
graph.add_node("query_executor", query_executor_node)
graph.add_node("result_evaluator", result_evaluator_node)
graph.add_node("visualization", visualization_node)
graph.add_node("insight", insight_node)
graph.add_node("recommendation", recommendation_node)
graph.add_node("response", response_node)
graph.add_node("persist", persist_node)

graph.add_edge(START, "guardrail")
graph.add_conditional_edges("guardrail", _after_guardrail, {"blocked": "persist", "proceed": "entity_resolver"})
graph.add_edge("entity_resolver", "planner")
# preview_data / schema_query skip persona + semantic_resolver and go straight to SQL
graph.add_conditional_edges("planner", _after_planner, {"fast_path": "vanna_sql", "full_path": "persona"})
graph.add_edge("persona", "semantic_resolver")
graph.add_edge("semantic_resolver", "vanna_sql")
graph.add_edge("vanna_sql", "sql_validator")
graph.add_edge("sql_validator", "query_router")
graph.add_edge("query_router", "query_executor")
graph.add_edge("query_executor", "result_evaluator")
graph.add_conditional_edges(
    "result_evaluator",
    _should_retry,
    {"retry": "vanna_sql", "continue": "visualization"},
)
graph.add_edge("visualization", "insight")
graph.add_edge("insight", "recommendation")
graph.add_edge("recommendation", "response")
graph.add_edge("response", "persist")
graph.set_entry_point("guardrail")
graph.set_finish_point("persist")
compiled_graph = graph.compile()

