"""
DataPrism Synthetic Data Program Pack – main entry point.

Usage (from repo root):
    cd data/synthetic/pack
    python main.py [--save-csv] [--skip-load]

Options:
    --save-csv    Write each DataFrame to output/<layer>/<table>.csv
    --skip-load   Generate data but do not INSERT into StarRocks
"""
import os
import sys
import random
import argparse
import numpy as np
import pandas as pd

# Make the pack directory the root for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RANDOM_SEED

from pipelines.raw_pipeline      import build_raw
from pipelines.ddm_pipeline      import build_ddm
from pipelines.dp_pipeline       import build_dp
from pipelines.semantic_pipeline import build_semantic
from pipelines.mapping_pipeline  import reload_mapping_tables
from loader                      import load_all


def _save_csv(frames: dict[str, pd.DataFrame], subdir: str) -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "output", subdir)
    os.makedirs(out_dir, exist_ok=True)
    for name, df in frames.items():
        if name.startswith("_"):
            continue
        path = os.path.join(out_dir, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"   saved → {path}")


def main():
    parser = argparse.ArgumentParser(description="DataPrism synthetic data generator")
    parser.add_argument("--save-csv",   action="store_true", help="Write CSVs to output/")
    parser.add_argument("--skip-load",  action="store_true", help="Skip StarRocks load")
    args = parser.parse_args()

    print("=" * 60)
    print("  DataPrism Synthetic Data Program Pack")
    print("=" * 60)

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # ── 1. Raw layer ──────────────────────────────────────────────
    print("\n[1/5] RAW LAYER")
    raw = build_raw()

    # ── 2. DDM layer ──────────────────────────────────────────────
    print("\n[2/5] DDM LAYER")
    ddm = build_ddm(raw)

    # ── 3. DP layer ───────────────────────────────────────────────
    print("\n[3/5] DP LAYER")
    dp = build_dp(raw, ddm)

    # ── 4. Semantic layer ─────────────────────────────────────────
    print("\n[4/5] SEMANTIC LAYER")
    semantic = build_semantic(raw, ddm, dp)

    # ── Optional CSV export ───────────────────────────────────────
    if args.save_csv:
        print("\n[CSV] Saving DataFrames …")
        raw_out = {k: v for k, v in raw.items() if not k.startswith("_")}
        _save_csv(raw_out,  "raw")
        _save_csv(ddm,       "ddm")
        _save_csv(dp,        "dp")
        _save_csv(semantic,  "semantic")

    # ── 5. Load to StarRocks ──────────────────────────────────────
    if args.skip_load:
        print("\n[5/5] LOAD SKIPPED (--skip-load)")
    else:
        print("\n[5/5] LOADING TO STARROCKS")
        raw_tables = {k: v for k, v in raw.items() if not k.startswith("_")}
        load_all({
            "raw":      raw_tables,
            "ddm":      ddm,
            "dp":       dp,
            "semantic": semantic,
        })

        print("\n→ Reloading mapping / reference tables …")
        reload_mapping_tables()

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
