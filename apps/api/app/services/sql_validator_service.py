import re


FORBIDDEN_PATTERNS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bTRUNCATE\b",
]


def validate_sql(sql: str) -> tuple[bool, list[str], str]:
    issues: list[str] = []
    normalized = sql.strip()

    if not normalized:
        return False, ["SQL is empty."], normalized

    if not normalized.upper().startswith("SELECT"):
        issues.append("Only SELECT statements are allowed.")

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            issues.append(f"Forbidden SQL keyword detected: {pattern}")

    if "LIMIT" not in normalized.upper():
        normalized = normalized.rstrip().rstrip(";") + "\nLIMIT 1000;"
        issues.append("LIMIT 1000 was automatically added.")

    return len([i for i in issues if "automatically added" not in i]) == 0, issues, normalized
