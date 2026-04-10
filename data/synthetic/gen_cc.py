"""
DataPrismAI — Credit Card accounts, cards, transactions, statements, payments generator
"""
import sys, os, random, hashlib
from datetime import date, datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from gen_ref_data import *
from gen_customers import rand_date

random.seed(random_seed + 1)


def rand_dt(start: datetime, end: datetime) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, max(1, delta)))


def overdue_bucket(days: int) -> str:
    if days <= 0:  return "CURRENT"
    if days <= 30: return "1-30"
    if days <= 60: return "31-60"
    if days <= 90: return "61-90"
    return "91+"


# ── ACCOUNTS + CARDS ──────────────────────────────────────────────────────────
def generate_cc_accounts(all_customers: dict) -> tuple[dict, list, list]:
    """
    Returns (all_accounts, raw_acct_rows, raw_card_rows)
    all_accounts: cc → list of account dicts (with _meta fields for downstream use)
    """
    all_accounts = {}
    raw_acct_rows = []
    raw_card_rows = []

    for cc, custs in all_customers.items():
        cfg = COUNTRY_CONF[cc]
        all_accounts[cc] = []

        for c in custs:
            seg    = c["_seg"]
            n_acct = 1 + (1 if random.random() < 0.30 else 0)  # 30% have 2nd card

            for j in range(n_acct):
                aid = f"{cc}_ACC_{c['customer_id'].split('_')[2]}_{j+1:02d}"

                lo, hi = cfg["credit_limits"][seg]
                clim   = round(random.uniform(lo, hi) / 100) * 100
                util   = round(random.uniform(0.05, 0.88), 4)
                bal    = round(clim * util, 2)
                avail  = round(clim - bal, 2)
                rate   = round(random.uniform(0.0199, 0.0549), 4)

                status = random.choices(
                    ["ACTIVE", "FROZEN", "DORMANT"],
                    weights=[88, 7, 5]
                )[0]
                freeze = (random.choice(["FRAUD_REVIEW", "CUSTOMER_REQUEST", "REGULATORY_HOLD"])
                          if status == "FROZEN" else None)
                open_d = rand_date(date(2019, 6, 1), date(2024, 6, 1))
                cycle  = random.randint(1, 28)
                tier   = {"MASS": "STANDARD", "AFFLUENT": "GOLD",
                          "PRIORITY": "PLATINUM", "HNW": "INFINITE"}[seg]
                prod_code = f"{cc}_{tier[:3]}_CC"

                acct = {
                    "account_id":       aid,
                    "customer_id":      c["customer_id"],
                    "country_code":     cc,
                    "legal_entity":     cfg["legal_entity"],
                    "account_type":     "CREDIT_CARD",
                    "product_code":     prod_code,
                    "currency_code":    cfg["currency"],
                    "current_balance":  bal,
                    "available_balance": avail,
                    "credit_limit":     clim,
                    "minimum_balance":  0,
                    "interest_rate":    rate,
                    "account_status":   status,
                    "freeze_reason":    freeze,
                    "branch_code":      f"{cc}_BR_{random.randint(1,10):02d}",
                    "product_name":     f"{tier.title()} Credit Card",
                    "open_date":        open_d,
                    "close_date":       None,
                    "last_activity_date": rand_date(date(2025, 6, 1), TODAY),
                    "cycle_day":        cycle,
                    "is_deleted":       0,
                    "created_at":       datetime.combine(open_d, datetime.min.time()),
                    "updated_at":       NOW,
                    # meta
                    "_credit_limit": clim,
                    "_util":         util,
                    "_tier":         tier,
                    "_rate":         rate,
                    "_customer":     c,
                }
                all_accounts[cc].append(acct)

                raw_acct_rows.append((
                    aid, c["customer_id"], cc, cfg["legal_entity"],
                    "CREDIT_CARD", prod_code, cfg["currency"],
                    bal, avail, clim, 0, rate, status, freeze,
                    f"{cc}_BR_{random.randint(1,10):02d}", f"{tier.title()} Credit Card",
                    open_d, None, rand_date(date(2025, 6, 1), TODAY),
                    cycle, 0,
                    datetime.combine(open_d, datetime.min.time()), NOW,
                ))

                # ── card record ──────────────────────────────────────────
                cid_num  = c["customer_id"].split("_")[2]
                card_id  = f"{cc}_CRD_{cid_num}_{j+1:02d}"
                iss      = open_d + timedelta(days=7)
                try:
                    exp  = iss.replace(year=iss.year + 5)
                except ValueError:  # Feb 29 on non-leap year
                    exp  = iss.replace(year=iss.year + 5, day=28)
                scheme   = random.choice(CARD_SCHEMES[seg])
                cst      = ("ACTIVE" if status == "ACTIVE"
                            else ("BLOCKED" if status == "FROZEN" else "INACTIVE"))
                card_last4 = str(random.randint(1000, 9999))
                card_masked = f"****-****-****-{card_last4}"

                raw_card_rows.append((
                    card_id, aid, c["customer_id"], cc, cfg["legal_entity"],
                    "CREDIT", scheme, card_masked, tier,
                    iss, exp, cst,
                    1,                        # is_primary
                    round(clim * 0.5, 2),     # daily_limit (50% of credit limit)
                    1,                        # international_enabled
                    1,                        # contactless_enabled
                    datetime.combine(iss, datetime.min.time()), NOW,
                ))

    return all_accounts, raw_acct_rows, raw_card_rows


# ── TRANSACTIONS ──────────────────────────────────────────────────────────────
N_TXN_PER_COUNTRY = 8000   # meaningful volume per country

def generate_transactions(all_accounts: dict) -> tuple[dict, list]:
    """Returns (all_txns_by_cc, txn_rows)"""
    all_txns  = {}
    txn_rows  = []

    for cc, accts in all_accounts.items():
        cfg = COUNTRY_CONF[cc]
        active = [a for a in accts if a["account_status"] == "ACTIVE"] or accts
        merchants = MERCHANT_DATA[cc]
        all_txns[cc] = []

        for t_idx in range(N_TXN_PER_COUNTRY):
            acct   = random.choice(active)
            merch  = random.choice(merchants)
            mid, mname, mcat, mmcc, m_online, m_risk, m_city = merch

            txn_dt = rand_dt(START_DATE, datetime.combine(TODAY, datetime.min.time()))
            raw_amt = random.expovariate(1.0 / cfg["avg_cc_txn"])
            amt    = round(max(1.0, min(raw_amt, acct["_credit_limit"] * 0.7)), 2)

            chan    = random.choice(CHANNELS_CC)
            ttype   = random.choice(TXN_TYPES_CC)
            auth    = random.choice(AUTH_STATUSES)
            decl_r  = random.choice(DECLINE_REASONS) if auth == "DECLINED" else None

            # ── realistic fraud model ──────────────────────────────────
            is_late_night = txn_dt.hour < 4
            is_intl       = bool(m_online and random.random() < 0.25)
            base_f = 0.08 if m_risk == "HIGH" else (0.015 if m_risk == "MEDIUM" else 0.003)
            fraud_score = round(min(0.99,
                base_f
                + (0.35 if m_risk == "HIGH" else 0)
                + (0.15 if is_late_night else 0)
                + (0.10 if is_intl else 0)
                + random.uniform(0, 0.05)
            ), 4)
            is_fraud = 1 if (fraud_score > 0.82 and auth == "APPROVED"
                             and random.random() < 0.20) else 0
            is_susp  = 1 if fraud_score > 0.55 else 0
            ftier = ("HIGH_RISK" if fraud_score > 0.60
                     else ("MEDIUM_RISK" if fraud_score > 0.30 else "LOW_RISK"))

            sett_dt = (txn_dt + timedelta(days=random.randint(1, 3))
                       if auth == "APPROVED" else None)
            ref_num = f"REF{random.randint(100000000, 999999999)}"
            txn_id  = f"{cc}_TXN_{t_idx+1:06d}"

            txn = {
                "transaction_id":   txn_id,
                "account_id":       acct["account_id"],
                "card_id":          f"{cc}_CRD_{acct['customer_id'].split('_')[2]}_01",
                "customer_id":      acct["customer_id"],
                "country_code":     cc,
                "legal_entity":     COUNTRY_CONF[cc]["legal_entity"],
                "transaction_date": txn_dt,
                "settlement_date":  sett_dt,
                "amount":           amt,
                "currency_code":    cfg["currency"],
                "transaction_type": ttype,
                "channel":          chan,
                "merchant_id":      mid,
                "merchant_name":    mname,
                "merchant_category": mcat,
                "mcc_code":         mmcc,
                "auth_status":      auth,
                "decline_reason":   decl_r,
                "is_fraud":         is_fraud,
                "fraud_score":      fraud_score,
                "fraud_tier":       ftier,
                "is_international": int(is_intl),
                "is_recurring":     int(random.random() < 0.08),
                "is_contactless":   int(chan == "CONTACTLESS"),
                "reference_number": ref_num,
                "description":      f"{mname} - {ttype}",
                "created_at":       txn_dt,
                # meta
                "_is_suspicious":   is_susp,
                "_merchant_risk":   m_risk,
            }
            all_txns[cc].append(txn)

            txn_rows.append((
                txn_id, acct["account_id"],
                f"{cc}_CRD_{acct['customer_id'].split('_')[2]}_01",
                acct["customer_id"], cc, COUNTRY_CONF[cc]["legal_entity"],
                txn_dt, sett_dt, amt, cfg["currency"],
                ttype, chan, mid, mname, mcat, mmcc,
                auth, decl_r, is_fraud, fraud_score, ftier,
                int(is_intl), int(random.random() < 0.08),
                int(chan == "CONTACTLESS"),
                ref_num, f"{mname} - {ttype}", txn_dt,
            ))

    return all_txns, txn_rows


# ── STATEMENTS + PAYMENTS ─────────────────────────────────────────────────────
N_STATEMENT_MONTHS = 18

def generate_statements(all_accounts: dict, all_txns: dict) -> tuple[list, list, dict]:
    """Returns (stmt_rows, pay_rows, stmt_by_acct)"""
    stmt_rows    = []
    pay_rows     = []
    stmt_by_acct = {}
    stmt_num     = 0
    pay_num      = 0

    for cc, accts in all_accounts.items():
        cfg     = COUNTRY_CONF[cc]
        cc_txns = all_txns.get(cc, [])

        for acct in accts:
            stmt_by_acct[acct["account_id"]] = []
            cust = acct["_customer"]

            acct_txns = [
                t for t in cc_txns
                if (t["account_id"] == acct["account_id"]
                    and t["auth_status"] == "APPROVED"
                    and t["transaction_type"] == "PURCHASE")
            ]

            for m_offset in range(N_STATEMENT_MONTHS - 1, -1, -1):
                base_month = (date(TODAY.year, TODAY.month, 1)
                              - timedelta(days=m_offset * 30))
                stmt_mth = base_month.strftime("%Y-%m")
                cycle_d  = min(28, acct["cycle_day"])
                try:
                    stmt_dt = date(int(stmt_mth[:4]), int(stmt_mth[5:7]), cycle_d)
                except ValueError:
                    stmt_dt = date(int(stmt_mth[:4]), int(stmt_mth[5:7]), 28)
                due_dt = stmt_dt + timedelta(days=21)

                mth_txns = [
                    t for t in acct_txns
                    if t["transaction_date"].strftime("%Y-%m") == stmt_mth
                ]
                total_spend = round(sum(t["amount"] for t in mth_txns), 2) or \
                              round(random.uniform(50, acct["_credit_limit"] * 0.25), 2)

                open_bal  = round(random.uniform(0, acct["_credit_limit"] * 0.45), 2)
                fees      = round(random.choice([0, 0, 0, 5.35, 8.56, 10.70, 15.00]), 2)
                interest  = round(open_bal * acct["_rate"] / 12, 2) if open_bal > 0 else 0
                close_bal = round(min(open_bal + total_spend + fees + interest,
                                      acct["_credit_limit"]), 2)
                total_due = close_bal
                min_due   = round(max(total_due * 0.05, 10.00), 2)
                avail_cr  = round(acct["_credit_limit"] - close_bal, 2)
                util_rate = round(close_bal / acct["_credit_limit"], 4) \
                            if acct["_credit_limit"] > 0 else 0

                # ── payment behaviour ──────────────────────────────────
                high_risk = cust["risk_rating"] in ("MEDIUM", "HIGH")
                overdue_prob = 0.20 if high_risk else 0.07
                is_overdue   = (random.random() < overdue_prob) and (due_dt < TODAY)
                pay_amt = 0.0
                days_od = 0

                if due_dt < TODAY:
                    if is_overdue:
                        pay_pct = random.uniform(0.0, 0.75)
                        pay_amt = round(total_due * pay_pct, 2)
                        days_od = (TODAY - due_dt).days
                        pay_stat = "OVERDUE"
                    else:
                        choice = random.random()
                        if choice < 0.55:   # full payment
                            pay_amt  = total_due
                            pay_stat = "PAID"
                        elif choice < 0.80:  # minimum only
                            pay_amt  = min_due
                            pay_stat = "PAID"
                        else:               # partial
                            pay_amt  = round(total_due * random.uniform(0.4, 0.95), 2)
                            pay_stat = "PAID"
                elif due_dt == TODAY:
                    pay_stat = "DUE_TODAY"
                else:
                    pay_stat = "UPCOMING"

                stmt_id = f"{cc}_STMT_{stmt_num+1:06d}"
                stmt_num += 1

                stmt = {
                    "statement_id":     stmt_id,
                    "account_id":       acct["account_id"],
                    "customer_id":      acct["customer_id"],
                    "country_code":     cc,
                    "legal_entity":     cfg["legal_entity"],
                    "statement_date":   stmt_dt,
                    "statement_month":  stmt_mth,
                    "opening_balance":  open_bal,
                    "closing_balance":  close_bal,
                    "total_spend":      total_spend,
                    "total_credits":    round(pay_amt, 2),
                    "total_fees":       fees,
                    "minimum_due":      min_due,
                    "total_due":        total_due,
                    "due_date":         due_dt,
                    "payment_status":   pay_stat,
                    "credit_limit":     acct["_credit_limit"],
                    "available_credit": avail_cr,
                    "utilization_rate": util_rate,
                    "transaction_count": len(mth_txns),
                    "interest_charged": interest,
                    "created_at":       datetime.combine(stmt_dt, datetime.min.time()),
                    # meta
                    "_days_od":  days_od,
                    "_pay_amt":  pay_amt,
                    "_min_due":  min_due,
                    "_total_due": total_due,
                    "_pay_stat": pay_stat,
                }
                stmt_by_acct[acct["account_id"]].append(stmt)
                stmt_rows.append(tuple(v for k, v in stmt.items() if not k.startswith("_")))

                # ── payment record ─────────────────────────────────────
                if pay_amt > 0:
                    late_fee = round(total_due * 0.015, 2) if is_overdue else 0.0
                    if is_overdue:
                        pay_dt = datetime.combine(
                            due_dt + timedelta(days=max(1, days_od - random.randint(0, 3))),
                            datetime.min.time()
                        )
                    else:
                        pay_dt = datetime.combine(
                            due_dt - timedelta(days=random.randint(1, 7)),
                            datetime.min.time()
                        )
                    method = random.choice(PAYMENT_METHODS[cc])
                    pay_id = f"{cc}_PAY_{pay_num+1:06d}"
                    pay_num += 1
                    pay_rows.append((
                        pay_id, acct["account_id"], acct["customer_id"], cc, cfg["legal_entity"],
                        pay_dt, due_dt, stmt_mth, min_due, total_due, pay_amt,
                        method, "MOBILE_APP", pay_stat, days_od, late_fee,
                        f"PAYREF{random.randint(100000, 9999999)}",
                        datetime.combine(stmt_dt, datetime.min.time()),
                    ))

    return stmt_rows, pay_rows, stmt_by_acct


if __name__ == "__main__":
    from gen_customers import generate_customers
    custs = generate_customers()
    accts, _, _ = generate_cc_accounts(custs)
    txns, _ = generate_transactions(accts)
    stmts, pays, _ = generate_statements(accts, txns)
    total_a = sum(len(v) for v in accts.values())
    total_t = sum(len(v) for v in txns.values())
    print(f"CC accounts: {total_a}, transactions: {total_t}, statements: {len(stmts)}, payments: {len(pays)}")
