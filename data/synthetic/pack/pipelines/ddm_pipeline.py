"""
DDM pipeline – enriches raw layer with derived / conformed columns.
Produces: ddm_customer, ddm_account, ddm_transaction, ddm_payment, ddm_statement.
"""
import pandas as pd
import numpy as np
from datetime import date


# ── helpers ────────────────────────────────────────────────────────────────

def _age_band(age: int) -> str:
    if age < 26:   return "18-25"
    if age < 36:   return "26-35"
    if age < 46:   return "36-45"
    if age < 56:   return "46-55"
    if age < 66:   return "56-65"
    return "65+"


def _income_band(annual: float, currency: str) -> str:
    # Normalise to SGD-equivalent for band logic
    fx = {"SGD": 1.0, "MYR": 1 / 3.5, "INR": 1 / 62.0}.get(currency, 1.0)
    sgd = annual * fx
    if sgd < 30_000:   return "low"
    if sgd < 80_000:   return "middle"
    if sgd < 200_000:  return "upper_middle"
    return "high"


def _credit_band(score: int) -> str:
    if score < 580:  return "poor"
    if score < 670:  return "fair"
    if score < 740:  return "good"
    if score < 800:  return "very_good"
    return "excellent"


def _util_band(rate: float) -> str:
    if rate < 0.30: return "low"
    if rate < 0.50: return "medium"
    if rate < 0.80: return "high"
    return "very_high"


def _overdue_bucket(days: int) -> str:
    if days <= 0:    return "current"
    if days <= 30:   return "1-30 days"
    if days <= 60:   return "31-60 days"
    if days <= 90:   return "61-90 days"
    return "90+ days"


def _ref_date() -> date:
    return date(2025, 12, 31)


# ── DDM customer ────────────────────────────────────────────────────────────

def build_ddm_customer(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    ref = _ref_date()
    df["full_name"]    = df["first_name"] + " " + df["last_name"]
    df["age"]          = df["date_of_birth"].apply(
        lambda d: (ref - date.fromisoformat(d)).days // 365
    )
    df["age_band"]     = df["age"].apply(_age_band)
    df["income_band"]  = df.apply(
        lambda r: _income_band(r["annual_income"], r["currency_code"]), axis=1
    )
    df["credit_band"]  = df["credit_score"].apply(_credit_band)
    df["effective_from"] = df["created_at"].str[:10]
    df["effective_to"]   = None
    df["is_current"]     = 1

    # Column order matching ddm_customer schema
    cols = [
        "customer_id", "country_code", "legal_entity", "full_name",
        "first_name", "last_name", "date_of_birth", "age", "age_band",
        "gender", "email", "phone", "city", "nationality",
        "id_type", "id_number", "customer_segment", "kyc_status", "risk_rating",
        "annual_income", "income_band", "currency_code", "occupation",
        "acquisition_channel", "credit_score", "credit_band",
        "is_deleted", "effective_from", "effective_to", "is_current",
        "created_at", "updated_at",
    ]
    return df[cols]


# ── DDM account ─────────────────────────────────────────────────────────────

def build_ddm_account(df_raw: pd.DataFrame, customers_by_id: dict) -> pd.DataFrame:
    df = df_raw.copy()
    ref = _ref_date()

    def _full_name(cid):
        c = customers_by_id.get(cid, {})
        return f"{c.get('first_name','')} {c.get('last_name','')}".strip()

    df["full_name"]        = df["customer_id"].apply(_full_name)
    df["customer_segment"] = df["customer_id"].apply(
        lambda cid: customers_by_id.get(cid, {}).get("customer_segment", "mass")
    )
    df["utilization_rate"] = np.where(
        df["credit_limit"] > 0,
        np.minimum(df["current_balance"] / df["credit_limit"], 9.9999).round(4),
        0.0,
    )
    df["utilization_band"] = df["utilization_rate"].apply(_util_band)
    df["account_age_days"] = df["open_date"].apply(
        lambda d: (ref - date.fromisoformat(d)).days
    )

    cols = [
        "account_id", "customer_id", "country_code", "legal_entity",
        "full_name", "customer_segment", "account_type", "product_code", "product_name",
        "currency_code", "current_balance", "available_balance", "credit_limit",
        "utilization_rate", "utilization_band", "interest_rate", "account_status",
        "open_date", "close_date", "account_age_days", "is_deleted",
        "created_at", "updated_at",
    ]
    return df[cols]


# ── DDM transaction ──────────────────────────────────────────────────────────

def build_ddm_transaction(df_raw: pd.DataFrame,
                           customers_by_id: dict,
                           merchants_by_id: dict) -> pd.DataFrame:
    df = df_raw.copy()

    def _full_name(cid):
        c = customers_by_id.get(cid, {})
        return f"{c.get('first_name','')} {c.get('last_name','')}".strip()

    df["full_name"]        = df["customer_id"].apply(_full_name)
    df["customer_segment"] = df["customer_id"].apply(
        lambda cid: customers_by_id.get(cid, {}).get("customer_segment", "mass")
    )
    df["txn_year_month"]   = df["transaction_date"].str[:7]
    df["merchant_risk_tier"] = df["merchant_id"].apply(
        lambda mid: merchants_by_id.get(mid, {}).get("risk_tier", "low")
    )
    df["is_suspicious"]    = np.where(df["fraud_score"] > 0.50, 1, 0)

    cols = [
        "transaction_id", "account_id", "card_id", "customer_id",
        "country_code", "legal_entity", "full_name", "customer_segment",
        "transaction_date", "txn_year_month", "amount", "currency_code",
        "transaction_type", "channel",
        "merchant_id", "merchant_name", "merchant_category", "merchant_risk_tier",
        "mcc_code", "auth_status", "decline_reason",
        "is_fraud", "fraud_score", "fraud_tier", "is_suspicious",
        "is_international", "is_contactless", "created_at",
    ]
    return df[cols]


# ── DDM payment ──────────────────────────────────────────────────────────────

def build_ddm_payment(df_raw: pd.DataFrame, customers_by_id: dict) -> pd.DataFrame:
    df = df_raw.copy()

    def _full_name(cid):
        c = customers_by_id.get(cid, {})
        return f"{c.get('first_name','')} {c.get('last_name','')}".strip()

    df["full_name"]         = df["customer_id"].apply(_full_name)
    df["customer_segment"]  = df["customer_id"].apply(
        lambda cid: customers_by_id.get(cid, {}).get("customer_segment", "mass")
    )
    df["payment_ratio"]     = np.where(
        df["total_due"] > 0,
        (df["payment_amount"] / df["total_due"]).round(4),
        0.0,
    )
    df["is_full_payment"]   = np.where(
        df["payment_amount"] >= df["total_due"] * 0.999, 1, 0
    )
    df["is_minimum_payment"] = np.where(
        (df["payment_amount"] >= df["minimum_due"] * 0.999) &
        (df["payment_amount"] <  df["total_due"]   * 0.999), 1, 0
    )
    df["overdue_bucket"]    = df["overdue_days"].apply(_overdue_bucket)

    cols = [
        "payment_id", "account_id", "customer_id", "country_code", "legal_entity",
        "full_name", "customer_segment",
        "payment_date", "due_date", "statement_month",
        "minimum_due", "total_due", "payment_amount",
        "payment_ratio", "is_full_payment", "is_minimum_payment",
        "payment_method", "payment_channel", "payment_status",
        "overdue_days", "overdue_bucket", "late_fee", "created_at",
    ]
    return df[cols]


# ── DDM statement ─────────────────────────────────────────────────────────────

def build_ddm_statement(df_raw: pd.DataFrame, customers_by_id: dict) -> pd.DataFrame:
    df = df_raw.copy()

    def _full_name(cid):
        c = customers_by_id.get(cid, {})
        return f"{c.get('first_name','')} {c.get('last_name','')}".strip()

    df["full_name"]        = df["customer_id"].apply(_full_name)
    df["customer_segment"] = df["customer_id"].apply(
        lambda cid: customers_by_id.get(cid, {}).get("customer_segment", "mass")
    )

    cols = [
        "statement_id", "account_id", "customer_id", "country_code", "legal_entity",
        "full_name", "customer_segment",
        "statement_month", "statement_date",
        "opening_balance", "closing_balance", "total_spend", "total_credits",
        "total_fees", "minimum_due", "total_due", "due_date", "payment_status",
        "credit_limit", "available_credit", "utilization_rate",
        "transaction_count", "interest_charged", "created_at",
    ]
    return df[cols]


# ── Orchestrator ─────────────────────────────────────────────────────────────

def build_ddm(raw: dict) -> dict[str, pd.DataFrame]:
    customers_by_id = raw["_customers_by_id"]
    merchants_by_id = {row["merchant_id"]: row
                       for row in raw["raw_merchant"].to_dict("records")}

    print("→ Building DDM customer …")
    df_ddm_cust = build_ddm_customer(raw["raw_customer"])

    print("→ Building DDM account …")
    df_ddm_acc  = build_ddm_account(raw["raw_account"], customers_by_id)

    print("→ Building DDM transaction …")
    df_ddm_txn  = build_ddm_transaction(
        raw["raw_transaction"], customers_by_id, merchants_by_id
    )

    print("→ Building DDM payment …")
    df_ddm_pay  = build_ddm_payment(raw["raw_payment"], customers_by_id)

    print("→ Building DDM statement …")
    df_ddm_stmt = build_ddm_statement(raw["raw_statement"], customers_by_id)

    return {
        "ddm_customer":    df_ddm_cust,
        "ddm_account":     df_ddm_acc,
        "ddm_transaction": df_ddm_txn,
        "ddm_payment":     df_ddm_pay,
        "ddm_statement":   df_ddm_stmt,
    }
