import logging
from app.services.sql_generation_service import generate_sql_from_question, _unknown_table_sql
from app.services.schema_registry import registry as _schema_registry

logger = logging.getLogger(__name__)


def _preview_sql(table_name: str, message: str) -> str:
    """Generate deterministic preview SQL for a known table. No LLM involved."""
    import re
    meta = _schema_registry.get_table(table_name)
    qualified = meta["qualified"] if meta else f"cc_analytics.{table_name}"

    # COUNT intent
    if re.search(r"\b(count|how many|total\s+count|number\s+of|row\s+count)\b", message, re.IGNORECASE):
        col_m = re.search(r"\bdistinct\s+(\w+)", message, re.IGNORECASE)
        if col_m:
            col = col_m.group(1)
            return f"SELECT COUNT(DISTINCT {col}) AS distinct_{col}_count FROM {qualified}"
        return f"SELECT COUNT(*) AS row_count FROM {qualified}"

    # Row limit from message, default 10
    limit_m = re.search(r"\b(\d+)\b", message)
    limit = min(int(limit_m.group(1)), 200) if limit_m else 10
    return f"SELECT * FROM {qualified} LIMIT {limit}"


def _schema_sql(table_name: str) -> str:
    """Generate SQL to retrieve column metadata for a table from information_schema."""
    return (
        f"SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT "
        f"FROM information_schema.columns "
        f"WHERE TABLE_SCHEMA = 'cc_analytics' "
        f"AND TABLE_NAME = '{table_name}' "
        f"ORDER BY ORDINAL_POSITION"
    )


def vanna_sql_node(state: dict) -> dict:
    if state.get("error"):
        return state

    message = state.get("user_message", "")
    persona = state.get("persona", "analyst")
    semantic_context = state.get("semantic_context", {})
    prior_context = state.get("prior_context") or []
    steps = list(state.get("reasoning_steps") or [])
    intent_type = state.get("intent_type", "metric_query")
    table_name = state.get("literal_table_name", "")

    # ── Fast path: preview_data — deterministic SQL, no LLM ──────────────────
    # Only take the fast path if the table is actually in the registry;
    # if not, fall through so the unknown-table handler produces a clean message.
    if intent_type == "preview_data" and table_name and _schema_registry.get_table(table_name):
        table_meta = _schema_registry.get_table(table_name)
        entity_filter = state.get("entity_filter")
        if entity_filter:
            # Entity ID lookup: SELECT * FROM table WHERE col = 'val'
            import re as _re
            meta = _schema_registry.get_table(table_name)
            qualified = meta["qualified"] if meta else f"cc_analytics.{table_name}"
            col = entity_filter["col"]
            # Sanitize: only allow alphanumeric, underscore, and hyphen in the ID value
            val = _re.sub(r"[^A-Za-z0-9_\-]", "", str(entity_filter["val"]))
            sql = f"SELECT * FROM {qualified} WHERE {col} = '{val}'"
            _schema_registry.log_table_lookup(
                table_name, True,
                category=table_meta.get("category") if table_meta else None,
                sql=sql,
                response_mode="table",
            )
            steps.append(f"SQL generation: entity_lookup fast path — {col} = '{val}' in '{table_name}'.")
            return {
                **state,
                "generated_sql": sql,
                "sql_explanation": f"Direct entity lookup: {col} = '{val}' in {table_name}.",
                "sql_assumptions": [f"Fetches the single record matching {col} = '{val}'.", "No aggregation applied."],
                "reasoning_steps": steps,
            }
        sql = _preview_sql(table_name, message)
        _schema_registry.log_table_lookup(
            table_name, True,
            category=table_meta.get("category") if table_meta else None,
            sql=sql,
            response_mode="table",
        )
        steps.append(f"SQL generation: preview_data fast path — deterministic SELECT from '{table_name}'.")
        return {
            **state,
            "generated_sql": sql,
            "sql_explanation": f"Direct table preview from {table_name}.",
            "sql_assumptions": [f"Shows rows from {table_name}.", "No aggregation applied.", "LIMIT capped at 200."],
            "reasoning_steps": steps,
        }

    # ── Fast path: schema_query — describe table columns ─────────────────────
    if intent_type == "schema_query" and table_name and _schema_registry.get_table(table_name):
        table_meta_sq = _schema_registry.get_table(table_name)
        sql = _schema_sql(table_name)
        _schema_registry.log_table_lookup(
            table_name, True,
            category=table_meta_sq.get("category") if table_meta_sq else None,
            sql=sql,
            response_mode="schema",
        )
        steps.append(f"SQL generation: schema_query — introspecting columns for '{table_name}'.")
        return {
            **state,
            "generated_sql": sql,
            "sql_explanation": f"Column metadata for {table_name}.",
            "sql_assumptions": ["Schema introspection via information_schema.columns."],
            "reasoning_steps": steps,
        }

    # ── Standard path: detect unknown table/view ──────────────────────────────
    unknown = _unknown_table_sql(message)
    # Also catch the case where planner extracted a table name that isn't in the registry
    if not unknown and table_name and not _schema_registry.get_table(table_name):
        unknown = f"SELECT 'Table or view \\'{table_name}\\' was not found in this system.' AS not_found"
    if unknown:
        import re
        from difflib import get_close_matches
        name_m = re.search(r"'([\w_]+)' was not found", unknown)
        name = name_m.group(1) if name_m else "the requested object"
        all_tables = _schema_registry.all_tables()
        known_names = list(all_tables.keys())
        close = get_close_matches(name, known_names, n=3, cutoff=0.4)
        suggestion = f" Did you mean **{close[0]}**?" if close else ""
        # Build a grouped summary: show up to 5 tables per category
        _CAT_ORDER = ("semantic", "dp", "ddm", "raw", "audit", "mapping", "other")
        by_cat: dict[str, list[str]] = {}
        for tname, meta in all_tables.items():
            by_cat.setdefault(meta["category"], []).append(tname)
        parts = []
        for cat in _CAT_ORDER:
            tables = sorted(by_cat.get(cat, []))
            if not tables:
                continue
            sample = ", ".join(tables[:5]) + (" …" if len(tables) > 5 else "")
            parts.append(f"**{cat}**: {sample}")
        available_str = " | ".join(parts) if parts else "none"
        _schema_registry.log_table_lookup(
            name, False,
            suggestions=close,
        )
        steps.append(f"SQL generation: unknown table '{name}' — skipping SQL execution.")
        return {
            **state,
            "generated_sql": "",
            "answer": (
                f"**'{name}'** was not found in this system.{suggestion}\n\n"
                f"Available tables by category: {available_str}."
            ),
            "query_result": {"rows": [], "columns": []},
            "insights": [],
            "bottlenecks": [],
            "highlight_actions": [],
            "kpi_metrics": [],
            "reasoning_steps": steps,
        }

    # ── Standard path: full SQL generation via LLM / Vanna ────────────────────
    try:
        chat_mode = state.get("chat_mode") or "hybrid"
        sql_result = generate_sql_from_question(message, persona, semantic_context, prior_context, chat_mode=chat_mode)
        metric = semantic_context.get("metric", "?")
        steps.append(
            f"SQL generation: built query for '{metric}' using engine '{semantic_context.get('engine', '?')}'. "
            f"Assumptions: {'; '.join(sql_result.assumptions[:2]) if sql_result.assumptions else 'none'}."
        )
        return {**state,
            "generated_sql": sql_result.sql,
            "sql_explanation": sql_result.explanation,
            "sql_assumptions": sql_result.assumptions,
            "sql_llm_used": sql_result.llm_was_used,
            "reasoning_steps": steps,
        }
    except Exception as e:
        steps.append(f"SQL generation: failed — {e}.")
        return {**state, "error": f"SQL generation failed: {e}", "reasoning_steps": steps}


