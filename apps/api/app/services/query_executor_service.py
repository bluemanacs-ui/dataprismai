from app.schemas.execution import QueryExecutionResult


def execute_query(engine: str, sql: str, semantic_context: dict) -> QueryExecutionResult:
    engine_normalized = (engine or "starrocks").lower()

    if engine_normalized == "trino":
        return _execute_trino_mock(sql, semantic_context)

    return _execute_starrocks_mock(sql, semantic_context)


def _execute_starrocks_mock(sql: str, semantic_context: dict) -> QueryExecutionResult:
    metric = semantic_context.get("metric", "Revenue")

    rows = [
        {"month": "2025-01", "region": "West", "value": 120000},
        {"month": "2025-02", "region": "West", "value": 128000},
        {"month": "2025-03", "region": "West", "value": 135000},
        {"month": "2025-01", "region": "South", "value": 98000},
        {"month": "2025-02", "region": "South", "value": 99000},
        {"month": "2025-03", "region": "South", "value": 99500},
    ]

    return QueryExecutionResult(
        engine="StarRocks",
        columns=["month", "region", "value"],
        rows=rows,
        row_count=len(rows),
        execution_time_ms=142,
        status=f"mock_success_{metric.lower().replace(' ', '_')}",
    )


def _execute_trino_mock(sql: str, semantic_context: dict) -> QueryExecutionResult:
    metric = semantic_context.get("metric", "Churn Rate")

    rows = [
        {"month": "2025-01", "channel": "Organic", "value": 4.2},
        {"month": "2025-02", "channel": "Organic", "value": 4.0},
        {"month": "2025-03", "channel": "Organic", "value": 3.8},
        {"month": "2025-01", "channel": "Paid", "value": 5.1},
        {"month": "2025-02", "channel": "Paid", "value": 5.4},
        {"month": "2025-03", "channel": "Paid", "value": 5.0},
    ]

    return QueryExecutionResult(
        engine="Trino",
        columns=["month", "channel", "value"],
        rows=rows,
        row_count=len(rows),
        execution_time_ms=286,
        status=f"mock_success_{metric.lower().replace(' ', '_')}",
    )
