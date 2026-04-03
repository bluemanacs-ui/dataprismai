from app.semantic.catalog import SEMANTIC_CATALOG


def _score_keywords(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in text_lower)


def resolve_semantic_context(message: str, persona: str) -> dict:
    message = message.strip().lower()

    metric_candidates = []
    for metric in SEMANTIC_CATALOG["metrics"]:
        score = _score_keywords(message, metric["keywords"])
        metric_candidates.append((score, metric))

    metric_candidates.sort(key=lambda item: item[0], reverse=True)
    best_metric = metric_candidates[0][1] if metric_candidates and metric_candidates[0][0] > 0 else SEMANTIC_CATALOG["metrics"][0]

    matched_dimensions = []
    for dimension in SEMANTIC_CATALOG["dimensions"]:
        if _score_keywords(message, dimension["keywords"]) > 0:
            matched_dimensions.append(dimension["name"])

    if not matched_dimensions:
        matched_dimensions = ["Region", "Month"]

    return {
        "metric": best_metric["name"],
        "dimensions": matched_dimensions,
        "engine": best_metric["engine"],
        "domain": best_metric["domain"],
        "definition": best_metric["definition"],
        "persona": persona,
    }
