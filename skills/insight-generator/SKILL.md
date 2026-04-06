# Skill: insight-generator

## Purpose

Generate a concise, human-readable narrative summary of a SQL result set,
including trend identification, anomaly calling, and key takeaways. Output
is structured so the frontend can display highlighted KPI cards alongside
the narrative.

## Inputs

| Field           | Type         | Description                                 |
| --------------- | ------------ | ------------------------------------------- |
| `rows`          | `list[dict]` | Query result rows                           |
| `columns`       | `list[str]`  | Ordered column names                        |
| `user_question` | `str`        | Original NL question                        |
| `sql`           | `str`        | Executed SQL (for attribution in narrative) |
| `persona`       | `str`        | Active persona (influences narrative tone)  |

## Outputs

| Field        | Type         | Description                                         |
| ------------ | ------------ | --------------------------------------------------- |
| `summary`    | `str`        | 2–4 sentence narrative covering the key finding     |
| `kpis`       | `list[dict]` | `[{label, value, trend, unit}]` — up to 5 KPI cards |
| `anomalies`  | `list[str]`  | Notable outliers or data-quality observations       |
| `follow_ups` | `list[str]`  | 3 suggested next questions                          |

## Guardrails

- Do not fabricate numbers not present in `rows`
- Do not expose raw SQL in the narrative unless explicitly asked
- Narrative must be factual and attribution-correct (cite metric names, not guesses)
- Follow-up questions must be answerable from the same data schema

## Tone by Persona

- **analyst** — concise, metric-first, uses percentages and comparisons
- **executive** — bullet-first, trend-focused, avoids jargon
- **developer** — technical, includes column names and data-type notes

## Success Criteria

- KPI values appear in the result rows (no hallucination)
- Summary is ≤ 120 words
- At least one anomaly or trend identified per response

## Implementation

`apps/api/app/graph_nodes/insight_node.py`
