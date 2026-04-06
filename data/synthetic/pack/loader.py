"""
StarRocks loader.
Streams DataFrames into StarRocks via batch INSERT statements piped to the
mysql CLI inside the Docker container.
"""
import subprocess
import numpy as np
import pandas as pd
from typing import Optional


_CONTAINER = "dataprismai-starrocks"
_HOST      = "127.0.0.1"
_PORT      = "9030"
_USER      = "root"
_DB        = "cc_analytics"


def _mysql_cmd() -> list[str]:
    return [
        "docker", "exec", "-i", _CONTAINER,
        "mysql", f"-h{_HOST}", f"-u{_USER}", f"-P{_PORT}", _DB,
    ]


def _val(v) -> str:
    """Convert a Python value to its SQL literal representation."""
    if v is None:
        return "NULL"
    if isinstance(v, float) and np.isnan(v):
        return "NULL"
    if isinstance(v, (bool, np.bool_)):
        return "1" if v else "0"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return str(round(float(v), 6))
    # String – escape single quotes
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


def truncate_table(table_name: str) -> None:
    sql = f"TRUNCATE TABLE `{table_name}`;"
    result = subprocess.run(_mysql_cmd(), input=sql, capture_output=True,
                            text=True, timeout=60)
    if result.returncode != 0:
        print(f"  [WARN] truncate {table_name}: {result.stderr[:200]}")


def load_df(df: pd.DataFrame, table_name: str,
            batch_size: int = 500, truncate: bool = True) -> None:
    """Load a DataFrame into a StarRocks table via batched INSERT statements."""
    if df is None or df.empty:
        print(f"  [SKIP] {table_name}: empty")
        return

    if truncate:
        truncate_table(table_name)

    cols     = list(df.columns)
    col_str  = ", ".join(f"`{c}`" for c in cols)
    total    = 0
    errors   = 0

    for start in range(0, len(df), batch_size):
        batch  = df.iloc[start : start + batch_size]
        values = []
        for row in batch.itertuples(index=False):
            row_vals = [_val(getattr(row, c)) for c in cols]
            values.append(f"({', '.join(row_vals)})")

        sql = f"INSERT INTO `{table_name}` ({col_str}) VALUES\n" + ",\n".join(values) + ";"
        result = subprocess.run(
            _mysql_cmd(), input=sql, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            errors += 1
            stderr = result.stderr.strip()
            if stderr:
                print(f"  [ERR] batch {start//batch_size + 1} of {table_name}: "
                      f"{stderr[:200]}")
        else:
            total += len(batch)

    status = "✓" if errors == 0 else f"⚠ {errors} batch errors"
    print(f"  {status}  {table_name}: {total:,} rows")


def load_all(layers: dict[str, dict[str, pd.DataFrame]]) -> None:
    """
    layers = {
        "raw":      {"raw_customer": df, ...},
        "ddm":      {"ddm_customer": df, ...},
        "dp":       {"dp_...", ...},
        "semantic": {"semantic_...", ...},
    }
    """
    # Load order must respect FK dependencies
    load_order = [
        # raw
        ("raw", "raw_merchant"),
        ("raw", "raw_customer"),
        ("raw", "raw_account"),
        ("raw", "raw_card"),
        ("raw", "raw_transaction"),
        ("raw", "raw_statement"),
        ("raw", "raw_payment"),
        # ddm
        ("ddm", "ddm_customer"),
        ("ddm", "ddm_account"),
        ("ddm", "ddm_transaction"),
        ("ddm", "ddm_payment"),
        ("ddm", "ddm_statement"),
        # dp
        ("dp", "dp_transaction_enriched"),
        ("dp", "dp_customer_spend_monthly"),
        ("dp", "dp_customer_balance_snapshot"),
        ("dp", "dp_payment_status"),
        ("dp", "dp_portfolio_kpis"),
        ("dp", "dp_risk_signals"),
        # semantic
        ("semantic", "semantic_transaction_summary"),
        ("semantic", "semantic_spend_metrics"),
        ("semantic", "semantic_payment_status"),
        ("semantic", "semantic_risk_metrics"),
        ("semantic", "semantic_customer_360"),
        ("semantic", "semantic_portfolio_kpis"),
    ]

    for layer_key, table_name in load_order:
        layer = layers.get(layer_key, {})
        df    = layer.get(table_name)
        if df is None:
            print(f"  [MISS] {table_name} not found in layers['{layer_key}']")
            continue
        load_df(df, table_name)
