from app.prompts.persona_loader import load_persona_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse


def _build_answer(message: str, persona: str) -> tuple[str, list[str], list[str], list[str]]:
    persona = (persona or "analyst").lower()

    if persona == "cfo":
        answer = (
            f"Executive summary for: '{message}'\n\n"
            "Revenue increased 14.2% over the selected period. West region was the primary growth contributor, "
            "while South region remained nearly flat.\n\n"
            "The main business implication is concentration risk in growth performance, with over-reliance on one region."
        )
        actions = ["Show SQL", "Explain Metric", "View Risk Drivers", "Drill Down"]
        follow_ups = [
            "Show margin trend",
            "Highlight business risks",
            "Compare quarterly variance",
        ]
        insights = [
            "Revenue grew 14.2% over the period.",
            "Growth is concentrated in West region.",
            "South region stagnation could affect future performance.",
        ]
        return answer, actions, follow_ups, insights

    if persona == "manager":
        answer = (
            f"Performance summary for: '{message}'\n\n"
            "Revenue is up 14.2%. West region is performing strongest, while South region needs attention.\n\n"
            "This suggests one strong growth area and one underperforming area that may require action."
        )
        actions = ["Show SQL", "Explain", "Drill Down", "View Recommendations"]
        follow_ups = [
            "Analyze South region",
            "Compare by team or segment",
            "Show action opportunities",
        ]
        insights = [
            "West region is the top performer.",
            "South region may need corrective action.",
            "Results suggest uneven regional performance.",
        ]
        return answer, actions, follow_ups, insights

    if persona == "product":
        answer = (
            f"Product insight summary for: '{message}'\n\n"
            "Revenue increased 14.2%, with strongest contribution from West region. "
            "This may indicate stronger acquisition, conversion, or retention in that area.\n\n"
            "South region appears flat and is a candidate for deeper cohort or funnel analysis."
        )
        actions = ["Show SQL", "Explain", "View Segments", "Suggest Experiments"]
        follow_ups = [
            "Break down by acquisition channel",
            "Compare retention by region",
            "Suggest product experiments",
        ]
        insights = [
            "Growth may be tied to stronger regional behavior patterns.",
            "South region is a candidate for funnel analysis.",
            "Segment-level analysis is recommended.",
        ]
        return answer, actions, follow_ups, insights

    if persona == "engineer":
        answer = (
            f"Technical summary for: '{message}'\n\n"
            "The query indicates 14.2% revenue growth over the selected period. "
            "West region is the dominant contributor and South region remains nearly flat.\n\n"
            "This response is based on a mock semantic mapping using Revenue grouped by Month and Region."
        )
        actions = ["Show SQL", "Explain Join Path", "Inspect Semantic Context", "Drill Down"]
        follow_ups = [
            "Show execution assumptions",
            "Inspect metric definition",
            "Review SQL plan",
        ]
        insights = [
            "Semantic mapping used Revenue, Region, and Month.",
            "StarRocks is the current mock execution target.",
            "SQL and join behavior should be reviewed in live mode.",
        ]
        return answer, actions, follow_ups, insights

    answer = (
        f"Analytical summary for: '{message}'\n\n"
        "Revenue increased 14.2% over the selected period. West region contributed the strongest growth, "
        "while South remained nearly flat.\n\n"
        "This suggests a strong regional concentration pattern and a useful opportunity for deeper drilldown."
    )
    actions = ["Show SQL", "Explain", "Change Chart", "Drill Down"]
    follow_ups = [
        "Compare by segment",
        "Analyze South region",
        "Show monthly contribution",
    ]
    insights = [
        "Revenue is up 14.2% over the selected period.",
        "West region is the strongest contributor.",
        "South region may require investigation.",
    ]
    return answer, actions, follow_ups, insights


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    persona_prompt = load_persona_prompt(persona)
    answer, actions, follow_ups, insights = _build_answer(message, persona)

    return ChatQueryResponse(
        answer=answer,
        actions=actions,
        follow_ups=follow_ups,
        chart_title="Revenue Trend by Region",
        chart_type="line",
        sql=(
            "SELECT month, region, SUM(revenue) AS revenue\n"
            "FROM sales\n"
            "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
            "GROUP BY month, region\n"
            "ORDER BY month ASC;"
        ),
        insights=insights,
        semantic_context={
            "metric": "Revenue",
            "dimensions": ["Region", "Month"],
            "engine": "StarRocks",
            "persona": persona,
            "prompt_template_loaded": persona_prompt.splitlines()[0],
        },
    )
