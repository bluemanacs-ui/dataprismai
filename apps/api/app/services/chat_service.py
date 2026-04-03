from app.schemas.chat import ChatQueryRequest, ChatQueryResponse


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()

    return ChatQueryResponse(
        answer=(
            f"You asked: '{message}'.\n\n"
            "Revenue increased 14.2% over the selected period. "
            "West region contributed the strongest growth, while South remained nearly flat.\n\n"
            "This is currently a mock GenBI response from DataPrismAI."
        ),
        actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
        follow_ups=[
            "Compare by segment",
            "Analyze South region",
            "Show monthly contribution",
        ],
        chart_title="Revenue Trend by Region",
        chart_type="line",
        sql=(
            "SELECT month, region, SUM(revenue) AS revenue\n"
            "FROM sales\n"
            "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
            "GROUP BY month, region\n"
            "ORDER BY month ASC;"
        ),
        insights=[
            "Revenue is up 14.2% over the selected period.",
            "West region is the strongest contributor.",
            "South region may require investigation.",
        ],
        semantic_context={
            "metric": "Revenue",
            "dimensions": ["Region", "Month"],
            "engine": "StarRocks",
            "persona": payload.persona,
        },
    )
