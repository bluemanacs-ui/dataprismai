def build_training_context(semantic_context: dict) -> dict:
    metric = semantic_context.get("metric", "Revenue")
    dimensions = semantic_context.get("dimensions", ["Region", "Month"])
    domain = semantic_context.get("domain", "Sales")
    definition = semantic_context.get("definition", "No definition available.")

    ddl = """
CREATE TABLE semantic_model_table (
    month TEXT,
    region TEXT,
    segment TEXT,
    product TEXT,
    channel TEXT,
    revenue NUMERIC,
    margin NUMERIC,
    churn_rate NUMERIC,
    retention NUMERIC
);
""".strip()

    documentation = f"""
Domain: {domain}
Metric: {metric}
Definition: {definition}
Supported dimensions: {", ".join(dimensions)}
Use semantic_model_table as the primary table.
Prefer read-only SELECT queries.
""".strip()

    examples = [
        {
            "question": "Show revenue by region and month",
            "sql": (
                "SELECT region, month, SUM(revenue) AS total_revenue "
                "FROM semantic_model_table "
                "GROUP BY region, month"
            ),
        },
        {
            "question": "Compare margin by product",
            "sql": (
                "SELECT product, AVG(margin) AS avg_margin "
                "FROM semantic_model_table "
                "GROUP BY product"
            ),
        },
        {
            "question": "Show churn by channel and month",
            "sql": (
                "SELECT channel, month, AVG(churn_rate) AS churn_rate "
                "FROM semantic_model_table "
                "GROUP BY channel, month"
            ),
        },
    ]

    return {
        "ddl": ddl,
        "documentation": documentation,
        "examples": examples,
    }
