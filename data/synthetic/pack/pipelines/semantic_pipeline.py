"""
Semantic pipeline.
Produces the six semantic_* views / tables from DDM + DP layer DataFrames.
"""
import pandas as pd
import numpy as np
from datetime import date
from calendar import monthrange

from config import COUNTRIES, DATA_MONTHS, CREATED_AT, AS_OF_DATE


def _last_day(ym: str) -> str:
    yr, mo = int(ym[:4]), int(ym[5:7])
    _, last = monthrange(yr, mo)
    return f"{yr}-{mo:02d}-{last:02d}"


# ── semantic_transaction_summary ─────────────────────────────────────────────

def build_semantic_txn_summary(dp_txn_enr: pd.DataFrame) -> pd.DataFrame:
    df = dp_txn_enr.copy()
    df["is_approved"] = np.where(df["auth_status"] == "approved", 1, 0)
    df["is_declined"] = np.where(df["auth_status"] == "declined", 1, 0)
    cols = [
        "transaction_id", "account_id", "customer_id",
        "country_code", "legal_entity", "full_name", "customer_segment",
        "transaction_date", "txn_year_month", "amount", "currency_code",
        "transaction_type", "channel",
        "merchant_name", "merchant_category", "merchant_risk_tier",
        "auth_status", "decline_reason",
        "is_approved", "is_declined", "is_fraud", "fraud_score",
        "is_suspicious", "is_international", "created_at",
    ]
    return df[cols]


# ── semantic_spend_metrics ────────────────────────────────────────────────────

def build_semantic_spend_metrics(dp_spend: pd.DataFrame,
                                   ddm_cust: pd.DataFrame) -> pd.DataFrame:
    cust_info = ddm_cust[["customer_id", "full_name"]].drop_duplicates()
    df = dp_spend.merge(cust_info, on="customer_id", how="left")

    # Month-over-month spend change
    df = df.sort_values(["customer_id", "spend_month"])
    df["prev_spend"] = df.groupby("customer_id")["total_spend"].shift(1)
    df["mom_spend_change_pct"] = np.where(
        df["prev_spend"] > 0,
        ((df["total_spend"] - df["prev_spend"]) / df["prev_spend"]).round(4),
        0.0,
    )
    df = df.drop(columns=["prev_spend"])

    cols = [
        "spend_month", "customer_id", "country_code", "legal_entity",
        "full_name", "customer_segment",
        "total_spend", "food_dining", "retail_shopping", "travel_transport",
        "healthcare", "entertainment", "utilities", "grocery", "hotel",
        "fuel", "other_spend",
        "transaction_count", "avg_txn_amount", "top_category", "top_merchant",
        "mom_spend_change_pct", "currency_code", "created_at",
    ]
    return df[cols]


# ── semantic_payment_status ───────────────────────────────────────────────────

def build_semantic_payment_status(dp_pay_status: pd.DataFrame,
                                    ddm_pay:        pd.DataFrame) -> pd.DataFrame:
    import random
    df = dp_pay_status.copy()

    # is_giro_enrolled: random 40 %
    rng = pd.Series([1 if random.random() < 0.4 else 0 for _ in range(len(df))])
    df["is_giro_enrolled"] = rng.values

    # preferred_method from ddm_payment
    pay_pref = ddm_pay.groupby(["account_id"])["payment_method"].agg(
        lambda x: x.mode()[0] if len(x) > 0 else "bank_transfer"
    ).rename("preferred_method").reset_index()
    df = df.merge(pay_pref, on="account_id", how="left")
    df["preferred_method"] = df["preferred_method"].fillna("bank_transfer")

    cols = [
        "as_of_date", "account_id", "customer_id",
        "country_code", "legal_entity", "full_name", "customer_segment",
        "statement_month", "due_date", "days_to_due",
        "minimum_due", "total_due", "amount_paid", "amount_outstanding",
        "payment_status", "overdue_days", "overdue_bucket",
        "consecutive_late", "late_fee", "interest_at_risk",
        "is_giro_enrolled", "preferred_method", "currency_code", "created_at",
    ]
    return df[cols]


# ── semantic_risk_metrics ──────────────────────────────────────────────────────

def build_semantic_risk_metrics(dp_risk: pd.DataFrame,
                                  dp_pay_status: pd.DataFrame) -> pd.DataFrame:
    rows = []
    segs = ["mass", "affluent", "premium"]

    for ym in DATA_MONTHS:
        last = _last_day(ym)
        for cc, cfg in COUNTRIES.items():
            for seg in segs:
                risk_row = dp_risk[
                    (dp_risk["signal_date"] == last) &
                    (dp_risk["country_code"] == cc) &
                    (dp_risk["customer_segment"] == seg)
                ]
                if risk_row.empty:
                    continue
                r = risk_row.iloc[0]

                # Delinquency buckets from dp_payment_status
                pay_seg = dp_pay_status[
                    (dp_pay_status["country_code"] == cc) &
                    (dp_pay_status["customer_segment"] == seg) &
                    (dp_pay_status["statement_month"] == ym)
                ]
                total_acct = len(pay_seg)

                def _delinq(lo, hi):
                    if total_acct == 0:
                        return 0.0
                    n = len(pay_seg[(pay_seg["overdue_days"] >= lo) &
                                     (pay_seg["overdue_days"] <= hi)])
                    return round(n / total_acct, 4)

                rows.append({
                    "metric_date":       last,
                    "country_code":      cc,
                    "legal_entity":      cfg["legal_entity"],
                    "customer_segment":  seg,
                    "total_txn":         int(r["total_txn"]),
                    "approved_txn":      int(r["approved_txn"]),
                    "declined_txn":      int(r["declined_txn"]),
                    "fraud_txn":         int(r["fraud_txn"]),
                    "suspicious_txn":    int(r["suspicious_txn"]),
                    "total_amount":      round(float(r["total_amount"]), 2),
                    "fraud_amount":      round(float(r["fraud_amount"]), 2),
                    "fraud_rate":        float(r["fraud_rate"]),
                    "decline_rate":      float(r["decline_rate"]),
                    "avg_fraud_score":   float(r["avg_fraud_score"]),
                    "delinquency_1_30":  _delinq(1,  30),
                    "delinquency_31_60": _delinq(31, 60),
                    "delinquency_61_90": _delinq(61, 90),
                    "delinquency_91plus":_delinq(91, 99999),
                    "high_risk_accounts":int(r["high_risk_accounts"]),
                    "currency_code":     cfg["currency"],
                    "created_at":        CREATED_AT,
                })

    return pd.DataFrame(rows)


# ── semantic_customer_360 ─────────────────────────────────────────────────────

def build_semantic_customer_360(ddm_cust:  pd.DataFrame,
                                  ddm_acc:   pd.DataFrame,
                                  dp_spend:  pd.DataFrame,
                                  dp_pay_st: pd.DataFrame) -> pd.DataFrame:
    as_of = AS_OF_DATE
    rows = []

    # Latest payment status per customer (December 2025)
    latest_pay = dp_pay_st[dp_pay_st["statement_month"] == DATA_MONTHS[-1]]
    pay_by_acc = latest_pay.set_index("account_id")

    # Latest spend (Dec + Nov for MoM)
    spend_dec = dp_spend[dp_spend["spend_month"] == DATA_MONTHS[-1]].set_index("customer_id")
    spend_nov = dp_spend[dp_spend["spend_month"] == DATA_MONTHS[-2]].set_index("customer_id") \
                if len(DATA_MONTHS) >= 2 else pd.DataFrame()

    # Primary account per customer (first account = primary)
    primary_acc = ddm_acc.groupby("customer_id").first().reset_index()
    primary_acc = primary_acc.set_index("customer_id")

    # Fraud alerts count per customer
    fraud_alerts = dp_pay_st[
        (dp_pay_st["overdue_days"] > 0) &
        (dp_pay_st["statement_month"] == DATA_MONTHS[-1])
    ].groupby("customer_id").size().rename("active_fraud_alerts")

    for _, c in ddm_cust.iterrows():
        cid = c["customer_id"]

        # Account info
        if cid in primary_acc.index:
            acc = primary_acc.loc[cid]
            p_acc_id   = acc["account_id"]
            acc_type   = acc["account_type"]
            cur_bal    = float(acc["current_balance"])
            avail_bal  = float(acc["available_balance"])
            cl         = float(acc["credit_limit"])
            util_pct   = float(acc["utilization_rate"])
        else:
            p_acc_id  = None
            acc_type  = None
            cur_bal = avail_bal = cl = util_pct = 0.0

        # Count of all accounts
        total_accts = len(ddm_acc[ddm_acc["customer_id"] == cid])

        # Spend
        mtd_spend   = float(spend_dec.loc[cid, "total_spend"])   if cid in spend_dec.index  else 0.0
        prev_spend  = float(spend_nov.loc[cid, "total_spend"])   if cid in spend_nov.index  else 0.0
        top_cat     = str(spend_dec.loc[cid, "top_category"]) if cid in spend_dec.index else ""
        spend_chg   = round((mtd_spend - prev_spend) / prev_spend, 4) if prev_spend > 0 else 0.0

        # Payment status
        if p_acc_id and p_acc_id in pay_by_acc.index:
            prow       = pay_by_acc.loc[p_acc_id]
            if isinstance(prow, pd.DataFrame):
                prow = prow.iloc[0]
            pay_status = str(prow["payment_status"])
            total_due  = float(prow["total_due"])
            days_to_due= int(prow["days_to_due"])
            is_overdue  = 1 if int(prow["overdue_days"]) > 0 else 0
            cons_late   = int(prow["consecutive_late"])
        else:
            pay_status = "current"
            total_due  = 0.0
            days_to_due= 0
            is_overdue  = 0
            cons_late   = 0

        alerts = int(fraud_alerts.get(cid, 0))

        rows.append({
            "as_of_date":          as_of,
            "customer_id":         cid,
            "country_code":        c["country_code"],
            "legal_entity":        c["legal_entity"],
            "full_name":           c["full_name"],
            "first_name":          c["first_name"],
            "last_name":           c["last_name"],
            "customer_segment":    c["customer_segment"],
            "risk_rating":         c["risk_rating"],
            "kyc_status":          c["kyc_status"],
            "age":                 int(c["age"]),
            "age_band":            c["age_band"],
            "credit_score":        int(c["credit_score"]),
            "credit_band":         c["credit_band"],
            "primary_account_id":  p_acc_id,
            "account_type":        acc_type,
            "current_balance":     round(cur_bal, 2),
            "available_balance":   round(avail_bal, 2),
            "credit_limit":        round(cl, 2),
            "utilization_pct":     round(util_pct, 4),
            "total_accounts":      total_accts,
            "mtd_spend":           round(mtd_spend, 2),
            "last_month_spend":    round(prev_spend, 2),
            "spend_change_pct":    spend_chg,
            "top_spend_category":  top_cat,
            "payment_status":      pay_status,
            "total_due":           round(total_due, 2),
            "days_to_due":         days_to_due,
            "is_overdue":          is_overdue,
            "consecutive_late":    cons_late,
            "active_fraud_alerts": alerts,
            "currency_code":       c["currency_code"],
            "created_at":          CREATED_AT,
        })

    return pd.DataFrame(rows)


# ── semantic_portfolio_kpis ───────────────────────────────────────────────────

def build_semantic_portfolio_kpis(dp_kpis: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "kpi_month", "country_code", "legal_entity",
        "total_customers", "active_customers", "new_customers",
        "customer_growth_pct", "churn_rate",
        "total_spend", "spend_growth_pct",
        "avg_balance", "avg_utilization",
        "fraud_rate", "decline_rate", "delinquency_rate",
        "full_payment_rate", "npl_rate", "est_interest_income",
        "currency_code", "fx_rate_to_usd", "created_at",
    ]
    return dp_kpis[cols].copy()


# ── Orchestrator ──────────────────────────────────────────────────────────────

def build_semantic(raw: dict, ddm: dict, dp: dict) -> dict[str, pd.DataFrame]:
    print("→ Building semantic_transaction_summary …")
    s_txn = build_semantic_txn_summary(dp["dp_transaction_enriched"])
    print(f"   {len(s_txn):,} rows")

    print("→ Building semantic_spend_metrics …")
    s_spend = build_semantic_spend_metrics(
        dp["dp_customer_spend_monthly"], ddm["ddm_customer"]
    )
    print(f"   {len(s_spend):,} rows")

    print("→ Building semantic_payment_status …")
    s_pay = build_semantic_payment_status(
        dp["dp_payment_status"], ddm["ddm_payment"]
    )
    print(f"   {len(s_pay):,} rows")

    print("→ Building semantic_risk_metrics …")
    s_risk = build_semantic_risk_metrics(
        dp["dp_risk_signals"], dp["dp_payment_status"]
    )
    print(f"   {len(s_risk):,} rows")

    print("→ Building semantic_customer_360 …")
    s_c360 = build_semantic_customer_360(
        ddm["ddm_customer"], ddm["ddm_account"],
        dp["dp_customer_spend_monthly"], dp["dp_payment_status"],
    )
    print(f"   {len(s_c360):,} rows")

    print("→ Building semantic_portfolio_kpis …")
    s_kpis = build_semantic_portfolio_kpis(dp["dp_portfolio_kpis"])
    print(f"   {len(s_kpis):,} rows")

    return {
        "semantic_transaction_summary": s_txn,
        "semantic_spend_metrics":       s_spend,
        "semantic_payment_status":      s_pay,
        "semantic_risk_metrics":        s_risk,
        "semantic_customer_360":        s_c360,
        "semantic_portfolio_kpis":      s_kpis,
    }
