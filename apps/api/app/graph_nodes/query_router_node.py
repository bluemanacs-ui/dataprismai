def query_router_node(state: dict) -> dict:
    semantic_context = state.get("semantic_context", {})
    # All queries route to StarRocks via MySQL wire protocol.
    engine = semantic_context.get("engine", "starrocks").lower()
    return {**state, "target_engine": engine}
