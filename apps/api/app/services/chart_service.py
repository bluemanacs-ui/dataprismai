from collections import defaultdict
from app.schemas.chart import ChartConfig, ChartRecommendation, ChartSeries


def build_chart_recommendations(
    result_columns: list[str],
    result_rows: list[dict],
    semantic_context: dict,
) -> tuple[ChartConfig, list[ChartRecommendation]]:
    metric = semantic_context.get("metric", "Metric")
    dimensions = semantic_context.get("dimensions", [])

    if not result_rows:
        empty = ChartConfig(
            chart_type="table",
            x_key="",
            series=[],
            title=f"{metric} Results",
            description="No rows available for chart rendering.",
            data=[],
        )
        return empty, []

    recommendations: list[ChartRecommendation] = []

    if "month" in result_columns and "value" in result_columns:
        if "region" in result_columns:
            pivoted = _pivot_rows(result_rows, x_key="month", series_key="region", value_key="value")
            series_names = sorted({row["region"] for row in result_rows if "region" in row})

            line_chart = ChartConfig(
                chart_type="line",
                x_key="month",
                series=[ChartSeries(key=name, label=name) for name in series_names],
                title=f"{metric} Trend by Region",
                description=f"Line chart of {metric} over time by region.",
                data=pivoted,
            )

            recommendations.append(
                ChartRecommendation(
                    id="line-trend",
                    label="Trend View",
                    reason="Best for showing changes over time.",
                    chart_config=line_chart,
                )
            )

            bar_latest = ChartConfig(
                chart_type="bar",
                x_key="region",
                series=[ChartSeries(key="value", label=metric)],
                title=f"{metric} Latest Comparison by Region",
                description=f"Bar chart comparing {metric} across regions.",
                data=_latest_period_bar(result_rows, group_key="region", value_key="value"),
            )

            recommendations.append(
                ChartRecommendation(
                    id="bar-compare",
                    label="Comparison View",
                    reason="Useful for comparing categories directly.",
                    chart_config=bar_latest,
                )
            )

            pie_latest = ChartConfig(
                chart_type="pie",
                x_key="region",
                series=[ChartSeries(key="value", label=metric)],
                title=f"{metric} Share by Region",
                description=f"Pie chart showing share of {metric} by region.",
                data=_latest_period_bar(result_rows, group_key="region", value_key="value"),
            )

            recommendations.append(
                ChartRecommendation(
                    id="pie-share",
                    label="Share View",
                    reason="Great for seeing relative contribution by region.",
                    chart_config=pie_latest,
                )
            )

            donut_latest = ChartConfig(
                chart_type="donut",
                x_key="region",
                series=[ChartSeries(key="value", label=metric)],
                title=f"{metric} Donut by Region",
                description=f"Donut chart focused on {metric} share by region.",
                data=_latest_period_bar(result_rows, group_key="region", value_key="value"),
            )

            recommendations.append(
                ChartRecommendation(
                    id="donut-share",
                    label="Donut View",
                    reason="Good for an alternative composition view.",
                    chart_config=donut_latest,
                )
            )

            return line_chart, recommendations

        if "channel" in result_columns:
            pivoted = _pivot_rows(result_rows, x_key="month", series_key="channel", value_key="value")
            series_names = sorted({row["channel"] for row in result_rows if "channel" in row})

            line_chart = ChartConfig(
                chart_type="line",
                x_key="month",
                series=[ChartSeries(key=name, label=name) for name in series_names],
                title=f"{metric} Trend by Channel",
                description=f"Line chart of {metric} over time by channel.",
                data=pivoted,
            )

            recommendations.append(
                ChartRecommendation(
                    id="line-trend",
                    label="Trend View",
                    reason="Best for time-based movement.",
                    chart_config=line_chart,
                )
            )

            bar_latest = ChartConfig(
                chart_type="bar",
                x_key="channel",
                series=[ChartSeries(key="value", label=metric)],
                title=f"{metric} Latest Comparison by Channel",
                description=f"Bar chart comparing {metric} by channel.",
                data=_latest_period_bar(result_rows, group_key="channel", value_key="value"),
            )

            recommendations.append(
                ChartRecommendation(
                    id="bar-compare",
                    label="Channel Comparison",
                    reason="Useful for channel-by-channel ranking.",
                    chart_config=bar_latest,
                )
            )

            pie_latest = ChartConfig(
                chart_type="pie",
                x_key="channel",
                series=[ChartSeries(key="value", label=metric)],
                title=f"{metric} Share by Channel",
                description=f"Pie chart showing share of {metric} by channel.",
                data=_latest_period_bar(result_rows, group_key="channel", value_key="value"),
            )

            recommendations.append(
                ChartRecommendation(
                    id="pie-share",
                    label="Share View",
                    reason="Great for seeing relative channel contribution.",
                    chart_config=pie_latest,
                )
            )

            donut_latest = ChartConfig(
                chart_type="donut",
                x_key="channel",
                series=[ChartSeries(key="value", label=metric)],
                title=f"{metric} Donut by Channel",
                description=f"Donut chart showing share of {metric} by channel.",
                data=_latest_period_bar(result_rows, group_key="channel", value_key="value"),
            )

            recommendations.append(
                ChartRecommendation(
                    id="donut-share",
                    label="Donut View",
                    reason="Good for an alternative composition visual.",
                    chart_config=donut_latest,
                )
            )

            return line_chart, recommendations

    first_dimension = dimensions[0].lower() if dimensions else ""
    if first_dimension in result_columns and "value" in result_columns:
        bar_chart = ChartConfig(
            chart_type="bar",
            x_key=first_dimension,
            series=[ChartSeries(key="value", label=metric)],
            title=f"{metric} by {first_dimension.capitalize()}",
            description=f"Bar chart of {metric} by {first_dimension}.",
            data=result_rows,
        )

        recommendations.append(
            ChartRecommendation(
                id="bar-default",
                label="Bar View",
                reason="Best default for grouped comparisons.",
                chart_config=bar_chart,
            )
        )

        pie_chart = ChartConfig(
            chart_type="pie",
            x_key=first_dimension,
            series=[ChartSeries(key="value", label=metric)],
            title=f"{metric} Share by {first_dimension.capitalize()}",
            description=f"Pie chart showing share of {metric} by {first_dimension}.",
            data=result_rows,
        )

        recommendations.append(
            ChartRecommendation(
                id="pie-default",
                label="Share View",
                reason="Great for seeing relative contribution across categories.",
                chart_config=pie_chart,
            )
        )

        donut_chart = ChartConfig(
            chart_type="donut",
            x_key=first_dimension,
            series=[ChartSeries(key="value", label=metric)],
            title=f"{metric} Donut by {first_dimension.capitalize()}",
            description=f"Donut chart showing share of {metric} by {first_dimension}.",
            data=result_rows,
        )

        recommendations.append(
            ChartRecommendation(
                id="donut-default",
                label="Donut View",
                reason="Great for a more compact share visual.",
                chart_config=donut_chart,
            )
        )

        return bar_chart, recommendations

    # Generic fallback: auto-detect dimension (x_key) and measure columns
    _sample = result_rows[0]

    _DIMENSION_KEYWORDS = {
        "category", "code", "id", "name", "type", "bucket",
        "flag", "channel", "region", "segment", "status", "label",
        "group", "tier", "class", "kind", "source", "brand",
    }
    _MEASURE_KEYWORDS = {
        "amount", "spend", "rate", "count", "pct", "percent", "score",
        "total", "sum", "avg", "average", "revenue", "value", "balance",
        "fee", "charge", "volume", "num", "number",
    }

    def _col_is_dimension(col: str) -> bool:
        col_lower = col.lower()
        if any(kw in col_lower for kw in _DIMENSION_KEYWORDS):
            return True
        if any(kw in col_lower for kw in _MEASURE_KEYWORDS):
            return False
        # Fall back to value type — if not a large float, treat as dimension
        val = _sample.get(col)
        if val is None:
            return True
        try:
            fval = float(val)
            # Small integers that look like codes (< 10_000 with no decimals) are dimensions
            return fval == int(fval) and abs(fval) < 10_000 and "." not in str(val)
        except (TypeError, ValueError):
            return True

    def _is_numeric(val) -> bool:
        if val is None:
            return False
        try:
            float(val)
            return True
        except (TypeError, ValueError):
            return False

    dim_cols = [c for c in result_columns if _col_is_dimension(c)]
    num_cols = [c for c in result_columns if not _col_is_dimension(c) and _is_numeric(_sample.get(c))]

    # Last resort: if nothing classified as dimension, use first column as x_key
    if not dim_cols and num_cols:
        dim_cols = [result_columns[0]]
        num_cols = [c for c in num_cols if c != result_columns[0]]

    if dim_cols and num_cols:
        x_key = dim_cols[0]
        primary_series = num_cols[0]
        series_list = [ChartSeries(key=c, label=c.replace("_", " ").title()) for c in num_cols]
        x_label = x_key.replace("_", " ").title()
        primary_label = primary_series.replace("_", " ").title()

        # Use line chart as primary for time-series data (month/date x-axis)
        _is_timeseries = any(kw in x_key.lower() for kw in ("month", "date", "week", "year", "quarter", "period", "time"))
        primary_chart_type = "line" if _is_timeseries else "bar"

        bar_chart = ChartConfig(
            chart_type=primary_chart_type,
            x_key=x_key,
            series=series_list,
            title=f"{metric} by {x_label}",
            description=f"{primary_chart_type.title()} chart of {metric} grouped by {x_label}.",
            data=result_rows[:50],
        )

        # Line chart
        recommendations.append(ChartRecommendation(
            id="line-trend",
            label="Line",
            reason="Shows value trajectory across categories.",
            chart_config=ChartConfig(
                chart_type="line",
                x_key=x_key,
                series=series_list,
                title=f"{metric} Line by {x_label}",
                description=f"Line view of {metric} across {x_label}.",
                data=result_rows[:50],
            ),
        ))

        # Pie chart
        recommendations.append(ChartRecommendation(
            id="pie-share",
            label="Pie",
            reason="Shows relative proportion across categories.",
            chart_config=ChartConfig(
                chart_type="pie",
                x_key=x_key,
                series=[ChartSeries(key=primary_series, label=primary_label)],
                title=f"{metric} Share by {x_label}",
                description=f"Pie chart showing share of {metric} by {x_label}.",
                data=result_rows[:20],
            ),
        ))

        # Donut chart
        recommendations.append(ChartRecommendation(
            id="donut-share",
            label="Donut",
            reason="Compact proportional ring chart.",
            chart_config=ChartConfig(
                chart_type="donut",
                x_key=x_key,
                series=[ChartSeries(key=primary_series, label=primary_label)],
                title=f"{metric} Donut by {x_label}",
                description=f"Donut chart showing share of {metric} by {x_label}.",
                data=result_rows[:20],
            ),
        ))

        # Funnel chart (great for sorted/ranked data)
        recommendations.append(ChartRecommendation(
            id="funnel-ranked",
            label="Funnel",
            reason="Best for visualizing ranked or top-N comparisons.",
            chart_config=ChartConfig(
                chart_type="funnel",
                x_key=x_key,
                series=[ChartSeries(key=primary_series, label=primary_label)],
                title=f"{metric} Funnel by {x_label}",
                description=f"Funnel chart showing ranked {metric} by {x_label}.",
                data=result_rows[:20],
            ),
        ))

        # Treemap (proportional area view)
        recommendations.append(ChartRecommendation(
            id="treemap-prop",
            label="Treemap",
            reason="Proportional area tiles, great for comparing many categories.",
            chart_config=ChartConfig(
                chart_type="treemap",
                x_key=x_key,
                series=[ChartSeries(key=primary_series, label=primary_label)],
                title=f"{metric} Treemap by {x_label}",
                description=f"Treemap showing proportional {metric} by {x_label}.",
                data=result_rows[:50],
            ),
        ))

        # Sunburst (hierarchical ring)
        recommendations.append(ChartRecommendation(
            id="sunburst-hier",
            label="Sunburst",
            reason="Ring chart ideal for hierarchical or categorical breakdowns.",
            chart_config=ChartConfig(
                chart_type="sunburst",
                x_key=x_key,
                series=[ChartSeries(key=primary_series, label=primary_label)],
                title=f"{metric} Sunburst by {x_label}",
                description=f"Sunburst chart showing {metric} by {x_label}.",
                data=result_rows[:30],
            ),
        ))

        # Area chart
        recommendations.append(ChartRecommendation(
            id="area-fill",
            label="Area",
            reason="Filled line chart emphasising volume.",
            chart_config=ChartConfig(
                chart_type="area",
                x_key=x_key,
                series=series_list,
                title=f"{metric} Area by {x_label}",
                description=f"Area chart of {metric} across {x_label}.",
                data=result_rows[:50],
            ),
        ))

        # Scatter (only when 2+ numeric cols — bivariate correlation)
        if len(num_cols) >= 2:
            recommendations.append(ChartRecommendation(
                id="scatter-bivariate",
                label="Scatter",
                reason="Spots correlations between two numeric measures.",
                chart_config=ChartConfig(
                    chart_type="scatter",
                    x_key=x_key,
                    series=[ChartSeries(key=c, label=c.replace("_", " ").title()) for c in num_cols[:2]],
                    title=f"{num_cols[0].replace('_', ' ').title()} vs {num_cols[1].replace('_', ' ').title()}",
                    description=f"Scatter plot comparing {num_cols[0]} against {num_cols[1]} by {x_label}.",
                    data=result_rows[:50],
                ),
            ))

        # Gauge (only for single-row results — single KPI)
        if len(result_rows) == 1:
            recommendations.append(ChartRecommendation(
                id="gauge-meter",
                label="Gauge",
                reason="Single-value meter, best for KPIs with a target.",
                chart_config=ChartConfig(
                    chart_type="gauge",
                    x_key=x_key,
                    series=[ChartSeries(key=primary_series, label=primary_label)],
                    title=f"{metric} Gauge",
                    description=f"Gauge meter for {metric}.",
                    data=result_rows[:1],
                ),
            ))

        # Heatmap (only when 2 dimension cols)
        if len(dim_cols) >= 2:
            recommendations.append(ChartRecommendation(
                id="heatmap-matrix",
                label="Heatmap",
                reason="Matrix view for comparing values across two dimensions.",
                chart_config=ChartConfig(
                    chart_type="heatmap",
                    x_key=dim_cols[0],
                    series=[
                        ChartSeries(key=dim_cols[1], label=dim_cols[1].replace("_", " ").title()),
                        ChartSeries(key=primary_series, label=primary_label),
                    ],
                    title=f"{metric} Heatmap",
                    description=f"Heatmap of {metric} by {dim_cols[0]} and {dim_cols[1]}.",
                    data=result_rows[:100],
                ),
            ))

        return bar_chart, recommendations

    fallback = ChartConfig(
        chart_type="table",
        x_key="",
        series=[],
        title=f"{metric} Results",
        description="Fallback table chart configuration.",
        data=result_rows,
    )

    return fallback, recommendations


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


def _latest_period_bar(rows: list[dict], group_key: str, value_key: str) -> list[dict]:
    latest_key = max(row["month"] for row in rows if "month" in row)
    latest_rows = [row for row in rows if row.get("month") == latest_key]

    return [
        {
            group_key: row.get(group_key),
            "value": row.get(value_key),
        }
        for row in latest_rows
    ]
