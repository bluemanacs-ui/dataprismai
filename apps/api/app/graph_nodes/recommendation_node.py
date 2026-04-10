"""Recommendation node — persona-aware follow-up suggestions.

Each persona maps to a curated set of metric-based and free-form follow-ups so
that every response surfaces contextually relevant next questions, not generic ones.
"""

# ── Per-metric follow-ups (universal, across personas) ───────────────────────
_METRIC_FOLLOW_UPS: dict[str, list[str]] = {
    "Total Spend": [
        "Show fraud rate by merchant category",
        "How many transactions per merchant this period?",
        "Show monthly spend trend over the last 12 months",
        "Which merchant category has the highest spend growth?",
        "Show dispute rate by merchant category",
    ],
    "Transaction Count": [
        "Show total spend trend by month",
        "What is the fraud rate per merchant?",
        "Show payment volume by month",
        "Which channel (online vs POS) has more transactions?",
        "Show average transaction value by merchant category",
    ],
    "Fraud Rate": [
        "Show suspicious transactions in the last 30 days",
        "What is the dispute rate by merchant?",
        "Show fraud breakdown by transaction count",
        "Which merchants have the highest fraud score?",
        "Show fraud trend by country code",
    ],
    "Delinquency Rate": [
        "Show account utilization by product",
        "Which customer segment has the highest delinquency?",
        "Show payment volume trend by month",
        "List overdue accounts by country",
        "Show delinquency bucket distribution (1-30, 31-60, 61-90, 91+)",
    ],
    "Account Utilization": [
        "Show delinquency rate by account status",
        "What is the average customer credit score?",
        "Show total spend by merchant category",
        "Which customer segment has highest utilization?",
        "Show utilization trend over last 6 months",
    ],
    "Payment Status": [
        "Show total spend trend by month",
        "What is the delinquency rate by account status?",
        "Show transaction count by merchant",
        "Which customers have upcoming due dates?",
        "Compare autopay vs manual payment split",
    ],
    "Dispute Rate": [
        "Show fraud rate by merchant category",
        "What is the total spend by merchant?",
        "How many transactions per merchant?",
        "Which merchants have unresolved disputes?",
        "Show dispute trend over last 3 months",
    ],
    "Customer Profile": [
        "Show delinquency rate by account status",
        "What is account utilization by segment?",
        "Show payment status distribution across all accounts",
        "Segment customers by credit band (POOR/FAIR/GOOD/EXCELLENT)",
        "Correlate credit score with spend behaviour",
        "Show top 10 customers by MTD spend",
    ],
    "Portfolio KPIs": [
        "What is the delinquency rate by country this quarter?",
        "Show total payment volume vs spend for the last 3 months",
        "Which legal entity has the highest revenue this month?",
        "Show portfolio NPL ratio trend by country",
        "Compare customer growth MoM across all entities",
    ],
}

# ── Per-metric insight recommendations (universal) ───────────────────────────
_METRIC_INSIGHT_RECS: dict[str, list[str]] = {
    "Total Spend": [
        "Compare total spend vs transaction count to detect avg ticket size shift",
        "Analyze spend concentration — are top 3 merchants driving >50% of volume?",
        "Show MoM spend trend to identify seasonal peaks",
    ],
    "Transaction Count": [
        "Show average transaction value per merchant to detect basket-size change",
        "Compare transaction count vs fraud rate — high volume + high fraud = priority",
        "Identify low-volume high-spend merchants for fraud profiling",
    ],
    "Fraud Rate": [
        "Cross-reference fraud rate with transaction volume by merchant",
        "Show fraud trend over 6 months — is it rising or stable?",
        "Compare fraud rate vs dispute rate — gap may indicate unreported fraud",
    ],
    "Delinquency Rate": [
        "Segment delinquent accounts by product type to find highest-risk product",
        "Correlate delinquency with credit utilization — high util = high risk",
        "Track delinquency trend monthly to detect early warning signals",
    ],
    "Account Utilization": [
        "Identify high-utilization segments (>80%) for proactive risk review",
        "Compare utilization across income/credit bands",
        "Track utilization changes MoM — rising util is an early delinquency signal",
    ],
    "Payment Status": [
        "Compare payment volume vs total spend — coverage ratio indicates health",
        "Identify months with payment drop-offs — seasonal or systemic issue?",
        "Analyze autopay vs manual payment split for collections strategy",
    ],
    "Dispute Rate": [
        "Compare dispute rate vs fraud rate — high dispute + low fraud = ops issue",
        "Identify merchants with high dispute concentration for review",
        "Track dispute resolution outcomes — resolution rate matters",
    ],
    "Customer Profile": [
        "Segment credit scores by product type — which product attracts riskiest customers?",
        "Correlate credit score with delinquency risk to validate scoring model",
        "Compare scores and utilization across income/age bands to detect mis-segmentation",
    ],
    "Portfolio KPIs": [
        "Compare KPIs QoQ across legal entities to identify margin pressure or growth drivers",
        "Segment delinquency by country and product for regional P&L attribution",
        "Review NPL trend vs customer growth to assess portfolio quality trajectory",
    ],
}

# ── Persona-specific default follow-ups (for free-form / no metric match) ────
_PERSONA_DEFAULTS: dict[str, dict[str, list[str]]] = {
    "fraud_analyst": {
        "follow_ups": [
            "Show top 10 suspicious transactions this week",
            "What is the fraud rate by merchant category this month?",
            "Show accounts with active fraud alerts",
            "Which country has the highest fraud score trend?",
            "Show declined transactions with high fraud score (>0.85)",
        ],
        "insight_recs": [
            "Cross-check fraud spikes vs transaction volume to isolate merchant/channel clusters",
            "Review fraud_score distribution — share of >0.85 vs 0.6–0.85 indicates severity",
            "Compare fraud trends by country_code to identify regional hot spots",
        ],
    },
    "retail_user": {
        "follow_ups": [
            "Show total spend by merchant category this month",
            "Which customers are overdue on payments?",
            "What is the average account utilization by segment?",
            "Show top 10 customers by MTD spend",
            "Show payment status distribution across all accounts",
        ],
        "insight_recs": [
            "Review overdue accounts by customer segment to prioritise collections outreach",
            "Compare MTD spend vs last month to gauge portfolio momentum",
            "Identify accounts approaching credit limit (util >80%) for proactive contact",
        ],
    },
    "finance_user": {
        "follow_ups": [
            "Show total payment volume this quarter vs last quarter",
            "What is the portfolio delinquency rate by country?",
            "Show MTD spend vs prior month across all segments",
            "Which legal entity has the highest revenue this month?",
            "Show portfolio KPIs — utilization, delinquency, spend",
        ],
        "insight_recs": [
            "Compare revenue KPIs QoQ to identify margin pressure or growth drivers",
            "Segment delinquency by country and product for regional P&L attribution",
            "Review fee income vs spend volume correlation across product lines",
        ],
    },
    "regional_finance_user": {
        "follow_ups": [
            "Show portfolio KPIs for each country this month",
            "What is the regional delinquency rate compared to global average?",
            "Show total spend by country and segment",
            "Which country had the biggest MoM spend change?",
            "Show payment volume by country this quarter",
        ],
        "insight_recs": [
            "Compare regional KPIs vs global benchmarks to identify outlier markets",
            "Review country-level delinquency for early regional risk signals",
            "Track MoM spend per country to detect regional growth or contraction",
        ],
    },
    "regional_risk_user": {
        "follow_ups": [
            "Show fraud rate by country and merchant category",
            "Which region has the highest delinquency rate?",
            "Show suspicious transactions by country this week",
            "What is the fraud trend by country over the last 3 months?",
            "Show high-risk accounts by country",
        ],
        "insight_recs": [
            "Cross-reference regional fraud rates with global baseline to flag anomalies",
            "Identify country-specific merchant categories with rising fraud scores",
            "Review delinquency bucket distribution by region for portfolio health dashboard",
        ],
    },
    "analyst": {
        "follow_ups": [
            "Show total spend by merchant category",
            "What is the fraud rate by merchant?",
            "Show payment volume trend",
            "Show customer distribution by segment",
            "Show monthly transaction count trend",
        ],
        "insight_recs": [
            "Drill deeper into the query results to identify sub-segment patterns",
            "Compare results over time to detect trends",
            "Segment findings by category or region for actionable insight",
        ],
    },
}

# Fallback for any unrecognised persona
_DEFAULT_PERSONA = "analyst"


def recommendation_node(state: dict) -> dict:
    from app.services.config_service import config_svc
    if not config_svc.get_bool("graph.enable_chart_recommendation", True):
        return {**state, "insight_recommendations": [], "follow_ups": [], "assumptions": []}
    # preview_data and schema_query should not generate follow-up recommendations
    response_mode = state.get("response_mode", "metric")
    if response_mode in ("table", "schema"):
        return {
            **state,
            "insight_recommendations": [],
            "follow_ups": [],
            "assumptions": [],
        }

    # On error: skip semantic context but still generate persona-based recommendations
    semantic_context = state.get("semantic_context", {}) if not state.get("error") else {}
    metric = semantic_context.get("metric", "")
    persona = (state.get("persona") or _DEFAULT_PERSONA).lower()
    assumptions = state.get("sql_assumptions", [])
    message = (state.get("user_message") or "").lower()

    # ── Build persona defaults (fallback when no metric matched or on error) ─
    persona_defaults = _PERSONA_DEFAULTS.get(persona) or _PERSONA_DEFAULTS[_DEFAULT_PERSONA]

    # ── Follow-ups: merge metric-specific + persona defaults (deduped pool) ──
    metric_followups = _METRIC_FOLLOW_UPS.get(metric, [])
    if metric_followups:
        seen_fu: set[str] = set()
        follow_ups: list[str] = []
        for q in metric_followups + persona_defaults["follow_ups"]:
            if q not in seen_fu:
                seen_fu.add(q)
                follow_ups.append(q)
    else:
        follow_ups = list(persona_defaults["follow_ups"])

    # ── Insight recommendations: merge metric + persona (deduped pool) ───────
    if metric and metric in _METRIC_INSIGHT_RECS:
        seen_rec: set[str] = set()
        insight_recs: list[str] = []
        for r in _METRIC_INSIGHT_RECS[metric] + persona_defaults["insight_recs"]:
            if r not in seen_rec:
                seen_rec.add(r)
                insight_recs.append(r)
    else:
        insight_recs = list(persona_defaults["insight_recs"])

    # ── Inject time-range context into suggestions if relevant ───────────────
    time_range = semantic_context.get("time_range", "")
    if time_range and "month" not in message and "week" not in message:
        follow_ups = [f"{q} ({time_range})" if i == 0 else q for i, q in enumerate(follow_ups)]

    # Return full pool — frontend shows 3 at a time with a refresh button
    return {
        **state,
        "insight_recommendations": insight_recs,
        "follow_ups": follow_ups,
        "assumptions": assumptions[:5],
    }
