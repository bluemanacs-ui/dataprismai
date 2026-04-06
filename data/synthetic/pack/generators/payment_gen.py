"""
Statement + Payment generator.

For each account × month:
  1. Build statement from approved transactions.
  2. Generate payment based on customer behaviour profile.

Maintains running balance state across months.
"""
import random
import numpy as np
from datetime import date, datetime, timedelta
from calendar import monthrange


def _last_day(year: int, month: int) -> date:
    _, last = monthrange(year, month)
    return date(year, month, last)


def _due_date(stmt_date: date) -> date:
    return stmt_date + timedelta(days=21)


def _overdue_bucket(days: int) -> str:
    if days <= 0:       return "current"
    if days <= 30:      return "1-30 days"
    if days <= 60:      return "31-60 days"
    if days <= 90:      return "61-90 days"
    return "90+ days"


def generate_statements_and_payments(
    accounts:            list[dict],
    customers_by_id:     dict,
    txn_list:            list[dict],
    data_months:         list[str],
    payment_profiles:    dict,
    country_cfg:         dict,
) -> tuple[list[dict], list[dict]]:
    """
    Returns (statements, payments).
    """
    # Index transactions by (account_id, ym)
    txn_index: dict = {}
    for t in txn_list:
        if t["auth_status"] != "approved":
            continue
        ym = t["transaction_date"][:7]
        key = (t["account_id"], ym)
        txn_index.setdefault(key, []).append(t)

    statements = []
    payments   = []
    s_counter  = 1
    p_counter  = 1

    for acc in accounts:
        aid      = acc["account_id"]
        cid      = acc["customer_id"]
        cust     = customers_by_id[cid]
        cc       = acc["country_code"]
        cfg      = country_cfg[cc]
        currency = acc["currency_code"]
        legal    = acc["legal_entity"]
        cl       = acc["credit_limit"]
        rate     = acc["interest_rate"]           # annual
        monthly_rate = rate / 12.0
        floor    = cfg["min_payment_floor"]
        profile  = payment_profiles[cust["risk_rating"]]
        full_name= f"{cust['first_name']} {cust['last_name']}"
        seg      = cust["customer_segment"]

        running_balance = acc["current_balance"]
        prev_due        = 0.0
        consecutive_late= 0

        for ym in data_months:
            yr, mo = int(ym[:4]), int(ym[5:7])

            txns_this_month = txn_index.get((aid, ym), [])
            # Only purchases (positive amounts)
            total_spend = round(sum(
                t["amount"] for t in txns_this_month
                if t["transaction_type"] == "purchase"
            ), 2)
            # Refunds reduce balance
            total_credits = round(sum(
                t["amount"] for t in txns_this_month
                if t["transaction_type"] == "refund"
            ), 2)

            # Interest charged on previous unpaid balance
            interest_charged = round(running_balance * monthly_rate, 2) if running_balance > 0 else 0.0
            total_fees        = round(interest_charged, 2)

            stmt_date       = _last_day(yr, mo)
            due_dt          = _due_date(stmt_date)
            opening_balance = running_balance

            closing_balance = round(
                opening_balance + total_spend - total_credits + total_fees, 2
            )
            closing_balance = max(0.0, closing_balance)

            min_due     = round(max(floor, closing_balance * 0.03), 2)
            total_due   = closing_balance
            avail_credit= round(max(0.0, cl - closing_balance), 2)
            util_rate   = round(min(closing_balance / cl, 9.9999), 4) if cl > 0 else 0.0

            txn_count   = len(txns_this_month)

            # ── Statement row ────────────────────────────────────────────
            sid = f"STMT_{s_counter:08d}"
            s_counter += 1

            statements.append({
                "statement_id":     sid,
                "account_id":       aid,
                "customer_id":      cid,
                "country_code":     cc,
                "legal_entity":     legal,
                "statement_date":   stmt_date.strftime("%Y-%m-%d"),
                "statement_month":  ym,
                "opening_balance":  opening_balance,
                "closing_balance":  closing_balance,
                "total_spend":      total_spend,
                "total_credits":    total_credits,
                "total_fees":       total_fees,
                "minimum_due":      min_due,
                "total_due":        total_due,
                "due_date":         due_dt.strftime("%Y-%m-%d"),
                "payment_status":   "pending",   # updated after payment
                "credit_limit":     cl,
                "available_credit": avail_credit,
                "utilization_rate": util_rate,
                "transaction_count":txn_count,
                "interest_charged": interest_charged,
                "created_at":       stmt_date.strftime("%Y-%m-%d 23:59:00"),
            })

            # ── Payment decision ─────────────────────────────────────────
            if closing_balance <= 0.0:
                # Nothing to pay
                running_balance  = 0.0
                statements[-1]["payment_status"] = "paid_full"
                continue

            beh = random.choices(
                ["full", "partial", "minimum", "late"],
                weights=[profile["full"], profile["partial"],
                         profile["minimum"], profile["late"]]
            )[0]

            if beh == "full":
                pay_amt  = total_due
                pay_dt   = due_dt - timedelta(days=random.randint(1, 10))
                overdue  = 0
                pay_status = "paid_full"
                consecutive_late = 0
            elif beh == "partial":
                pay_pct  = random.uniform(0.30, 0.95)
                pay_amt  = round(max(min_due, total_due * pay_pct), 2)
                pay_dt   = due_dt - timedelta(days=random.randint(0, 7))
                overdue  = 0
                pay_status = "paid_partial"
                consecutive_late = 0
            elif beh == "minimum":
                pay_amt  = min_due
                pay_dt   = due_dt + timedelta(days=random.randint(-2, 3))
                overdue  = max(0, (pay_dt - due_dt).days)
                pay_status = "paid_minimum" if overdue == 0 else "overdue"
                if overdue > 0:
                    consecutive_late += 1
                else:
                    consecutive_late = 0
            else:  # late / no pay
                pay_amt  = 0.0 if random.random() < 0.3 else min_due
                pay_dt   = due_dt + timedelta(days=random.randint(5, 45))
                overdue  = (pay_dt - due_dt).days
                pay_status = "overdue"
                consecutive_late += 1

            # Late fee
            late_fee = round(max(0, floor * 0.50) if overdue > 0 else 0.0, 2)

            # Update running balance
            running_balance = round(max(0.0, closing_balance - pay_amt + late_fee), 2)

            # Update statement payment_status
            statements[-1]["payment_status"] = pay_status

            # Ensure pay_dt within 2025
            if pay_dt.year > 2025:
                py = pay_dt.replace(year=2025, month=12, day=28)
            else:
                py = pay_dt

            pid = f"PAY_{p_counter:08d}"
            p_counter += 1

            ref = f"PREF{p_counter:012d}"
            payments.append({
                "payment_id":       pid,
                "account_id":       aid,
                "customer_id":      cid,
                "country_code":     cc,
                "legal_entity":     legal,
                "payment_date":     py.strftime("%Y-%m-%d %H:%M:%S"),
                "due_date":         due_dt.strftime("%Y-%m-%d"),
                "statement_month":  ym,
                "minimum_due":      min_due,
                "total_due":        total_due,
                "payment_amount":   pay_amt,
                "payment_method":   random.choice(["bank_transfer", "giro", "online_banking", "cheque"]),
                "payment_channel":  random.choice(["internet_banking", "mobile_app", "atm", "branch"]),
                "payment_status":   pay_status,
                "overdue_days":     overdue,
                "late_fee":         late_fee,
                "reference_number": ref,
                "created_at":       py.strftime("%Y-%m-%d %H:%M:%S"),
            })

    return statements, payments
