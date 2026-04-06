"""
DP (Data Products) pipeline.
Produces:
  dp_customer_balance_snapshot  (monthly, per customer)
  dp_customer_spend_monthly     (monthly, per customer)
  dp_payment_status             (monthly, per account – as_of last day of month)
  dp_portfolio_kpis             (monthly, per country)
  dp_risk_signals               (monthly, per country × segment)
  dp_transaction_enriched       (one row per transaction)
"""
import random
import pandas as pd
import numpy as np
from datetime import date, datetime
from calendar import monthrange

from config import COUNTRIES, DATA_MONTHS, CAT_NAMES, CREATED_AT


# ── helpers ─────────────────────────────────────────────────────────────────

def _last_day(ym: str) -> str:
    yr, mo = int(ym[:4]), int(ym[5:7])
    _, last = monthrange(yr, mo)
    return f"{yr}-{mo:02d}-{last:02d}"


def _overdue_bucket(days: int) -> str:
    if days <= 0:    return "current"
    if days <= 30:   return "1-30 days"
    if days <= 60:   return "31-60 days"
    if days <= 90:   return "61-90 days"
    return "90+ days"


# ── dp_transaction_enriched ──────────────────────────────────────────────────

def build_dp_txn_enriched(ddm_txn: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "transaction_id", "account_id", "customer_id",
        "country_code", "legal_entity", "full_name", "customer_segment",
        "transaction_date", "txn_year_month", "amount", "currency_code",
        "transaction_type", "channel",
        "merchant_name", "merchant_category", "merchant_risk_tier",
        "auth_status", "decline_reason",
        "is_fraud", "fraud_score", "is_suspicious", "is_international",
        "created_at",
    ]
    return ddm_txn[cols].copy()


# ── dp_customer_spend_monthly ────────────────────────────────────────────────

def build_dp_spend_monthly(ddm_txn: pd.DataFrame,
                            ddm_cust: pd.DataFrame) -> pd.DataFrame:
    approved = ddm_txn[ddm_txn["auth_status"] == "approved"].copy()
    approved["spend_month"] = approved["txn_year_month"]

    cust_info = ddm_cust[["customer_id", "country_code", "legal_entity",
                            "customer_segment", "currency_code"]].drop_duplicates()

    cat_names = [c[0] for c in [
        ("food_dining",), ("retail_shopping",), ("travel_transport",),
        ("healthcare",),  ("entertainment",),   ("utilities",),
        ("grocery",),     ("hotel",),           ("fuel",),
    ]]

    rows = []
    for (cid, ym), grp in approved.groupby(["customer_id", "spend_month"]):
        spend_by_cat = grp.groupby("merchant_category")["amount"].sum().to_dict()
        total_spend  = grp["amount"].sum()
        txn_count    = len(grp)
        avg_txn      = total_spend / txn_count if txn_count else 0.0

        # top merchant & category
        top_merch = grp.groupby("merchant_name")["amount"].sum().idxmax() if txn_count else ""
        top_cat   = grp.groupby("merchant_category")["amount"].sum().idxmax() if txn_count else ""

        c_info = cust_info[cust_info["customer_id"] == cid]
        cc     = c_info["country_code"].values[0] if len(c_info) else "SG"
        le     = c_info["legal_entity"].values[0]  if len(c_info) else ""
        seg    = c_info["customer_segment"].values[0] if len(c_info) else "mass"
        cur    = c_info["currency_code"].values[0]  if len(c_info) else "SGD"

        rows.append({
            "spend_month":       ym,
            "customer_id":       cid,
            "country_code":      cc,
            "legal_entity":      le,
            "customer_segment":  seg,
            "total_spend":       round(total_spend, 2),
            "food_dining":       round(spend_by_cat.get("food_dining", 0), 2),
            "retail_shopping":   round(spend_by_cat.get("retail_shopping", 0), 2),
            "travel_transport":  round(spend_by_cat.get("travel_transport", 0), 2),
            "healthcare":        round(spend_by_cat.get("healthcare", 0), 2),
            "entertainment":     round(spend_by_cat.get("entertainment", 0), 2),
            "utilities":         round(spend_by_cat.get("utilities", 0), 2),
            "grocery":           round(spend_by_cat.get("grocery", 0), 2),
            "hotel":             round(spend_by_cat.get("hotel", 0), 2),
            "fuel":              round(spend_by_cat.get("fuel", 0), 2),
            "other_spend":       round(spend_by_cat.get("other", 0), 2),
            "transaction_count": txn_count,
            "avg_txn_amount":    round(avg_txn, 2),
            "top_merchant":      str(top_merch)[:100],
            "top_category":      str(top_cat)[:50],
            "currency_code":     cur,
            "created_at":        CREATED_AT,
        })

    return pd.DataFrame(rows)


# ── dp_customer_balance_snapshot ─────────────────────────────────────────────

def build_dp_balance_snapshot(ddm_acc: pd.DataFrame,
                               ddm_stmt: pd.DataFrame,
                               ddm_cust: pd.DataFrame) -> pd.DataFrame:
    cust_info = ddm_cust[["customer_id", "country_code", "legal_entity",
                            "full_name", "customer_segment", "currency_code"]].drop_duplicates()
    rows = []

    for ym in DATA_MONTHS:
        # Use closing_balance from statements for that month
        stmt_month = ddm_stmt[ddm_stmt["statement_month"] == ym][
            ["account_id", "customer_id", "closing_balance", "credit_limit"]
        ]

        if stmt_month.empty:
            continue

        for cid, grp in stmt_month.groupby("customer_id"):
            total_balance = grp["closing_balance"].sum()
            total_limit   = grp["credit_limit"].sum()
            total_avail   = max(0.0, total_limit - total_balance)
            avg_util      = min(total_balance / total_limit, 9.9999) if total_limit > 0 else 0.0

            # Account with highest utilisation
            grp2 = grp.copy()
            grp2["util"] = np.where(grp2["credit_limit"] > 0,
                                    grp2["closing_balance"] / grp2["credit_limit"], 0)
            hi_acc = grp2.loc[grp2["util"].idxmax(), "account_id"] if len(grp2) else ""

            c_info = cust_info[cust_info["customer_id"] == cid]
            cc     = c_info["country_code"].values[0]  if len(c_info) else "SG"
            le     = c_info["legal_entity"].values[0]   if len(c_info) else ""
            fn     = c_info["full_name"].values[0]       if len(c_info) else ""
            seg    = c_info["customer_segment"].values[0] if len(c_info) else "mass"
            cur    = c_info["currency_code"].values[0]   if len(c_info) else "SGD"

            rows.append({
                "snapshot_month":       ym,
                "customer_id":          cid,
                "country_code":         cc,
                "legal_entity":         le,
                "full_name":            fn,
                "customer_segment":     seg,
                "total_accounts":       len(grp),
                "total_credit_limit":   round(total_limit, 2),
                "total_balance":        round(total_balance, 2),
                "total_available":      round(total_avail, 2),
                "avg_utilization":      round(avg_util, 4),
                "highest_util_account": str(hi_acc)[:20],
                "currency_code":        cur,
                "created_at":           CREATED_AT,
            })

    return pd.DataFrame(rows)


# ── dp_payment_status ────────────────────────────────────────────────────────

def build_dp_payment_status(ddm_stmt: pd.DataFrame,
                              ddm_pay:  pd.DataFrame,
                              ddm_cust: pd.DataFrame) -> pd.DataFrame:
    cust_info = ddm_cust[["customer_id", "country_code", "legal_entity",
                            "full_name", "customer_segment", "currency_code"]].drop_duplicates()
    pay_idx   = ddm_pay.set_index(["account_id", "statement_month"])
    rows      = []

    for _, stmt in ddm_stmt.iterrows():
        aid = stmt["account_id"]
        cid = stmt["customer_id"]
        ym  = stmt["statement_month"]
        as_of = _last_day(ym)

        c_info = cust_info[cust_info["customer_id"] == cid]
        cc     = c_info["country_code"].values[0]  if len(c_info) else "SG"
        le     = c_info["legal_entity"].values[0]   if len(c_info) else ""
        fn     = c_info["full_name"].values[0]       if len(c_info) else ""
        seg    = c_info["customer_segment"].values[0] if len(c_info) else "mass"
        cur    = c_info["currency_code"].values[0]   if len(c_info) else "SGD"

        key = (aid, ym)
        if key in pay_idx.index:
            p          = pay_idx.loc[key]
            # handle multiple matches (take first)
            if isinstance(p, pd.DataFrame):
                p = p.iloc[0]
            paid       = float(p["payment_amount"])
            overdue_d  = int(p["overdue_days"])
            late_fee   = float(p["late_fee"])
            pay_status = str(p["payment_status"])
        else:
            paid       = 0.0
            overdue_d  = 0
            late_fee   = 0.0
            pay_status = "pending"

        total_due      = float(stmt["total_due"])
        outstanding    = max(0.0, total_due - paid)
        due_dt         = stmt["due_date"]
        days_to_due    = (date.fromisoformat(due_dt) - date.fromisoformat(as_of)).days
        interest_risk  = round(outstanding * float(
            ddm_cust[ddm_cust["customer_id"] == cid]["credit_band"].values[0]
            if False else 0   # placeholder – filled below
        ), 2)
        interest_risk  = round(outstanding * 0.015, 2)  # ~18% pa / 12

        rows.append({
            "as_of_date":       as_of,
            "account_id":       aid,
            "customer_id":      cid,
            "country_code":     cc,
            "legal_entity":     le,
            "full_name":        fn,
            "customer_segment": seg,
            "statement_month":  ym,
            "due_date":         due_dt,
            "days_to_due":      days_to_due,
            "minimum_due":      round(float(stmt["minimum_due"]), 2),
            "total_due":        round(total_due, 2),
            "amount_paid":      round(paid, 2),
            "amount_outstanding": round(outstanding, 2),
            "payment_status":   pay_status,
            "overdue_days":     overdue_d,
            "overdue_bucket":   _overdue_bucket(overdue_d),
            "consecutive_late": 0,  # simplified
            "late_fee":         round(late_fee, 2),
            "interest_at_risk": round(interest_risk, 2),
            "currency_code":    cur,
            "created_at":       CREATED_AT,
        })

    return pd.DataFrame(rows)


# ── dp_portfolio_kpis ────────────────────────────────────────────────────────

def build_dp_portfolio_kpis(ddm_cust:  pd.DataFrame,
                              ddm_acc:   pd.DataFrame,
                              ddm_txn:   pd.DataFrame,
                              ddm_stmt:  pd.DataFrame,
                              ddm_pay:   pd.DataFrame) -> pd.DataFrame:
    rows = []
    prev_row = {}   # {(cc, ym-1)} → {"total_customers", "total_spend"}

    for ym in DATA_MONTHS:
        for cc, cfg in COUNTRIES.items():
            le       = cfg["legal_entity"]
            currency = cfg["currency"]
            fx       = cfg["fx_to_usd"]

            c_cc     = ddm_cust[ddm_cust["country_code"] == cc]
            a_cc     = ddm_acc[ddm_acc["country_code"] == cc]
            t_cc     = ddm_txn[(ddm_txn["country_code"] == cc) &
                                (ddm_txn["txn_year_month"] == ym) &
                                (ddm_txn["auth_status"] == "approved")]
            s_cc     = ddm_stmt[(ddm_stmt["country_code"] == cc) &
                                 (ddm_stmt["statement_month"] == ym)]
            p_cc     = ddm_pay[(ddm_pay["country_code"] == cc) &
                                (ddm_pay["statement_month"] == ym)]

            total_cust   = len(c_cc)
            active_cust  = t_cc["customer_id"].nunique()
            new_cust     = len(c_cc[c_cc["created_at"].str[:7] == ym])
            churned      = max(0, int(total_cust * random.uniform(0.005, 0.02)))

            total_acct   = len(a_cc)
            active_acct  = t_cc["account_id"].nunique()
            total_cl     = a_cc["credit_limit"].sum()
            total_bal    = s_cc["closing_balance"].sum() if not s_cc.empty else 0.0
            total_spend  = t_cc["amount"].sum()
            avg_bal      = total_bal / total_acct if total_acct else 0.0
            avg_util     = (total_bal / total_cl) if total_cl > 0 else 0.0

            total_txn    = len(ddm_txn[(ddm_txn["country_code"] == cc) &
                                        (ddm_txn["txn_year_month"] == ym)])
            fraud_txn    = len(ddm_txn[(ddm_txn["country_code"] == cc) &
                                        (ddm_txn["txn_year_month"] == ym) &
                                        (ddm_txn["is_fraud"] == 1)])
            declined     = len(ddm_txn[(ddm_txn["country_code"] == cc) &
                                        (ddm_txn["txn_year_month"] == ym) &
                                        (ddm_txn["auth_status"] == "declined")])

            fraud_rate   = round(fraud_txn / total_txn, 6) if total_txn else 0.0
            decline_rate = round(declined  / total_txn, 6) if total_txn else 0.0

            overdue_acct = len(p_cc[p_cc["overdue_days"] > 0])
            delinq_rate  = round(overdue_acct / total_acct, 4) if total_acct else 0.0
            full_pay     = len(p_cc[p_cc["payment_status"] == "paid_full"])
            full_pay_rate= round(full_pay / len(p_cc), 4) if len(p_cc) > 0 else 0.0
            npl_acct     = len(p_cc[p_cc["overdue_days"] > 90])
            npl_rate     = round(npl_acct / total_acct, 4) if total_acct else 0.0
            est_int_inc  = round(total_bal * 0.015, 2)   # ~18% pa /12

            # Growth vs previous month
            prev_key = f"{cc}|{ym}"
            prev_spend   = prev_row.get(cc, {}).get("spend", 0.0)
            prev_cust    = prev_row.get(cc, {}).get("cust", total_cust)
            cust_growth  = round((total_cust - prev_cust) / prev_cust, 4) if prev_cust else 0.0
            spend_growth = round((total_spend - prev_spend) / prev_spend, 4) if prev_spend else 0.0
            churn_rate   = round(churned / total_cust, 4) if total_cust else 0.0

            prev_row[cc] = {"spend": total_spend, "cust": total_cust}

            rows.append({
                "kpi_month":           ym,
                "country_code":        cc,
                "legal_entity":        le,
                "total_customers":     total_cust,
                "active_customers":    active_cust,
                "new_customers":       new_cust,
                "churned_customers":   churned,
                "customer_growth_pct": cust_growth,
                "churn_rate":          churn_rate,
                "total_accounts":      total_acct,
                "active_accounts":     active_acct,
                "total_credit_extended": round(float(total_cl), 2),
                "total_outstanding":   round(float(total_bal), 2),
                "total_spend":         round(float(total_spend), 2),
                "spend_growth_pct":    spend_growth,
                "avg_balance":         round(float(avg_bal), 2),
                "avg_utilization":     round(float(avg_util), 4),
                "fraud_rate":          fraud_rate,
                "decline_rate":        decline_rate,
                "delinquency_rate":    delinq_rate,
                "full_payment_rate":   full_pay_rate,
                "npl_rate":            npl_rate,
                "est_interest_income": est_int_inc,
                "currency_code":       currency,
                "fx_rate_to_usd":      fx,
                "created_at":          CREATED_AT,
            })

    return pd.DataFrame(rows)


# ── dp_risk_signals ──────────────────────────────────────────────────────────

def build_dp_risk_signals(ddm_txn: pd.DataFrame,
                           ddm_pay: pd.DataFrame) -> pd.DataFrame:
    rows = []
    segs = ["mass", "affluent", "premium"]

    for ym in DATA_MONTHS:
        last = _last_day(ym)
        for cc, cfg in COUNTRIES.items():
            for seg in segs:
                mask = (
                    (ddm_txn["country_code"] == cc) &
                    (ddm_txn["txn_year_month"] == ym) &
                    (ddm_txn["customer_segment"] == seg)
                )
                grp = ddm_txn[mask]
                if grp.empty:
                    continue

                total_txn    = len(grp)
                approved     = len(grp[grp["auth_status"] == "approved"])
                declined     = total_txn - approved
                fraud_txn    = int(grp["is_fraud"].sum())
                suspicious   = int(grp["is_suspicious"].sum())
                total_amt    = float(grp[grp["auth_status"] == "approved"]["amount"].sum())
                fraud_amt    = float(grp[grp["is_fraud"] == 1]["amount"].sum())
                fraud_rate   = round(fraud_txn / total_txn, 6) if total_txn else 0.0
                decline_rate = round(declined  / total_txn, 6) if total_txn else 0.0
                avg_frd_sc   = round(float(grp["fraud_score"].mean()), 4)
                hi_risk_acct = int(grp[(grp["fraud_score"] > 0.5)]["account_id"].nunique())
                new_alerts   = int(grp[(grp["is_fraud"] == 1)]["account_id"].nunique())

                rows.append({
                    "signal_date":       last,
                    "country_code":      cc,
                    "legal_entity":      cfg["legal_entity"],
                    "customer_segment":  seg,
                    "total_txn":         total_txn,
                    "approved_txn":      approved,
                    "declined_txn":      declined,
                    "fraud_txn":         fraud_txn,
                    "suspicious_txn":    suspicious,
                    "total_amount":      round(total_amt, 2),
                    "fraud_amount":      round(fraud_amt, 2),
                    "fraud_rate":        fraud_rate,
                    "decline_rate":      decline_rate,
                    "avg_fraud_score":   avg_frd_sc,
                    "high_risk_accounts":hi_risk_acct,
                    "new_fraud_alerts":  new_alerts,
                    "currency_code":     cfg["currency"],
                    "created_at":        CREATED_AT,
                })

    return pd.DataFrame(rows)


# ── Orchestrator ─────────────────────────────────────────────────────────────

def build_dp(raw: dict, ddm: dict) -> dict[str, pd.DataFrame]:
    print("→ Building dp_transaction_enriched …")
    dp_txn_enr = build_dp_txn_enriched(ddm["ddm_transaction"])
    print(f"   {len(dp_txn_enr):,} rows")

    print("→ Building dp_customer_spend_monthly …")
    dp_spend = build_dp_spend_monthly(ddm["ddm_transaction"], ddm["ddm_customer"])
    print(f"   {len(dp_spend):,} rows")

    print("→ Building dp_customer_balance_snapshot …")
    dp_bal = build_dp_balance_snapshot(
        ddm["ddm_account"], ddm["ddm_statement"], ddm["ddm_customer"]
    )
    print(f"   {len(dp_bal):,} rows")

    print("→ Building dp_payment_status …")
    dp_pay_status = build_dp_payment_status(
        ddm["ddm_statement"], ddm["ddm_payment"], ddm["ddm_customer"]
    )
    print(f"   {len(dp_pay_status):,} rows")

    print("→ Building dp_portfolio_kpis …")
    dp_kpis = build_dp_portfolio_kpis(
        ddm["ddm_customer"], ddm["ddm_account"],
        ddm["ddm_transaction"], ddm["ddm_statement"], ddm["ddm_payment"]
    )
    print(f"   {len(dp_kpis):,} rows")

    print("→ Building dp_risk_signals …")
    dp_risk = build_dp_risk_signals(ddm["ddm_transaction"], ddm["ddm_payment"])
    print(f"   {len(dp_risk):,} rows")

    return {
        "dp_transaction_enriched":     dp_txn_enr,
        "dp_customer_spend_monthly":   dp_spend,
        "dp_customer_balance_snapshot":dp_bal,
        "dp_payment_status":           dp_pay_status,
        "dp_portfolio_kpis":           dp_kpis,
        "dp_risk_signals":             dp_risk,
    }
