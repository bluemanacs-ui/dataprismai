from app.services.chart_service import build_chart_recommendations

def visualization_node(state: dict) -> dict:
    # Always produces a valid visualization_config for the frontend.
    query_result = state.get("query_result", {})
    semantic_context = state.get("semantic_context", {})
    columns = query_result.get("columns", [])
    rows = query_result.get("rows", [])
    try:
        primary_chart, chart_recs = build_chart_recommendations(columns, rows, semantic_context)
        # For table-type charts use rows/columns payload (frontend table renderer
        # expects {rows, columns} not ChartConfig.data)
        if primary_chart.chart_type == "table":
            payload = {"columns": columns, "rows": rows}
        else:
            payload = primary_chart.model_dump()
        return {**state,
            "visualization_config": {
                "visualization_type": primary_chart.chart_type,
                "title": primary_chart.title,
                "description": getattr(primary_chart, 'description', ''),
                "payload": payload,
            },
            "visualization_recommendations": [rec.model_dump() for rec in chart_recs],
        }
    except Exception:
        return {**state,
            "visualization_config": {
                "visualization_type": "table",
                "title": "Results",
                "description": "No data available",
                "payload": {"columns": columns, "rows": rows},
            },
            "visualization_recommendations": [],
        }
