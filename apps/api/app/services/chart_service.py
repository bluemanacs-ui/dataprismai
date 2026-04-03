from collections import defaultdict
from app.schemas.chart import ChartConfig, ChartSeries


def build_chart_config(
    result_columns: list[str],
    result_rows: list[dict],
    semantic_context: dict,
) -> ChartConfig:
    metric = semantic_context.get("metric", "Metric")
    dimensions = semantic_context.get("dimensions", [])

    if not result_rows:
        return ChartConfig(
            chart_type="table",
            x_key="",
            series=[],
            title=f"{metric} Results",
            description="No rows available for chart rendering.",
            data=[],
        )

    if "month" in result_columns and "value" in result_columns:
        if "region" in result_columns:
            pivoted = _pivot_rows(result_rows, x_key="month", series_key="region", value_key="value")
            series_names = sorted({row["region"] for row in result_rows if "region" in row})
            return ChartConfig(
                chart_type="line",
                x_key="month",
                series=[ChartSeries(key=name, label=name) for name in series_names],
                title=f"{metric} Trend by Region",
                description=f"Line chart of {metric} over time by region.",
                data=pivoted,
            )

        if "channel" in result_columns:
            pivoted = _pivot_rows(result_rows, x_key="month", series_key="channel", value_key="value")
            series_names = sorted({row["channel"] for row in result_rows if "channel" in row})
            return ChartConfig(
                chart_type="line",
                x_key="month",
                series=[ChartSeries(key=name, label=name) for name in series_names],
                title=f"{metric} Trend by Channel",
                description=f"Line chart of {metric} over time by channel.",
                data=pivoted,
            )

    first_dimension = dimensions[0].lower() if dimensions else ""
    if first_dimension in result_columns and "value" in result_columns:
        return ChartConfig(
            chart_type="bar",
            x_key=first_dimension,
            series=[ChartSeries(key="value", label=metric)],
            title=f"{metric} by {first_dimension.capitalize()}",
            description=f"Bar chart of {metric} by {first_dimension}.",
            data=result_rows,
        )

    return ChartConfig(
        chart_type="table",
        x_key="",
        series=[],
        title=f"{metric} Results",
        description="Fallback table chart configuration.",
        data=result_rows,
    )


def _pivot_rows(rows: list[dict], x_key: str, series_key: str, value_key: str) -> list[dict]:
    grouped: dict[str, dict] = defaultdict(dict)

    for row in rows:
        x_val = row.get(x_key)
        s_val = row.get(series_key)
        v_val = row.get(value_key)

        if x_val is None or s_val is None:
            continue

        grouped[x_val][x_key] = x_val
        grouped[x_val][str(s_val)] = v_val

    return [grouped[key] for key in sorted(grouped.keys())]
