#!/usr/bin/env python3
"""
sync_semantic_access.py
-----------------------
Ensures every semantic_* table in cc_analytics is registered in:
  1. semantic_access_control  — one row per persona with configurable defaults
  2. semantic_metric_mapping  — auto-derives value metrics from numeric columns

Run this after adding any new semantic table:

    python data/scripts/sync_semantic_access.py

Safe to run repeatedly — uses INSERT IGNORE so existing rows are untouched.

Persona default policy
----------------------
OPEN_PERSONAS   : admin bypass (no rows needed), plus personas listed here
                  get can_access=1 for every new semantic table.
CLOSED_PERSONAS : get can_access=0 for every new table (must be opened manually).

Override per-table in TABLE_POLICY below.
"""

import os
import sys
import mysql.connector

# ── Connection settings ───────────────────────────────────────────────────────
SR_HOST = os.getenv("STARROCKS_HOST", "localhost")
SR_PORT = int(os.getenv("STARROCKS_PORT", "9030"))
SR_DB   = os.getenv("STARROCKS_DB", "cc_analytics")

# ── Persona policy ────────────────────────────────────────────────────────────
# admin = no rows needed (None rules → allow all)
OPEN_PERSONAS = [
    # persona               country_filter         restricted_cols  row_limit description
    ("retail_user",         "user_country_scope",  "national_id",   1000,  "Default open access"),
    ("fraud_analyst",       "user_country_scope",  "none",          5000,  "Default open access"),
    ("regional_risk_user",  "user_country_scope",  "none",          5000,  "Default open access"),
    ("finance_user",        "user_country_scope",  "customer_id",   5000,  "Default open access"),
    ("regional_finance_user","user_country_scope", "customer_id",   5000,  "Default open access"),
]

CLOSED_PERSONAS: list[str] = []   # add persona names here to default-block

# ── Metadata/config tables — never treated as chat-queryable ─────────────────
EXCLUDE_TABLES = {
    "semantic_access_control",
    "semantic_metric_mapping",
    "semantic_dimension_mapping",
    "semantic_glossary_metrics",
}

# ── Per-table override (optional) ─────────────────────────────────────────────
# table_name → {persona: (can_access, country_filter, restricted_cols, row_limit)}
TABLE_POLICY: dict[str, dict] = {
    # Example — override loan portfolio to block finance users:
    # "semantic_loan_portfolio": {
    #     "finance_user":          (0, "none", "none", 0),
    #     "regional_finance_user": (0, "none", "none", 0),
    # },
}

# ── Aggregations tried in order when auto-deriving metrics from columns ───────
_SUM_TYPES    = {"decimal", "bigint", "int", "double", "float", "largeint"}
_COUNT_TYPES  = {"tinyint"}   # flag columns → count where = 1
_SKIP_COLS    = {              # never generate metrics for these
    "snapshot_month", "customer_id", "country_code", "legal_entity",
    "currency_code", "dw_refreshed_at", "created_at", "updated_at",
    "as_of_date", "report_date",
}


def connect(database: str = "") -> mysql.connector.MySQLConnection:
    return mysql.connector.connect(
        host=SR_HOST, port=SR_PORT, user="root", password="",
        database=database, connection_timeout=30, autocommit=True,
    )


def get_semantic_tables(cur) -> list[str]:
    cur.execute("SHOW TABLES")
    return sorted(
        r[0] for row in cur.fetchall()
        for r in [list(row.values()) if isinstance(row, dict) else row]
        if r[0].startswith("semantic_") and r[0] not in EXCLUDE_TABLES
    )


def get_registered_tables(cur) -> set[str]:
    cur.execute("SELECT DISTINCT semantic_table FROM semantic_access_control")
    return {r[0] for r in cur.fetchall()}


def get_registered_metrics(cur) -> set[str]:
    cur.execute("SELECT DISTINCT metric_name FROM semantic_metric_mapping")
    return {r[0] for r in cur.fetchall()}


def describe_table(cur, table: str) -> list[tuple[str, str]]:
    """Returns list of (col_name, base_type) for a table."""
    cur.execute(f"DESCRIBE `{table}`")
    result = []
    for row in cur.fetchall():
        if isinstance(row, dict):
            name, full_type = row.get("Field", ""), row.get("Type", "")
        else:
            name, full_type = row[0], row[1]
        base_type = full_type.split("(")[0].lower()
        result.append((name, base_type))
    return result


def sync_access_control(cur, table: str, existing: set[str]) -> int:
    overrides = TABLE_POLICY.get(table, {})
    rows = []
    for (persona, country_filter, restricted_cols, row_limit, desc) in OPEN_PERSONAS:
        if (table, persona) in existing:
            continue
        if persona in overrides:
            can, cf, rc, rl = overrides[persona]
        else:
            can, cf, rc, rl = 1, country_filter, restricted_cols, row_limit
        rows.append((persona, table, can, cf, rc, rl, desc))
    for persona in CLOSED_PERSONAS:
        if (table, persona) in existing:
            continue
        if persona in overrides:
            can, cf, rc, rl = overrides[persona]
        else:
            can, cf, rc, rl = 0, "none", "none", 0
        rows.append((persona, table, can, cf, rc, rl, "Closed by default policy"))
    if rows:
        cur.executemany(
            """INSERT INTO semantic_access_control
               (persona, semantic_table, can_access, country_filter,
                restricted_columns, max_row_limit, description)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            rows,
        )
    return len(rows)


def sync_metrics(cur, table: str, existing_metrics: set[str]) -> int:
    cols = describe_table(cur, table)
    # Infer group_by from first VARCHAR pk-ish col
    group_by = next(
        (c for c, t in cols if t.startswith("varchar") and c not in _SKIP_COLS),
        "customer_id",
    )
    rows = []
    for col_name, base_type in cols:
        if col_name in _SKIP_COLS:
            continue
        metric_name = col_name
        if metric_name in existing_metrics:
            continue
        if base_type in _SUM_TYPES:
            agg = "sum"
        elif base_type in _COUNT_TYPES:
            agg = "count"
            metric_name = f"count_{col_name}"
            if metric_name in existing_metrics:
                continue
        else:
            continue
        rows.append((metric_name, table, col_name, "snapshot_month", group_by, agg))
        existing_metrics.add(metric_name)
    if rows:
        cur.executemany(
            """INSERT INTO semantic_metric_mapping
               (metric_name, semantic_table, value_column,
                filter_column, group_by_column, aggregation)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            rows,
        )
    return len(rows)


def main():
    print(f"Connecting to StarRocks {SR_HOST}:{SR_PORT} / {SR_DB} …")
    conn = connect(SR_DB)
    cur = conn.cursor()

    semantic_tables = get_semantic_tables(cur)
    print(f"Found {len(semantic_tables)} semantic_* tables: {semantic_tables}")

    registered = get_registered_tables(cur)
    new_tables = [t for t in semantic_tables if t not in registered]
    if not new_tables:
        print("All semantic tables already registered in access_control — nothing to do.")
    else:
        print(f"\nNew tables to register: {new_tables}")

    # Build existing (table, persona) pairs to avoid re-inserting
    cur.execute("SELECT semantic_table, persona FROM semantic_access_control")
    existing_pairs = {(r[0], r[1]) for r in cur.fetchall()}

    existing_metrics = get_registered_metrics(cur)

    total_access = 0
    total_metrics = 0
    for table in semantic_tables:
        ac = sync_access_control(cur, table, existing_pairs)
        mt = sync_metrics(cur, table, existing_metrics)
        if ac or mt:
            print(f"  {table}: +{ac} access rules, +{mt} metrics")
        total_access += ac
        total_metrics += mt

    conn.close()
    print(f"\nDone. Inserted {total_access} access rows, {total_metrics} metric rows.")
    print("admin is always unrestricted (no rows needed).")


if __name__ == "__main__":
    main()
