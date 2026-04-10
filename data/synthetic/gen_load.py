"""
DataPrismAI — Main data loader
Generates ALL synthetic banking data and inserts into StarRocks cc_analytics database.

Usage:
    cd /home/acs1980/workspace/dataprismai/data/synthetic
    python gen_load.py [--host localhost] [--port 9030] [--user root]
"""
import sys, os, random, argparse
from datetime import date, datetime, timedelta
from collections import defaultdict
import mysql.connector

sys.path.insert(0, os.path.dirname(__file__))
from gen_ref_data import COUNTRY_CONF, TODAY, NOW, START_DATE
from gen_customers  import generate_customers, generate_merchants, age_band, credit_band
from gen_cc         import generate_cc_accounts, generate_transactions, generate_statements, overdue_bucket
from gen_deposits   import generate_deposit_accounts, generate_deposit_transactions
from gen_loans      import generate_loans, dpd_bucket, dpd_bucket as dpd_label

random.seed(42)

BATCH = 500

# ── DB helpers ─────────────────────────────────────────────────────────────────
def connect(host, port, user, password=""):
    return mysql.connector.connect(
        host=host, port=port, user=user, password=password,
        database="cc_analytics", connection_timeout=30,
    )

def batch_insert(cur, table: str, cols: list, rows: list, batch=BATCH):
    if not rows:
        return 0
    ph  = ",".join(["%s"] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({ph})"
    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i+batch]
        cur.executemany(sql, chunk)
        total += len(chunk)
    return total

def fmt(v):
    """Convert Python types to MySQL-safe values."""
    if isinstance(v, datetime): return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):     return v.strftime("%Y-%m-%d")
    return v

def row(d: dict, cols: list) -> tuple:
    return tuple(fmt(d.get(c)) for c in cols)

# ── RAW: customers & merchants ─────────────────────────────────────────────────
def load_raw_customers(cur, all_customers):
    cols = ["customer_id","country_code","legal_entity","first_name","last_name",
            "date_of_birth","gender","email","phone","address","city",
            "state_province","postal_code","nationality","id_type","id_number",
            "customer_segment","kyc_status","risk_rating","annual_income",
            "currency_code","occupation","acquisition_channel",
            "is_deleted","created_at","updated_at"]
    rows = []
    for custs in all_customers.values():
        for c in custs:
            c2 = {**c, "address": c.get("address_line1")}
            rows.append(row(c2, cols))
    n = batch_insert(cur, "raw_customer", cols, rows)
    print(f"  raw_customer: {n}")

def load_raw_merchants(cur, merchants):
    cols = ["merchant_id","country_code","merchant_name","merchant_category",
            "mcc_code","address","city","is_online","risk_tier",
            "created_at","updated_at"]
    rows = [row(m, cols) for m in merchants]
    n = batch_insert(cur, "raw_merchant", cols, rows)
    print(f"  raw_merchant: {n}")

# ── RAW: CC accounts, cards, transactions, statements, payments ────────────────
def load_raw_cc(cur, all_accounts, all_txns, stmt_rows, pay_rows, card_rows):
    # raw_account
    acct_cols = ["account_id","customer_id","country_code","legal_entity",
                 "account_type","product_code","currency_code","current_balance",
                 "available_balance","credit_limit","minimum_balance","interest_rate",
                 "status","status_reason","branch_code","product_name",
                 "open_date","close_date","last_activity_date",
                 "is_deleted","created_at","updated_at"]
    acct_rows = []
    for accts in all_accounts.values():
        for a in accts:
            a2 = {**a, "status": a.get("account_status"), "status_reason": a.get("freeze_reason")}
            acct_rows.append(row(a2, acct_cols))
    n = batch_insert(cur, "raw_account", acct_cols, acct_rows)
    print(f"  raw_account: {n}")

    # raw_card — tuple layout from gen_cc (18 items):
    # 0:card_id 1:account_id 2:customer_id 3:country_code 4:legal_entity
    # 5:card_type 6:scheme 7:card_hash [8:tier SKIP] 9:issue_date 10:expiry_date
    # 11:status 12:is_primary [13:daily_limit SKIP] 14:intl_enabled 15:contactless
    # 16:created_at 17:updated_at
    card_cols = ["card_id","account_id","customer_id","country_code","legal_entity",
                 "card_type","card_category","card_number_masked",
                 "issue_date","expiry_date","status","is_primary",
                 "intl_enabled","contactless_enabled",
                 "created_at","updated_at"]
    filtered_card_rows = [r[:8] + r[9:13] + r[14:] for r in card_rows]
    n = batch_insert(cur, "raw_card", card_cols, filtered_card_rows)
    print(f"  raw_card: {n}")

    # raw_transaction
    txn_cols = ["transaction_id","account_id","card_id","customer_id","country_code",
                "legal_entity","transaction_date","posting_date","amount",
                "currency_code","transaction_type","channel","merchant_id",
                "merchant_name","merchant_category","mcc_code","status",
                "decline_reason","is_fraud","fraud_score","fraud_rule_hit",
                "is_international","is_recurring","is_contactless",
                "reference_number","description","created_at"]
    txn_flat = []
    for txns in all_txns.values():
        for t in txns:
            t2 = {**t, "posting_date": t.get("settlement_date"),
                  "status": t.get("auth_status"), "fraud_rule_hit": t.get("fraud_tier")}
            txn_flat.append(row(t2, txn_cols))
    n = batch_insert(cur, "raw_transaction", txn_cols, txn_flat)
    print(f"  raw_transaction: {n}")

    # raw_statement — tuple layout from gen_cc (22 items):
    # 0:statement_id 1:account_id 2:customer_id 3:country_code 4:legal_entity
    # 5:statement_date [6:statement_month SKIP] 7:opening_balance 8:closing_balance
    # 9:total_spend→total_debits 10:total_credits [11:total_fees SKIP]
    # 12:minimum_due 13:total_due 14:due_date [15:payment_status SKIP]
    # [16:credit_limit SKIP] [17:available_credit SKIP] [18:utilization_rate SKIP]
    # 19:transaction_count 20:interest_charged 21:created_at
    stmt_cols = ["statement_id","account_id","customer_id","country_code","legal_entity",
                 "statement_date","opening_balance","closing_balance",
                 "total_debits","total_credits","minimum_due","total_due",
                 "due_date","transaction_count","interest_charged","created_at"]
    filtered_stmt_rows = [r[:6] + r[7:11] + r[12:15] + r[19:22] for r in stmt_rows]
    n = batch_insert(cur, "raw_statement", stmt_cols, filtered_stmt_rows)
    print(f"  raw_statement: {n}")

    # raw_payment
    pay_cols = ["payment_id","account_id","customer_id","country_code","legal_entity",
                "payment_date","due_date","statement_date","minimum_due","total_due",
                "amount_paid","payment_method","payment_channel","payment_status",
                "overdue_days","late_fee","reference_number","created_at"]
    n = batch_insert(cur, "raw_payment", pay_cols, pay_rows)
    print(f"  raw_payment: {n}")

# ── RAW: deposits ──────────────────────────────────────────────────────────────
def load_raw_deposits(cur, raw_dep_accts, dep_txns):
    dep_cols = ["deposit_id","account_id","customer_id","country_code","legal_entity",
                "deposit_type","deposit_category","product_code","product_name",
                "currency_code","current_balance","minimum_balance","interest_rate",
                "interest_frequency","interest_earned_ytd","tenor_months",
                "deposit_amount","maturity_date","maturity_amount","auto_renewal",
                "auto_renewal_tenor","avg_monthly_balance","has_salary_credit",
                "salary_credit_amount","sweep_enabled","sweep_linked_account",
                "status","open_date","close_date","last_debit_date","last_credit_date",
                "branch_code","source_system","is_deleted","created_at","updated_at"]
    rows = []
    for d in raw_dep_accts:
        rows.append((
            d["deposit_account_id"], d["deposit_account_id"],  # deposit_id, account_id (same)
            d["customer_id"], d["country_code"], d["legal_entity"],
            d["account_type"], d["account_category"],
            d["product_code"], d["product_name"], d["currency_code"],
            d["current_balance"], d["minimum_balance"], d["interest_rate"],
            d["interest_payment_frequency"], d["accrued_interest"],
            d["tenor_months"],
            d["current_balance"],  # deposit_amount
            fmt(d["maturity_date"]), None,  # maturity_date, maturity_amount
            d["auto_renewal"], None,        # auto_renewal, auto_renewal_tenor
            d["_avg_bal_6m"], 0, 0.0,       # avg_monthly_balance, has_salary_credit, salary_credit_amount
            0, None,                         # sweep_enabled, sweep_linked_account
            d["account_status"],
            fmt(d["open_date"]), fmt(d["close_date"]),
            None, fmt(d["last_transaction_date"]),  # last_debit_date, last_credit_date
            d["branch_code"], "CBS", d["is_deleted"],
            fmt(d["created_at"]), fmt(d["updated_at"]),
        ))
    n = batch_insert(cur, "raw_deposit_account", dep_cols, rows)
    print(f"  raw_deposit_account: {n}")

    dep_txn_cols = ["txn_id","deposit_id","account_id","customer_id","country_code",
                    "legal_entity","txn_date","value_date","amount","txn_direction",
                    "txn_type","txn_category","channel","description","beneficiary_name",
                    "beneficiary_account","reference_number","balance_after","status",
                    "source_system","created_at"]
    txn_rows = []
    dep_id_to_entity = {d["deposit_account_id"]: d["legal_entity"] for d in raw_dep_accts}
    ttype_to_cat = {
        "SALARY_CREDIT":"SALARY","TRANSFER_IN":"TRANSFER","TRANSFER_OUT":"TRANSFER",
        "ATM_WITHDRAWAL":"CASH","UPI_PAYMENT":"UTILITY","NEFT":"TRANSFER",
        "IMPS":"TRANSFER","PAYNOW":"TRANSFER","FPS":"TRANSFER",
        "INTEREST_CREDIT":"INTEREST","STANDING_ORDER":"UTILITY",
        "CASH_DEPOSIT":"CASH","UTILITY_PAYMENT":"UTILITY","FD_ROLLOVER":"INVESTMENT",
        "FD_MATURITY":"INVESTMENT","FEE_DEBIT":"FEE","GIRO":"TRANSFER","CHEQUE":"TRANSFER",
        "FD_PLACEMENT":"INVESTMENT",
    }
    for t in dep_txns:
        legal = dep_id_to_entity.get(t["deposit_account_id"], "UNKNOWN")
        txn_rows.append((
            t["deposit_txn_id"], t["deposit_account_id"], t["deposit_account_id"],
            t["customer_id"], t["country_code"], legal,
            fmt(t["transaction_date"]), fmt(t["value_date"]),
            t["amount"], t["direction"], t["transaction_type"],
            ttype_to_cat.get(t["transaction_type"], "OTHER"),
            t["channel"], t["description"], None, None,
            t["reference_number"], t["running_balance"],
            "COMPLETED", "CBS", fmt(t["created_at"]),
        ))
    n = batch_insert(cur, "raw_deposit_transaction", dep_txn_cols, txn_rows)
    print(f"  raw_deposit_transaction: {n}")

# ── RAW: loans ─────────────────────────────────────────────────────────────────
def load_raw_loans(cur, raw_loans, raw_reps):
    loan_cols = ["loan_id","account_id","customer_id","country_code","legal_entity",
                 "loan_type","loan_category","loan_purpose","product_code","product_name",
                 "currency_code","loan_amount","disbursement_date","loan_term_months",
                 "interest_type","annual_interest_rate","emi_amount","total_interest_payable",
                 "outstanding_principal","outstanding_balance","accrued_interest",
                 "total_paid","last_payment_date","next_due_date","payments_made",
                 "payments_remaining","overdue_amount","overdue_days","dpd_bucket",
                 "npa_flag","npa_date","restructured_flag","restructure_date",
                 "written_off_flag","collateral_type","collateral_description",
                 "collateral_value","ltv_ratio","loan_status","branch_code",
                 "sourced_by","source_system","is_deleted","created_at","updated_at"]
    rows = []
    for l in raw_loans:
        disburse = l["disbursement_date"]
        maturity = disburse + timedelta(days=30 * l["_term"])
        months_paid = l["_months_paid"]
        next_due = disburse + timedelta(days=30 * (months_paid + 1))
        npa_dt = (TODAY - timedelta(days=90)) if l["is_npa"] else None
        ltv = round(l["_principal"] / (l["_principal"] * 1.2), 4) if l["loan_type"] in ("HOME","AUTO") else None
        colval = round(l["_principal"] * 1.25, 2) if l["loan_type"] in ("HOME","AUTO") else None
        rows.append((
            l["loan_id"], l["loan_id"],  # loan_id, account_id (self-ref)
            l["customer_id"], l["country_code"], l["legal_entity"],
            l["loan_type"], l["loan_category"], l["loan_purpose"],
            l["product_code"], l["product_name"], l["currency_code"],
            l["principal_amount"], fmt(disburse), l["tenor_months"],
            "FIXED", l["interest_rate"], l["emi_amount"], l["total_interest_payable"],
            l["outstanding_balance"], l["outstanding_balance"],
            round(l["outstanding_balance"] * l["_rate"] / 12, 2),  # accrued_interest
            round(l["principal_paid_to_date"] + l["interest_paid_to_date"], 2),
            fmt(disburse + timedelta(days=30 * max(1, months_paid))),  # last_payment_date
            fmt(next_due), months_paid, max(0, l["_term"] - months_paid),
            l["overdue_amount"], l["current_dpd"],
            dpd_bucket(l["current_dpd"]),
            l["is_npa"], fmt(npa_dt), 0, None, 0,
            l["collateral_type"], None, colval, ltv,
            l["loan_status"], l["branch_code"],
            random.choice(["BRANCH","ONLINE","AGENT","REFERRAL"]),
            "LOS", 0, fmt(l["created_at"]), fmt(l["updated_at"]),
        ))
    n = batch_insert(cur, "raw_loan", loan_cols, rows)
    print(f"  raw_loan: {n}")

    rep_cols = ["repayment_id","loan_id","customer_id","country_code","legal_entity",
                "installment_number","due_date","payment_date",
                "principal_due","interest_due","emi_due","penalty_charges",
                "amount_paid","principal_paid","interest_paid","outstanding_principal",
                "overdue_days","cumulative_overdue","payment_status",
                "payment_method","payment_channel","reference_number",
                "source_system","created_at"]
    r_rows = []
    for r in raw_reps:
        is_paid = r["payment_status"] in ("PAID","LATE_PAID")
        sched_d = r["scheduled_date"]
        actual_d = r["actual_payment_date"]
        r_rows.append((
            r["repayment_id"], r["loan_id"], r["customer_id"],
            r["country_code"], r["legal_entity"],
            r["installment_number"],
            fmt(sched_d), fmt(actual_d),
            r["principal_component"], r["interest_component"], r["emi_amount"],
            r["penalty_amount"],
            r["emi_amount"] if is_paid else 0.0,
            r["principal_component"] if is_paid else 0.0,
            r["interest_component"] if is_paid else 0.0,
            r["outstanding_after"], r["penalty_amount"],
            0.0,  # cumulative_overdue
            r["payment_status"],
            random.choice(["GIRO","UPI","NEFT","AUTO_DEBIT","MANUAL"]),
            random.choice(["MOBILE","INTERNET","AUTO_DEBIT"]),
            f"RREF{random.randint(10000000,99999999)}",
            "LOS", fmt(r["created_at"]),
        ))
    n = batch_insert(cur, "raw_loan_repayment", rep_cols, r_rows)
    print(f"  raw_loan_repayment: {n}")


# ── DDM: customers & merchants ─────────────────────────────────────────────────
def load_ddm_customers(cur, all_customers):
    cols = ["customer_key","customer_id","country_code","legal_entity","full_name",
            "date_of_birth","age","age_band","gender","email","phone",
            "city","nationality","id_type","id_number_masked","customer_segment",
            "kyc_status","kyc_expiry_date","risk_rating","annual_income","income_band",
            "occupation","tenure_months","acquisition_channel","relationship_manager",
            "is_active","effective_from","effective_to","is_current",
            "dw_created_at","dw_updated_at"]
    rows = []
    key = 1
    for custs in all_customers.values():
        for c in custs:
            age = (TODAY - c["date_of_birth"]).days // 365
            tenure = max(0, (TODAY - c["created_at"].date()).days // 30)
            rows.append((
                key, c["customer_id"], c["country_code"], c["legal_entity"],
                c["full_name"], fmt(c["date_of_birth"]), age, age_band(age), c["gender"],
                c["email"], c["phone"], c["city"], c["nationality"],
                c["id_type"], c["id_number"][:4] + "****",
                c["customer_segment"], c["kyc_status"], None,
                c["risk_rating"], c["annual_income"], c["income_band"],
                c["occupation"], tenure, c["acquisition_channel"], None,
                1,
                fmt(c["created_at"].date()), None, 1,
                fmt(c["created_at"]), fmt(NOW),
            ))
            key += 1
    n = batch_insert(cur, "ddm_customer", cols, rows)
    print(f"  ddm_customer: {n}")


def load_ddm_merchants(cur, merchants):
    MCAT_GROUP = {
        "GROCERY": "RETAIL", "RETAIL": "RETAIL", "FASHION": "RETAIL",
        "ELECTRONICS": "RETAIL", "FURNITURE": "RETAIL",
        "RESTAURANT": "F&B", "FOOD_DELIVERY": "F&B", "CAFE": "F&B",
        "TRAVEL": "TRAVEL", "AIRLINE": "TRAVEL", "HOTEL": "TRAVEL",
        "TRANSPORT": "TRANSPORT", "PETROL": "TRANSPORT",
        "HEALTHCARE": "SERVICES", "INSURANCE": "SERVICES",
        "ENTERTAINMENT": "LEISURE", "SPORTS": "LEISURE",
    }
    cols = ["merchant_key","merchant_id","merchant_name","merchant_name_clean",
            "merchant_category","merchant_category_group","mcc_code","country_code",
            "city","is_online","risk_tier","is_blacklisted",
            "total_transaction_count","total_transaction_volume","avg_transaction_amount",
            "fraud_rate","decline_rate","dw_created_at"]
    rows = []
    for i, m in enumerate(merchants, 1):
        vol = round(random.uniform(50000, 5000000), 2)
        cnt = random.randint(500, 50000)
        rows.append((
            i, m["merchant_id"], m["merchant_name"],
            m["merchant_name"].lower().strip(),
            m["merchant_category"],
            MCAT_GROUP.get(m["merchant_category"], "OTHER"),
            m["mcc_code"], m["country_code"], m["city"],
            m["is_online"], m["risk_tier"], 0,
            cnt, vol, round(vol / cnt, 2),
            m["fraud_rate"], m["decline_rate"],
            fmt(m["created_at"]),
        ))
    n = batch_insert(cur, "ddm_merchant", cols, rows)
    print(f"  ddm_merchant: {n}")


# ── DDM: CC accounts, cards, transactions, statements, payments ────────────────
def load_ddm_cc(cur, all_customers, all_accounts, all_txns, stmt_rows, pay_rows, card_rows):
    # ddm_account
    acols = ["account_key","account_id","customer_key","customer_id","country_code",
             "legal_entity","account_type","account_subtype","currency_code",
             "current_balance","available_balance","credit_limit","utilization_pct",
             "interest_rate","status","status_reason","branch_code","product_code",
             "product_name","open_date","tenure_months","last_activity_date",
             "days_since_activity","is_active","effective_from","effective_to",
             "is_current","dw_created_at"]
    arows = []
    key = 1
    for accts in all_accounts.values():
        for a in accts:
            u = a["_util"]
            open_d = a["open_date"]
            tenure = max(0, (TODAY - open_d).days // 30) if isinstance(open_d, date) else 0
            last_act = a["last_activity_date"]
            days_since = (TODAY - last_act).days if isinstance(last_act, date) else 0
            is_active = 1 if a["account_status"] == "ACTIVE" else 0
            arows.append((
                key, a["account_id"], 0, a["customer_id"],
                a["country_code"], a["legal_entity"],
                a["account_type"], None,
                a["currency_code"], a["current_balance"], a["available_balance"],
                a["credit_limit"], u, a["_rate"],
                a["account_status"], a.get("freeze_reason"),
                a["branch_code"], a["product_code"], a["product_name"],
                fmt(open_d), tenure, fmt(last_act), days_since,
                is_active, fmt(open_d), None, 1,
                fmt(a["created_at"]),
            ))
            key += 1
    n = batch_insert(cur, "ddm_account", acols, arows)
    print(f"  ddm_account: {n}")

    # ddm_card
    # card_rows unfiltered tuples (18 items):
    # card_id,account_id,customer_id,cc,le,card_type,scheme,card_masked,tier,
    # iss,exp,status,is_primary,daily_limit,intl,contactless,created_at,updated_at
    card_ddm_cols = ["card_key","card_id","account_key","customer_key","country_code",
                     "card_type","card_category","card_number_masked",
                     "credit_limit","available_credit","outstanding_balance","utilization_pct",
                     "min_payment_due","expiry_date","days_to_expiry","status",
                     "is_primary","is_expired","is_blocked","reward_points",
                     "contactless_enabled","online_enabled","intl_enabled","dw_created_at"]
    crows = []
    for k, t in enumerate(card_rows, 1):
        (card_id,account_id,customer_id,cc,le,ctype,scheme,card_masked,tier,
         iss,exp,cst,primary,dlim,intl,cont,cat,uat) = t
        days_exp = max(0, (exp - TODAY).days) if isinstance(exp, date) else 0
        is_exp = 1 if isinstance(exp, date) and exp < TODAY else 0
        is_blk = 1 if cst == "BLOCKED" else 0
        crows.append((
            k, card_id, 0, 0, cc,
            ctype, scheme, card_masked,
            dlim, dlim, 0.0, 0.0,
            0.0,
            fmt(exp), days_exp, cst,
            primary, is_exp, is_blk, 0,
            cont, 1, intl,
            fmt(cat),
        ))
    n = batch_insert(cur, "ddm_card", card_ddm_cols, crows)
    print(f"  ddm_card: {n}")

    # ddm_transaction
    txn_cols = ["transaction_key","transaction_id","account_key","card_key","customer_key",
                "merchant_key","country_code","transaction_date","posting_date",
                "year_month","year_quarter","amount_local","amount_usd","currency_code",
                "fx_rate","transaction_type","channel","merchant_category",
                "merchant_category_group","mcc_code","status","decline_reason",
                "is_fraud","fraud_score","fraud_tier","is_international",
                "is_contactless","is_recurring","dw_created_at"]
    MCAT_GROUP = {
        "GROCERY": "RETAIL", "RETAIL": "RETAIL", "FASHION": "RETAIL",
        "ELECTRONICS": "RETAIL", "RESTAURANT": "F&B", "FOOD_DELIVERY": "F&B",
        "TRAVEL": "TRAVEL", "AIRLINE": "TRAVEL", "HOTEL": "TRAVEL",
        "TRANSPORT": "TRANSPORT", "PETROL": "TRANSPORT",
        "HEALTHCARE": "SERVICES", "ENTERTAINMENT": "LEISURE",
    }
    FX = {"SGD": 0.74, "MYR": 0.22, "INR": 0.012}
    trows = []
    for k, txns in enumerate(all_txns.values()):
        for j, t in enumerate(txns):
            tkey = k * 100000 + j + 1
            td = t["transaction_date"]
            quarter = f"{td.year}-Q{(td.month-1)//3+1}"
            fx = FX.get(t["currency_code"], 1.0)
            trows.append((
                tkey, t["transaction_id"],
                0, 0, 0, 0,
                t["country_code"], fmt(td), fmt(t["settlement_date"]),
                td.strftime("%Y-%m"), quarter,
                t["amount"], round(t["amount"] * fx, 2), t["currency_code"],
                fx, t["transaction_type"], t["channel"],
                t["merchant_category"],
                MCAT_GROUP.get(t["merchant_category"], "OTHER"),
                t["mcc_code"], t["auth_status"], t["decline_reason"],
                t["is_fraud"], t["fraud_score"], t["fraud_tier"],
                t["is_international"], t["is_contactless"],
                t.get("is_recurring", 0),
                fmt(t["created_at"]),
            ))
    n = batch_insert(cur, "ddm_transaction", txn_cols, trows)
    print(f"  ddm_transaction: {n}")

    # ddm_payment
    pay_ddm_cols = ["payment_key","payment_id","account_key","customer_key",
                    "country_code","payment_date","due_date","statement_date",
                    "days_before_due","is_early","is_on_time","is_late",
                    "minimum_due","total_due","amount_paid","payment_ratio",
                    "is_full_payment","is_minimum_only","is_partial",
                    "payment_method","payment_status","overdue_days","late_fee",
                    "dw_created_at"]
    # pay_rows: (pay_id,acct_id,cust_id,cc,le,pay_dt,due_dt,stmt_mth,min_due,total_due,
    #            pay_amt,method,channel,stat,days_od,late_fee,ref,created_at)
    prows = []
    for k, pr in enumerate(pay_rows, 1):
        (pid,aid,cid,cc,le,pdt,ddt,smth,mdue,tdue,pamt,meth,chan,pstat,dod,ltfee,ref,cat) = pr
        ratio   = round(pamt / tdue, 4) if tdue and tdue > 0 else 0
        is_full = 1 if pamt >= tdue * 0.99 else 0
        is_min  = 1 if (not is_full and mdue and abs(pamt - mdue) < 1.0) else 0
        is_part = 1 if (not is_full and not is_min) else 0
        if isinstance(pdt, datetime) and isinstance(ddt, date):
            dbefore = (ddt - pdt.date()).days
        else:
            dbefore = 0
        is_early  = 1 if dbefore >  3 else 0
        is_ontime = 1 if 0 <= dbefore <= 3 else 0
        is_late   = 1 if dod and dod > 0 else 0
        prows.append((
            k, pid, 0, 0,
            cc, fmt(pdt), fmt(ddt), smth,
            dbefore, is_early, is_ontime, is_late,
            mdue, tdue, pamt, ratio,
            is_full, is_min, is_part,
            meth, pstat, dod or 0, ltfee or 0.0,
            fmt(cat),
        ))
    n = batch_insert(cur, "ddm_payment", pay_ddm_cols, prows)
    print(f"  ddm_payment: {n}")

    # ddm_statement
    stmt_ddm_cols = ["statement_key","statement_id","account_key","customer_key",
                     "country_code","statement_year_month","statement_date","due_date",
                     "payment_date","days_to_due","opening_balance","closing_balance",
                     "total_spend","total_credits","minimum_due","total_due",
                     "interest_charged","late_fee","reward_points_earned",
                     "reward_points_redeemed","transaction_count",
                     "is_paid","is_overdue","days_overdue","dw_created_at"]
    # stmt_rows tuples (22 items):
    # 0:sid 1:aid 2:cid 3:cc 4:le 5:sdt 6:smth 7:obal 8:cbal 9:tspend 10:tcrdt
    # 11:tfees 12:mdue 13:tdue 14:ddt 15:pstat 16:clim 17:avail 18:util 19:tcnt
    # 20:intch 21:cat
    srows = []
    for k, sr in enumerate(stmt_rows, 1):
        (sid,aid,cid,cc,le,sdt,smth,obal,cbal,tspend,tcrdt,tfees,mdue,tdue,
         ddt,pstat,clim,avail,util,tcnt,intch,cat) = sr
        sdt_d = sdt if isinstance(sdt, date) else sdt
        ddt_d = ddt if isinstance(ddt, date) else ddt
        days_to = (ddt_d - sdt_d).days if isinstance(ddt_d, date) and isinstance(sdt_d, date) else 0
        is_paid = 1 if pstat in ("PAID", "PAID_LATE") else 0
        is_ovrd = 1 if pstat in ("OVERDUE", "UNPAID") else 0
        srows.append((
            k, sid, 0, 0,
            cc, smth, fmt(sdt), fmt(ddt),
            None,
            days_to, obal, cbal, tspend, tcrdt,
            mdue, tdue, intch, tfees,
            0, 0,
            tcnt, is_paid, is_ovrd, 0,
            fmt(cat),
        ))
    n = batch_insert(cur, "ddm_statement", stmt_ddm_cols, srows)
    print(f"  ddm_statement: {n}")

# ── DDM: deposits ──────────────────────────────────────────────────────────────
def load_ddm_deposits(cur, all_customers, raw_dep_accts, ddm_dep_rows):
    cust_map = {}
    for custs in all_customers.values():
        for c in custs:
            cust_map[c["customer_id"]] = c

    cols = ["deposit_key","deposit_id","account_id","customer_id","country_code",
            "legal_entity","customer_segment","deposit_type","deposit_category",
            "product_name","currency_code","current_balance","deposit_amount",
            "interest_rate","interest_earned_ytd","tenor_months","balance_band",
            "is_fd","is_term_maturing_30d","has_salary_credit","tenure_months",
            "status","open_date","maturity_date","last_debit_date","last_credit_date",
            "dw_refreshed_at"]
    rows = []
    for i, d in enumerate(ddm_dep_rows):
        mat_d = d["maturity_date"]
        is_maturing_30d = (1 if mat_d and isinstance(mat_d, date) and
                           (mat_d - TODAY).days <= 30 and mat_d >= TODAY else 0)
        rows.append((
            i + 1,  # deposit_key
            d["deposit_account_id"], d["deposit_account_id"],  # deposit_id, account_id
            d["customer_id"], d["country_code"], d["legal_entity"],
            d["customer_segment"], d["account_type"], d["account_category"],
            d["product_name"], d["currency_code"],
            d["current_balance"], d["current_balance"],  # deposit_amount = balance
            d["interest_rate"], d["accrued_interest"],
            d["tenor_months"],
            d["balance_band"], d["is_fd"], is_maturing_30d,
            0,  # has_salary_credit
            d.get("_tenor_months", 0), d["account_status"],
            fmt(d["open_date"]), fmt(d["maturity_date"]),
            None,  # last_debit_date
            fmt(d["last_transaction_date"]),
            fmt(NOW),
        ))
    n = batch_insert(cur, "ddm_deposit_account", cols, rows)
    print(f"  ddm_deposit_account: {n}")

# ── DDM: loans ─────────────────────────────────────────────────────────────────
def load_ddm_loans(cur, all_customers, raw_loans, raw_reps, ddm_loan_rows, ddm_rep_rows):
    cust_map = {}
    for custs in all_customers.values():
        for c in custs:
            cust_map[c["customer_id"]] = c

    loan_cols = ["loan_key","loan_id","account_id","customer_id","country_code",
                 "legal_entity","customer_segment","loan_type","loan_category",
                 "currency_code","loan_amount","outstanding_balance","interest_rate",
                 "emi_amount","loan_term_months","months_remaining","disbursement_date",
                 "maturity_date","loan_status","dpd_bucket","overdue_days","npa_flag",
                 "ltv_ratio","loan_to_income_ratio","dw_refreshed_at"]
    lrows = []
    for i, l in enumerate(ddm_loan_rows):
        c = cust_map.get(l["customer_id"], {})
        disburs = l["disbursement_date"]
        maturity = disburs + timedelta(days=30 * l["tenor_months"])
        months_rem = max(0, l["tenor_months"] - ((TODAY - disburs).days // 30))
        ltv = round(l["principal_amount"] / (l["principal_amount"] * 1.25), 4) if l["loan_type"] in ("HOME","AUTO") else None
        lrows.append((
            i+1, l["loan_id"], l["loan_id"],
            l["customer_id"], l["country_code"], l["legal_entity"],
            l["customer_segment"], l["loan_type"], l["loan_category"],
            l["currency_code"], l["principal_amount"], l["outstanding_balance"],
            l["interest_rate"], l["emi_amount"], l["tenor_months"], months_rem,
            fmt(disburs), fmt(maturity), l["loan_status"],
            l["dpd_bucket"], l["current_dpd"], l["is_npa"],
            ltv, l["loan_to_income_ratio"], fmt(NOW),
        ))
    n = batch_insert(cur, "ddm_loan", loan_cols, lrows)
    print(f"  ddm_loan: {n}")

    rep_cols = ["repayment_key","repayment_id","loan_id","customer_id","country_code",
                "legal_entity","customer_segment","loan_type","installment_number",
                "due_date","payment_date","emi_due","amount_paid","outstanding_principal",
                "overdue_days","payment_status","is_late","delay_days","dw_refreshed_at"]
    loan_meta = {l["loan_id"]: l for l in ddm_loan_rows}
    rrows = []
    for i, r in enumerate(ddm_rep_rows):
        lm = loan_meta.get(r["loan_id"], {})
        c  = cust_map.get(r["customer_id"], {})
        is_paid = r["payment_status"] in ("PAID","LATE_PAID")
        rrows.append((
            i+1, r["repayment_id"], r["loan_id"],
            r["customer_id"], r["country_code"], r.get("legal_entity", ""),
            c.get("customer_segment",""), lm.get("loan_type",""),
            r["installment_number"],
            fmt(r["scheduled_date"]), fmt(r["actual_payment_date"]),
            r["emi_amount"], r["emi_amount"] if is_paid else 0.0,
            r["outstanding_after"],
            0,  # overdue_days
            r["payment_status"],
            r["is_late"], r["delay_days"], fmt(NOW),
        ))
    n = batch_insert(cur, "ddm_loan_repayment", rep_cols, rrows)
    print(f"  ddm_loan_repayment: {n}")

# ── DP LAYER ───────────────────────────────────────────────────────────────────
def load_dp_layer(cur, all_customers, all_accounts, all_txns, stmt_rows, pay_rows,
                  raw_dep_accts, raw_loans):
    from collections import defaultdict
    cust_map = {}
    acct_map = {}  # customer_id -> list of accounts
    for custs in all_customers.values():
        for c in custs:
            cust_map[c["customer_id"]] = c
    for accts in all_accounts.values():
        for a in accts:
            acct_map.setdefault(a["customer_id"], []).append(a)

    dep_by_cust  = defaultdict(list)
    for d in raw_dep_accts:
        dep_by_cust[d["customer_id"]].append(d)

    loan_by_cust = defaultdict(list)
    for l in raw_loans:
        loan_by_cust[l["customer_id"]].append(l)

    txn_by_cust  = defaultdict(list)
    for txns in all_txns.values():
        for t in txns:
            if t["auth_status"] == "APPROVED":
                txn_by_cust[t["customer_id"]].append(t)

    # ── dp_customer_balance_snapshot ─────────────────────────────────────────
    # One row per account snapshot
    bal_cols = ["snapshot_date","customer_id","account_id","country_code","legal_entity",
                "customer_segment","account_type","currency_code",
                "current_balance","available_balance","credit_limit","utilization_pct",
                "outstanding_balance","min_payment_due","is_overdue","overdue_days",
                "account_status","dw_refreshed_at"]
    bal_rows = []
    snap_date = fmt(TODAY)
    snap_month = TODAY.strftime("%Y-%m")
    for accts in all_accounts.values():
        for a in accts:
            c = cust_map.get(a["customer_id"], {})
            is_ov = 1 if a.get("current_dpd", 0) > 0 else 0
            bal_rows.append((snap_date, a["customer_id"], a["account_id"],
                             a["country_code"], a["legal_entity"],
                             c.get("customer_segment"), a["account_type"],
                             a["currency_code"],
                             a["current_balance"], a["available_balance"],
                             a["credit_limit"], a["_util"],
                             a["current_balance"],  # outstanding ≈ current_balance
                             0.0,  # min_payment_due
                             is_ov, a.get("current_dpd", 0),
                             a["account_status"], fmt(NOW)))
    n = batch_insert(cur, "dp_customer_balance_snapshot", bal_cols, bal_rows)
    print(f"  dp_customer_balance_snapshot: {n}")

    # ── dp_customer_spend_monthly ─────────────────────────────────────────────
    # Per customer-month-category row
    MCAT_GRP = {
        "GROCERY": "RETAIL", "RETAIL": "RETAIL", "FASHION": "RETAIL",
        "ELECTRONICS": "RETAIL", "FURNITURE": "RETAIL",
        "RETAIL_SHOPPING": "RETAIL",
        "RESTAURANT": "F&B", "FOOD_DELIVERY": "F&B", "CAFE": "F&B",
        "FOOD_DINING": "F&B",
        "TRAVEL": "TRAVEL", "AIRLINE": "TRAVEL", "HOTEL": "TRAVEL",
        "TRAVEL_TRANSPORT": "TRAVEL", "HOTEL_LODGING": "TRAVEL",
        "TRANSPORT": "TRANSPORT", "PETROL": "TRANSPORT", "FUEL_PETROL": "TRANSPORT",
        "HEALTHCARE": "SERVICES", "INSURANCE": "SERVICES",
        "ENTERTAINMENT": "LEISURE", "SPORTS": "LEISURE",
        "UTILITIES": "UTILITIES", "EDUCATION": "EDUCATION",
    }
    spend_cols = ["year_month","customer_id","country_code","legal_entity",
                  "merchant_category","merchant_category_group",
                  "total_spend","transaction_count","avg_transaction_amount",
                  "max_single_transaction","unique_merchants","currency_code",
                  "channel_online_pct","channel_intl_pct","dw_refreshed_at"]
    spend_rows = []
    for cid, txns in txn_by_cust.items():
        c = cust_map.get(cid)
        if not c: continue
        by_month_cat = defaultdict(list)
        for t in txns:
            key = (t["transaction_date"].strftime("%Y-%m"), t["merchant_category"])
            by_month_cat[key].append(t)
        for (mth, cat), mtxns in by_month_cat.items():
            amounts  = [float(t["amount"]) for t in mtxns]
            tspend   = sum(amounts)
            if tspend == 0: continue
            merchants = set(t["merchant_name"] for t in mtxns)
            online_n  = sum(1 for t in mtxns if t["channel"] in ("ONLINE", "MOBILE"))
            intl_n    = sum(1 for t in mtxns if t["is_international"])
            spend_rows.append((
                mth, cid, c["country_code"], c["legal_entity"],
                cat, MCAT_GRP.get(cat, "OTHER"),
                round(tspend, 2), len(mtxns),
                round(tspend / len(mtxns), 2),
                round(max(amounts), 2),
                len(merchants), c["currency_code"],
                round(online_n / len(mtxns), 4),
                round(intl_n / len(mtxns), 4),
                fmt(NOW),
            ))
    n = batch_insert(cur, "dp_customer_spend_monthly", spend_cols, spend_rows)
    print(f"  dp_customer_spend_monthly: {n}")

    # ── dp_transaction_enriched ───────────────────────────────────────────────
    TE_MCAT_GRP = {
        "GROCERY": "RETAIL", "RETAIL": "RETAIL", "RETAIL_SHOPPING": "RETAIL",
        "FASHION": "RETAIL", "ELECTRONICS": "RETAIL",
        "RESTAURANT": "F&B", "FOOD_DELIVERY": "F&B", "FOOD_DINING": "F&B",
        "TRAVEL": "TRAVEL", "AIRLINE": "TRAVEL", "HOTEL": "TRAVEL",
        "TRAVEL_TRANSPORT": "TRAVEL",
        "TRANSPORT": "TRANSPORT", "PETROL": "TRANSPORT", "FUEL_PETROL": "TRANSPORT",
        "HEALTHCARE": "SERVICES", "INSURANCE": "SERVICES",
        "ENTERTAINMENT": "LEISURE", "SPORTS": "LEISURE",
        "UTILITIES": "UTILITIES", "EDUCATION": "EDUCATION",
    }
    te_cols = ["transaction_id","transaction_date","year_month",
               "customer_id","account_id","card_id",
               "country_code","legal_entity","customer_segment","risk_rating","full_name",
               "amount_local","currency_code","transaction_type","channel",
               "merchant_id","merchant_name","merchant_category","merchant_category_group",
               "mcc_code","merchant_risk_tier","status","decline_reason",
               "is_fraud","fraud_score","fraud_tier",
               "is_international","is_contactless","is_recurring","dw_refreshed_at"]
    te_rows = []
    for txns in all_txns.values():
        for t in txns:
            c = cust_map.get(t["customer_id"], {})
            te_rows.append((
                t["transaction_id"],
                fmt(t["transaction_date"]),
                t["transaction_date"].strftime("%Y-%m"),
                t["customer_id"], t["account_id"], t.get("card_id"),
                t["country_code"], t["legal_entity"],
                c.get("customer_segment"), c.get("risk_rating"), c.get("full_name"),
                t["amount"], t["currency_code"], t["transaction_type"], t["channel"],
                t.get("merchant_id"), t["merchant_name"],
                t["merchant_category"],
                TE_MCAT_GRP.get(t["merchant_category"], "OTHER"),
                t["mcc_code"], t["_merchant_risk"],
                t["auth_status"], t["decline_reason"],
                t["is_fraud"], t["fraud_score"], t["fraud_tier"],
                t["is_international"], t["is_contactless"],
                t.get("is_recurring", 0),
                fmt(NOW),
            ))
    n = batch_insert(cur, "dp_transaction_enriched", te_cols, te_rows)
    print(f"  dp_transaction_enriched: {n}")

    # ── dp_payment_status ─────────────────────────────────────────────────────
    ps_cols = ["as_of_date","account_id","customer_id","country_code","legal_entity",
               "statement_year_month","statement_date","due_date","days_to_due",
               "minimum_due","total_due","amount_paid","amount_outstanding","payment_status",
               "overdue_days","overdue_bucket","late_fee","interest_at_risk",
               "payment_method","is_giro_enabled","consecutive_late_months",
               "customer_segment","dw_refreshed_at"]
    ps_rows = []
    for pr in pay_rows:
        (pid,aid,cid,cc,le,pdt,ddt,smth,mdue,tdue,pamt,meth,chan,pstat,dod,ltfee,ref,cat) = pr
        c = cust_map.get(cid, {})
        dtd = (ddt - TODAY).days if isinstance(ddt, date) else 0
        amt_out = round(max(0, tdue - pamt), 2)
        int_risk = round(amt_out * 0.015, 2) if pstat == "OVERDUE" else 0
        # Derive statement_date from statement_year_month (first day of month)
        try:
            from datetime import datetime as _dt
            stmt_d = fmt(_dt.strptime(smth, "%Y-%m").date()) if smth else None
        except Exception:
            stmt_d = None
        is_giro = 1 if meth == "GIRO" else 0
        ps_rows.append((
            fmt(TODAY), aid, cid, cc, le,
            smth, stmt_d, fmt(ddt), dtd, mdue, tdue, pamt, amt_out, pstat,
            dod or 0, overdue_bucket(dod), ltfee or 0.0, int_risk,
            meth, is_giro, 0,
            c.get("customer_segment"), fmt(NOW),
        ))
    n = batch_insert(cur, "dp_payment_status", ps_cols, ps_rows)
    print(f"  dp_payment_status: {n}")

    # ── dp_deposit_portfolio ──────────────────────────────────────────────────
    ddp_cols = ["snapshot_month","customer_id","country_code","legal_entity",
                "customer_segment","currency_code",
                "savings_balance","savings_account_count","savings_interest_rate","savings_interest_earned",
                "current_balance","current_account_count",
                "fd_balance","fd_count","fd_avg_rate","fd_maturing_next_30d","fd_maturing_next_90d",
                "total_deposit_balance","total_deposit_accounts","total_interest_earned_ytd",
                "avg_monthly_credits","avg_monthly_debits","monthly_credit_count","monthly_debit_count",
                "has_salary_credit","salary_credit_amount",
                "deposit_balance_mom_change","deposit_balance_mom_pct","dw_refreshed_at"]
    ddp_rows = []
    for custs in all_customers.values():
        for c in custs:
            deps = dep_by_cust.get(c["customer_id"], [])
            if not deps: continue
            sav   = [d for d in deps if d["account_category"] == "SAVINGS"]
            cur_d = [d for d in deps if d["account_category"] == "CURRENT"]
            fds   = [d for d in deps if d["account_category"] == "TERM_DEPOSIT"]
            sbal  = sum(d["current_balance"] for d in sav)
            cbal  = sum(d["current_balance"] for d in cur_d)
            fbal  = sum(d["current_balance"] for d in fds)
            savrate= round(sum(d["interest_rate"] for d in sav)/len(sav),4) if sav else 0
            fdrate = round(sum(d["interest_rate"] for d in fds)/len(fds),4) if fds else 0
            sav_int= round(sum(d["accrued_interest"] for d in sav),2)
            fd_mat30  = sum(d["current_balance"] for d in fds
                           if d["maturity_date"] and isinstance(d["maturity_date"],date) and
                           0 <= (d["maturity_date"]-TODAY).days <= 30)
            fd_mat90  = sum(d["current_balance"] for d in fds
                           if d["maturity_date"] and isinstance(d["maturity_date"],date) and
                           0 <= (d["maturity_date"]-TODAY).days <= 90)
            tbal  = sbal + cbal + fbal
            int_ytd = round(sum(d["accrued_interest"] for d in deps), 2)
            avg_cr = round(tbal * 0.12, 2)
            avg_dr = round(tbal * 0.10, 2)
            ddp_rows.append((
                snap_month, c["customer_id"], c["country_code"], c["legal_entity"],
                c["customer_segment"], c["currency_code"],
                round(sbal,2), len(sav), savrate, sav_int,
                round(cbal,2), len(cur_d),
                round(fbal,2), len(fds), fdrate, round(fd_mat30,2), round(fd_mat90,2),
                round(tbal,2), len(deps), int_ytd,
                avg_cr, avg_dr, random.randint(8,20), random.randint(15,35),
                0, 0.0,
                round(tbal * random.uniform(-0.05, 0.08), 2),
                round(random.uniform(-0.05, 0.08), 4),
                fmt(NOW),
            ))
    n = batch_insert(cur, "dp_deposit_portfolio", ddp_cols, ddp_rows)
    print(f"  dp_deposit_portfolio: {n}")

    # ── dp_loan_portfolio ─────────────────────────────────────────────────────
    dlp_cols = ["snapshot_month","customer_id","country_code","legal_entity",
                "customer_segment","currency_code","annual_income",
                "personal_loan_outstanding","personal_loan_count","personal_loan_emi",
                "home_loan_outstanding","home_loan_count","home_loan_emi",
                "auto_loan_outstanding","auto_loan_count","auto_loan_emi",
                "business_loan_outstanding","business_loan_count","business_loan_emi",
                "education_loan_outstanding","education_loan_count",
                "total_loan_outstanding","total_loan_count","total_monthly_emi",
                "max_overdue_days","overdue_loan_count","is_npa","npa_amount",
                "dpd_bucket","debt_to_income_ratio","debt_service_ratio","dw_refreshed_at"]
    dlp_rows = []
    for custs in all_customers.values():
        for c in custs:
            loans = loan_by_cust.get(c["customer_id"], [])
            if not loans: continue
            def lsub(lt):
                sl = [l for l in loans if l["loan_type"] == lt]
                return (sum(l["outstanding_balance"] for l in sl),
                        len(sl), sum(l["emi_amount"] for l in sl))
            pl = lsub("PERSONAL"); hl = lsub("HOME"); al = lsub("AUTO")
            bl = lsub("BUSINESS"); el = lsub("EDUCATION")
            tot_out = pl[0]+hl[0]+al[0]+bl[0]+el[0]
            tot_emi = pl[2]+hl[2]+al[2]+bl[2]+el[2]
            tot_cnt = pl[1]+hl[1]+al[1]+bl[1]+el[1]
            max_dpd = max((l["current_dpd"] for l in loans), default=0)
            od_cnt  = sum(1 for l in loans if l["current_dpd"] > 0)
            is_npa  = 1 if any(l["is_npa"] for l in loans) else 0
            npa_amt = sum(l["outstanding_balance"] for l in loans if l["is_npa"])
            dti     = round(tot_out / max(1, c["annual_income"]), 4)
            dsr     = round(tot_emi / max(1, c["annual_income"]/12), 4)
            dlp_rows.append((
                snap_month, c["customer_id"], c["country_code"], c["legal_entity"],
                c["customer_segment"], c["currency_code"], c["annual_income"],
                round(pl[0],2),pl[1],round(pl[2],2),
                round(hl[0],2),hl[1],round(hl[2],2),
                round(al[0],2),al[1],round(al[2],2),
                round(bl[0],2),bl[1],round(bl[2],2),
                round(el[0],2),el[1],
                round(tot_out,2),tot_cnt,round(tot_emi,2),
                max_dpd, od_cnt, is_npa, round(npa_amt,2),
                dpd_bucket(max_dpd), dti, dsr, fmt(NOW),
            ))
    n = batch_insert(cur, "dp_loan_portfolio", dlp_cols, dlp_rows)
    print(f"  dp_loan_portfolio: {n}")

    # ── dp_risk_signals ───────────────────────────────────────────────────────
    rs_cols = ["signal_date","customer_id","country_code","legal_entity","risk_rating",
               "fraud_transaction_count","fraud_transaction_amount",
               "fraud_rate_30d","fraud_score_avg_30d","fraud_score_max_30d",
               "high_risk_merchant_count","blacklisted_merchant_count",
               "card_decline_count_30d","card_decline_rate_30d",
               "intl_transaction_count_30d","intl_transaction_amount_30d",
               "transaction_count_24h","transaction_amount_24h",
               "unique_merchants_24h","unique_countries_24h",
               "overdue_accounts_count","max_overdue_days","total_overdue_amount",
               "composite_risk_score","risk_tier",
               "alert_triggered","alert_type","dw_refreshed_at"]
    rs_rows = []
    signal_date = fmt(TODAY)
    for custs in all_customers.values():
        for c in custs:
            cid = c["customer_id"]
            ctxns = txn_by_cust.get(cid, [])
            total = len(ctxns)
            fraud_txns  = [t for t in ctxns if t["is_fraud"]]
            fraud_n     = len(fraud_txns)
            fraud_amt   = round(sum(float(t["amount"]) for t in fraud_txns), 2)
            fraud_rate  = round(fraud_n / max(1, total), 6)
            scores      = [float(t["fraud_score"]) for t in ctxns]
            avg_score   = round(sum(scores) / len(scores), 4) if scores else 0
            max_score   = round(max(scores), 4) if scores else 0
            dec_txns    = [t for t in ctxns if t["auth_status"] == "DECLINED"]
            intl_txns   = [t for t in ctxns if t["is_international"]]
            intl_amt    = round(sum(float(t["amount"]) for t in intl_txns), 2)
            hi_risk_m   = sum(1 for t in ctxns if t["_merchant_risk"] in ("HIGH", "VERY_HIGH"))
            accts       = acct_map.get(cid, [])
            ov_accts    = [a for a in accts if a.get("current_dpd", 0) > 0]
            max_dpd     = max((a.get("current_dpd", 0) for a in accts), default=0)
            ov_amt      = round(sum(a["current_balance"] for a in ov_accts), 2)
            comp_score  = round(min(1.0, fraud_rate * 5 + avg_score * 0.5 +
                                   (max_dpd / 30) * 0.3), 4)
            risk_tier   = ("CRITICAL" if comp_score > 0.7 else
                           "HIGH" if comp_score > 0.4 else
                           "MEDIUM" if comp_score > 0.2 else "LOW")
            alert = 1 if comp_score > 0.5 or fraud_n > 0 else 0
            alert_type = ("FRAUD" if fraud_n > 0 else
                          "DELINQUENCY" if max_dpd > 30 else None)
            rs_rows.append((
                signal_date, cid, c["country_code"], c["legal_entity"],
                c["risk_rating"],
                fraud_n, fraud_amt, fraud_rate, avg_score, max_score,
                hi_risk_m, 0,  # blacklisted_merchant_count
                len(dec_txns), round(len(dec_txns) / max(1, total), 4),
                len(intl_txns), intl_amt,
                min(total, 5), round(sum(float(t["amount"]) for t in ctxns[:5]), 2),
                len(set(t["merchant_name"] for t in ctxns[:5])),
                len(set(t["country_code"] for t in ctxns[:5])),
                len(ov_accts), max_dpd, ov_amt,
                comp_score, risk_tier, alert, alert_type,
                fmt(NOW),
            ))
    n = batch_insert(cur, "dp_risk_signals", rs_cols, rs_rows)
    print(f"  dp_risk_signals: {n}")

    # ── dp_portfolio_kpis ─────────────────────────────────────────────────────
    kpi_cols = ["kpi_year_month","country_code","legal_entity","customer_segment",
                "account_type","total_customers","active_customers",
                "new_customers","churned_customers",
                "total_accounts","active_accounts","total_cards","active_cards",
                "total_outstanding_balance","total_credit_limit","avg_utilization_pct",
                "total_transaction_volume","total_transaction_count","avg_transaction_amount",
                "fraud_rate","decline_rate","delinquency_rate","overdue_amount",
                "payment_count","full_payment_rate","late_payment_rate",
                "total_late_fee_collected","estimated_interest_income","estimated_fee_income",
                "dw_refreshed_at"]
    kpi_rows = []
    end_m = TODAY.replace(day=1)
    all_pay_by_acct = defaultdict(list)
    for pr in pay_rows:
        all_pay_by_acct[pr[1]].append({"status": pr[13], "due": pr[8], "paid": pr[10],
                                        "late_fee": pr[15] or 0})
    for mo_off in range(18, -1, -1):
        mdate = end_m - timedelta(days=mo_off * 30)
        mstr  = mdate.strftime("%Y-%m")
        for cc, custs in all_customers.items():
            cfg   = COUNTRY_CONF[cc]
            accts = all_accounts.get(cc, [])
            cc_txns = [t for t in all_txns.get(cc, [])
                       if t["auth_status"] == "APPROVED" and
                       t["transaction_date"].strftime("%Y-%m") == mstr]
            n_cust  = len(custs)
            n_act   = int(n_cust * random.uniform(0.88, 0.96))
            tclim   = round(sum(a["credit_limit"] for a in accts), 2)
            tbal    = round(sum(a["current_balance"] for a in accts), 2)
            n_cards = len(accts)  # cc accounts = cards
            tspend  = round(sum(float(t["amount"]) for t in cc_txns), 2)
            t_cnt   = len(cc_txns)
            avg_u   = round(tbal / max(1, tclim), 4)
            frate   = round(sum(1 for t in cc_txns if t["is_fraud"]) / max(1, t_cnt), 6)
            drate   = round(sum(1 for t in all_txns.get(cc, []) if t["auth_status"] == "DECLINED") /
                            max(1, len(all_txns.get(cc, []))), 6)
            ov_amt  = round(sum(a["current_balance"] for a in accts
                               if a.get("current_dpd", 0) > 0), 2)
            pay_cnt = len([pr for pr in pay_rows if pr[3] == cc])
            full_pay= round(sum(1 for pr in pay_rows if pr[3] == cc and pr[10] >= pr[9] * 0.99)
                            / max(1, pay_cnt), 4)
            late_pay= round(sum(1 for pr in pay_rows if pr[3] == cc and (pr[14] or 0) > 0)
                            / max(1, pay_cnt), 4)
            late_fee= round(sum(float(pr[15] or 0) for pr in pay_rows if pr[3] == cc), 2)
            for seg in set(c["customer_segment"] for c in custs):
                kpi_rows.append((
                    mstr, cc, cfg["legal_entity"], seg, "CC",
                    n_cust, n_act,
                    random.randint(1, 10), random.randint(0, 5),
                    len(accts), int(len(accts) * 0.90), n_cards, int(n_cards * 0.88),
                    tbal, tclim, avg_u,
                    tspend, t_cnt,
                    round(tspend / max(1, t_cnt), 2),
                    frate, drate,
                    round(random.uniform(0.02, 0.08), 4),
                    ov_amt, pay_cnt, full_pay, late_pay,
                    late_fee,
                    round(tbal * 0.018 / 12, 2),
                    round(late_fee * 0.3, 2),
                    fmt(NOW),
                ))
    n = batch_insert(cur, "dp_portfolio_kpis", kpi_cols, kpi_rows)
    print(f"  dp_portfolio_kpis: {n}")

# ── SEMANTIC LAYER ─────────────────────────────────────────────────────────────
def load_semantic_layer(cur, all_customers, all_accounts, all_txns, stmt_rows,
                        raw_dep_accts, raw_loans, pay_rows):
    from collections import defaultdict
    cust_map = {}
    acct_map = defaultdict(list)
    for custs in all_customers.values():
        for c in custs:
            cust_map[c["customer_id"]] = c
    for accts in all_accounts.values():
        for a in accts:
            acct_map[a["customer_id"]].append(a)

    dep_by_cust  = defaultdict(list)
    for d in raw_dep_accts:
        dep_by_cust[d["customer_id"]].append(d)

    loan_by_cust = defaultdict(list)
    for l in raw_loans:
        loan_by_cust[l["customer_id"]].append(l)

    txn_by_cust  = defaultdict(list)
    for txns in all_txns.values():
        for t in txns:
            txn_by_cust[t["customer_id"]].append(t)

    snap_month = TODAY.strftime("%Y-%m")

    # Build account_id lookup for semantic_payment_status
    acct_by_id = {}
    for accts in all_accounts.values():
        for a in accts:
            acct_by_id[a["account_id"]] = a

    # ── semantic_customer_360 ─────────────────────────────────────────────────
    s360_cols = ["customer_id","country_code","legal_entity","full_name",
                 "customer_segment","risk_rating","kyc_status",
                 "age","age_band","income_band","tenure_months",
                 "primary_account_id","primary_account_type",
                 "current_balance","available_balance","credit_limit","utilization_pct",
                 "active_card_count","total_credit_limit_cards","total_outstanding_cards",
                 "max_card_utilization_pct",
                 "spend_last_30d","transaction_count_last_30d","top_spend_category",
                 "payment_status","total_due","days_to_due",
                 "consecutive_late_months","is_overdue",
                 "as_of_date","dw_refreshed_at"]
    s360_rows = []
    mtd_mth  = TODAY.strftime("%Y-%m")
    cutoff30 = datetime.combine(TODAY - timedelta(days=30), datetime.min.time())
    for custs in all_customers.values():
        for c in custs:
            accts = acct_map.get(c["customer_id"], [])
            if not accts:
                prim_acct = None; cbal=0; abal=0; clim=0; util=0; max_util=0
            else:
                prim_acct = accts[0]
                cbal  = prim_acct["current_balance"]
                abal  = prim_acct["available_balance"]
                clim  = prim_acct["credit_limit"]
                util  = round(cbal / clim, 4) if clim > 0 else 0
                max_util = max(a["_util"] for a in accts)
            tc_lim  = sum(a["credit_limit"] for a in accts)
            tc_out  = sum(a["current_balance"] for a in accts)
            ctxns   = txn_by_cust.get(c["customer_id"], [])
            spend30 = sum(float(t["amount"]) for t in ctxns
                          if t["auth_status"] == "APPROVED" and
                          t["transaction_date"] >= cutoff30)
            cnt30   = sum(1 for t in ctxns
                          if t["auth_status"] == "APPROVED" and
                          t["transaction_date"] >= cutoff30)
            cats    = defaultdict(float)
            for t in ctxns:
                if t["auth_status"] == "APPROVED":
                    cats[t["merchant_category"]] += float(t["amount"])
            top_cat = max(cats, key=cats.get) if cats else ""
            age     = (TODAY - c["date_of_birth"]).days // 365
            tenure  = max(0, (TODAY - c["created_at"].date()).days // 30)
            s360_rows.append((
                c["customer_id"], c["country_code"], c["legal_entity"],
                c["full_name"], c["customer_segment"], c["risk_rating"], c["kyc_status"],
                age, age_band(age), c["income_band"], tenure,
                prim_acct["account_id"] if prim_acct else None,
                prim_acct["account_type"] if prim_acct else None,
                cbal, abal, clim, util,
                len(accts), round(tc_lim, 2), round(tc_out, 2), round(max_util, 4),
                round(spend30, 2), cnt30, top_cat,
                "PAID", 0.0, 0,
                0, 0,
                fmt(TODAY), fmt(NOW),
            ))
    n = batch_insert(cur, "semantic_customer_360", s360_cols, s360_rows)
    print(f"  semantic_customer_360: {n}")
    # ── semantic_transaction_summary (VIEW — populated via view definition) ──
    # ── semantic_spend_metrics ────────────────────────────────────────────────
    SSM_CAT = {
        "FOOD_DINING": "food_dining_spend", "RESTAURANT": "food_dining_spend",
        "FOOD_DELIVERY": "food_dining_spend", "CAFE": "food_dining_spend",
        "RETAIL_SHOPPING": "shopping_retail_spend", "RETAIL": "shopping_retail_spend",
        "FASHION": "shopping_retail_spend", "ELECTRONICS": "shopping_retail_spend",
        "TRAVEL_TRANSPORT": "travel_transport_spend", "TRAVEL": "travel_transport_spend",
        "AIRLINE": "travel_transport_spend", "HOTEL": "travel_transport_spend",
        "HOTEL_LODGING": "travel_transport_spend", "TRANSPORT": "travel_transport_spend",
        "HEALTHCARE": "healthcare_spend",
        "ENTERTAINMENT": "entertainment_spend", "SPORTS": "entertainment_spend",
        "UTILITIES": "utilities_spend",
    }
    ssm_cols = ["year_month","customer_id","country_code","legal_entity",
                "customer_segment","total_spend",
                "food_dining_spend","shopping_retail_spend","travel_transport_spend",
                "healthcare_spend","entertainment_spend","utilities_spend","other_spend",
                "total_transactions","unique_merchants",
                "online_spend_pct","offline_spend_pct","international_spend",
                "spend_mom_change_pct","spend_yoy_change_pct",
                "top_merchant","top_category","currency_code","dw_refreshed_at"]
    ssm_rows = []
    for cid, txns in txn_by_cust.items():
        c = cust_map.get(cid)
        if not c: continue
        by_month = defaultdict(list)
        for t in txns:
            if t["auth_status"]=="APPROVED" and t["transaction_type"]=="PURCHASE":
                by_month[t["transaction_date"].strftime("%Y-%m")].append(t)
        prev_spend = 0.0
        for mth in sorted(by_month):
            mtxns  = by_month[mth]
            cats   = defaultdict(float)
            mnames = defaultdict(float)
            online_n = 0; intl_amt = 0.0
            for t in mtxns:
                col = SSM_CAT.get(t["merchant_category"], "other_spend")
                cats[col] += float(t["amount"])
                mnames[t["merchant_name"]] += float(t["amount"])
                if t["channel"] in ("ONLINE", "MOBILE"): online_n += 1
                if t["is_international"]: intl_amt += float(t["amount"])
            tspend  = sum(cats.values())
            mom     = round((tspend - prev_spend) / prev_spend, 4) if prev_spend > 0 else 0
            prev_spend = tspend
            n_txn   = len(mtxns)
            o_pct   = round(online_n / n_txn, 4) if n_txn else 0
            ssm_rows.append((
                mth, cid, c["country_code"], c["legal_entity"],
                c["customer_segment"], round(tspend, 2),
                round(cats.get("food_dining_spend", 0), 2),
                round(cats.get("shopping_retail_spend", 0), 2),
                round(cats.get("travel_transport_spend", 0), 2),
                round(cats.get("healthcare_spend", 0), 2),
                round(cats.get("entertainment_spend", 0), 2),
                round(cats.get("utilities_spend", 0), 2),
                round(cats.get("other_spend", 0), 2),
                n_txn, len(mnames),
                o_pct, round(1 - o_pct, 4),
                round(intl_amt, 2),
                mom, 0.0,
                max(mnames, key=mnames.get) if mnames else "",
                max(cats, key=cats.get) if cats else "",
                c["currency_code"], fmt(NOW),
            ))
    n = batch_insert(cur, "semantic_spend_metrics", ssm_cols, ssm_rows)
    print(f"  semantic_spend_metrics: {n}")
    # ── semantic_payment_status (latest per account) ──────────────────────────
    sps_cols = ["as_of_date","customer_id","country_code","legal_entity",
                "customer_name","customer_segment","account_id","account_type",
                "statement_month","due_date","days_to_due",
                "minimum_due","total_due","amount_paid","amount_still_owed",
                "payment_status","overdue_days","overdue_bucket","late_fee_applied",
                "is_giro_enabled","preferred_payment_method",
                "consecutive_late_months","dw_refreshed_at"]
    sps_rows = []
    seen_accts = set()
    for pr in reversed(pay_rows):
        (pid,aid,cid,cc,le,pdt,ddt,smth,mdue,tdue,pamt,meth,chan,pstat,dod,ltfee,ref,cat) = pr
        if aid in seen_accts: continue
        seen_accts.add(aid)
        c    = cust_map.get(cid, {})
        acct = acct_by_id.get(aid, {})
        dtd  = (ddt - TODAY).days if isinstance(ddt, date) else 0
        amt_out = round(max(0, tdue - pamt), 2)
        is_giro = 1 if meth == "GIRO" else 0
        sps_rows.append((
            fmt(TODAY), cid, cc, le,
            c.get("full_name"), c.get("customer_segment"),
            aid, acct.get("account_type"),
            smth, fmt(ddt), dtd, mdue, tdue, pamt, amt_out, pstat,
            dod or 0, overdue_bucket(dod), ltfee or 0.0,
            is_giro, meth, 0,
            fmt(NOW),
        ))
    n = batch_insert(cur, "semantic_payment_status", sps_cols, sps_rows)
    print(f"  semantic_payment_status: {n}")

    # ── semantic_risk_metrics (VIEW — populated via view definition) ──────────
    # ── semantic_portfolio_kpis ───────────────────────────────────────────────
    spk_cols = ["kpi_month","country_code","legal_entity","total_customers",
                "active_customers","customer_growth_pct","churn_rate",
                "total_spend_volume","spend_growth_pct","avg_spend_per_customer",
                "estimated_interest_income","estimated_fee_income",
                "fraud_rate","delinquency_rate","npl_rate",
                "avg_utilization_pct","full_payment_rate","approval_rate",
                "currency_code","fx_rate_to_usd","dw_refreshed_at"]
    spk_rows = []
    end_m = TODAY.replace(day=1)
    for mo_off in range(18, -1, -1):
        mdate = end_m - timedelta(days=mo_off * 30)
        mstr  = mdate.strftime("%Y-%m")
        for cc, custs in all_customers.items():
            cfg = COUNTRY_CONF[cc]
            accts = all_accounts.get(cc, [])
            cc_txns = [t for t in all_txns.get(cc, [])
                       if t["auth_status"] == "APPROVED" and
                       t["transaction_date"].strftime("%Y-%m") == mstr]
            all_cc_txns = all_txns.get(cc, [])
            tclim = sum(a["credit_limit"] for a in accts)
            tbal  = sum(a["current_balance"] for a in accts)
            tspend = round(sum(float(t["amount"]) for t in cc_txns), 2)
            n_cust = len(custs)
            n_act  = int(n_cust * random.uniform(0.88, 0.96))
            avg_u  = round(tbal / max(1, tclim), 4)
            frate  = round(sum(1 for t in cc_txns if t["is_fraud"]) / max(1, len(cc_txns)), 6)
            appr_n = sum(1 for t in all_cc_txns if t["auth_status"] == "APPROVED")
            appr_rt = round(appr_n / max(1, len(all_cc_txns)), 4)
            full_prt = round(sum(1 for pr in pay_rows if pr[3] == cc and pr[10] >= pr[9] * 0.99)
                             / max(1, sum(1 for pr in pay_rows if pr[3] == cc)), 4)
            est_int = round(tbal * 0.018 / 12, 2)
            est_fee = round(sum(float(pr[15] or 0) for pr in pay_rows if pr[3] == cc) * 0.5, 2)
            spk_rows.append((
                mstr, cc, cfg["legal_entity"], n_cust, n_act,
                round(random.uniform(0.005, 0.03), 4),
                round(random.uniform(0.002, 0.01), 4),
                tspend,
                round(random.uniform(-0.05, 0.12), 4),
                round(tspend / max(1, n_cust), 2),
                est_int, est_fee,
                frate,
                round(random.uniform(0.02, 0.08), 4),
                round(random.uniform(0.01, 0.04), 4),
                avg_u, full_prt, appr_rt,
                cfg["currency"], float(cfg["fx_to_usd"]), fmt(NOW),
            ))
    n = batch_insert(cur, "semantic_portfolio_kpis", spk_cols, spk_rows)
    print(f"  semantic_portfolio_kpis: {n}")
    # ── semantic_deposit_portfolio ────────────────────────────────────────────
    sdp_cols = ["snapshot_month","customer_id","country_code","legal_entity",
                "customer_name","customer_segment","risk_rating","currency_code",
                "savings_account_id","savings_balance","savings_interest_rate","savings_interest_ytd",
                "current_account_id","current_balance","fd_count","total_fd_balance",
                "fd_avg_rate","fd_maturing_next_30d","total_deposit_balance",
                "deposit_mom_change_pct","has_salary_credit",
                "avg_monthly_credit","avg_monthly_debit","dw_refreshed_at"]
    sdp_rows = []
    for custs in all_customers.values():
        for c in custs:
            deps = dep_by_cust.get(c["customer_id"],[])
            if not deps: continue
            sav   = [d for d in deps if d["account_category"]=="SAVINGS"]
            cur_d = [d for d in deps if d["account_category"]=="CURRENT"]
            fds   = [d for d in deps if d["account_category"]=="TERM_DEPOSIT"]
            sbal  = sum(d["current_balance"] for d in sav)
            cbal  = sum(d["current_balance"] for d in cur_d)
            fbal  = sum(d["current_balance"] for d in fds)
            savrate = round(sum(d["interest_rate"] for d in sav)/len(sav),4) if sav else 0
            fdrate  = round(sum(d["interest_rate"] for d in fds)/len(fds),4) if fds else 0
            sav_int = round(sum(d["accrued_interest"] for d in sav),2)
            fd_mat30= sum(d["current_balance"] for d in fds
                          if d["maturity_date"] and isinstance(d["maturity_date"],date)
                          and 0<=(d["maturity_date"]-TODAY).days<=30)
            tbal    = sbal+cbal+fbal
            avg_cr  = round(tbal*0.12,2)
            avg_dr  = round(tbal*0.10,2)
            sdp_rows.append((
                snap_month, c["customer_id"], c["country_code"], c["legal_entity"],
                c["full_name"], c["customer_segment"], c["risk_rating"], c["currency_code"],
                sav[0]["deposit_account_id"] if sav else None,
                round(sbal,2), savrate, sav_int,
                cur_d[0]["deposit_account_id"] if cur_d else None,
                round(cbal,2),
                len(fds), round(fbal,2), fdrate, round(fd_mat30,2),
                round(tbal,2), round(random.uniform(-0.05,0.08),4),
                0, avg_cr, avg_dr, fmt(NOW),
            ))
    n = batch_insert(cur, "semantic_deposit_portfolio", sdp_cols, sdp_rows)
    print(f"  semantic_deposit_portfolio: {n}")

    # ── semantic_loan_portfolio ───────────────────────────────────────────────
    slp_cols = ["snapshot_month","customer_id","country_code","legal_entity",
                "customer_name","customer_segment","risk_rating","kyc_status",
                "currency_code","annual_income",
                "personal_loan_id","personal_loan_disbursed","personal_loan_outstanding",
                "personal_loan_rate","personal_loan_emi","personal_loan_term_months",
                "personal_loan_months_remaining","personal_loan_status","personal_loan_overdue_days",
                "home_loan_id","home_loan_disbursed","home_loan_outstanding",
                "home_loan_rate","home_loan_emi","home_loan_ltv","home_loan_status",
                "auto_loan_id","auto_loan_disbursed","auto_loan_outstanding",
                "auto_loan_rate","auto_loan_emi","auto_loan_status",
                "total_loan_outstanding","total_loan_count","total_monthly_emi",
                "max_overdue_days","overdue_bucket","is_npa","total_overdue_amount",
                "loan_to_income_ratio","debt_service_ratio","dw_refreshed_at"]
    slp_rows = []
    for custs in all_customers.values():
        for c in custs:
            loans = loan_by_cust.get(c["customer_id"],[])
            if not loans: continue
            def fl(lt):
                sl = [l for l in loans if l["loan_type"]==lt]
                return sl[0] if sl else None
            pl = fl("PERSONAL"); hl = fl("HOME"); al = fl("AUTO")
            all_l = loans
            tot_out = sum(l["outstanding_balance"] for l in all_l)
            tot_emi = sum(l["emi_amount"] for l in all_l)
            max_dpd = max((l["current_dpd"] for l in all_l),default=0)
            is_npa  = 1 if any(l["is_npa"] for l in all_l) else 0
            npa_amt = sum(l["outstanding_balance"] for l in all_l if l["is_npa"])
            dti = round(tot_out/max(1,c["annual_income"]),4)
            dsr = round(tot_emi/max(1,c["annual_income"]/12),4)
            def lv(loan,field): return loan[field] if loan else None
            def lrate(loan): return loan["_rate"] if loan else None
            def lterm(loan): return loan["tenor_months"] if loan else None
            def lrem(loan):
                if not loan: return None
                return max(0, loan["_term"] - loan["_months_paid"])
            def ltv(loan):
                if not loan or loan["loan_type"] not in ("HOME","AUTO"): return None
                return round(loan["_principal"]/(loan["_principal"]*1.25),4)
            slp_rows.append((
                snap_month, c["customer_id"], c["country_code"], c["legal_entity"],
                c["full_name"], c["customer_segment"], c["risk_rating"], c["kyc_status"],
                c["currency_code"], c["annual_income"],
                lv(pl,"loan_id"), lv(pl,"principal_amount"), lv(pl,"outstanding_balance"),
                lrate(pl), lv(pl,"emi_amount"), lterm(pl), lrem(pl),
                lv(pl,"loan_status"), lv(pl,"current_dpd"),
                lv(hl,"loan_id"), lv(hl,"principal_amount"), lv(hl,"outstanding_balance"),
                lrate(hl), lv(hl,"emi_amount"), ltv(hl), lv(hl,"loan_status"),
                lv(al,"loan_id"), lv(al,"principal_amount"), lv(al,"outstanding_balance"),
                lrate(al), lv(al,"emi_amount"), lv(al,"loan_status"),
                round(tot_out,2), len(all_l), round(tot_emi,2),
                max_dpd, dpd_bucket(max_dpd), is_npa, round(npa_amt,2),
                dti, dsr, fmt(NOW),
            ))
    n = batch_insert(cur, "semantic_loan_portfolio", slp_cols, slp_rows)
    print(f"  semantic_loan_portfolio: {n}")

    # ── semantic_customer_product_mix ─────────────────────────────────────────
    spm_cols = ["snapshot_month","customer_id","country_code","legal_entity",
                "customer_name","date_of_birth","age","age_band","gender","city",
                "customer_segment","risk_rating","kyc_status","occupation",
                "annual_income","income_band","tenure_months","currency_code",
                "total_product_count","has_credit_card","has_savings","has_current",
                "has_fd","has_loan","has_personal_loan","has_home_loan","has_auto_loan",
                "total_asset_balance","total_liability_balance","net_balance",
                "cc_outstanding","cc_credit_limit","cc_utilization_pct","cc_spend_last_month",
                "total_deposit_balance","total_loan_outstanding","total_monthly_emi",
                "payment_status","consecutive_late_months","is_overdue",
                "wallet_share_score","dw_refreshed_at"]
    spm_rows = []
    for custs in all_customers.values():
        for c in custs:
            cc_accts = acct_map.get(c["customer_id"],[])
            deps     = dep_by_cust.get(c["customer_id"],[])
            loans    = loan_by_cust.get(c["customer_id"],[])

            age = (TODAY - c["date_of_birth"]).days // 365
            tenure = (TODAY - c["created_at"].date()).days // 30

            cc_bal  = sum(a["current_balance"] for a in cc_accts)
            cc_lim  = sum(a["credit_limit"] for a in cc_accts)
            cc_util = round(cc_bal/cc_lim,4) if cc_lim > 0 else 0
            ctxns   = txn_by_cust.get(c["customer_id"],[])
            last_mth_str = (TODAY.replace(day=1)-timedelta(days=1)).strftime("%Y-%m")
            cc_spend_lm = sum(float(t["amount"]) for t in ctxns
                              if t["transaction_date"].strftime("%Y-%m")==last_mth_str
                              and t["auth_status"]=="APPROVED")

            sav      = [d for d in deps if d["account_category"]=="SAVINGS"]
            cur_d    = [d for d in deps if d["account_category"]=="CURRENT"]
            fds      = [d for d in deps if d["account_category"]=="TERM_DEPOSIT"]
            dep_bal  = sum(d["current_balance"] for d in deps)
            ln_out   = sum(l["outstanding_balance"] for l in loans)
            ln_emi   = sum(l["emi_amount"] for l in loans)

            assets   = round(dep_bal, 2)
            liab     = round(cc_bal + ln_out, 2)
            net      = round(assets - liab, 2)
            prod_cnt = (1 if cc_accts else 0) + (1 if sav else 0) + \
                       (1 if cur_d else 0) + (1 if fds else 0) + len(loans)
            wallet   = round(min(1.0, prod_cnt / 8.0), 4)

            has_pl = int(any(l["loan_type"]=="PERSONAL" for l in loans))
            has_hl = int(any(l["loan_type"]=="HOME" for l in loans))
            has_al = int(any(l["loan_type"]=="AUTO" for l in loans))

            spm_rows.append((
                snap_month, c["customer_id"], c["country_code"], c["legal_entity"],
                c["full_name"], fmt(c["date_of_birth"]), age, age_band(age),
                c["gender"], c["city"],
                c["customer_segment"], c["risk_rating"], c["kyc_status"],
                c["occupation"], c["annual_income"], c["income_band"],
                tenure, c["currency_code"],
                prod_cnt,
                int(bool(cc_accts)), int(bool(sav)), int(bool(cur_d)),
                int(bool(fds)), int(bool(loans)), has_pl, has_hl, has_al,
                assets, liab, net,
                round(cc_bal,2), round(cc_lim,2), cc_util, round(cc_spend_lm,2),
                round(dep_bal,2), round(ln_out,2), round(ln_emi,2),
                "PAID", 0, 0, wallet, fmt(NOW),
            ))
    n = batch_insert(cur, "semantic_customer_product_mix", spm_cols, spm_rows)
    print(f"  semantic_customer_product_mix: {n}")


# ── ENTRY POINT ────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host",     default="localhost")
    p.add_argument("--port",     type=int, default=9030)
    p.add_argument("--user",     default="root")
    p.add_argument("--password", default="")
    args = p.parse_args()

    print("=== DataPrismAI Banking Data Generator ===")
    print("Generating in-memory data...")

    all_customers = generate_customers()
    total_custs   = sum(len(v) for v in all_customers.values())
    print(f"  Customers: {total_custs}")

    merchants = generate_merchants()
    print(f"  Merchants: {len(merchants)}")

    all_accounts, raw_acct_rows, raw_card_rows = generate_cc_accounts(all_customers)
    total_accts = sum(len(v) for v in all_accounts.values())
    print(f"  CC accounts: {total_accts}, cards: {len(raw_card_rows)}")

    all_txns, _ = generate_transactions(all_accounts)
    total_txns  = sum(len(v) for v in all_txns.values())
    print(f"  CC transactions: {total_txns}")

    stmt_rows, pay_rows, stmt_by_acct = generate_statements(all_accounts, all_txns)
    print(f"  Statements: {len(stmt_rows)}, payments: {len(pay_rows)}")

    raw_dep_accts, ddm_dep_rows = generate_deposit_accounts(all_customers)
    dep_txns = generate_deposit_transactions(raw_dep_accts)
    print(f"  Deposit accounts: {len(raw_dep_accts)}, deposit txns: {len(dep_txns)}")

    raw_loans, raw_reps, ddm_loan_rows, ddm_rep_rows = generate_loans(all_customers)
    print(f"  Loans: {len(raw_loans)}, repayments: {len(raw_reps)}")

    print(f"\nConnecting to StarRocks at {args.host}:{args.port}...")
    conn = connect(args.host, args.port, args.user, args.password)
    conn.autocommit = True
    cur  = conn.cursor()

    print("\n--- RAW LAYER ---")
    load_raw_customers(cur, all_customers)
    load_raw_merchants(cur, merchants)
    load_raw_cc(cur, all_accounts, all_txns, stmt_rows, pay_rows, raw_card_rows)
    load_raw_deposits(cur, raw_dep_accts, dep_txns)
    load_raw_loans(cur, raw_loans, raw_reps)

    print("\n--- DDM LAYER ---")
    load_ddm_customers(cur, all_customers)
    load_ddm_merchants(cur, merchants)
    load_ddm_cc(cur, all_customers, all_accounts, all_txns, stmt_rows, pay_rows, raw_card_rows)
    load_ddm_deposits(cur, all_customers, raw_dep_accts, ddm_dep_rows)
    load_ddm_loans(cur, all_customers, raw_loans, raw_reps, ddm_loan_rows, ddm_rep_rows)

    print("\n--- DATA PRODUCTS LAYER ---")
    load_dp_layer(cur, all_customers, all_accounts, all_txns, stmt_rows, pay_rows,
                  raw_dep_accts, raw_loans)

    print("\n--- SEMANTIC LAYER ---")
    load_semantic_layer(cur, all_customers, all_accounts, all_txns, stmt_rows,
                        raw_dep_accts, raw_loans, pay_rows)

    cur.close()
    conn.close()
    print("\n=== Done! All data loaded successfully. ===")


if __name__ == "__main__":
    main()
