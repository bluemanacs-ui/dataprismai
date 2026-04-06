"""Insight node — generates rich structured analytics using pure-Python statistical analysis.

Returns:
  - insights: list[str]  — key data findings (lead insight + statistical analysis)
  - bottlenecks: list[str]  — critical issues / alerts identified in the data
  - highlight_actions: list[str]  — specific recommended actions with detail
  - kpi_metrics: list[dict]  — {label, value, trend} for KPI card display

No LLM call is made here — all analysis is rule-based for speed.
"""
import json

_METRIC_CONTEXT: dict[str, dict] = {
    "Total Spend":          {"unit": "$",  "direction": "high", "domain": "revenue"},
    "Transaction Count":    {"unit": "",   "direction": "high", "domain": "activity"},
    "Fraud Rate":           {"unit": "%",  "direction": "low",  "domain": "risk"},
    "Delinquency Rate":     {"unit": "%",  "direction": "low",  "domain": "credit risk"},
    "Account Utilization":  {"unit": "%",  "direction": "high", "domain": "credit"},
    "Payment Volume":       {"unit": "$",  "direction": "high", "domain": "collections"},
    "Dispute Rate":         {"unit": "%",  "direction": "low",  "domain": "operations"},
    "Customer Credit Score":{"unit": "",   "direction": "high", "domain": "credit quality"},
}

_RISK_THRESHOLDS: dict[str, float] = {
    "Fraud Rate": 15.0,
    "Dispute Rate": 5.0,
    "Delinquency Rate": 10.0,
}


def _is_numeric(val) -> bool:
    if val is None:
        return False
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


_MEASURE_KW = {
    "amount", "spend", "rate", "count", "pct", "percent", "score", "total",
    "sum", "avg", "average", "revenue", "value", "balance", "fee", "charge",
    "volume", "num", "number", "payments", "utilization", "customers", "accounts",
    "transactions", "txn", "income", "interest", "growth", "churn", "npl",
}

_DIM_SUFFIXES = ("_code", "_id", "_name", "_status", "_method", "_type", "_category",
                 "_key", "_label", "_flag", "_entity", "_segment", "_channel", "_band")
_DIM_EXACT = {"country_code", "legal_entity", "currency_code", "merchant_category",
              "customer_segment", "payment_status", "channel", "auth_status",
              "merchant_type", "age_band", "overdue_bucket", "spend_month",
              "metric_date", "kpi_month", "txn_year_month", "as_of_date"}


def _classify_cols(columns: list, sample: dict):
    def _is_dim(col: str) -> bool:
        cl = col.lower()
        # Explicit dimension lookup
        if cl in _DIM_EXACT:
            return True
        if any(cl.endswith(sfx) for sfx in _DIM_SUFFIXES):
            return True
        # If a known measure keyword appears in the column name, it's a measure
        if any(kw in cl for kw in _MEASURE_KW):
            return False
        # Fall back: non-numeric values are always dimensions
        v = sample.get(col)
        if not _is_numeric(v):
            return True
        # Pure integer that looks like a code (small int, no fraction) — check further
        try:
            fv = float(v)
            # Treat as dimension only if it looks like an encoded label (< 100 and whole)
            return fv == int(fv) and 0 < abs(fv) < 100 and "." not in str(v)
        except Exception:
            return True
    dim_cols = [c for c in columns if _is_dim(c)]
    num_cols = [c for c in columns if not _is_dim(c) and _is_numeric(sample.get(c))]
    return dim_cols, num_cols


def _fmt(val: float, unit: str) -> str:
    if unit == "$":
        return f"${val:,.0f}" if val >= 100 else f"${val:,.2f}"
    if unit == "%":
        return f"{val:.1f}%"
    return f"{val:,.0f}"


def _statistical_insights(rows, columns, metric, ctx) -> tuple[list, list, list]:
    """Pure-Python statistical insights, bottlenecks, kpis — no LLM needed."""
    unit = ctx["unit"]
    direction = ctx["direction"]
    domain = ctx["domain"]

    if not rows or not columns:
        return [], [], []

    sample = rows[0]
    dim_cols, num_cols = _classify_cols(columns, sample)
    insights, bottlenecks, kpis = [], [], []

    if not dim_cols or not num_cols:
        # Single-row lookup — build KPI cards from all numeric columns
        kpis = [
            {"label": c.replace("_", " ").title(), "value": str(sample.get(c, "")), "trend": None}
            for c in columns
            if _is_numeric(sample.get(c))
        ][:6]
        if not kpis:
            kpis = [{"label": c.replace("_", " ").title(), "value": str(sample.get(c, "")), "trend": None}
                    for c in columns[:4]]
        # For single-row lookups, still generate brief insights per numeric field
        for kpi in kpis[:3]:
            insights.append(
                f"**{kpi['label']}** — value is **{kpi['value']}** for this record."
            )
        return insights, [], kpis

    x_key = dim_cols[0]
    val_key = num_cols[0]
    val_label = val_key.replace("_", " ").title()

    # Use "period" for date columns, "segment" for categorical ones
    x_key_lower = (x_key or "").lower()
    _DATE_COLS = {"metric_date", "spend_month", "kpi_month", "as_of_date", "txn_year_month", "payment_date", "statement_month"}
    is_time_dim = x_key_lower in _DATE_COLS or bool(__import__("re").match(r"^\d{4}-\d{2}", str(rows[0].get(x_key, ""))))
    segment_label = "period" if is_time_dim else "segment"
    dim_label = "date" if is_time_dim else x_key.replace("_", " ").replace("_code", "").title()
    n = len(rows)

    sorted_rows = sorted(rows, key=lambda r: float(r.get(val_key, 0) or 0), reverse=True)
    top = sorted_rows[0]
    top_name = str(top.get(x_key, "N/A"))
    top_val = float(top.get(val_key, 0) or 0)
    bottom = sorted_rows[-1]
    bot_name = str(bottom.get(x_key, "N/A"))
    bot_val = float(bottom.get(val_key, 0) or 0)
    total = sum(float(r.get(val_key, 0) or 0) for r in rows)
    avg_val = total / n if n else 0
    median_val = float(sorted_rows[n // 2].get(val_key, 0) or 0)
    share = (top_val / total * 100) if total else 0
    top_fmt = _fmt(top_val, unit)
    total_fmt = _fmt(total, unit)
    avg_fmt = _fmt(avg_val, unit)
    median_fmt = _fmt(median_val, unit)
    bot_fmt = _fmt(bot_val, unit)
    above_avg = sum(1 for r in rows if float(r.get(val_key, 0) or 0) > avg_val)

    # KPI cards — up to 5 meaningful ones
    # For risk metrics (direction=low), label the best (lowest) value as the highlight
    if direction == "low":
        highlight_row = sorted_rows[-1]   # best = lowest value
        highlight_name = str(highlight_row.get(x_key, "N/A"))
        highlight_val = _fmt(float(highlight_row.get(val_key, 0) or 0), unit)
        worst_row = sorted_rows[0]        # worst = highest value
        worst_name = str(worst_row.get(x_key, "N/A"))
        worst_val_fmt = _fmt(float(worst_row.get(val_key, 0) or 0), unit)
        top_label = f"Latest: {top_name}" if is_time_dim else f"Best: {highlight_name}"
        risk_label = f"Latest: {top_name}" if is_time_dim else f"Highest Risk: {worst_name}"
        count_label = "Periods" if is_time_dim else "Segments"
        kpis = [
            {"label": f"Avg {val_label}", "value": avg_fmt, "trend": None},
            {"label": f"Median {val_label}", "value": median_fmt, "trend": None},
            {"label": count_label, "value": str(n), "trend": None},
            {"label": top_label, "value": highlight_val, "trend": "down"},
            {"label": risk_label, "value": worst_val_fmt, "trend": "up"},
        ]
    else:
        top_label = f"Latest: {top_name}" if is_time_dim else f"Top: {top_name}"
        count_label = "Periods" if is_time_dim else "Segments"
        kpis = [
            {"label": f"Total {val_label}", "value": total_fmt, "trend": None},
            {"label": f"Avg {val_label}", "value": avg_fmt, "trend": None},
            {"label": f"Median {val_label}", "value": median_fmt, "trend": None},
            {"label": count_label, "value": str(n), "trend": None},
            {"label": top_label, "value": top_fmt, "trend": "up"},
        ]

    # ── Insight 1: Lead — most prominent entry ───────────────────────────
    if is_time_dim:
        insights.append(
            f"**{top_name}** — highest {val_label} period at **{top_fmt}** "
            f"(out of {n} {segment_label}s). Average across all periods is {avg_fmt}."
        )
    elif direction == "low":
        # For risk metrics, high value = BAD. Highlight worst and best.
        best_row = sorted_rows[-1]
        best_name = str(best_row.get(x_key, "N/A"))
        best_val_fmt = _fmt(float(best_row.get(val_key, 0) or 0), unit)
        insights.append(
            f"**{top_name}** has the highest {val_label} at **{top_fmt}** — "
            f"the highest-risk {segment_label} among {n}. "
            f"**{best_name}** is the best-performing {segment_label} at {best_val_fmt}. "
            f"Average across all {segment_label}s is {avg_fmt}."
        )
    else:
        insights.append(
            f"**{top_name}** leads with {val_label} of **{top_fmt}**, "
            f"representing **{share:.1f}%** of the total {total_fmt} across {n} {dim_label} {segment_label}s. "
            f"Average across all {segment_label}s is {avg_fmt}."
        )

    # ── Insight 2: Distribution — above vs below average ─────────────────
    below_avg = n - above_avg
    insights.append(
        f"**Distribution** — {above_avg} of {n} {segment_label}s ({above_avg/n*100:.0f}%) are above the average "
        f"of {avg_fmt}, while {below_avg} {segment_label}s ({below_avg/n*100:.0f}%) are below. "
        f"Median is {median_fmt}."
    )

    # ── Insight 3: Concentration ──────────────────────────────────────────
    if n >= 3:
        top3 = sum(float(r.get(val_key, 0) or 0) for r in sorted_rows[:3])
        top3_share = (top3 / total * 100) if total else 0
        top3_names = ", ".join(str(r.get(x_key, "")) for r in sorted_rows[:3])
        insights.append(
            f"**Top-3 Concentration** — {top3_names} collectively hold **{top3_share:.0f}%** of total "
            f"{val_label} ({_fmt(top3, unit)} of {total_fmt}). "
            f"{'High concentration — diversification may be needed.' if top3_share > 70 else f'Relatively balanced distribution across {n} {segment_label}s.'}"
        )
        if top3_share > 80:
            bottlenecks.append(
                f"**Extreme Concentration** — top 3 {segment_label}s hold {top3_share:.0f}% of {val_label} "
                f"({_fmt(top3, unit)}). Single-{segment_label} underperformance could materially impact total {domain} outcomes. "
                f"Risk review recommended for remaining {n - 3} {segment_label}s."
            )

    # ── Insight 4: Spread (min–max ratio) ────────────────────────────────
    if bot_val > 0 and top_val > 0:
        ratio = top_val / bot_val
        insights.append(
            f"**Range Analysis** — {val_label} ranges from **{bot_fmt}** ({bot_name}) to **{top_fmt}** ({top_name}), "
            f"a **{ratio:.1f}×** spread. "
            f"{'Wide variance suggests structural differences between segments.' if ratio > 5 else 'Moderate spread — performance is reasonably consistent.'}"
        )

    # ── Insight 5: Second tier (2nd and 3rd places) ───────────────────────
    if n >= 2:
        second = sorted_rows[1]
        sec_name = str(second.get(x_key, "N/A"))
        sec_val = float(second.get(val_key, 0) or 0)
        sec_fmt = _fmt(sec_val, unit)
        gap_pct = ((top_val - sec_val) / top_val * 100) if top_val else 0
        insights.append(
            f"**Runner-up Gap** — **{sec_name}** is second at {sec_fmt}, "
            f"trailing {top_name} by **{gap_pct:.1f}%** ({_fmt(top_val - sec_val, unit)}). "
            f"{'Narrow gap — leadership may be contested.' if gap_pct < 15 else 'Significant gap from the leader.'}"
        )

    # ── Risk threshold alerts ─────────────────────────────────────────────
    threshold = _RISK_THRESHOLDS.get(metric)
    if threshold and direction == "low":
        above_thresh = [r for r in rows if float(r.get(val_key, 0) or 0) > threshold]
        if above_thresh:
            names = ", ".join(str(r.get(x_key, "")) for r in sorted_rows if float(r.get(val_key, 0) or 0) > threshold)
            bottlenecks.append(
                f"**Risk Threshold Breach** — **{len(above_thresh)} of {n} segment(s)** exceed the "
                f"{_fmt(threshold, unit)} risk threshold: {names}. "
                f"Combined exposure is {_fmt(sum(float(r.get(val_key,0) or 0) for r in above_thresh), unit)}. "
                f"Immediate {domain} team review required."
            )

    # ── Time trend (time-series data) ─────────────────────────────────────
    x_key_lower = (x_key or "").lower()
    if x_key_lower in ("month", "txn_year_month", "as_of_date", "payment_date") and n >= 4:
        time_sorted = sorted(rows, key=lambda r: str(r.get(x_key, "")))
        half = max(n // 2, 2)
        recent_half = [float(r.get(val_key, 0) or 0) for r in time_sorted[-half:]]
        prior_half  = [float(r.get(val_key, 0) or 0) for r in time_sorted[:half]]
        r_avg = sum(recent_half) / len(recent_half) if recent_half else 0
        p_avg = sum(prior_half) / len(prior_half) if prior_half else 0
        if p_avg > 0:
            chg = (r_avg - p_avg) / p_avg * 100
            direction_word = "risen" if chg > 0 else "fallen"
            arrow = "↑" if chg > 0 else "↓"
            insights.append(
                f"**Trend ({arrow} {abs(chg):.1f}%)** — {val_label} has {direction_word} "
                f"{abs(chg):.1f}% in the recent {half} periods (avg {_fmt(r_avg, unit)}) "
                f"vs the prior {half} periods (avg {_fmt(p_avg, unit)}). "
                f"{'Accelerating — needs monitoring.' if abs(chg) > 20 else 'Gradual movement.'}"
            )
            if direction == "low" and chg > 10:
                bottlenecks.append(
                    f"**Deteriorating Trend** — {val_label} rose {abs(chg):.1f}% in recent periods. "
                    f"Early warning: if this continues, portfolio {domain} health may be at risk. "
                    f"Investigate root cause across segments immediately."
                )

    return insights, bottlenecks, kpis


def _rule_based_actions(rows, columns, metric: str, ctx: dict, bottlenecks: list[str], insights: list[str]) -> list[str]:
    """Generate specific recommended actions from statistical findings — no LLM needed."""
    actions: list[str] = []
    direction = ctx.get("direction", "high")
    unit = ctx.get("unit", "")
    domain = ctx.get("domain", "business")

    if not rows or not columns:
        return actions

    sample = rows[0]
    dim_cols, num_cols = _classify_cols(columns, sample)
    if not dim_cols or not num_cols:
        return actions

    x_key = dim_cols[0]
    val_key = num_cols[0]
    sorted_rows = sorted(rows, key=lambda r: float(r.get(val_key, 0) or 0), reverse=True)
    top = sorted_rows[0]
    top_name = str(top.get(x_key, "N/A"))
    top_val = float(top.get(val_key, 0) or 0)
    total = sum(float(r.get(val_key, 0) or 0) for r in rows)
    share = (top_val / total * 100) if total else 0

    val_label = val_key.replace("_", " ").title()
    top_fmt = _fmt(top_val, unit)

    # Action 1 — focus on top segment
    if direction == "low":
        actions.append(
            f"**Prioritise {top_name}:** Highest {val_label} at {top_fmt} ({share:.0f}% of total) — "
            f"escalate to {domain} team for immediate review."
        )
    else:
        actions.append(
            f"**Leverage {top_name}:** Top performer with {val_label} of {top_fmt} ({share:.0f}% of total) — "
            f"analyse and replicate this segment's success drivers."
        )

    # Action 2 — concentration risk
    if len(sorted_rows) >= 3:
        top3 = sum(float(r.get(val_key, 0) or 0) for r in sorted_rows[:3])
        top3_share = (top3 / total * 100) if total else 0
        if top3_share > 65:
            actions.append(
                f"**Reduce Concentration Risk:** Top 3 segments hold {top3_share:.0f}% of {val_label}. "
                f"Diversify exposure across remaining {len(sorted_rows) - 3} segments."
            )

    # Action 3 — bottom segment opportunity
    if len(sorted_rows) >= 5:
        bottom = sorted_rows[-1]
        bot_name = str(bottom.get(x_key, "N/A"))
        bot_val = float(bottom.get(val_key, 0) or 0)
        bot_fmt = _fmt(bot_val, unit)
        if direction == "high" and bot_val > 0:
            actions.append(
                f"**Investigate Underperformance in {bot_name}:** Lowest {val_label} at {bot_fmt}. "
                f"Review root cause and consider targeted intervention."
            )

    # Action 4 — forward-looking from bottlenecks
    for b in bottlenecks[:1]:
        clean = b.replace("**", "").split(".")[0]
        actions.append(f"**Address Alert:** {clean}. Schedule immediate {domain} team review.")

    # Action 5 — trend-based
    x_key_lower = (x_key or "").lower()
    if x_key_lower in ("month", "txn_year_month", "as_of_date") and len(sorted_rows) >= 3:
        time_sorted = sorted(rows, key=lambda r: str(r.get(x_key, "")))
        last_val = float(time_sorted[-1].get(val_key, 0) or 0)
        prev_val = float(time_sorted[-2].get(val_key, 0) or 0) if len(time_sorted) >= 2 else 0
        if prev_val > 0:
            chg = (last_val - prev_val) / prev_val * 100
            if abs(chg) > 10:
                word = "risen" if chg > 0 else "fallen"
                actions.append(
                    f"**Monitor Trend:** {val_label} has {word} {abs(chg):.0f}% in the latest period. "
                    f"Investigate cause and adjust {domain} strategy accordingly."
                )

    return actions[:5]


def _is_record_result(rows: list, columns: list) -> bool:
    """True when the result looks like individual records rather than aggregated metrics."""
    if not rows or not columns:
        return False
    _IDENTITY_COLS = {"customer_id", "full_name", "first_name", "last_name", "name",
                      "email", "phone", "customer_name", "account_id", "card_id"}
    return any(c.lower() in _IDENTITY_COLS for c in columns)


def insight_node(state: dict) -> dict:
    # Answer already composed upstream (e.g. unknown table short-circuit) — skip entirely
    if state.get("answer"):
        return state

    # preview_data and schema_query responses never need KPI cards or statistical insight
    response_mode = state.get("response_mode", "metric")
    if response_mode in ("table", "schema"):
        steps = list(state.get("reasoning_steps") or [])
        steps.append(f"Insight: skipped (response_mode={response_mode} — no analysis for raw data preview).")
        return {
            **state,
            "insights": [],
            "bottlenecks": [],
            "highlight_actions": [],
            "kpi_metrics": [],
            "reasoning_steps": steps,
        }

    query_result = state.get("query_result", {})
    semantic_context = state.get("semantic_context", {})
    user_message = state.get("user_message", "")
    rows = query_result.get("rows", [])
    columns = query_result.get("columns", [])
    metric = semantic_context.get("metric", "")
    is_free_form = semantic_context.get("free_form", False)
    steps = list(state.get("reasoning_steps") or [])

    if not rows:
        steps.append("Insight: no rows returned — skipping analysis.")
        return {
            **state,
            "insights": [f"No data is available for **your query** at this time. Verify the data source is loaded."],
            "bottlenecks": [],
            "highlight_actions": [],
            "kpi_metrics": [],
            "reasoning_steps": steps,
        }

    # Free-form queries have no known metric context — any statistical analysis
    # would compare arbitrary columns against each other, producing nonsense.
    # Skip entirely and let response_node describe the result plainly.
    if is_free_form:
        n = len(rows)
        steps.append(f"Insight: free-form query — skipping statistical analysis ({n} rows returned).")
        return {
            **state,
            "insights": [],
            "bottlenecks": [],
            "highlight_actions": [],
            "kpi_metrics": [],
            "reasoning_steps": steps,
        }

    ctx = _METRIC_CONTEXT.get(metric, {"unit": "", "direction": "high", "domain": "business"})

    # Statistical insights are always fast
    insights, bottlenecks, kpis = _statistical_insights(rows, columns, metric, ctx)

    # Rule-based actions — no LLM call, instant
    actions = _rule_based_actions(rows, columns, metric or "general analytics", ctx, bottlenecks, insights)

    # Fallback actions from statistical bottlenecks if rule engine returned nothing
    if not actions and bottlenecks:
        actions = [f"Investigate: {b}" for b in bottlenecks[:3]]

    steps.append(
        f"Insight: generated {len(insights)} insight(s), {len(bottlenecks)} bottleneck(s), "
        f"{len(actions)} action(s) from {len(rows)} rows."
    )

    return {
        **state,
        "insights": insights,
        "bottlenecks": bottlenecks,
        "highlight_actions": actions,
        "kpi_metrics": kpis,
        "reasoning_steps": steps,
    }

