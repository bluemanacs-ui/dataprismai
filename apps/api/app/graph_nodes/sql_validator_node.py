from app.services.sql_validator_service import validate_sql

def sql_validator_node(state: dict) -> dict:
    if state.get("error") or not state.get("generated_sql"):
        return state
    try:
        valid, issues, normalized = validate_sql(state["generated_sql"])
        return {**state,
            "generated_sql": normalized,
            "sql_validation_issues": issues,
        }
    except Exception as e:
        return {**state, "error": f"SQL validation failed: {e}"}
