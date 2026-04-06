from app.services.query_executor_service import execute_query
from app.services.thread_memory import store_turn, store_entity
from app.services.entity_extractor import extract_entity

def query_executor_node(state: dict) -> dict:
    if state.get("error") or not state.get("generated_sql"):
        return state
    steps = list(state.get("reasoning_steps") or [])
    try:
        result = execute_query(
            state.get("target_engine", "starrocks"),
            state["generated_sql"],
            state.get("semantic_context", {}),
        )
        rd = result.model_dump()
        steps.append(
            f"Query execution: {rd.get('row_count', 0)} rows returned from "
            f"'starrocks' in {rd.get('execution_time_ms', 0)}ms."
        )
        thread_id    = state.get("thread_id", "")
        user_message = state.get("user_message", "")
        rows         = rd.get("rows", [])
        columns      = rd.get("columns", [])

        # Store turn so follow-up questions can reference this result
        store_turn(
            thread_id=thread_id,
            user_message=user_message,
            sql=state["generated_sql"],
            rows=rows,
            columns=columns,
        )
        # Extract and persist the primary entity touched by this query
        # (e.g. single customer/account from a filtered result)
        entity = extract_entity(user_message, rows, columns)
        if entity:
            store_entity(thread_id, **entity)
            steps.append(
                f"Entity resolver: stored {entity['entity_type']} {entity['entity_id']} "
                f"from query result."
            )
        return {**state, "query_result": rd, "reasoning_steps": steps}
    except Exception as e:
        steps.append(f"Query execution: failed — {e}.")
        return {**state, "error": f"Query execution failed: {e}", "reasoning_steps": steps}

