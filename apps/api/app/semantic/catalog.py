SEMANTIC_CATALOG = {
    "metrics": [
        {
            "name": "Revenue",
            "keywords": ["revenue", "sales", "income"],
            "dimensions": ["Region", "Month", "Segment", "Product"],
            "engine": "StarRocks",
            "domain": "Sales",
            "definition": "Sum of recognized revenue over the selected time period.",
        },
        {
            "name": "Margin",
            "keywords": ["margin", "gross margin", "profit margin"],
            "dimensions": ["Region", "Month", "Segment", "Product"],
            "engine": "StarRocks",
            "domain": "Finance",
            "definition": "Gross margin percentage over the selected time period.",
        },
        {
            "name": "Churn Rate",
            "keywords": ["churn", "attrition", "customer loss"],
            "dimensions": ["Region", "Month", "Segment", "Channel"],
            "engine": "Trino",
            "domain": "Customer",
            "definition": "Percentage of customers lost over the selected time period.",
        },
        {
            "name": "Retention",
            "keywords": ["retention", "customer retention", "repeat rate"],
            "dimensions": ["Region", "Month", "Segment", "Channel"],
            "engine": "Trino",
            "domain": "Customer",
            "definition": "Percentage of customers retained over the selected time period.",
        },
    ],
    "dimensions": [
        {"name": "Region", "keywords": ["region", "geography", "area"]},
        {"name": "Month", "keywords": ["month", "monthly", "last 12 months", "quarter"]},
        {"name": "Segment", "keywords": ["segment", "customer segment", "tier"]},
        {"name": "Product", "keywords": ["product", "sku", "category"]},
        {"name": "Channel", "keywords": ["channel", "acquisition channel", "source"]},
    ],
}
