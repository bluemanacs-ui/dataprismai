# Skill: chart-recommender

## Purpose

Given a SQL result set, recommend the most appropriate chart type and produce
an ECharts-compatible configuration object so the frontend can render the
visualisation without additional logic.

## Inputs

| Field           | Type             | Description                                        |
| --------------- | ---------------- | -------------------------------------------------- |
| `rows`          | `list[dict]`     | Query result rows (max 10 000)                     |
| `columns`       | `list[str]`      | Ordered column names                               |
| `user_question` | `str`            | Original NL question (used for axis label context) |
| `persona`       | `str` (optional) | Active persona name                                |

## Outputs

| Field          | Type   | Description                                                 |
| -------------- | ------ | ----------------------------------------------------------- |
| `chart_type`   | `str`  | One of: `bar`, `line`, `pie`, `scatter`, `heatmap`, `table` |
| `chart_config` | `dict` | Full ECharts `option` object (xAxis, yAxis, series, …)      |

## Selection Rules

1. **Time-series data** (column contains date/timestamp) → `line`
2. **Single numeric measure with category dimension** → `bar`
3. **Part-of-whole with ≤ 8 categories** → `pie`
4. **Two numeric measures** → `scatter`
5. **Matrix (rows × cols both categorical)** → `heatmap`
6. **All other cases / wide tables** → `table`

## Guardrails

- Never include raw PII in axis labels
- Cap series data at 500 points; aggregate remainder into "Other"
- Always set a title derived from `user_question`

## Success Criteria

- `chart_config` can be passed directly to `echarts.init().setOption(chart_config)`
- Chart type matches the data shape at least 90 % of the time on test fixtures
- PDF export: chart rendered on `<canvas>` using ECharts canvas renderer

## Implementation

`apps/api/app/graph_nodes/visualization_node.py`
