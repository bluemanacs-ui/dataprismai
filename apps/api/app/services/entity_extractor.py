"""Extract the primary entity (customer, account, card, etc.)
from a user message and/or SQL query result rows.

Rules
-----
1. Scan user_message for explicit ID patterns (CUST_xxx, ACC_xxx, …) — highest priority.
2. Fall back to result rows: accept only when **one unique value** exists for an entity
   ID column (i.e. the query was scoped to a single entity).
3. Attempt to extract a human-readable name from the row (first_name/last_name etc.).
"""

import re
from typing import Optional

# (entity_type, id_column_names_set, id_regex)
# Listed in priority order — customer > account > card > …
_ENTITY_PRIORITY: list[tuple[str, set[str], re.Pattern]] = [
    ("customer",    {"customer_id", "cust_id"},                re.compile(r"\bCUST_\w+\b",  re.IGNORECASE)),
    ("account",     {"account_id",  "acc_id"},                 re.compile(r"\bACC_\w+\b",   re.IGNORECASE)),
    ("card",        {"card_id"},                               re.compile(r"\bCARD_\w+\b",  re.IGNORECASE)),
    ("merchant",    {"merchant_id", "merch_id"},               re.compile(r"\bMERCH_\w+\b", re.IGNORECASE)),
    ("transaction", {"transaction_id", "txn_id", "payment_id"},re.compile(r"\bTXN_\w+\b",   re.IGNORECASE)),
    ("product",     {"product_id",  "prod_id"},                re.compile(r"\bPROD_\w+\b",  re.IGNORECASE)),
]


def _name_from_row(row: dict) -> str:
    """Assemble a human-readable name from a result row when name columns exist."""
    first = str(row.get("first_name") or "").strip()
    last  = str(row.get("last_name")  or "").strip()
    if first or last:
        return f"{first} {last}".strip()
    for col in ("full_name", "customer_name", "name", "merchant_name"):
        val = row.get(col)
        if val:
            return str(val).strip()
    return ""


def extract_entity(user_message: str, rows: list, columns: list) -> Optional[dict]:
    """Return a dict ``{entity_type, entity_id, entity_name}`` or ``None``.

    Parameters
    ----------
    user_message: the raw user query text for this turn.
    rows:         list of row dicts returned by the query executor.
    columns:      column names in the result set.
    """
    # Build a lowercase → original-case column map for O(1) lookup
    cols_lower_map: dict[str, str] = {c.lower(): c for c in (columns or [])}
    first_row = rows[0] if rows else {}

    for entity_type, id_col_names, id_re in _ENTITY_PRIORITY:

        # ── Priority 1: explicit ID in user message ──────────────────────────
        m = id_re.search(user_message)
        if m:
            entity_id   = m.group(0).upper()
            entity_name = _name_from_row(first_row) if first_row else ""
            return {"entity_type": entity_type, "entity_id": entity_id, "entity_name": entity_name}

        # ── Priority 2: single-entity result (all rows have the same ID) ─────
        if not rows:
            continue
        for id_col in id_col_names:
            if id_col not in cols_lower_map:
                continue
            actual_col = cols_lower_map[id_col]
            unique_vals = {
                str(r.get(actual_col, "")).upper()
                for r in rows
                if r.get(actual_col)
            }
            unique_vals.discard("")
            if len(unique_vals) == 1:
                entity_id   = next(iter(unique_vals))
                entity_name = _name_from_row(first_row)
                return {"entity_type": entity_type, "entity_id": entity_id, "entity_name": entity_name}

    return None
