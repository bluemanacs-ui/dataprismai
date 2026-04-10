"""
DataPrismAI — Loans generator
Generates: raw_loan, raw_loan_repayment, ddm_loan, ddm_loan_repayment
"""
import sys, os, random
from datetime import date, datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from gen_ref_data import *
from gen_customers import rand_date

random.seed(random_seed + 3)


def rand_dt(start: datetime, end: datetime) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, max(1, delta)))


LOAN_AMOUNT_RANGES = {
    "SG": {
        "PERSONAL":   {"MASS":(5000,40000),   "AFFLUENT":(10000,100000),  "PRIORITY":(50000,300000),  "HNW":(100000,500000)},
        "HOME":       {"MASS":(200000,700000), "AFFLUENT":(400000,1500000),"PRIORITY":(800000,4000000),"HNW":(2000000,15000000)},
        "AUTO":       {"MASS":(30000,120000),  "AFFLUENT":(80000,250000),  "PRIORITY":(200000,800000), "HNW":(300000,2000000)},
        "BUSINESS":   {"MASS":(20000,200000),  "AFFLUENT":(50000,600000),  "PRIORITY":(200000,2000000),"HNW":(500000,5000000)},
        "EDUCATION":  {"MASS":(10000,60000),   "AFFLUENT":(20000,80000),   "PRIORITY":(30000,120000),  "HNW":(50000,200000)},
        "RENOVATION": {"MASS":(5000,50000),    "AFFLUENT":(20000,150000),  "PRIORITY":(50000,400000),  "HNW":(100000,800000)},
    },
    "MY": {
        "PERSONAL":   {"MASS":(5000,60000),    "AFFLUENT":(20000,200000),  "PRIORITY":(80000,500000),  "HNW":(200000,1000000)},
        "HOME":       {"MASS":(150000,600000), "AFFLUENT":(350000,1500000),"PRIORITY":(700000,4000000),"HNW":(1500000,10000000)},
        "AUTO":       {"MASS":(40000,120000),  "AFFLUENT":(80000,300000),  "PRIORITY":(200000,800000), "HNW":(500000,2000000)},
        "BUSINESS":   {"MASS":(20000,200000),  "AFFLUENT":(60000,600000),  "PRIORITY":(200000,2000000),"HNW":(500000,5000000)},
        "EDUCATION":  {"MASS":(10000,80000),   "AFFLUENT":(30000,150000),  "PRIORITY":(50000,200000),  "HNW":(100000,300000)},
        "RENOVATION": {"MASS":(5000,50000),    "AFFLUENT":(20000,150000),  "PRIORITY":(50000,500000),  "HNW":(100000,800000)},
    },
    "IN": {
        "PERSONAL":   {"MASS":(50000,500000),    "AFFLUENT":(200000,2000000),  "PRIORITY":(500000,6000000),   "HNW":(1000000,15000000)},
        "HOME":       {"MASS":(1000000,6000000), "AFFLUENT":(3000000,20000000),"PRIORITY":(8000000,60000000), "HNW":(20000000,150000000)},
        "AUTO":       {"MASS":(300000,1200000),  "AFFLUENT":(800000,4000000),  "PRIORITY":(2000000,12000000), "HNW":(5000000,30000000)},
        "BUSINESS":   {"MASS":(100000,1500000),  "AFFLUENT":(500000,8000000),  "PRIORITY":(2000000,30000000), "HNW":(10000000,100000000)},
        "EDUCATION":  {"MASS":(100000,1000000),  "AFFLUENT":(500000,3000000),  "PRIORITY":(1000000,6000000),  "HNW":(2000000,10000000)},
        "RENOVATION": {"MASS":(50000,500000),    "AFFLUENT":(200000,1500000),  "PRIORITY":(500000,4000000),   "HNW":(1000000,8000000)},
    },
}


def dpd_bucket(dpd: int) -> str:
    if dpd == 0:    return "CURRENT"
    if dpd <= 30:   return "1-30 DPD"
    if dpd <= 60:   return "31-60 DPD"
    if dpd <= 90:   return "61-90 DPD"
    if dpd <= 180:  return "91-180 DPD"
    return "NPA"


def loan_status_from_dpd(dpd: int, is_closed: bool) -> str:
    if is_closed: return "CLOSED"
    if dpd == 0:   return "PERFORMING"
    if dpd <= 30:  return "WATCHLIST"
    if dpd <= 90:  return "SUB_STANDARD"
    if dpd <= 180: return "DOUBTFUL"
    return "NPA"


def emi_formula(principal: float, annual_rate: float, months: int) -> float:
    if annual_rate == 0:
        return round(principal / months, 2)
    r = annual_rate / 12
    return round(principal * r * (1 + r) ** months / ((1 + r) ** months - 1), 2)


def generate_loans(all_customers: dict) -> tuple[list, list, list, list]:
    """Returns (raw_loan_rows, raw_repayment_rows, ddm_loan_rows, ddm_repayment_rows)"""
    raw_loan_rows  = []
    raw_rep_rows   = []
    ddm_loan_rows  = []
    ddm_rep_rows   = []
    loan_num = 0
    rep_num  = 0

    for cc, custs in all_customers.items():
        cfg      = COUNTRY_CONF[cc]
        products = LOAN_PRODUCTS[cc]

        for cust in custs:
            seg = cust["_seg"]

            # decide which loan products this customer has
            loan_probs = {
                "PERSONAL":   {"MASS": 0.40, "AFFLUENT": 0.35, "PRIORITY": 0.25, "HNW": 0.15}[seg],
                "HOME":       {"MASS": 0.30, "AFFLUENT": 0.55, "PRIORITY": 0.70, "HNW": 0.80}[seg],
                "AUTO":       {"MASS": 0.25, "AFFLUENT": 0.45, "PRIORITY": 0.55, "HNW": 0.60}[seg],
                "BUSINESS":   {"MASS": 0.10, "AFFLUENT": 0.20, "PRIORITY": 0.30, "HNW": 0.40}[seg],
                "EDUCATION":  {"MASS": 0.12, "AFFLUENT": 0.08, "PRIORITY": 0.05, "HNW": 0.03}[seg],
                "RENOVATION": {"MASS": 0.08, "AFFLUENT": 0.18, "PRIORITY": 0.22, "HNW": 0.25}[seg],
            }

            chosen_loans = []
            for prod in products:
                pcode, pname, ltype, cat, rate_range, max_term, collateral = prod
                if ltype not in LOAN_AMOUNT_RANGES[cc]:
                    continue
                if LOAN_AMOUNT_RANGES[cc][ltype].get(seg) is None:
                    continue
                prob = loan_probs.get(ltype, 0)
                if random.random() < prob:
                    chosen_loans.append(prod)

            for prod in chosen_loans:
                pcode, pname, ltype, cat, rate_range, max_term, collateral = prod
                loan_num += 1
                loan_id = f"{cc}_LN_{loan_num:06d}"

                lo, hi = LOAN_AMOUNT_RANGES[cc][ltype][seg]
                principal = round(random.uniform(lo, hi) / 100) * 100
                rate  = round(random.uniform(*rate_range), 4)
                term  = random.choice([12, 24, 36, 48, 60, 84] if max_term >= 84
                                      else [12, 24, 36, 60] if max_term >= 60
                                      else [12, 24, 36])
                term  = min(term, max_term)

                disburse_d = rand_date(date(2019, 1, 1), date(2024, 6, 1))
                maturity_d = disburse_d + timedelta(days=30 * term)

                emi = emi_formula(principal, rate, term)
                purpose = random.choice(LOAN_PURPOSES.get(ltype, ["General"]))

                # delinquency model — linked to customer risk
                risk_weights = {
                    "LOW":    [0.80, 0.10, 0.05, 0.03, 0.015, 0.005],
                    "MEDIUM": [0.60, 0.15, 0.10, 0.08, 0.04,  0.03],
                    "HIGH":   [0.35, 0.20, 0.15, 0.15, 0.09,  0.06],
                }[cust["risk_rating"]]
                dpd_buckets = ["0", "1-30", "31-60", "61-90", "91-180", "180+"]
                dpd_label   = random.choices(dpd_buckets, weights=risk_weights)[0]
                current_dpd = {
                    "0": 0,
                    "1-30":   random.randint(1,  30),
                    "31-60":  random.randint(31, 60),
                    "61-90":  random.randint(61, 90),
                    "91-180": random.randint(91, 180),
                    "180+":   random.randint(181, 365),
                }[dpd_label]
                max_dpd = current_dpd + random.randint(0, 30)

                is_closed  = maturity_d < TODAY and random.random() < 0.70
                loan_stat  = loan_status_from_dpd(current_dpd, is_closed)
                is_npa     = int(current_dpd > 90)

                months_paid = (TODAY - disburse_d).days // 30 if not is_closed else term
                months_paid = min(months_paid, term)
                principal_paid   = round(emi * months_paid * 0.35, 2)   # approx amortisation
                interest_paid    = round(emi * months_paid * 0.65, 2)
                outstanding_bal  = round(max(0, principal - principal_paid), 2)
                overdue_amt      = round(emi * (current_dpd / 30) * 1.0, 2) if current_dpd > 0 else 0
                loan_to_income   = round(principal / max(1, cust["annual_income"]), 2)
                total_interest   = round(emi * term - principal, 2)

                # ── RAW loan ──────────────────────────────────────────
                raw_loan_rows.append({
                    "loan_id":              loan_id,
                    "customer_id":          cust["customer_id"],
                    "country_code":         cc,
                    "legal_entity":         cfg["legal_entity"],
                    "product_code":         pcode,
                    "product_name":         pname,
                    "loan_type":            ltype,
                    "loan_category":        cat,
                    "loan_purpose":         purpose,
                    "principal_amount":     principal,
                    "outstanding_balance":  outstanding_bal,
                    "disbursement_date":    disburse_d,
                    "maturity_date":        maturity_d,
                    "interest_rate":        rate,
                    "emi_amount":           emi,
                    "tenor_months":         term,
                    "payment_frequency":    "MONTHLY",
                    "loan_status":          loan_stat,
                    "collateral_type":      collateral,
                    "current_dpd":          current_dpd,
                    "max_dpd":              max_dpd,
                    "is_npa":               is_npa,
                    "overdue_amount":       overdue_amt,
                    "total_interest_payable": total_interest,
                    "interest_paid_to_date": interest_paid,
                    "principal_paid_to_date": principal_paid,
                    "currency_code":        cfg["currency"],
                    "branch_code":          f"{cc}_BR_{random.randint(1,10):02d}",
                    "relationship_manager": f"RM_{random.randint(1,20):03d}",
                    "credit_score_at_origination": cust["credit_score"],
                    "is_deleted":           0,
                    "created_at":           datetime.combine(disburse_d, datetime.min.time()),
                    "updated_at":           NOW,
                    # meta
                    "_emi":        emi,
                    "_term":       term,
                    "_disburse":   disburse_d,
                    "_months_paid": months_paid,
                    "_dpd":        current_dpd,
                    "_outstanding": outstanding_bal,
                    "_principal":  principal,
                    "_rate":       rate,
                    "_is_closed":  is_closed,
                })

                # ── DDM loan ──────────────────────────────────────────
                ddm_loan_rows.append({
                    "loan_id":              loan_id,
                    "customer_id":          cust["customer_id"],
                    "country_code":         cc,
                    "legal_entity":         cfg["legal_entity"],
                    "product_code":         pcode,
                    "product_name":         pname,
                    "loan_type":            ltype,
                    "loan_category":        cat,
                    "customer_segment":     seg,
                    "principal_amount":     principal,
                    "outstanding_balance":  outstanding_bal,
                    "disbursement_date":    disburse_d,
                    "maturity_date":        maturity_d,
                    "interest_rate":        rate,
                    "emi_amount":           emi,
                    "tenor_months":         term,
                    "loan_status":          loan_stat,
                    "current_dpd":          current_dpd,
                    "dpd_bucket":           dpd_bucket(current_dpd),
                    "is_npa":               is_npa,
                    "overdue_amount":       overdue_amt,
                    "loan_to_income_ratio": loan_to_income,
                    "total_interest_payable": total_interest,
                    "interest_paid_to_date": interest_paid,
                    "principal_paid_to_date": principal_paid,
                    "currency_code":        cfg["currency"],
                    "collateral_type":      collateral,
                    "is_deleted":           0,
                    "created_at":           datetime.combine(disburse_d, datetime.min.time()),
                    "updated_at":           NOW,
                })

                # ── Repayment schedule ─────────────────────────────────
                for mo in range(1, min(months_paid + 1, term + 1)):
                    rep_num += 1
                    sched_dt  = disburse_d + timedelta(days=30 * mo)
                    expected_dt = sched_dt
                    is_paid   = mo <= months_paid
                    is_late   = False
                    delay_days = 0
                    actual_dt = None

                    if is_paid:
                        if current_dpd > 0 and mo >= months_paid - 2:
                            delay_days = random.randint(5, max(6, current_dpd))
                            is_late    = True
                            actual_dt  = sched_dt + timedelta(days=delay_days)
                        else:
                            delay_days = 0
                            actual_dt  = sched_dt + timedelta(days=random.randint(-3, 5))

                    # EMI split (simplified reducing balance)
                    int_component  = round(outstanding_bal * rate / 12 * (1 - mo / (term + 1)), 2)
                    prin_component = round(emi - int_component, 2)

                    raw_rep_rows.append({
                        "repayment_id":       f"{cc}_REP_{rep_num:08d}",
                        "loan_id":            loan_id,
                        "customer_id":        cust["customer_id"],
                        "country_code":       cc,
                        "legal_entity":       cfg["legal_entity"],
                        "installment_number": mo,
                        "scheduled_date":     expected_dt,
                        "actual_payment_date": actual_dt,
                        "emi_amount":         emi,
                        "principal_component": prin_component,
                        "interest_component": int_component,
                        "outstanding_after":  round(max(0, outstanding_bal - prin_component * mo), 2),
                        "currency_code":      cfg["currency"],
                        "payment_status":     ("PAID" if is_paid and not is_late
                                               else "LATE_PAID" if is_paid and is_late
                                               else "PENDING" if sched_dt > TODAY
                                               else "OVERDUE"),
                        "penalty_amount":     round(emi * 0.02 * delay_days / 30, 2) if is_late else 0.0,
                        "created_at":         datetime.combine(disburse_d, datetime.min.time()),
                    })

                    ddm_rep_rows.append({
                        "repayment_id":       f"{cc}_REP_{rep_num:08d}",
                        "loan_id":            loan_id,
                        "customer_id":        cust["customer_id"],
                        "country_code":       cc,
                        "installment_number": mo,
                        "scheduled_date":     expected_dt,
                        "actual_payment_date": actual_dt,
                        "emi_amount":         emi,
                        "principal_component": prin_component,
                        "interest_component": int_component,
                        "outstanding_after":  round(max(0, outstanding_bal - prin_component * mo), 2),
                        "is_paid":            int(is_paid),
                        "is_late":            int(is_late),
                        "delay_days":         delay_days,
                        "payment_status":     ("PAID" if is_paid and not is_late
                                               else "LATE_PAID" if is_paid and is_late
                                               else "PENDING" if sched_dt > TODAY
                                               else "OVERDUE"),
                        "penalty_amount":     round(emi * 0.02 * delay_days / 30, 2) if is_late else 0.0,
                        "created_at":         datetime.combine(disburse_d, datetime.min.time()),
                    })

    return raw_loan_rows, raw_rep_rows, ddm_loan_rows, ddm_rep_rows


if __name__ == "__main__":
    from gen_customers import generate_customers
    custs = generate_customers()
    raw_l, raw_r, ddm_l, ddm_r = generate_loans(custs)
    print(f"Loans: {len(raw_l)}, Repayments: {len(raw_r)}, DDM loans: {len(ddm_l)}, DDM reps: {len(ddm_r)}")
