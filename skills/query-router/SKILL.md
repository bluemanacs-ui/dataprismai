# Skill: query-router

## Purpose

Decide which query engine (StarRocks, Postgres, or a federation layer) should
execute a given SQL statement, based on table ownership, query complexity, and
engine availability.

## Inputs

| Field         | Type        | Description                                  |
| ------------- | ----------- | -------------------------------------------- |
| `sql`         | `str`       | Validated SQL ready for execution            |
| `tables_used` | `list[str]` | Table names extracted from the SQL           |
| `intent`      | `str`       | Planner intent (`exploratory`, `kpi`, `raw`) |

## Outputs

| Field    | Type  | Description                                  |
| -------- | ----- | -------------------------------------------- |
| `engine` | `str` | One of: `starrocks`, `postgres`, `trino`     |
| `reason` | `str` | One-line explanation of the routing decision |

## Routing Rules

| Condition                                    | Engine      |
| -------------------------------------------- | ----------- |
| Table belongs to `STARROCKS_DATABASE` schema | `starrocks` |
| Table belongs to operational Postgres schema | `postgres`  |
| Query JOINs across both schemas              | `trino`     |
| ENGINE env var explicitly set to `trino`     | `trino`     |
| Fallback (unknown table)                     | `starrocks` |

## Guardrails

- Never route DDL/DML to any engine (`sql_validator` must run first)
- If `trino` is not configured (`TRINO_HOST` not set), fall back to `starrocks`
- Log routing decision at DEBUG level with reason

## HOW TO ADD A NEW ENGINE:

1. Add `ENGINE_<NAME>=true` to `.env.example`
2. Add a connector in `apps/api/app/db/<engine>.py`
3. Extend routing rules in `apps/api/app/graph_nodes/query_router_node.py`
4. Update this SKILL.md

## Success Criteria

- All tables in `cc_analytics` (StarRocks) route to `starrocks`
- All tables in `dataprismai` (Postgres) route to `postgres`
- Unknown tables log a warning and do not crash

## Implementation

`apps/api/app/graph_nodes/query_router_node.py`
