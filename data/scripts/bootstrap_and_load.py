#!/usr/bin/env python3
"""
StarRocks bootstrap & bulk-loader.
Runs once at stack startup (after StarRocks is healthy).
Steps:
  1. Wait for BE to register with FE (queries need BE)
  2. Run all DDL files in data/ddl/starrocks/
  3. Bulk-load all synthetic CSVs into raw_* tables
  4. Seed semantic metadata tables
Performance: executemany() in 5 000-row chunks ≈ 100-500× faster than
             single-row inserts.
"""
import os
import csv
import sys
import time
import glob
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import mysql.connector
from mysql.connector import Error as MySQLError

STARROCKS_HOST = os.getenv("STARROCKS_HOST", "localhost")
STARROCKS_PORT = int(os.getenv("STARROCKS_PORT", "9030"))
DATA_DIR = "/workspace/data"
CHUNK_SIZE = 5000  # rows per executemany batch

# ── Connection helpers ────────────────────────────────────────────────────────

def connect(database: str = "") -> mysql.connector.MySQLConnection:
    return mysql.connector.connect(
        host=STARROCKS_HOST,
        port=STARROCKS_PORT,
        user="root",
        password="",
        database=database,
        connection_timeout=30,
        autocommit=True,
    )


def wait_for_backend(timeout: int = 120) -> None:
    """Wait until at least one BE is alive in FE's SHOW BACKENDS."""
    print(f"  Waiting for StarRocks BE to register (up to {timeout}s)…")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = connect()
            cur = conn.cursor()
            cur.execute("SHOW BACKENDS")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            if rows:
                print(f"  BE registered: {len(rows)} backend(s) found.")
                return
        except MySQLError:
            pass
        time.sleep(5)
    print("  WARNING: No BE registered after timeout — queries may fail.")


# ── DDL ───────────────────────────────────────────────────────────────────────

def run_ddl_file(path: str) -> None:
    print(f"  DDL: {os.path.basename(path)}")
    with open(path, encoding="utf-8") as f:
        sql_text = f.read()

    conn = connect()
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS cc_analytics")
    cur.execute("USE cc_analytics")

    # Strip comment lines before splitting on semicolons to avoid false splits
    # on semicolons that appear inside SQL comments.
    cleaned_lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)

    for stmt in cleaned.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            cur.execute(stmt)
            # Consume any result set (e.g. from SELECT statements in DDL files)
            # to prevent mysql.connector from raising "Unread result found".
            if cur.with_rows:
                cur.fetchall()
        except MySQLError as e:
            # 1050 = table already exists — safe to ignore
            if e.errno != 1050:
                print(f"    DDL note ({e.errno}): {e.msg} — stmt: {stmt[:80]!r}")
    cur.close()
    conn.close()


# ── Type coercion ─────────────────────────────────────────────────────────────

DATE_COLS = {
    "statement_date", "open_date", "close_date", "issued_date",
    "expiration_date", "payment_due_date", "date_of_birth", "payment_date",
}
DATETIME_COLS = {
    "transaction_date", "alert_date", "created_at", "dispute_date",
}
INT_COLS = {"credit_score", "cycle_day", "ssn_last4"}
BOOL_COLS = {"dispute_flag", "autopay_flag", "revolving_flag", "confirmed_fraud"}
DECIMAL_COLS = {
    "apr", "fraud_score", "utilization_rate", "credit_limit", "amount",
    "ending_balance", "minimum_due", "interchange_fee", "payment_amount",
}


def coerce(col: str, val):
    if val in ("None", "", None):
        return None
    if col in DATETIME_COLS:
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(str(val)[:26], fmt)
            except ValueError:
                continue
        return None
    if col in DATE_COLS:
        try:
            return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    if col in INT_COLS:
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0
    if col in BOOL_COLS:
        return 1 if str(val).lower() in ("true", "1", "yes") else 0
    if col in DECIMAL_COLS:
        try:
            return Decimal(str(val))
        except InvalidOperation:
            return Decimal("0")
    return val


# ── CSV bulk loader ───────────────────────────────────────────────────────────

def load_csv(table: str, csv_path: str) -> int:
    if not os.path.exists(csv_path):
        print(f"  SKIP {table}: {csv_path} not found")
        return 0

    conn = connect("cc_analytics")
    cur = conn.cursor()

    # Truncate before loading so reruns are idempotent
    try:
        cur.execute(f"TRUNCATE TABLE {table}")
    except MySQLError:
        pass  # table may not exist yet if DDL failed; INSERT will create it

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = list(reader.fieldnames or [])
        placeholders = ", ".join(["%s"] * len(cols))
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"

        chunk: list[tuple] = []
        total = 0
        t0 = time.time()
        for row in reader:
            chunk.append(tuple(coerce(c, row.get(c)) for c in cols))
            if len(chunk) >= CHUNK_SIZE:
                cur.executemany(sql, chunk)
                total += len(chunk)
                chunk = []
        if chunk:
            cur.executemany(sql, chunk)
            total += len(chunk)

    elapsed = time.time() - t0
    rate = int(total / elapsed) if elapsed > 0 else 0
    print(f"  Loaded {total:>7,} rows → {table:<28} {elapsed:5.1f}s  ({rate:,} rows/s)")
    cur.close()
    conn.close()
    return total


# ── Semantic metadata loaders ─────────────────────────────────────────────────

def load_semantic_metrics() -> None:
    path = f"{DATA_DIR}/semantics/metrics/metrics.csv"
    if not os.path.exists(path):
        return
    conn = connect("cc_analytics")
    cur = conn.cursor()
    try:
        cur.execute("TRUNCATE TABLE semantic_metrics")
    except MySQLError:
        pass
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    sql = (
        "INSERT INTO semantic_metrics "
        "(metric_name, business_name, definition, grain, owner, default_engine, sql_expression, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    data = [
        (r["metric_name"], r["business_name"], r["definition"], r["grain"],
         r["owner"], r["default_engine"], r["sql_expression"], r.get("status", "active"))
        for r in rows
    ]
    cur.executemany(sql, data)
    print(f"  Loaded {len(data):>7,} rows → semantic_metrics")
    cur.close()
    conn.close()


def load_semantic_dimensions() -> None:
    path = f"{DATA_DIR}/semantics/dimensions/dimensions.csv"
    if not os.path.exists(path):
        return
    conn = connect("cc_analytics")
    cur = conn.cursor()
    try:
        cur.execute("TRUNCATE TABLE semantic_dimensions")
    except MySQLError:
        pass
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    sql = (
        "INSERT INTO semantic_dimensions "
        "(dimension_name, business_name, definition, domain, allowed_values) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    data = [
        (r["dimension_name"], r["business_name"], r["definition"],
         r["domain"], r.get("allowed_values_jsonb", ""))
        for r in rows
    ]
    cur.executemany(sql, data)
    print(f"  Loaded {len(data):>7,} rows → semantic_dimensions")
    cur.close()
    conn.close()


def load_semantic_joins() -> None:
    path = f"{DATA_DIR}/semantics/joins/joins.csv"
    if not os.path.exists(path):
        return
    conn = connect("cc_analytics")
    cur = conn.cursor()
    try:
        cur.execute("TRUNCATE TABLE semantic_joins")
    except MySQLError:
        pass
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    sql = (
        "INSERT INTO semantic_joins "
        "(left_entity, right_entity, join_sql, join_type, approved_flag) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    data = [
        (r["left_entity"], r["right_entity"], r["join_sql"], r["join_type"],
         1 if r.get("approved_flag", "true").lower() == "true" else 0)
        for r in rows
    ]
    cur.executemany(sql, data)
    print(f"  Loaded {len(data):>7,} rows → semantic_joins")
    cur.close()
    conn.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("StarRocks Bootstrap & Bulk-Load")
    print("=" * 60)

    # Wait for BEs to register before running DDL (DDL is FE-only, so
    # we wait here so that the subsequent data load also succeeds)
    wait_for_backend(timeout=180)

    # 1. DDL
    print("\n[1/3] Running DDL files…")
    ddl_dir = f"{DATA_DIR}/ddl/starrocks"
    for ddl_file in sorted(glob.glob(f"{ddl_dir}/*.sql")):
        run_ddl_file(ddl_file)

    # 2. Business CSV data
    print("\n[2/3] Bulk-loading CSV data…")
    raw_dir = f"{DATA_DIR}/synthetic/raw"
    tables_and_files = [
        ("raw_customers",    "customers.csv"),
        ("raw_merchants",    "merchants.csv"),
        ("raw_card_accounts","card_accounts.csv"),
        ("raw_cards",        "cards.csv"),
        ("raw_transactions", "transactions.csv"),
        ("raw_payments",     "payments.csv"),
        ("raw_statements",   "statements.csv"),
        ("raw_disputes",     "disputes.csv"),
        ("raw_fraud_alerts", "fraud_alerts.csv"),
    ]
    total_rows = 0
    t0 = time.time()
    for table, csv_file in tables_and_files:
        total_rows += load_csv(table, f"{raw_dir}/{csv_file}")
    elapsed = time.time() - t0
    print(f"\n  Total: {total_rows:,} rows loaded in {elapsed:.1f}s")

    # 3. Semantic metadata
    print("\n[3/3] Seeding semantic metadata…")
    load_semantic_metrics()
    load_semantic_dimensions()
    load_semantic_joins()

    print("\n" + "=" * 60)
    print("Bootstrap complete — StarRocks is ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
