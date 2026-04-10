from app.services.config_service import config_svc


def result_evaluator_node(state: dict) -> dict:
    query_result = state.get("query_result", {})
    rows = query_result.get("rows", [])
    retry_count = state.get("_retry_count", 0)

    max_retry = config_svc.get_int("evaluator.max_retry", 1)
    empty_triggers_retry = config_svc.get_bool("evaluator.empty_triggers_retry", True)

    # If query execution failed (error set) we don't retry — let pipeline continue
    # to visualization so the UI still renders a meaningful response
    if state.get("error"):
        return {**state, "_needs_retry": False}

    # If result is empty and we haven't retried yet, flag for retry
    if empty_triggers_retry and not rows and retry_count < max_retry:
        return {**state, "_retry_count": retry_count + 1, "_needs_retry": True}
    return {**state, "_needs_retry": False}
