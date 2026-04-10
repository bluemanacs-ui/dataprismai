"""
DataPrismAI — Deposit accounts generator
Generates: raw_deposit_account, raw_deposit_transaction, ddm_deposit_account
"""
import sys, os, random
from datetime import date, datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from gen_ref_data import *
from gen_customers import rand_date

random.seed(random_seed + 2)


def rand_dt(start: datetime, end: datetime) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, max(1, delta)))


BALANCE_RANGES = {
    "SG": {"MASS":(1000,40000), "AFFLUENT":(15000,200000), "PRIORITY":(50000,800000), "HNW":(200000,5000000)},
    "MY": {"MASS":(500,20000),  "AFFLUENT":(10000,150000), "PRIORITY":(30000,600000), "HNW":(100000,3000000)},
    "IN": {"MASS":(5000,200000),"AFFLUENT":(100000,2000000),"PRIORITY":(500000,10000000),"HNW":(2000000,50000000)},
}

FD_BAL_RANGES = {
    "SG": {"MASS":(5000,30000),"AFFLUENT":(30000,300000),"PRIORITY":(100000,1500000),"HNW":(500000,10000000)},
    "MY": {"MASS":(2000,20000),"AFFLUENT":(20000,200000),"PRIORITY":(80000,1000000), "HNW":(300000,6000000)},
    "IN": {"MASS":(10000,100000),"AFFLUENT":(100000,2000000),"PRIORITY":(1000000,20000000),"HNW":(5000000,100000000)},
}


def balance_band(bal: float, cc: str) -> str:
    thresholds = {
        "SG": [(5000,"<5K"),(20000,"5K-20K"),(100000,"20K-100K"),(500000,"100K-500K"),(float("inf"),">500K")],
        "MY": [(3000,"<3K"),(15000,"3K-15K"),(60000,"15K-60K"), (300000,"60K-300K"), (float("inf"),">300K")],
        "IN": [(25000,"<25K"),(100000,"25K-100K"),(500000,"100K-500K"),(2500000,"500K-2.5M"),(float("inf"),">2.5M")],
    }
    for thresh, label in thresholds.get(cc, []):
        if bal < thresh:
            return label
    return "Unknown"


def generate_deposit_accounts(all_customers: dict) -> tuple[list, list]:
    """Returns (raw_deposit_account rows, ddm_deposit_account rows)"""
    raw_rows = []
    ddm_rows = []
    acct_num = 0

    for cc, custs in all_customers.items():
        cfg = COUNTRY_CONF[cc]
        products = DEPOSIT_PRODUCTS[cc]
        sav_prods = [p for p in products if p[3] == "SAVINGS"]
        cur_prods = [p for p in products if p[3] == "CURRENT"]
        fd_prods  = [p for p in products if p[3] == "TERM_DEPOSIT"]

        for cust in custs:
            seg = cust["_seg"]

            # every customer gets 1 savings account
            # AFFLUENT+ also get current
            # 40% MASS, 70% AFFLUENT, 90% PRIORITY, 100% HNW get at least 1 FD
            accounts_to_create = []

            prod = random.choice(sav_prods)
            accounts_to_create.append(("SAVINGS", prod))

            if seg in ("AFFLUENT", "PRIORITY", "HNW"):
                accounts_to_create.append(("CURRENT", random.choice(cur_prods)))

            fd_prob = {"MASS": 0.35, "AFFLUENT": 0.65, "PRIORITY": 0.88, "HNW": 1.0}[seg]
            if random.random() < fd_prob:
                n_fds = 1 if seg in ("MASS","AFFLUENT") else random.randint(1, 3)
                for _ in range(n_fds):
                    accounts_to_create.append(("FIXED_DEPOSIT", random.choice(fd_prods)))

            for dep_type, prod in accounts_to_create:
                acct_num += 1
                dep_id   = f"{cc}_DEP_{acct_num:06d}"
                is_fd    = dep_type == "FIXED_DEPOSIT"
                prod_code, prod_name, _, _, rate_range = prod

                rate = round(random.uniform(*rate_range), 4)

                open_d = rand_date(date(2019, 1, 1), date(2024, 6, 1))

                if is_fd:
                    tenor = random.choice(FD_TENORS)
                    mat_d = open_d + timedelta(days=30 * tenor)
                    lo, hi = FD_BAL_RANGES[cc][seg]
                    bal   = round(random.uniform(lo, hi) / 100) * 100
                    min_b = bal  # FD balance = principal
                    hold_b = bal
                    lien_b = 0.0
                    status_choices = (["ACTIVE"] * 7 + ["MATURED"] * 2 + ["BROKEN"] * 1)
                    status  = random.choice(status_choices)
                    close_d = mat_d if status in ("MATURED","BROKEN") else None
                    auto_r  = 1 if random.random() < 0.60 else 0
                    int_pay = random.choice(["ON_MATURITY", "MONTHLY", "QUARTERLY"])
                else:
                    tenor    = None
                    mat_d    = None
                    lo, hi   = BALANCE_RANGES[cc][seg]
                    bal      = round(random.uniform(lo, hi), 2)
                    min_b    = round(bal * 0.05, 2)
                    hold_b   = round(bal * random.uniform(0, 0.10), 2)
                    lien_b   = 0.0
                    status   = random.choices(
                        ["ACTIVE", "DORMANT", "CLOSED"],
                        weights=[88, 7, 5]
                    )[0]
                    close_d  = None if status == "ACTIVE" else rand_date(
                        date(2025, 1, 1), TODAY
                    )
                    auto_r   = 0
                    int_pay  = "MONTHLY"

                tenor_months = tenor or (
                    (TODAY - open_d).days // 30
                )

                # interest accrued (simple)
                accrued_int = round(bal * rate * min(tenor_months, 12) / 12, 2)

                cumulative_int = round(accrued_int * random.uniform(0.8, 1.2), 2)
                avg_bal_6m     = round(bal * random.uniform(0.7, 1.1), 2)
                last_txn_dt    = rand_date(date(2025, 12, 1), TODAY)

                # ── RAW row ───────────────────────────────────────────
                raw_rows.append({
                    "deposit_account_id":  dep_id,
                    "customer_id":         cust["customer_id"],
                    "country_code":        cc,
                    "legal_entity":        cfg["legal_entity"],
                    "product_code":        prod_code,
                    "product_name":        prod_name,
                    "account_type":        dep_type,
                    "account_category":    prod[3],
                    "currency_code":       cfg["currency"],
                    "current_balance":     bal,
                    "available_balance":   round(bal - hold_b, 2),
                    "hold_balance":        hold_b,
                    "lien_balance":        lien_b,
                    "minimum_balance":     min_b,
                    "interest_rate":       rate,
                    "interest_payment_frequency": int_pay,
                    "accrued_interest":    accrued_int,
                    "account_status":      status,
                    "open_date":           open_d,
                    "maturity_date":       mat_d,
                    "close_date":          close_d,
                    "tenor_months":        tenor,
                    "auto_renewal":        auto_r,
                    "last_transaction_date": last_txn_dt,
                    "branch_code":         f"{cc}_BR_{random.randint(1,10):02d}",
                    "is_deleted":          0,
                    "created_at":          datetime.combine(open_d, datetime.min.time()),
                    "updated_at":          NOW,
                    # meta (not directly inserted)
                    "_seg":           seg,
                    "_is_fd":         is_fd,
                    "_tenor":         tenor,
                    "_actual_bal":    bal,
                    "_rate":          rate,
                    "_cumulative_int": cumulative_int,
                    "_avg_bal_6m":    avg_bal_6m,
                    "_tenor_months":  tenor_months,
                })

                # ── DDM row ───────────────────────────────────────────
                ddm_rows.append({
                    "deposit_account_id":   dep_id,
                    "customer_id":          cust["customer_id"],
                    "country_code":         cc,
                    "legal_entity":         cfg["legal_entity"],
                    "product_code":         prod_code,
                    "product_name":         prod_name,
                    "account_type":         dep_type,
                    "account_category":     prod[3],
                    "customer_segment":     seg,
                    "currency_code":        cfg["currency"],
                    "current_balance":      bal,
                    "available_balance":    round(bal - hold_b, 2),
                    "interest_rate":        rate,
                    "accrued_interest":     accrued_int,
                    "cumulative_interest":  cumulative_int,
                    "average_balance_6m":   avg_bal_6m,
                    "account_status":       status,
                    "balance_band":         balance_band(bal, cc),
                    "is_fd":                int(is_fd),
                    "tenor_months":         tenor_months,
                    "open_date":            open_d,
                    "maturity_date":        mat_d,
                    "days_to_maturity": max(0,(mat_d - TODAY).days) if mat_d and mat_d >= TODAY else None,
                    "close_date":           close_d,
                    "last_transaction_date": last_txn_dt,
                    "is_deleted":           0,
                    "created_at":           datetime.combine(open_d, datetime.min.time()),
                    "updated_at":           NOW,
                })

    return raw_rows, ddm_rows


# ── DEPOSIT TRANSACTIONS ──────────────────────────────────────────────────────
N_DEP_TXN_PER_ACCT = 24   # avg deposit transactions per savings account over 18 months

def generate_deposit_transactions(raw_deposit_accounts: list) -> list:
    txn_rows = []
    txn_num  = 0

    for acct in raw_deposit_accounts:
        if acct["_is_fd"]:
            # FD: only opening, interest credits, maturity
            cc = acct["country_code"]
            cfg = COUNTRY_CONF[cc]
            dep_id = acct["deposit_account_id"]
            open_d = acct["open_date"]
            mat_d  = acct["maturity_date"] or (open_d + timedelta(days=90))

            # FD opening deposit
            txn_num += 1
            txn_rows.append({
                "deposit_txn_id":       f"{cc}_DTXN_{txn_num:08d}",
                "deposit_account_id":   dep_id,
                "customer_id":          acct["customer_id"],
                "country_code":         cc,
                "transaction_date":     datetime.combine(open_d, datetime.min.time()),
                "value_date":           datetime.combine(open_d + timedelta(days=1), datetime.min.time()),
                "amount":               acct["_actual_bal"],
                "direction":            "CREDIT",
                "transaction_type":     "FD_PLACEMENT",
                "channel":              "BRANCH",
                "running_balance":      acct["_actual_bal"],
                "currency_code":        cfg["currency"],
                "description":          f"FD Opening - {acct['product_name']}",
                "reference_number":     f"FD{random.randint(10000000,99999999)}",
                "created_at":           datetime.combine(open_d, datetime.min.time()),
            })

            # Monthly interest credits
            tenor = acct["_tenor"] or 12
            for mo in range(1, min(tenor, 12) + 1):
                int_d = open_d + timedelta(days=30 * mo)
                if int_d > TODAY:
                    break
                int_amt = round(acct["_actual_bal"] * acct["_rate"] / 12, 2)
                txn_num += 1
                txn_rows.append({
                    "deposit_txn_id":       f"{cc}_DTXN_{txn_num:08d}",
                    "deposit_account_id":   dep_id,
                    "customer_id":          acct["customer_id"],
                    "country_code":         cc,
                    "transaction_date":     datetime.combine(int_d, datetime.min.time()),
                    "value_date":           datetime.combine(int_d + timedelta(days=1), datetime.min.time()),
                    "amount":               int_amt,
                    "direction":            "CREDIT",
                    "transaction_type":     "INTEREST_CREDIT",
                    "channel":              "SYSTEM",
                    "running_balance":      round(acct["_actual_bal"] + int_amt * mo, 2),
                    "currency_code":        cfg["currency"],
                    "description":          "FD Interest Credit",
                    "reference_number":     f"INT{random.randint(10000000,99999999)}",
                    "created_at":           datetime.combine(int_d, datetime.min.time()),
                })
            continue   # skip random txns for FD

        # ── Savings / Current accounts ────────────────────────────────
        cc = acct["country_code"]
        cfg = COUNTRY_CONF[cc]
        dep_id = acct["deposit_account_id"]
        open_d = acct["open_date"]
        n_txns = random.randint(int(N_DEP_TXN_PER_ACCT * 0.5), int(N_DEP_TXN_PER_ACCT * 1.8))
        run_bal = acct["_actual_bal"]

        for _ in range(n_txns):
            txn_dt = rand_dt(
                datetime.combine(open_d, datetime.min.time()),
                datetime.combine(TODAY, datetime.min.time()),
            )
            ttype = random.choice(DEPOSIT_TXN_TYPES)
            chan  = random.choice(DEPOSIT_CHANNELS)
            is_credit = ttype in (
                "SALARY_CREDIT", "TRANSFER_IN", "INTEREST_CREDIT",
                "CASH_DEPOSIT", "FD_MATURITY",
            )
            direction = "CREDIT" if is_credit else "DEBIT"

            avg = cfg["avg_deposit_bal"]
            if is_credit:
                amt = round(random.expovariate(1.0 / (avg * 0.5)), 2)
                amt = max(1, min(amt, avg * 5))
            else:
                amt = round(random.expovariate(1.0 / (avg * 0.1)), 2)
                amt = max(1, min(amt, run_bal * 0.40))

            run_bal += amt if is_credit else -amt
            run_bal = max(0, round(run_bal, 2))

            txn_num += 1
            txn_rows.append({
                "deposit_txn_id":       f"{cc}_DTXN_{txn_num:08d}",
                "deposit_account_id":   dep_id,
                "customer_id":          acct["customer_id"],
                "country_code":         cc,
                "transaction_date":     txn_dt,
                "value_date":           txn_dt + timedelta(days=0 if direction == "DEBIT" else 1),
                "amount":               amt,
                "direction":            direction,
                "transaction_type":     ttype,
                "channel":              chan,
                "running_balance":      run_bal,
                "currency_code":        cfg["currency"],
                "description":          ttype.replace("_", " ").title(),
                "reference_number":     f"DREF{random.randint(10000000,99999999)}",
                "created_at":           txn_dt,
            })

    return txn_rows


if __name__ == "__main__":
    from gen_customers import generate_customers
    custs = generate_customers()
    raw_dep, ddm_dep = generate_deposit_accounts(custs)
    txns = generate_deposit_transactions(raw_dep)
    print(f"Deposit accounts (raw): {len(raw_dep)}, DDM: {len(ddm_dep)}, transactions: {len(txns)}")
