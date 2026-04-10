"""
DataPrismAI — Customer 360 generator
Generates: raw_customer, ddm_customer, raw_merchant, ddm_merchant
"""
import sys, os, random, hashlib
from datetime import date, datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from gen_ref_data import *

random.seed(random_seed)


# ── helpers ────────────────────────────────────────────────────────────────────
def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def age_band(age: int) -> str:
    if age < 25: return "<25"
    if age < 35: return "25-34"
    if age < 45: return "35-44"
    if age < 55: return "45-54"
    return "55+"


def credit_band(score: int) -> str:
    if score >= 750: return "EXCELLENT"
    if score >= 700: return "GOOD"
    if score >= 650: return "FAIR"
    if score >= 600: return "POOR"
    return "VERY_POOR"


def income_band(inc: float, cc: str) -> str:
    thresholds = {
        "SG": [(80000,  "< SGD 80K"),  (150000, "SGD 80K-150K"),  (300000, "SGD 150K-300K"),  (float("inf"), "> SGD 300K")],
        "MY": [(72000,  "< MYR 72K"),  (150000, "MYR 72K-150K"),  (360000, "MYR 150K-360K"),  (float("inf"), "> MYR 360K")],
        "IN": [(800000, "< INR 800K"), (2000000,"INR 800K-2M"),    (6000000,"INR 2M-6M"),       (float("inf"), "> INR 6M")],
    }
    for thresh, label in thresholds.get(cc, []):
        if inc < thresh:
            return label
    return "Unknown"


def sg_nric() -> str:
    prefix = random.choice(["S", "T"])
    digits = random.randint(1000000, 9999999)
    suffix = random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
    return f"{prefix}{digits}{suffix}"


def my_mykad(dob: date) -> str:
    yr  = str(dob.year)[2:]
    mn  = f"{dob.month:02d}"
    dy  = f"{dob.day:02d}"
    st  = f"{random.randint(1,16):02d}"
    seq = f"{random.randint(1000,9999)}"
    return f"{yr}{mn}{dy}-{st}-{seq}"


def in_aadhar() -> str:
    return f"{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"


def phone(cc: str, dob: date) -> str:
    if cc == "SG":
        return f"+65 {random.randint(8000,9999)} {random.randint(1000,9999)}"
    if cc == "MY":
        return f"+60 {random.randint(10,19)}-{random.randint(1000000,9999999)}"
    return f"+91 {random.randint(70000,99999)} {random.randint(10000,99999)}"


def postal(cc: str) -> str:
    if cc == "SG":
        return f"{random.randint(10000, 829999):06d}"
    if cc == "MY":
        return f"{random.randint(10000, 98999):05d}"
    return f"{random.randint(100000, 999999)}"


# ── GENERATE CUSTOMERS ─────────────────────────────────────────────────────────
def generate_customers() -> dict:
    """Returns dict: country_code → list of customer dicts"""
    all_customers = {}
    for cc, cfg in COUNTRY_CONF.items():
        all_customers[cc] = []
        for i in range(1, cfg["n_customers"] + 1):
            seg    = random.choice(SEGMENT_POOL)
            gender = random.choice(["M", "F"])
            fname  = random.choice(cfg["m_names"] if gender == "M" else cfg["f_names"])
            lname  = random.choice(cfg["surnames"])
            dob    = rand_date(date(1960, 1, 1), date(2000, 12, 31))
            age    = (TODAY - dob).days // 365

            lo, hi  = cfg["incomes"][seg]
            income  = round(random.uniform(lo, hi), 2)
            score   = {
                "MASS":     random.randint(560, 720),
                "AFFLUENT": random.randint(640, 780),
                "PRIORITY": random.randint(700, 820),
                "HNW":      random.randint(740, 850),
            }[seg]

            kyc  = random.choices(["VERIFIED", "PENDING", "FAILED"], weights=[88, 9, 3])[0]
            risk = random.choices(["LOW", "MEDIUM", "HIGH"],          weights=[72, 20, 8])[0]
            city = random.choice(cfg["cities"])
            state = random.choice(cfg["states"])
            acq   = random.choice(["ONLINE", "BRANCH", "AGENT", "REFERRAL"])
            occ   = random.choice(OCCUPATIONS)
            creat = rand_date(date(2019, 1, 1), date(2024, 6, 1))

            id_num = {
                "SG": sg_nric,
                "MY": lambda: my_mykad(dob),
                "IN": in_aadhar,
            }[cc]()

            email = (fname.lower().replace(" ", "") + "." +
                     lname.lower().replace(" ", "") + "@" +
                     random.choice(["gmail.com", "yahoo.com", "hotmail.com",
                                    f"email.{cc.lower()}", "outlook.com"]))

            c = {
                "customer_id":      f"{cc}_CUST_{i:04d}",
                "country_code":     cc,
                "legal_entity":     cfg["legal_entity"],
                "first_name":       fname,
                "last_name":        lname,
                "full_name":        f"{fname} {lname}",
                "date_of_birth":    dob,
                "gender":           gender,
                "email":            email,
                "phone":            phone(cc, dob),
                "address_line1":    f"{random.randint(1,999)} {random.choice(['Main St','Park Ave','High St','Garden Rd','Central Blvd','Jalan Besar','MG Road'])}",
                "city":             city,
                "state_province":   state,
                "postal_code":      postal(cc),
                "nationality":      {"SG":"Singaporean","MY":"Malaysian","IN":"Indian"}[cc],
                "id_type":          cfg["id_type"],
                "id_number":        id_num,
                "customer_segment": seg,
                "kyc_status":       kyc,
                "risk_rating":      risk,
                "annual_income":    income,
                "income_band":      income_band(income, cc),
                "currency_code":    cfg["currency"],
                "occupation":       occ,
                "acquisition_channel": acq,
                "credit_score":     score,
                "credit_band":      credit_band(score),
                "is_deleted":       0,
                "created_at":       datetime.combine(creat, datetime.min.time()),
                "updated_at":       NOW,
                # ── private meta (not inserted directly) ──
                "_age":  age,
                "_seg":  seg,
            }
            all_customers[cc].append(c)
    return all_customers


# ── GENERATE MERCHANTS ─────────────────────────────────────────────────────────
def generate_merchants() -> list:
    rows = []
    for cc, merchants in MERCHANT_DATA.items():
        for mid, mname, mcat, mmcc, is_online, risk_tier, city in merchants:
            if risk_tier == "HIGH":
                fraud_rate   = round(random.uniform(0.04, 0.12), 4)
                decline_rate = round(random.uniform(0.05, 0.15), 4)
            elif risk_tier == "MEDIUM":
                fraud_rate   = round(random.uniform(0.01, 0.04), 4)
                decline_rate = round(random.uniform(0.02, 0.06), 4)
            else:
                fraud_rate   = round(random.uniform(0.001, 0.008), 4)
                decline_rate = round(random.uniform(0.005, 0.025), 4)

            rows.append({
                "merchant_id":      mid,
                "country_code":     cc,
                "merchant_name":    mname,
                "merchant_category": mcat,
                "mcc_code":         mmcc,
                "business_type":    mcat,
                "address":          f"{random.randint(1,999)} Commerce Street",
                "city":             city,
                "is_online":        int(is_online),
                "risk_tier":        risk_tier,
                "fraud_rate":       fraud_rate,
                "decline_rate":     decline_rate,
                "created_at":       datetime(2019, 1, 1) + timedelta(days=random.randint(0, 365)),
                "updated_at":       NOW,
            })
    return rows


if __name__ == "__main__":
    custs = generate_customers()
    total = sum(len(v) for v in custs.values())
    print(f"Customers generated: {total}")
    merch = generate_merchants()
    print(f"Merchants generated: {len(merch)}")
