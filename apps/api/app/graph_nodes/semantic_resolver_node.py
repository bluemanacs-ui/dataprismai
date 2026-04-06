from app.services.semantic_service import resolve_semantic_context
from app.services.thread_memory import get_context

def semantic_resolver_node(state: dict) -> dict:
    # preview_data and schema_query are routed here only on the retry path (result_evaluator→vanna_sql),
    # but guard proactively: never run semantic scoring for these intents.
    intent_type = state.get("intent_type", "metric_query")
    if intent_type in ("preview_data", "schema_query"):
        steps = list(state.get("reasoning_steps") or [])
        steps.append(f"Semantic resolver: skipped (intent={intent_type} — no metric scoring needed).")
        return {**state, "reasoning_steps": steps}

    message = state.get("user_message", "")
    persona = state.get("persona", "analyst")
    thread_id = state.get("thread_id", "")
    time_range = state.get("time_range", "ALL")
    steps = list(state.get("reasoning_steps") or [])
    prior_context = get_context(thread_id)
    try:
        semantic_context = resolve_semantic_context(message, persona)
        # Inject time_range into semantic context so downstream nodes can use it
        semantic_context["time_range"] = time_range
        # If an entity was resolved from a pronoun rewrite, annotate semantic context
        # so SQL-generation nodes can add an appropriate WHERE clause filter.
        resolved_entity = state.get("resolved_entity") or state.get("last_entity")
        if resolved_entity and resolved_entity.get("entity_id"):
            semantic_context["resolved_entity_type"] = resolved_entity["entity_type"]
            semantic_context["resolved_entity_id"]   = resolved_entity["entity_id"]
            semantic_context["resolved_entity_name"] = resolved_entity.get("entity_name", "")
            steps.append(
                f"Semantic resolver: entity context injected — "
                f"{resolved_entity['entity_type']} {resolved_entity['entity_id']}."
            )
        if semantic_context.get("free_form"):
            steps.append(f"Semantic resolver: no metric keyword matched — routing to free-form LLM SQL generation. Time range: {time_range}.")
        else:
            steps.append(
                f"Semantic resolver: matched metric '{semantic_context.get('metric')}' "
                f"in domain '{semantic_context.get('domain')}' via keyword scoring. Time range: {time_range}."
            )
    except Exception as e:
        semantic_context = {"metric": "", "dimensions": ["Month"], "engine": "starrocks", "domain": "CreditCard", "definition": "", "persona": persona, "free_form": True, "time_range": time_range}
        steps.append(f"Semantic resolver: fallback to free-form (error: {e}).")
    return {**state, "semantic_context": semantic_context, "prior_context": prior_context, "reasoning_steps": steps}

