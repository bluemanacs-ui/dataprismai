import re
import logging
from app.services.llm_service import generate_with_ollama

logger = logging.getLogger(__name__)

_DATE_LIKE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def _build_narrative_prompt(
    user_message: str,
    persona: str,
    metric: str,
    rows: list,
    columns: list,
    insights: list,
) -> str:
    """Build a concise LLM prompt to narrate query results."""
    from app.services.config_service import config_svc
    sample_rows = config_svc.get_int("prompt.narrative_sample_rows", 8)
    max_insights = config_svc.get_int("prompt.narrative_max_insights", 4)
    n = len(rows)
    top_rows = rows[:sample_rows]
    data_lines = []
    for i, row in enumerate(top_rows):
        vals = ", ".join(f"{c}: {row.get(c, 'N/A')}" for c in columns[:7])
        data_lines.append(f"  {i+1}. {vals}")
    data_str = "\n".join(data_lines) or "  (no rows)"
    insights_str = "\n".join(f"- {s}" for s in insights[:max_insights]) if insights else "- none"

    return (
        f"You are a {persona} analytics assistant for a credit card portfolio.\n\n"
        f"User asked: {user_message}\n"
        f"Metric: {metric or 'general analytics'}\n"
        f"Total rows returned: {n}\n\n"
        f"Top data rows:\n{data_str}\n\n"
        f"Statistical insights:\n{insights_str}\n\n"
        "Write a concise 2-3 sentence analytical response directly answering the user's question.\n"
        "Rules:\n"
        "- Be specific — include actual numbers from the data\n"
        "- Bold the most important values with **value**\n"
        "- Lead with the key finding, not background\n"
        "- Do NOT start with 'Based on', 'The data shows', or 'I'\n"
        "- Do NOT output JSON, markdown code blocks, or headings\n"
        "- Output only the narrative text"
    )


def _llm_narrative(state: dict, rule_answer: str) -> tuple[str, bool]:
    """
    Attempt to generate an LLM narrative answer.
    Returns (answer_text, llm_was_used).
    Falls back to rule_answer if LLM fails or is not applicable.
    """
    response_mode = state.get("response_mode", "metric")
    # Only narrate aggregated analytics — not raw table previews or schema
    if response_mode in ("table", "schema"):
        return rule_answer, False

    rows = (state.get("query_result") or {}).get("rows", [])
    columns = (state.get("query_result") or {}).get("columns", [])
    if not rows:
        return rule_answer, False

    try:
        prompt = _build_narrative_prompt(
            user_message=state.get("user_message", ""),
            persona=state.get("persona", "analyst"),
            metric=(state.get("semantic_context") or {}).get("metric", ""),
            rows=rows,
            columns=columns,
            insights=state.get("insights") or [],
        )
        llm_text = generate_with_ollama(prompt, temperature=0.3).strip()
        # Sanity check — reject empty or error responses
        if llm_text and not llm_text.startswith("DataPrismAI could not reach"):
            return llm_text, True
    except Exception as exc:
        logger.warning("LLM narrative failed, using rule-based answer: %s", exc)

    return rule_answer, False

# Maps numeric column name fragments to human-readable units for inline display
_UNIT_HINTS = {
    "rate_pct": "%",
    "rate": "%",
    "pct": "%",
    "score": "",
    "amount": "",
    "spend": "",
    "income": "",
    "count": "",
    "txn": "",
}


def _unit_for(col: str) -> str:
    col_lower = col.lower()
    for fragment, unit in _UNIT_HINTS.items():
        if fragment in col_lower:
            return unit
    return ""


def _fmt_val(val, col: str = "") -> str:
    """Format a result value for display in the response sentence."""
    if val is None:
        return "N/A"
    try:
        fv = float(val)
        unit = _unit_for(col)
        if unit == "%":
            return f"{fv:.2f}%"
        if fv >= 1_000_000:
            return f"{fv/1_000_000:.2f}M"
        if fv >= 1_000:
            return f"{fv:,.0f}"
        return f"{fv:.2f}"
    except (TypeError, ValueError):
        return str(val)


def response_node(state: dict) -> dict:
    if state.get("error"):
        return {**state, "answer": "I wasn't able to retrieve data for that query. Please try rephrasing — for example, specify a table or metric name."}

    # Answer already composed upstream (e.g. unknown table short-circuit)
    if state.get("answer"):
        return state

    response_mode = state.get("response_mode", "metric")
    semantic_context = state.get("semantic_context", {})
    metric = semantic_context.get("metric") or ""
    user_message = state.get("user_message", "")
    table_name = state.get("literal_table_name", "")
    query_result = state.get("query_result", {})
    rows = query_result.get("rows", [])
    columns = query_result.get("columns", [])
    insights = state.get("insights", [])
    bottlenecks = state.get("bottlenecks", [])
    highlight_actions = state.get("highlight_actions", [])
    is_free_form = semantic_context.get("free_form", False)

    if not rows or not columns:
        if response_mode == "schema":
            return {**state, "answer": f"No schema information found for **{table_name or 'this table'}**."}
        subject = f"**{metric}**" if metric else "your query"
        return {**state, "answer": f"No data was found for {subject}. Try broadening the query or checking the time range."}

    n = len(rows)
    top_row = rows[0]
    dim_col = columns[0]

    # ── Unknown table/view sentinel ───────────────────────────────────────
    if n == 1 and len(columns) == 1 and columns[0] == "not_found":
        from app.services.schema_registry import registry as _sr
        available = ", ".join(sorted(_sr.known_table_names())[:20])
        msg = str(top_row.get("not_found", ""))
        return {**state, "answer": f"{msg} Available tables include: {available}."}

    # ── Schema query — render column list ────────────────────────────────────
    if response_mode == "schema":
        col_lines = []
        for row in rows:
            col_name = row.get("COLUMN_NAME", row.get("column_name", ""))
            data_type = row.get("DATA_TYPE", row.get("data_type", ""))
            nullable = row.get("IS_NULLABLE", row.get("is_nullable", "YES"))
            null_flag = " (nullable)" if nullable == "YES" else " NOT NULL"
            col_lines.append(f"- `{col_name}` — **{data_type}**{null_flag}")
        tbl_display = f"`{table_name}`" if table_name else "this table"
        answer = f"Schema for {tbl_display} ({len(rows)} columns):\n\n" + "\n".join(col_lines)
        return {**state, "answer": answer}

    # ── Preview / table mode — describe result set simply, no insight prose ──
    if response_mode == "table":
        tbl_display = f"`{table_name}`" if table_name else "the table"
        # COUNT result
        if n == 1 and len(columns) == 1 and "count" in columns[0].lower():
            count_val = top_row.get(columns[0], 0)
            try:
                count_val = f"{int(count_val):,}"
            except (TypeError, ValueError):
                count_val = str(count_val)
            return {**state, "answer": f"There are **{count_val}** records in {tbl_display}."}
        col_list = ", ".join(f"`{c}`" for c in columns[:8])
        more = f" (+{len(columns)-8} more)" if len(columns) > 8 else ""
        answer = f"Showing **{n} rows** from {tbl_display}. Columns: {col_list}{more}."
        return {**state, "answer": answer}


    # ── Free-form / row-level lookup — describe the result set simply ──────
    if is_free_form or not metric:
        # COUNT(*) result — single row, single column with 'count' in name
        if n == 1 and len(columns) == 1 and "count" in columns[0].lower():
            count_val = top_row.get(columns[0], 0)
            try:
                count_val = f"{int(count_val):,}"
            except (TypeError, ValueError):
                count_val = str(count_val)
            # Extract table name hint from SQL for a cleaner answer
            sql = state.get("generated_sql", "")
            import re as _re
            tbl_m = _re.search(r"FROM\s+(\S+)", sql, _re.IGNORECASE)
            tbl_name = tbl_m.group(1).split(".")[-1] if tbl_m else "the table"
            return {**state, "answer": f"There are **{count_val}** records in **{tbl_name}**."}

        # Detect if result looks like individual records (has name/id columns)
        _IDENTITY_COLS = {"first_name", "last_name", "full_name", "customer_id",
                          "name", "email", "phone", "customer_name"}
        has_identity = any(c.lower() in _IDENTITY_COLS for c in columns)

        if has_identity:
            name_col = next((c for c in columns if c.lower() in {"first_name", "full_name", "name", "customer_name"}), None)
            id_col = next((c for c in columns if "id" in c.lower()), None)
            # Check if there's a ranking/count metric column (card_count, txn_count, total_spend, etc.)
            _RANK_KW = ("count", "spend", "total", "amount", "sum", "num", "balance")
            rank_col = next((c for c in columns if any(kw in c.lower() for kw in _RANK_KW)), None)
            first_name = top_row.get(name_col, "") if name_col else ""
            sample = f"**{first_name}**" if first_name else f"record `{top_row.get(id_col, '')}`"
            if rank_col and first_name:
                rank_val = top_row.get(rank_col, "")
                rank_label = rank_col.replace("_", " ").title()
                try:
                    rank_val = f"{int(rank_val):,}" if "." not in str(rank_val) else f"{float(rank_val):,.2f}"
                except (TypeError, ValueError):
                    rank_val = str(rank_val)
                answer = (
                    f"**{n:,} customers** meet this criteria, ranked by {rank_label}. "
                    f"Top result: {sample} with **{rank_val} {rank_label}**."
                )
            else:
                answer = f"Found **{n} customer record(s)**. First result: {sample} ({', '.join(str(top_row.get(c, '')) for c in columns[:4] if top_row.get(c))})"
        elif len(columns) >= 4:
            # Raw table scan — give a column preview and row count
            col_list = ", ".join(f"`{c}`" for c in columns[:8])
            more = f" (+{len(columns)-8} more)" if len(columns) > 8 else ""
            first_vals = ", ".join(f"{c}={repr(str(top_row.get(c, '')))}" for c in columns[:4])
            answer = (
                f"Showing **{n} rows** from the table. "
                f"Columns: {col_list}{more}. "
                f"First row: {first_vals}."
            )
        else:
            col_list = ", ".join(columns[:5])
            answer = f"Found **{n} row(s)** with columns: {col_list}."

        if bottlenecks:
            answer += f" {len(bottlenecks)} flag(s) raised."
        rule_answer = answer
        answer, answer_llm_used = _llm_narrative(state, rule_answer)
        return {**state, "answer": answer, "answer_llm_used": answer_llm_used}

    # Determine if the first column is a date/period (time-series) vs a categorical dimension
    top_dim_val = str(top_row.get(dim_col, ""))
    is_time_series = bool(_DATE_LIKE_RE.match(top_dim_val))

    # Identify secondary dimension columns (text/code) vs numeric metric columns
    _NON_NUMERIC_SUFFIXES = ("_code", "_id", "_name", "_status", "_method", "_type", "_category")
    _NON_NUMERIC_COLS = {"country_code", "legal_entity", "currency_code", "merchant_category",
                         "customer_segment", "payment_status", "channel", "auth_status"}

    def _is_dim_col(col: str) -> bool:
        col_l = col.lower()
        return col_l in _NON_NUMERIC_COLS or any(col_l.endswith(s) for s in _NON_NUMERIC_SUFFIXES)

    def _try_numeric(val) -> bool:
        try:
            float(val)
            return True
        except (TypeError, ValueError):
            return False

    # Pick the primary metric column — prefer rate/pct/spend columns over raw counts
    _PREFERRED_KW = ("rate_pct", "rate", "_pct", "spend", "amount", "income", "balance", "score")
    num_cols = [
        c for c in columns[1:]
        if not _is_dim_col(c) and _try_numeric(top_row.get(c))
    ]
    # Sort: preferred keyword columns first, then rest
    def _col_priority(c: str) -> int:
        cl = c.lower()
        for i, kw in enumerate(_PREFERRED_KW):
            if kw in cl:
                return i
        return len(_PREFERRED_KW)
    num_cols.sort(key=_col_priority)
    primary_num_col = num_cols[0] if num_cols else None
    num_label = primary_num_col.replace("_", " ").title() if primary_num_col else ""

    # ── Detect metric direction ───────────────────────────────────────────────
    _RISK_METRICS = {"Fraud Rate", "Delinquency Rate", "Dispute Rate"}
    is_risk_metric = metric in _RISK_METRICS

    # For non-time-series summaries, decide which row is "top" based on metric direction
    if primary_num_col and not is_time_series:
        def _safe_float(v):
            try: return float(v)
            except: return 0.0
        sorted_rows = sorted(rows, key=lambda r: _safe_float(r.get(primary_num_col)), reverse=True)
        top_row = sorted_rows[0]
        second_row = sorted_rows[1] if n > 1 else None
    else:
        sorted_rows = rows
        second_row = rows[1] if n > 1 else None

    top_dim_val = str(top_row.get(dim_col, ""))  # refresh after sort
    primary_val = _fmt_val(top_row.get(primary_num_col), primary_num_col) if primary_num_col else None

    if is_time_series:
        dim_label = "month" if len(top_dim_val) == 7 else "date"
        answer_parts = [f"Here is the **{metric or 'data'} trend** across {n} {dim_label}s."]
        if primary_val:
            answer_parts.append(
                f"The most recent period (**{top_dim_val}**) shows **{primary_val}** {num_label.lower()}."
            )
    elif n == 1:
        dim_label = dim_col.replace("_", " ").replace("code", "").strip().title()
        answer_parts = [f"Result for **{top_dim_val}**:"]
        detail_parts = []
        for col in columns[1:5]:
            val = top_row.get(col)
            if val is not None:
                detail_parts.append(f"{col.replace('_',' ').title()} = **{_fmt_val(val, col)}**")
        if detail_parts:
            answer_parts.append(", ".join(detail_parts) + ".")
    elif n <= 5 and len(num_cols) >= 3:
        # Multi-metric comparison (e.g. portfolio across countries) — build a per-entity summary
        dim_label = dim_col.replace("_code", "").replace("_", " ").strip().title()
        # Build grammatically correct plural without adding "s" to already-plural words
        _PLURALS = {"Country": "Countries", "Category": "Categories", "Entity": "Entities"}
        dim_label_plural = _PLURALS.get(dim_label, f"{dim_label}s")
        summary_parts = []
        for row in rows:
            entity = str(row.get(dim_col, ""))
            vals = [f"{c.replace('_',' ').title()} **{_fmt_val(row.get(c), c)}**" for c in num_cols[:3]]
            summary_parts.append(f"**{entity}**: {', '.join(vals)}")
        answer_parts = [f"Comparing **{n} {dim_label_plural}** — " + "; ".join(summary_parts) + "."]
    else:
        dim_label = dim_col.replace("_code", "").replace("_", " ").strip().title()
        answer_parts = []
        if primary_val and primary_num_col:
            second_row = rows[1] if n > 1 else None
            if is_risk_metric:
                # Highest value = worst performer — use explicit risk language
                answer_parts.append(
                    f"**{top_dim_val}** has the highest **{primary_val}** {num_label.lower()}"
                    + (
                        f", followed by **{second_row.get(dim_col)}** at "
                        f"{_fmt_val(second_row.get(primary_num_col), primary_num_col)}."
                        if second_row else "."
                    )
                )
            else:
                answer_parts.append(
                    f"**{top_dim_val}** leads with **{primary_val}** {num_label.lower()}"
                    + (
                        f", followed by **{second_row.get(dim_col)}** at "
                        f"{_fmt_val(second_row.get(primary_num_col), primary_num_col)}."
                        if second_row else "."
                    )
                )
            answer_parts.append(f"{n} {dim_label} groups analysed.")

    # ── Add counts for bottlenecks / actions ──────────────────────────────────
    if bottlenecks:
        answer_parts.append(f"{len(bottlenecks)} critical issue(s) identified.")
    if highlight_actions:
        answer_parts.append(f"{len(highlight_actions)} recommended action(s) generated.")

    rule_answer = " ".join(answer_parts)
    answer, answer_llm_used = _llm_narrative(state, rule_answer)
    return {**state, "answer": answer, "answer_llm_used": answer_llm_used}

