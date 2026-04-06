#!/usr/bin/env python3
"""
DataPrismAI Banking Platform — Complete Synthetic Data Generator
Generates multi-country (SG, MY, IN) data across ALL layers:
  raw_ → ddm_ → dp_ → semantic_
Run: python3 generate_banking_data.py
"""
import os, random, hashlib, uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import mysql.connector

random.seed(42)

# ─────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────
def get_conn():
    return mysql.connector.connect(
        host=os.getenv("STARROCKS_HOST", "127.0.0.1"),
        port=int(os.getenv("STARROCKS_PORT", "9030")),
        user=os.getenv("STARROCKS_USER", "root"),
        password=os.getenv("STARROCKS_PASSWORD", ""),
        database=os.getenv("STARROCKS_DATABASE", "cc_analytics"),
        connection_timeout=60,
    )

CHUNK = 500

def bulk_insert(cur, conn, table, cols, rows):
    if not rows:
        return 0
    ph = ','.join(['%s'] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({ph})"
    total = 0
    for i in range(0, len(rows), CHUNK):
        batch = rows[i:i + CHUNK]
        cur.executemany(sql, batch)
        conn.commit()
        total += len(batch)
    return total

def rand_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(1, delta)))

def rand_dt(start, end):
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, max(1, delta)))

# ─────────────────────────────────────────────────────────────────
# Reference Data
# ─────────────────────────────────────────────────────────────────
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2026, 3, 31)

COUNTRY_CONF = {
    "SG": {
        "legal_entity": "SG_BANK", "currency": "SGD", "n": 60,
        "cities": ["Singapore", "Jurong East", "Tampines", "Bishan", "Clementi", "Bedok", "Punggol"],
        "m_names": ["Wei", "Ahmad", "Brendan", "Marcus", "Kai", "Jun", "Ethan", "Leon", "Ryan", "Aaron", "Daryl", "Ivan"],
        "f_names": ["Priya", "Siti", "Emily", "Grace", "Cheryl", "Mei", "Nadia", "Sharon", "Karen", "Nicole", "Jasmine", "Belle"],
        "surnames": ["Tan", "Lee", "Lim", "Wong", "Ng", "Ridzwan", "Kumar", "Singh", "Ong", "Koh", "Ho", "Chua", "Chan"],
        "id_type": "NRIC",
        "credit_limits": {"MASS": (3000, 10000), "AFFLUENT": (10000, 50000), "PRIORITY": (50000, 150000), "HNW": (150000, 500000)},
        "incomes":       {"MASS": (36000, 80000), "AFFLUENT": (80000, 250000), "PRIORITY": (250000, 700000), "HNW": (700000, 5000000)},
        "avg_txn": 150, "txn_currency": "SGD",
    },
    "MY": {
        "legal_entity": "MY_BANK", "currency": "MYR", "n": 60,
        "cities": ["Kuala Lumpur", "Petaling Jaya", "Penang", "Johor Bahru", "Subang Jaya", "Shah Alam", "Cyberjaya"],
        "m_names": ["Raj", "David", "Ahmad", "Chong", "Muthu", "Faisal", "Darren", "Jason", "Kevin", "Daniel", "Azman", "Hakim"],
        "f_names": ["Siti", "Amy", "Priya", "Mei Ling", "Nora", "Jasmine", "Kelly", "Sarah", "Kavya", "Diana", "Aishah", "Farah"],
        "surnames": ["Kumar", "Lim", "Abdullah", "Tan", "Krishnan", "Yong", "Hassan", "Singh", "Ng", "Chan", "Ibrahim", "Rahman"],
        "id_type": "MYKAD",
        "credit_limits": {"MASS": (5000, 15000), "AFFLUENT": (15000, 80000), "PRIORITY": (80000, 300000), "HNW": (300000, 1000000)},
        "incomes":       {"MASS": (24000, 72000), "AFFLUENT": (72000, 240000), "PRIORITY": (240000, 700000), "HNW": (700000, 5000000)},
        "avg_txn": 250, "txn_currency": "MYR",
    },
    "IN": {
        "legal_entity": "IN_BANK", "currency": "INR", "n": 60,
        "cities": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Ahmedabad", "Kolkata"],
        "m_names": ["Ravi", "Vikram", "Arjun", "Rohit", "Suresh", "Pradeep", "Nitin", "Arun", "Sanjay", "Mahesh", "Rajesh", "Dinesh"],
        "f_names": ["Anita", "Priya", "Deepa", "Kavya", "Sunita", "Rekha", "Nisha", "Pooja", "Divya", "Smita", "Geeta", "Meena"],
        "surnames": ["Sharma", "Patel", "Kumar", "Singh", "Gupta", "Nair", "Iyer", "Mehta", "Desai", "Joshi", "Verma", "Pillai"],
        "id_type": "AADHAR",
        "credit_limits": {"MASS": (50000, 200000), "AFFLUENT": (200000, 800000), "PRIORITY": (800000, 3000000), "HNW": (3000000, 15000000)},
        "incomes":       {"MASS": (240000, 800000), "AFFLUENT": (800000, 3000000), "PRIORITY": (3000000, 10000000), "HNW": (10000000, 50000000)},
        "avg_txn": 2500, "txn_currency": "INR",
    },
}

SEGMENT_POOL = ["MASS"] * 60 + ["AFFLUENT"] * 25 + ["PRIORITY"] * 12 + ["HNW"] * 3

MERCHANT_DATA = {
    "SG": [
        ("SG_MERCH_01", "Crystal Jade", "FOOD_DINING", "5812", False, "LOW"),
        ("SG_MERCH_02", "NTUC FairPrice", "GROCERY", "5411", False, "LOW"),
        ("SG_MERCH_03", "Singapore Airlines", "TRAVEL_TRANSPORT", "4511", True,  "LOW"),
        ("SG_MERCH_04", "Grab SG", "TRAVEL_TRANSPORT", "7299", True,  "LOW"),
        ("SG_MERCH_05", "Raffles Medical", "HEALTHCARE", "5912", False, "LOW"),
        ("SG_MERCH_06", "Golden Village", "ENTERTAINMENT", "7832", False, "LOW"),
        ("SG_MERCH_07", "SP Services", "UTILITIES", "4900", True,  "LOW"),
        ("SG_MERCH_08", "Marina Bay Sands", "HOTEL", "7011", False, "LOW"),
        ("SG_MERCH_09", "Shell SG", "FUEL", "5541", False, "LOW"),
        ("SG_MERCH_10", "Uniqlo SG", "RETAIL_SHOPPING", "5999", False, "LOW"),
        ("SG_MERCH_11", "Din Tai Fung", "FOOD_DINING", "5812", False, "LOW"),
        ("SG_MERCH_12", "Cold Storage", "GROCERY", "5411", False, "LOW"),
        ("SG_MERCH_13", "Lazada SG", "RETAIL_SHOPPING", "5999", True,  "MEDIUM"),
        ("SG_MERCH_14", "ComfortDelGro", "TRAVEL_TRANSPORT", "4131", False, "LOW"),
        ("SG_MERCH_15", "Singtel", "UTILITIES", "4813", True,  "LOW"),
        ("SG_MERCH_16", "ION Orchard", "RETAIL_SHOPPING", "5311", False, "LOW"),
        ("SG_MERCH_17", "Grand Hyatt", "HOTEL", "7011", False, "LOW"),
        ("SG_MERCH_18", "Caltex SG", "FUEL", "5541", False, "LOW"),
        ("SG_MERCH_19", "Kaplan SG", "EDUCATION", "8299", True,  "LOW"),
        ("SG_MERCH_20", "CryptoMerch SG", "OTHER", "7995", True,  "HIGH"),
    ],
    "MY": [
        ("MY_MERCH_01", "PappaRich", "FOOD_DINING", "5812", False, "LOW"),
        ("MY_MERCH_02", "Giant MY", "GROCERY", "5411", False, "LOW"),
        ("MY_MERCH_03", "AirAsia", "TRAVEL_TRANSPORT", "4511", True,  "LOW"),
        ("MY_MERCH_04", "Grab MY", "TRAVEL_TRANSPORT", "7299", True,  "LOW"),
        ("MY_MERCH_05", "Pantai Hospital", "HEALTHCARE", "8062", False, "LOW"),
        ("MY_MERCH_06", "GSC Cinemas", "ENTERTAINMENT", "7832", False, "LOW"),
        ("MY_MERCH_07", "Telekom Malaysia", "UTILITIES", "4813", True,  "LOW"),
        ("MY_MERCH_08", "Mandarin Oriental KL", "HOTEL", "7011", False, "LOW"),
        ("MY_MERCH_09", "Petronas", "FUEL", "5541", False, "LOW"),
        ("MY_MERCH_10", "Pavilion KL", "RETAIL_SHOPPING", "5311", False, "LOW"),
        ("MY_MERCH_11", "OldTown Coffee", "FOOD_DINING", "5812", False, "LOW"),
        ("MY_MERCH_12", "Village Grocer", "GROCERY", "5411", False, "LOW"),
        ("MY_MERCH_13", "Shopee MY", "RETAIL_SHOPPING", "5999", True,  "MEDIUM"),
        ("MY_MERCH_14", "Rapid KL", "TRAVEL_TRANSPORT", "4131", False, "LOW"),
        ("MY_MERCH_15", "Maxis MY", "UTILITIES", "4813", True,  "LOW"),
        ("MY_MERCH_16", "AEON MY", "RETAIL_SHOPPING", "5311", False, "LOW"),
        ("MY_MERCH_17", "JW Marriott KL", "HOTEL", "7011", False, "LOW"),
        ("MY_MERCH_18", "Petron MY", "FUEL", "5541", False, "LOW"),
        ("MY_MERCH_19", "Taylor University", "EDUCATION", "8299", False, "LOW"),
        ("MY_MERCH_20", "BettingMY Online", "OTHER", "7995", True,  "HIGH"),
    ],
    "IN": [
        ("IN_MERCH_01", "Swiggy", "FOOD_DINING", "5812", True,  "LOW"),
        ("IN_MERCH_02", "BigBasket", "GROCERY", "5411", True,  "LOW"),
        ("IN_MERCH_03", "IndiGo", "TRAVEL_TRANSPORT", "4511", True,  "LOW"),
        ("IN_MERCH_04", "Ola Cabs", "TRAVEL_TRANSPORT", "7299", True,  "LOW"),
        ("IN_MERCH_05", "Apollo Hospitals", "HEALTHCARE", "8062", False, "LOW"),
        ("IN_MERCH_06", "PVR Cinemas", "ENTERTAINMENT", "7832", False, "LOW"),
        ("IN_MERCH_07", "Jio", "UTILITIES", "4813", True,  "LOW"),
        ("IN_MERCH_08", "Taj Hotels", "HOTEL", "7011", False, "LOW"),
        ("IN_MERCH_09", "Indian Oil", "FUEL", "5541", False, "LOW"),
        ("IN_MERCH_10", "Flipkart", "RETAIL_SHOPPING", "5999", True,  "MEDIUM"),
        ("IN_MERCH_11", "Zomato", "FOOD_DINING", "5812", True,  "LOW"),
        ("IN_MERCH_12", "DMart", "GROCERY", "5411", False, "LOW"),
        ("IN_MERCH_13", "Amazon IN", "RETAIL_SHOPPING", "5999", True,  "MEDIUM"),
        ("IN_MERCH_14", "IRCTC", "TRAVEL_TRANSPORT", "4111", True,  "LOW"),
        ("IN_MERCH_15", "Airtel", "UTILITIES", "4813", True,  "LOW"),
        ("IN_MERCH_16", "Myntra", "RETAIL_SHOPPING", "5311", True,  "LOW"),
        ("IN_MERCH_17", "Marriott IN", "HOTEL", "7011", False, "LOW"),
        ("IN_MERCH_18", "HPCL", "FUEL", "5541", False, "LOW"),
        ("IN_MERCH_19", "Byju's", "EDUCATION", "8299", True,  "LOW"),
        ("IN_MERCH_20", "CryptoIN Exchange", "OTHER", "7995", True,  "HIGH"),
    ],
}

OCCUPATIONS = [
    "Software Engineer", "Doctor", "Teacher", "Business Owner", "Manager",
    "Accountant", "Lawyer", "Engineer", "Nurse", "Consultant",
    "IT Professional", "Banker", "Entrepreneur", "Government Employee", "Freelancer",
    "Architect", "Chef", "Pharmacist", "Researcher", "Marketing Manager",
]

PAYMENT_METHODS = {
    "SG": ["GIRO", "PAYNOW", "TRANSFER", "DEBIT_CARD", "ONLINE_BANKING"],
    "MY": ["TRANSFER", "FPXPAY", "ONLINE_BANKING", "CHEQUE", "DEBIT_CARD"],
    "IN": ["UPI", "NEFT", "IMPS", "NETBANKING", "DEBIT_CARD"],
}

CHANNELS = ["POS", "POS", "POS", "ONLINE", "ONLINE", "CONTACTLESS", "CONTACTLESS", "MOBILE", "ATM"]
TXN_TYPES = ["PURCHASE"] * 7 + ["REFUND", "WITHDRAWAL", "FEE"]
AUTH_STATUS_POOL = ["APPROVED"] * 85 + ["DECLINED"] * 10 + ["REVERSED"] * 5
DECLINE_REASONS = ["INSUFFICIENT_FUNDS", "LIMIT_EXCEEDED", "FRAUD_SUSPECT", "INVALID_CVV", "CARD_BLOCKED", "EXPIRED_CARD"]


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────
def age_band(a):
    if a < 25: return "<25"
    if a < 35: return "25-34"
    if a < 45: return "35-44"
    if a < 55: return "45-54"
    return "55+"

def credit_band(s):
    if s >= 750: return "EXCELLENT"
    if s >= 700: return "GOOD"
    if s >= 650: return "FAIR"
    if s >= 600: return "POOR"
    return "VERY_POOR"

def income_band(inc, cc):
    thresholds = {
        "SG": [(80000, "< SGD 80K"), (150000, "SGD 80K-150K"), (300000, "SGD 150K-300K"), (float('inf'), "> SGD 300K")],
        "MY": [(72000, "< MYR 72K"), (150000, "MYR 72K-150K"), (360000, "MYR 150K-360K"), (float('inf'), "> MYR 360K")],
        "IN": [(800000, "< INR 800K"), (2000000, "INR 800K-2M"),  (6000000, "INR 2M-6M"),   (float('inf'), "> INR 6M")],
    }
    for thresh, label in thresholds.get(cc, []):
        if inc < thresh:
            return label
    return "Unknown"

def overdue_bucket(days):
    if days <= 0:   return "CURRENT"
    if days <= 30:  return "1-30"
    if days <= 60:  return "31-60"
    if days <= 90:  return "61-90"
    return "91+"

def months_between(d1, d2):
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


# ─────────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────────────────────────
def main():
    conn = get_conn()
    cur  = conn.cursor()
    TODAY = date.today()
    NOW   = datetime.now()

    print("=" * 60)
    print("DataPrismAI — Banking Data Generator")
    print("=" * 60)

    # ── STEP 0: Merchant data ──────────────────────────────────────
    print("\n[1/9] Generating merchants...")
    merch_rows = []
    merchant_lookup = {}  # cc → list of (id, name, cat, mcc, is_online, risk_tier)
    for cc, merchants in MERCHANT_DATA.items():
        merchant_lookup[cc] = merchants
        for mid, name, cat, mcc, is_online, risk_tier in merchants:
            fr = round(random.uniform(0.002, 0.08) if risk_tier == "HIGH" else random.uniform(0.0005, 0.02), 4)
            dr = round(random.uniform(0.01, 0.08)  if risk_tier == "HIGH" else random.uniform(0.005, 0.03), 4)
            merch_rows.append((
                mid, cc, name, cat, mcc, cat,
                f"{random.randint(1, 999)} Commerce St", merchant_lookup[cc][0][0].split("_")[0] + " City",
                int(is_online), risk_tier, fr, dr,
                rand_dt(datetime(2020, 1, 1), START_DATE), NOW,
            ))
    cols = ["merchant_id","country_code","merchant_name","merchant_category","mcc_code","business_type",
            "address","city","is_online","risk_tier","fraud_rate","decline_rate","created_at","updated_at"]
    n = bulk_insert(cur, conn, "raw_merchant", cols, merch_rows)
    print(f"  raw_merchant: {n} rows")

    # ── STEP 1: Customers ──────────────────────────────────────────
    print("[2/9] Generating customers...")
    all_customers = {}  # cc → list of customer dicts
    cust_rows_raw = []

    for cc, cfg in COUNTRY_CONF.items():
        all_customers[cc] = []
        for i in range(1, cfg["n"] + 1):
            cid = f"{cc}_CUST_{i:04d}"
            seg = random.choice(SEGMENT_POOL)
            gender = random.choice(["M", "F"])
            fname = random.choice(cfg["m_names"] if gender == "M" else cfg["f_names"])
            lname = random.choice(cfg["surnames"])
            dob   = rand_date(date(1960, 1, 1), date(2000, 1, 1))
            a     = (TODAY - dob).days // 365
            lo, hi = cfg["incomes"][seg]
            income = round(random.uniform(lo, hi), 2)
            score  = random.randint(500, 850)
            kyc    = random.choices(["VERIFIED", "PENDING", "FAILED"], weights=[85, 10, 5])[0]
            risk   = random.choices(["LOW", "MEDIUM", "HIGH"],          weights=[70, 20, 10])[0]
            city   = random.choice(cfg["cities"])
            acq    = random.choice(["ONLINE", "BRANCH", "AGENT", "REFERRAL"])
            occ    = random.choice(OCCUPATIONS)
            creat  = rand_date(date(2020, 1, 1), date(2024, 6, 1))

            if cc == "SG":
                pfx = random.choice(["S", "T"])
                id_num = f"{pfx}{random.randint(1000000,9999999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
            elif cc == "MY":
                yr = str(dob.year)[2:]
                id_num = f"{yr}{random.randint(100000,999999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
            else:
                id_num = f"{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"

            c = {
                "customer_id": cid, "country_code": cc, "legal_entity": cfg["legal_entity"],
                "first_name": fname, "last_name": lname, "date_of_birth": dob,
                "gender": gender,
                "email": f"{fname.lower().replace(' ','')}.{lname.lower()}@email.{cc.lower()}",
                "phone": f"+{random.randint(60000000000, 99999999999)}",
                "address_line1": f"{random.randint(1,999)} {random.choice(['Main St','Park Ave','High St','Garden Rd','Central Blvd'])}",
                "city": city, "state_province": city, "postal_code": f"{random.randint(10000,99999)}",
                "nationality": {"SG":"Singaporean","MY":"Malaysian","IN":"Indian"}[cc],
                "id_type": cfg["id_type"], "id_number": id_num,
                "customer_segment": seg, "kyc_status": kyc, "risk_rating": risk,
                "annual_income": income, "currency_code": cfg["currency"],
                "occupation": occ, "acquisition_channel": acq, "credit_score": score,
                "is_deleted": 0,
                "created_at": datetime.combine(creat, datetime.min.time()),
                "updated_at": NOW,
                # derived (not in raw_customer but used for ddm)
                "_age": a, "_seg": seg,
            }
            all_customers[cc].append(c)
            cust_rows_raw.append(tuple(v for k, v in c.items() if not k.startswith("_")))

    raw_cust_cols = ["customer_id","country_code","legal_entity","first_name","last_name","date_of_birth",
                     "gender","email","phone","address_line1","city","state_province","postal_code",
                     "nationality","id_type","id_number","customer_segment","kyc_status","risk_rating",
                     "annual_income","currency_code","occupation","acquisition_channel","credit_score",
                     "is_deleted","created_at","updated_at"]
    n = bulk_insert(cur, conn, "raw_customer", raw_cust_cols, cust_rows_raw)
    print(f"  raw_customer: {n} rows")

    # ── STEP 2: Accounts ───────────────────────────────────────────
    print("[3/9] Generating accounts + cards...")
    all_accounts = {}  # cc → list of account dicts
    acct_rows_raw = []
    card_rows_raw = []

    for cc, custs in all_customers.items():
        cfg = COUNTRY_CONF[cc]
        all_accounts[cc] = []

        for c in custs:
            # 1 primary account, 30% chance of 2nd account
            n_accts = 1 + (1 if random.random() < 0.3 else 0)
            for j in range(n_accts):
                aid = f"{cc}_ACC_{c['customer_id'].split('_')[2]}_{j+1:02d}"
                lo, hi = cfg["credit_limits"][c["_seg"]]
                clim = round(random.uniform(lo, hi) / 100) * 100
                util = round(random.uniform(0.10, 0.90), 4)
                bal  = round(clim * util, 2)
                avail = round(clim - bal, 2)
                rate = round(random.uniform(0.0199, 0.0549), 4)
                status = random.choices(["ACTIVE","FROZEN","DORMANT"], weights=[90, 6, 4])[0]
                freeze = random.choice(["FRAUD_REVIEW","CUSTOMER_REQUEST",None]) if status == "FROZEN" else None
                open_d = rand_date(date(2020, 1, 1), date(2024, 1, 1))
                cycle  = random.randint(1, 28)
                tiers  = ["STANDARD","GOLD","PLATINUM","INFINITE"]
                tier   = {"MASS":"STANDARD","AFFLUENT":"GOLD","PRIORITY":"PLATINUM","HNW":"INFINITE"}[c["_seg"]]
                prod_code = f"{cc}_{tier[:3]}_CC"

                acct = {
                    "account_id": aid, "customer_id": c["customer_id"],
                    "country_code": cc, "legal_entity": cfg["legal_entity"],
                    "account_type": "CREDIT_CARD", "product_code": prod_code,
                    "currency_code": cfg["currency"],
                    "current_balance": bal, "available_balance": avail,
                    "credit_limit": clim, "minimum_balance": 0,
                    "interest_rate": rate, "account_status": status,
                    "freeze_reason": freeze, "branch_code": f"{cc}_BR_{random.randint(1,10):02d}",
                    "product_name": f"{tier.title()} Credit Card",
                    "open_date": open_d, "close_date": None,
                    "last_activity_date": rand_date(date(2025, 1, 1), TODAY),
                    "cycle_day": cycle, "is_deleted": 0,
                    "created_at": datetime.combine(open_d, datetime.min.time()), "updated_at": NOW,
                    # metadata
                    "_credit_limit": clim, "_util": util, "_tier": tier, "_rate": rate,
                    "_customer": c,
                }
                all_accounts[cc].append(acct)
                acct_rows_raw.append((
                    aid, c["customer_id"], cc, cfg["legal_entity"],
                    "CREDIT_CARD", prod_code, cfg["currency"],
                    bal, avail, clim, 0, rate, status, freeze,
                    f"{cc}_BR_{random.randint(1,10):02d}", f"{tier.title()} Credit Card",
                    open_d, None, rand_date(date(2025,1,1), TODAY),
                    cycle, 0, datetime.combine(open_d, datetime.min.time()), NOW,
                ))

                # Card
                cid_num = c["customer_id"].split("_")[2]
                card_id = f"{cc}_CRD_{cid_num}_{j+1:02d}"
                iss = open_d + timedelta(days=7)
                exp = iss.replace(year=iss.year + 4)
                scheme = random.choice(["VISA", "MASTERCARD", "AMEX"])
                days_exp = (exp - TODAY).days
                cst = "ACTIVE" if status == "ACTIVE" else ("BLOCKED" if status == "FROZEN" else "INACTIVE")
                h = hashlib.sha256(f"{card_id}{random.random()}".encode()).hexdigest()

                card_rows_raw.append((
                    card_id, aid, c["customer_id"], cc, cfg["legal_entity"],
                    "CREDIT", scheme, h, tier,
                    iss, exp, cst,
                    1, clim * 0.5, 1, 1,
                    datetime.combine(iss, datetime.min.time()), NOW,
                ))

    acct_cols = ["account_id","customer_id","country_code","legal_entity","account_type","product_code",
                 "currency_code","current_balance","available_balance","credit_limit","minimum_balance",
                 "interest_rate","account_status","freeze_reason","branch_code","product_name",
                 "open_date","close_date","last_activity_date","cycle_day","is_deleted","created_at","updated_at"]
    n1 = bulk_insert(cur, conn, "raw_account", acct_cols, acct_rows_raw)
    print(f"  raw_account: {n1} rows")

    card_cols = ["card_id","account_id","customer_id","country_code","legal_entity","card_type","card_scheme",
                 "card_number_hash","card_tier","issued_date","expiry_date","card_status",
                 "is_primary_card","daily_limit","international_enabled","contactless_enabled",
                 "created_at","updated_at"]
    n2 = bulk_insert(cur, conn, "raw_card", card_cols, card_rows_raw)
    print(f"  raw_card: {n2} rows")

    # ── STEP 3: Transactions ───────────────────────────────────────
    print("[4/9] Generating transactions...")
    N_TXN_PER_COUNTRY = 3500
    all_txns = {}  # cc → list of txn dicts
    txn_rows = []

    for cc, accts in all_accounts.items():
        cfg = COUNTRY_CONF[cc]
        active_accts = [a for a in accts if a["account_status"] == "ACTIVE"]
        if not active_accts:
            active_accts = accts
        merchants = merchant_lookup[cc]
        all_txns[cc] = []

        for t in range(N_TXN_PER_COUNTRY):
            acct   = random.choice(active_accts)
            merch  = random.choice(merchants)
            mid, mname, mcat, mmcc, m_online, m_risk = merch
            txn_dt = rand_dt(START_DATE, datetime.combine(TODAY, datetime.min.time()))
            amt    = round(random.expovariate(1 / cfg["avg_txn"]), 2)
            amt    = max(1.0, min(amt, acct["_credit_limit"] * 0.8))
            chan   = random.choice(CHANNELS)
            ttype  = random.choice(TXN_TYPES)
            auth   = random.choice(AUTH_STATUS_POOL)
            decl_r = random.choice(DECLINE_REASONS) if auth == "DECLINED" else None

            # Fraud logic
            base_fraud = 0.90 if m_risk == "HIGH" else 0.02
            is_late_night = txn_dt.hour < 4 or txn_dt.hour >= 23
            fraud_score = round(min(0.99, random.betavariate(0.5, 10) + (0.4 if m_risk == "HIGH" else 0) + (0.2 if is_late_night else 0)), 4)
            is_fraud   = 1 if fraud_score > 0.85 and auth == "APPROVED" and random.random() < 0.15 else 0
            is_susp    = 1 if fraud_score > 0.6 else 0
            fraud_tier = "HIGH_RISK" if fraud_score > 0.6 else ("MEDIUM_RISK" if fraud_score > 0.3 else "LOW_RISK")

            sett_dt = txn_dt + timedelta(days=random.randint(1, 3)) if auth == "APPROVED" else None
            ref_num = f"REF{random.randint(100000000, 999999999)}"
            txn_id  = f"{cc}_TXN_{t+1:06d}"

            txn = {
                "transaction_id": txn_id,
                "account_id": acct["account_id"],
                "card_id": f"{cc}_CRD_{acct['customer_id'].split('_')[2]}_01",
                "customer_id": acct["customer_id"],
                "country_code": cc, "legal_entity": COUNTRY_CONF[cc]["legal_entity"],
                "transaction_date": txn_dt, "settlement_date": sett_dt,
                "amount": amt, "currency_code": cfg["currency"],
                "transaction_type": ttype, "channel": chan,
                "merchant_id": mid, "merchant_name": mname,
                "merchant_category": mcat, "mcc_code": mmcc,
                "auth_status": auth, "decline_reason": decl_r,
                "is_fraud": is_fraud, "fraud_score": fraud_score, "fraud_tier": fraud_tier,
                "is_international": int(m_online and random.random() < 0.3),
                "is_recurring": int(random.random() < 0.1),
                "is_contactless": int(chan == "CONTACTLESS"),
                "reference_number": ref_num, "description": f"{mname} - {ttype}",
                "created_at": txn_dt,
                "_is_suspicious": is_susp,
                "_merchant_risk": m_risk,
            }
            all_txns[cc].append(txn)
            txn_rows.append(tuple(v for k, v in txn.items() if not k.startswith("_")))

    txn_cols = ["transaction_id","account_id","card_id","customer_id","country_code","legal_entity",
                "transaction_date","settlement_date","amount","currency_code","transaction_type","channel",
                "merchant_id","merchant_name","merchant_category","mcc_code","auth_status","decline_reason",
                "is_fraud","fraud_score","fraud_tier","is_international","is_recurring","is_contactless",
                "reference_number","description","created_at"]
    n = bulk_insert(cur, conn, "raw_transaction", txn_cols, txn_rows)
    print(f"  raw_transaction: {n} rows")

    # ── STEP 4: Statements (15 months per account) ─────────────────
    print("[5/9] Generating statements + payments...")
    stmt_rows = []
    pay_rows  = []
    stmt_by_acct = {}  # account_id → list of stmt dicts (for semantic later)

    stmt_num = 0
    pay_num  = 0

    for cc, accts in all_accounts.items():
        cfg = COUNTRY_CONF[cc]
        cc_txns = all_txns[cc]

        for acct in accts:
            stmt_by_acct[acct["account_id"]] = []
            # Build monthly spend from transactions
            acct_txns = [t for t in cc_txns
                         if t["account_id"] == acct["account_id"] and t["auth_status"] == "APPROVED"
                         and t["transaction_type"] == "PURCHASE"]

            for m_offset in range(14, -1, -1):  # 15 months back from current
                stmt_mth = (TODAY.replace(day=1) - timedelta(days=m_offset * 30)).strftime("%Y-%m")
                stmt_dt  = date(int(stmt_mth[:4]), int(stmt_mth[5:7]), acct.get("cycle_day", 20))
                try:
                    stmt_dt = stmt_dt.replace(day=min(28, acct.get("cycle_day", 20)))
                except ValueError:
                    stmt_dt = stmt_dt.replace(day=28)
                due_dt  = stmt_dt + timedelta(days=25)

                # Spend from transactions this month
                mth_txns = [t for t in acct_txns if t["transaction_date"].strftime("%Y-%m") == stmt_mth]
                total_spend = round(sum(t["amount"] for t in mth_txns), 2) or round(random.uniform(50, acct["_credit_limit"] * 0.3), 2)
                open_bal    = round(random.uniform(0, acct["_credit_limit"] * 0.5), 2)
                fees        = round(random.uniform(0, 15), 2)
                interest    = round(open_bal * acct["_rate"] / 12, 2) if open_bal > 0 else 0
                close_bal   = round(min(open_bal + total_spend + fees + interest, acct["_credit_limit"]), 2)
                total_due   = close_bal
                min_due     = round(max(total_due * 0.05, 10), 2)
                avail_cred  = round(acct["_credit_limit"] - close_bal, 2)
                util_rate   = round(close_bal / acct["_credit_limit"], 4) if acct["_credit_limit"] > 0 else 0

                # Payment status
                is_overdue = random.random() < (0.15 if acct["_customer"]["risk_rating"] in ("MEDIUM","HIGH") else 0.05)
                pay_amt    = 0.0
                days_od    = 0
                if due_dt < TODAY:
                    if is_overdue:
                        pay_amt  = round(random.uniform(0, total_due * 0.8), 2)
                        days_od  = (TODAY - due_dt).days
                        pay_stat = "OVERDUE"
                    else:
                        pay_amt  = round(random.choice([total_due, min_due, total_due * random.uniform(0.5, 1)]), 2)
                        pay_stat = "PAID"
                elif due_dt == TODAY:
                    pay_stat = "DUE_TODAY"
                    pay_amt  = 0.0
                else:
                    pay_stat = "UPCOMING"
                    pay_amt  = 0.0

                stmt_id = f"{cc}_STMT_{stmt_num+1:06d}"
                stmt_num += 1

                stmt = {
                    "statement_id": stmt_id, "account_id": acct["account_id"],
                    "customer_id": acct["customer_id"], "country_code": cc,
                    "legal_entity": cfg["legal_entity"],
                    "statement_date": stmt_dt, "statement_month": stmt_mth,
                    "opening_balance": open_bal, "closing_balance": close_bal,
                    "total_spend": total_spend, "total_credits": round(pay_amt, 2),
                    "total_fees": fees, "minimum_due": min_due, "total_due": total_due,
                    "due_date": due_dt, "payment_status": pay_stat,
                    "credit_limit": acct["_credit_limit"],
                    "available_credit": avail_cred, "utilization_rate": util_rate,
                    "transaction_count": len(mth_txns), "interest_charged": interest,
                    "created_at": datetime.combine(stmt_dt, datetime.min.time()),
                    "_days_od": days_od, "_pay_amt": pay_amt, "_min_due": min_due,
                    "_total_due": total_due, "_pay_stat": pay_stat,
                }
                stmt_by_acct[acct["account_id"]].append(stmt)
                stmt_rows.append(tuple(v for k, v in stmt.items() if not k.startswith("_")))

                # Payment record
                if pay_amt > 0 or pay_stat in ("PAID",):
                    pay_dt  = datetime.combine(due_dt - timedelta(days=random.randint(0, 5)), datetime.min.time()) if not is_overdue else datetime.combine(due_dt + timedelta(days=days_od - random.randint(0, 2)), datetime.min.time())
                    late_fee = round(pay_amt * 0.015, 2) if is_overdue else 0
                    pay_id  = f"{cc}_PAY_{pay_num+1:06d}"
                    pay_num += 1
                    method  = random.choice(PAYMENT_METHODS[cc])
                    pay_rows.append((
                        pay_id, acct["account_id"], acct["customer_id"], cc, cfg["legal_entity"],
                        pay_dt, due_dt, stmt_mth, min_due, total_due, pay_amt, method,
                        "MOBILE_APP", pay_stat, days_od, late_fee,
                        f"PAYREF{random.randint(100000, 999999)}",
                        datetime.combine(stmt_dt, datetime.min.time()),
                    ))

    stmt_cols = ["statement_id","account_id","customer_id","country_code","legal_entity",
                 "statement_date","statement_month","opening_balance","closing_balance",
                 "total_spend","total_credits","total_fees","minimum_due","total_due",
                 "due_date","payment_status","credit_limit","available_credit",
                 "utilization_rate","transaction_count","interest_charged","created_at"]
    n1 = bulk_insert(cur, conn, "raw_statement", stmt_cols, stmt_rows)
    print(f"  raw_statement: {n1} rows")

    pay_cols = ["payment_id","account_id","customer_id","country_code","legal_entity",
                "payment_date","due_date","statement_month","minimum_due","total_due",
                "payment_amount","payment_method","payment_channel","payment_status",
                "overdue_days","late_fee","reference_number","created_at"]
    n2 = bulk_insert(cur, conn, "raw_payment", pay_cols, pay_rows)
    print(f"  raw_payment: {n2} rows")

    # ── STEP 5: DDM Layer ──────────────────────────────────────────
    print("[6/9] Building DDM layer...")

    # ddm_customer
    ddm_cust_rows = []
    for cc, custs in all_customers.items():
        for c in custs:
            a = c["_age"]
            ddm_cust_rows.append((
                c["customer_id"], cc, COUNTRY_CONF[cc]["legal_entity"],
                f"{c['first_name']} {c['last_name']}",
                c["first_name"], c["last_name"],
                c["date_of_birth"], a, age_band(a), c["gender"],
                c["email"], c["phone"], c["city"], c["nationality"],
                c["id_type"], c["id_number"], c["_seg"],
                c["kyc_status"], c["risk_rating"],
                c["annual_income"], income_band(c["annual_income"], cc),
                c["currency_code"], c["occupation"], c["acquisition_channel"],
                c["credit_score"], credit_band(c["credit_score"]),
                0, c["created_at"].date(), date(9999, 12, 31), 1,
                c["created_at"], NOW,
            ))
    ddm_cust_cols = ["customer_id","country_code","legal_entity","full_name","first_name","last_name",
                     "date_of_birth","age","age_band","gender","email","phone","city","nationality",
                     "id_type","id_number","customer_segment","kyc_status","risk_rating",
                     "annual_income","income_band","currency_code","occupation","acquisition_channel",
                     "credit_score","credit_band","is_deleted","effective_from","effective_to","is_current",
                     "created_at","updated_at"]
    n = bulk_insert(cur, conn, "ddm_customer", ddm_cust_cols, ddm_cust_rows)
    print(f"  ddm_customer: {n} rows")

    # ddm_account
    ddm_acct_rows = []
    cust_lookup = {c["customer_id"]: c for cc_custs in all_customers.values() for c in cc_custs}
    for cc, accts in all_accounts.items():
        for a in accts:
            c = cust_lookup.get(a["customer_id"], {})
            util = round((a["current_balance"] / a["_credit_limit"]) if a["_credit_limit"] > 0 else 0, 4)
            uband = "HIGH" if util > 0.75 else ("MEDIUM" if util > 0.40 else "LOW")
            age_days = (TODAY - a["open_date"]).days
            ddm_acct_rows.append((
                a["account_id"], a["customer_id"], cc, COUNTRY_CONF[cc]["legal_entity"],
                f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg", "MASS"),
                "CREDIT_CARD", a["product_code"], a["product_name"],
                COUNTRY_CONF[cc]["currency"],
                a["current_balance"], a["available_balance"], a["_credit_limit"],
                util, uband, a["_rate"], a["account_status"],
                a["open_date"], a["close_date"], age_days, 0,
                a["created_at"], NOW,
            ))
    ddm_acct_cols = ["account_id","customer_id","country_code","legal_entity","full_name","customer_segment",
                     "account_type","product_code","product_name","currency_code",
                     "current_balance","available_balance","credit_limit","utilization_rate","utilization_band",
                     "interest_rate","account_status","open_date","close_date","account_age_days","is_deleted",
                     "created_at","updated_at"]
    n = bulk_insert(cur, conn, "ddm_account", ddm_acct_cols, ddm_acct_rows)
    print(f"  ddm_account: {n} rows")

    # ddm_transaction
    ddm_txn_rows = []
    for cc, txns in all_txns.items():
        for t in txns:
            c = cust_lookup.get(t["customer_id"], {})
            ddm_txn_rows.append((
                t["transaction_id"], t["account_id"], t["card_id"],
                t["customer_id"], cc, COUNTRY_CONF[cc]["legal_entity"],
                f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg","MASS"),
                t["transaction_date"], t["transaction_date"].strftime("%Y-%m"),
                t["amount"], COUNTRY_CONF[cc]["currency"],
                t["transaction_type"], t["channel"],
                t["merchant_id"], t["merchant_name"], t["merchant_category"], t["_merchant_risk"],
                t["mcc_code"], t["auth_status"], t["decline_reason"],
                t["is_fraud"], t["fraud_score"], t["fraud_tier"],
                t["_is_suspicious"], t["is_international"], t["is_contactless"],
                t["created_at"],
            ))
    ddm_txn_cols = ["transaction_id","account_id","card_id","customer_id","country_code","legal_entity",
                    "full_name","customer_segment","transaction_date","txn_year_month",
                    "amount","currency_code","transaction_type","channel",
                    "merchant_id","merchant_name","merchant_category","merchant_risk_tier","mcc_code",
                    "auth_status","decline_reason","is_fraud","fraud_score","fraud_tier",
                    "is_suspicious","is_international","is_contactless","created_at"]
    n = bulk_insert(cur, conn, "ddm_transaction", ddm_txn_cols, ddm_txn_rows)
    print(f"  ddm_transaction: {n} rows")

    # ddm_payment (from pay_rows)
    ddm_pay_rows = []
    for pr in pay_rows:
        pid,aid,cid,cc,le,pdt,ddt,smth,mnd,tdu,pamt,pmth,pchan,pstat,ods,lf,ref,cat = pr
        c = cust_lookup.get(cid, {})
        ratio = round(pamt / tdu, 4) if tdu > 0 else 0
        ob = overdue_bucket(ods)
        ddm_pay_rows.append((
            pid, aid, cid, cc, le,
            f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg","MASS"),
            pdt, ddt, smth, mnd, tdu, pamt, ratio,
            int(pamt >= tdu * 0.99), int(abs(pamt - mnd) < 5),
            pmth, pchan, pstat, ods, ob, lf, cat,
        ))
    ddm_pay_cols = ["payment_id","account_id","customer_id","country_code","legal_entity",
                    "full_name","customer_segment","payment_date","due_date","statement_month",
                    "minimum_due","total_due","payment_amount","payment_ratio",
                    "is_full_payment","is_minimum_payment","payment_method","payment_channel",
                    "payment_status","overdue_days","overdue_bucket","late_fee","created_at"]
    n = bulk_insert(cur, conn, "ddm_payment", ddm_pay_cols, ddm_pay_rows)
    print(f"  ddm_payment: {n} rows")

    # ddm_statement
    ddm_stmt_rows = []
    for cc, accts in all_accounts.items():
        for acct in accts:
            for s in stmt_by_acct.get(acct["account_id"], []):
                c = cust_lookup.get(acct["customer_id"], {})
                ddm_stmt_rows.append((
                    s["statement_id"], s["account_id"], s["customer_id"], cc,
                    COUNTRY_CONF[cc]["legal_entity"],
                    f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg","MASS"),
                    s["statement_month"], s["statement_date"],
                    s["opening_balance"], s["closing_balance"], s["total_spend"],
                    s["total_credits"], s["total_fees"], s["minimum_due"], s["total_due"],
                    s["due_date"], s["payment_status"], s["credit_limit"],
                    s["available_credit"], s["utilization_rate"],
                    s["transaction_count"], s["interest_charged"], s["created_at"],
                ))
    ddm_stmt_cols = ["statement_id","account_id","customer_id","country_code","legal_entity",
                     "full_name","customer_segment","statement_month","statement_date",
                     "opening_balance","closing_balance","total_spend","total_credits","total_fees",
                     "minimum_due","total_due","due_date","payment_status","credit_limit",
                     "available_credit","utilization_rate","transaction_count","interest_charged","created_at"]
    n = bulk_insert(cur, conn, "ddm_statement", ddm_stmt_cols, ddm_stmt_rows)
    print(f"  ddm_statement: {n} rows")

    # ddm_merchant
    ddm_merch_rows = []
    for r in merch_rows:
        mid,cc,mname,mcat,mmcc,btype,addr,city,is_onl,rtier,fr,dr,cat,upd = r
        ddm_merch_rows.append((mid,cc,mname,mcat,btype,mmcc,city,is_onl,rtier,fr,dr,0,0,cat,upd))
    ddm_merch_cols = ["merchant_id","country_code","merchant_name","merchant_category","business_type",
                      "mcc_code","city","is_online","risk_tier","fraud_rate","decline_rate",
                      "total_transaction_count","total_transaction_volume","created_at","updated_at"]
    n = bulk_insert(cur, conn, "ddm_merchant", ddm_merch_cols, ddm_merch_rows)
    print(f"  ddm_merchant: {n} rows")

    # ── STEP 6: DP Layer ───────────────────────────────────────────
    print("[7/9] Building data products layer...")

    # dp_customer_balance_snapshot — one row per customer per month
    dp_bal_rows = []
    cur_month = TODAY.strftime("%Y-%m")
    for cc, accts in all_accounts.items():
        # Group by customer
        cust_accts = {}
        for a in accts:
            cust_accts.setdefault(a["customer_id"], []).append(a)
        for cid, c_accts in cust_accts.items():
            c = cust_lookup.get(cid, {})
            total_lim = sum(a["_credit_limit"] for a in c_accts)
            total_bal = sum(a["current_balance"] for a in c_accts)
            total_av  = sum(a["available_balance"] for a in c_accts)
            avg_util  = round(total_bal / total_lim if total_lim > 0 else 0, 4)
            high_acct = sorted(c_accts, key=lambda x: x["_util"], reverse=True)[0]["account_id"]
            dp_bal_rows.append((
                cur_month, cid, cc, COUNTRY_CONF[cc]["legal_entity"],
                f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg","MASS"),
                len(c_accts), total_lim, total_bal, total_av, avg_util, high_acct,
                COUNTRY_CONF[cc]["currency"], NOW,
            ))
    dp_bal_cols = ["snapshot_month","customer_id","country_code","legal_entity","full_name","customer_segment",
                   "total_accounts","total_credit_limit","total_balance","total_available","avg_utilization",
                   "highest_util_account","currency_code","created_at"]
    n = bulk_insert(cur, conn, "dp_customer_balance_snapshot", dp_bal_cols, dp_bal_rows)
    print(f"  dp_customer_balance_snapshot: {n} rows")

    # dp_customer_spend_monthly
    dp_spend_rows = []
    CAT_COLS = ["FOOD_DINING","RETAIL_SHOPPING","TRAVEL_TRANSPORT","HEALTHCARE",
                "ENTERTAINMENT","UTILITIES","GROCERY","HOTEL","FUEL","EDUCATION"]
    for cc, txns in all_txns.items():
        agg = {}  # (customer_id, month) → spend by category
        for t in txns:
            if t["auth_status"] != "APPROVED" or t["transaction_type"] != "PURCHASE":
                continue
            k = (t["customer_id"], t["transaction_date"].strftime("%Y-%m"))
            if k not in agg:
                agg[k] = {cat: 0.0 for cat in CAT_COLS}
                agg[k]["total"] = 0.0
                agg[k]["count"] = 0
                agg[k]["merchants"] = {}
            agg[k][t["merchant_category"]] = agg[k].get(t["merchant_category"], 0) + t["amount"]
            agg[k]["total"] += t["amount"]
            agg[k]["count"] += 1
            agg[k]["merchants"][t["merchant_name"]] = agg[k]["merchants"].get(t["merchant_name"], 0) + t["amount"]

        for (cid, mth), data in agg.items():
            c = cust_lookup.get(cid, {})
            total = round(data["total"], 2)
            cnt   = data["count"]
            top_m = max(data["merchants"], key=data["merchants"].get) if data["merchants"] else ""
            cats  = {cat: round(data.get(cat, 0), 2) for cat in CAT_COLS}
            top_c = max(cats, key=cats.get) if any(cats.values()) else "RETAIL_SHOPPING"
            other = round(total - sum(cats.values()), 2)
            dp_spend_rows.append((
                mth, cid, cc, COUNTRY_CONF[cc]["legal_entity"],
                c.get("_seg","MASS"), total,
                cats["FOOD_DINING"], cats["RETAIL_SHOPPING"], cats["TRAVEL_TRANSPORT"],
                cats["HEALTHCARE"], cats["ENTERTAINMENT"], cats["UTILITIES"],
                cats["GROCERY"], cats["HOTEL"], cats["FUEL"],
                max(0, other), cnt,
                round(total / cnt, 2) if cnt else 0,
                top_m, top_c, COUNTRY_CONF[cc]["currency"], NOW,
            ))
    dp_spend_cols = ["spend_month","customer_id","country_code","legal_entity","customer_segment",
                     "total_spend","food_dining","retail_shopping","travel_transport","healthcare",
                     "entertainment","utilities","grocery","hotel","fuel","other_spend",
                     "transaction_count","avg_txn_amount","top_merchant","top_category",
                     "currency_code","created_at"]
    n = bulk_insert(cur, conn, "dp_customer_spend_monthly", dp_spend_cols, dp_spend_rows)
    print(f"  dp_customer_spend_monthly: {n} rows")

    # dp_payment_status — one row per account as of today
    dp_pay_rows = []
    for cc, accts in all_accounts.items():
        for acct in accts:
            stmts = stmt_by_acct.get(acct["account_id"], [])
            if not stmts:
                continue
            latest = max(stmts, key=lambda s: s["statement_date"])
            c = cust_lookup.get(acct["customer_id"], {})
            days = (TODAY - latest["due_date"]).days  # negative = future
            ods  = max(0, days) if latest["_pay_stat"] == "OVERDUE" else 0
            ob   = overdue_bucket(ods)
            late = round(latest["_total_due"] * 0.015, 2) if ods > 0 else 0
            dp_pay_rows.append((
                TODAY, acct["account_id"], acct["customer_id"], cc,
                COUNTRY_CONF[cc]["legal_entity"],
                f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg","MASS"),
                latest["statement_month"], latest["due_date"],
                (latest["due_date"] - TODAY).days,
                latest["_min_due"], latest["_total_due"],
                latest["_pay_amt"], round(latest["_total_due"] - latest["_pay_amt"], 2),
                latest["_pay_stat"], ods, ob,
                sum(1 for s in stmts if s["_pay_stat"] == "OVERDUE"), late,
                round(latest["_total_due"] * acct["_rate"] / 12, 2),
                COUNTRY_CONF[cc]["currency"], NOW,
            ))
    dp_pay_cols = ["as_of_date","account_id","customer_id","country_code","legal_entity",
                   "full_name","customer_segment","statement_month","due_date","days_to_due",
                   "minimum_due","total_due","amount_paid","amount_outstanding",
                   "payment_status","overdue_days","overdue_bucket","consecutive_late",
                   "late_fee","interest_at_risk","currency_code","created_at"]
    n = bulk_insert(cur, conn, "dp_payment_status", dp_pay_cols, dp_pay_rows)
    print(f"  dp_payment_status: {n} rows")

    # dp_risk_signals — daily by country for last 30 days
    dp_risk_rows = []
    for cc, txns in all_txns.items():
        for day_offset in range(30):
            d = TODAY - timedelta(days=day_offset)
            day_txns = [t for t in txns if t["transaction_date"].date() == d]
            if not day_txns:
                continue
            total  = len(day_txns)
            appr   = sum(1 for t in day_txns if t["auth_status"] == "APPROVED")
            decl   = sum(1 for t in day_txns if t["auth_status"] == "DECLINED")
            fraud  = sum(1 for t in day_txns if t["is_fraud"] == 1)
            susp   = sum(1 for t in day_txns if t["_is_suspicious"] == 1)
            t_amt  = round(sum(t["amount"] for t in day_txns), 2)
            f_amt  = round(sum(t["amount"] for t in day_txns if t["is_fraud"] == 1), 2)
            avg_fs = round(sum(t["fraud_score"] for t in day_txns) / total, 4) if total else 0
            dp_risk_rows.append((
                d, cc, COUNTRY_CONF[cc]["legal_entity"], None,
                total, appr, decl, fraud, susp, t_amt, f_amt,
                round(fraud / total, 6) if total else 0,
                round(decl  / total, 6) if total else 0,
                avg_fs, 0, 0,
                COUNTRY_CONF[cc]["currency"], NOW,
            ))
    dp_risk_cols = ["signal_date","country_code","legal_entity","customer_segment",
                    "total_txn","approved_txn","declined_txn","fraud_txn","suspicious_txn",
                    "total_amount","fraud_amount","fraud_rate","decline_rate","avg_fraud_score",
                    "high_risk_accounts","new_fraud_alerts","currency_code","created_at"]
    n = bulk_insert(cur, conn, "dp_risk_signals", dp_risk_cols, dp_risk_rows)
    print(f"  dp_risk_signals: {n} rows")

    # dp_portfolio_kpis — monthly by country for last 15 months
    dp_port_rows = []
    FX = {"SG": Decimal("0.748"), "MY": Decimal("0.223"), "IN": Decimal("0.012")}
    for cc, custs in all_customers.items():
        cfg = COUNTRY_CONF[cc]
        for m_offset in range(14, -1, -1):
            kpi_mth = (TODAY.replace(day=1) - timedelta(days=m_offset * 30)).strftime("%Y-%m")
            mth_txns = [t for t in all_txns[cc]
                        if t["transaction_date"].strftime("%Y-%m") == kpi_mth
                        and t["auth_status"] == "APPROVED"
                        and t["transaction_type"] == "PURCHASE"]
            total_cust  = len(custs)
            active_cust = int(total_cust * random.uniform(0.82, 0.95))
            new_cust    = random.randint(2, 10)
            churn       = random.randint(1, 5)
            g_pct       = round((new_cust - churn) / total_cust, 4)
            churn_r     = round(churn / total_cust, 4)
            accts       = all_accounts[cc]
            total_lim   = round(sum(a["_credit_limit"] for a in accts), 2)
            total_out   = round(sum(a["current_balance"] for a in accts) * random.uniform(0.8, 1.1), 2)
            total_spend = round(sum(t["amount"] for t in mth_txns), 2)
            avg_bal     = round(total_out / len(accts) if accts else 0, 2)
            avg_util    = round(total_out / total_lim if total_lim > 0 else 0, 4)
            t_total     = len([t for t in all_txns[cc] if t["transaction_date"].strftime("%Y-%m") == kpi_mth])
            t_fraud     = sum(1 for t in all_txns[cc] if t["transaction_date"].strftime("%Y-%m") == kpi_mth and t["is_fraud"])
            t_decl      = sum(1 for t in all_txns[cc] if t["transaction_date"].strftime("%Y-%m") == kpi_mth and t["auth_status"] == "DECLINED")
            fr          = round(t_fraud / t_total, 6) if t_total else 0
            dr          = round(t_decl  / t_total, 6) if t_total else 0
            delinq      = round(random.uniform(0.03, 0.12), 4)
            full_pay    = round(random.uniform(0.55, 0.80), 4)
            npl         = round(random.uniform(0.005, 0.025), 4)
            interest    = round(total_out * 0.0399 / 12, 2)
            dp_port_rows.append((
                kpi_mth, cc, cfg["legal_entity"],
                total_cust, active_cust, new_cust, churn, g_pct, churn_r,
                len(accts), int(len(accts) * 0.88),
                total_lim, total_out, total_spend,
                round(random.uniform(-0.05, 0.12), 4),
                avg_bal, avg_util, fr, dr, delinq, full_pay, npl, interest,
                cfg["currency"], FX[cc], NOW,
            ))
    dp_port_cols = ["kpi_month","country_code","legal_entity","total_customers","active_customers",
                    "new_customers","churned_customers","customer_growth_pct","churn_rate",
                    "total_accounts","active_accounts","total_credit_extended","total_outstanding",
                    "total_spend","spend_growth_pct","avg_balance","avg_utilization",
                    "fraud_rate","decline_rate","delinquency_rate","full_payment_rate","npl_rate",
                    "est_interest_income","currency_code","fx_rate_to_usd","created_at"]
    n = bulk_insert(cur, conn, "dp_portfolio_kpis", dp_port_cols, dp_port_rows)
    print(f"  dp_portfolio_kpis: {n} rows")

    # ── STEP 7: Semantic Layer ─────────────────────────────────────
    print("[8/9] Building semantic layer...")

    # semantic_customer_360
    sem_c360_rows = []
    for cc, custs in all_customers.items():
        for c in custs:
            c_accts = [a for a in all_accounts[cc] if a["customer_id"] == c["customer_id"]]
            if not c_accts:
                continue
            prim = c_accts[0]
            # last month spend
            tm_mth = TODAY.strftime("%Y-%m")
            pm_mth = (TODAY.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
            c_txns = [t for t in all_txns[cc] if t["customer_id"] == c["customer_id"] and t["auth_status"] == "APPROVED" and t["transaction_type"] == "PURCHASE"]
            mtd  = round(sum(t["amount"] for t in c_txns if t["transaction_date"].strftime("%Y-%m") == tm_mth), 2)
            prev = round(sum(t["amount"] for t in c_txns if t["transaction_date"].strftime("%Y-%m") == pm_mth), 2)
            chg  = round((mtd - prev) / prev, 4) if prev > 0 else 0
            cat_spend = {}
            for t in c_txns:
                cat_spend[t["merchant_category"]] = cat_spend.get(t["merchant_category"], 0) + t["amount"]
            top_cat = max(cat_spend, key=cat_spend.get) if cat_spend else "RETAIL_SHOPPING"
            # payment status
            c_stmts = [s for a in c_accts for s in stmt_by_acct.get(a["account_id"], [])]
            latest_s = max(c_stmts, key=lambda s: s["statement_date"]) if c_stmts else None
            p_stat   = latest_s["_pay_stat"] if latest_s else "UPCOMING"
            t_due    = latest_s["_total_due"] if latest_s else 0
            dtd      = (latest_s["due_date"] - TODAY).days if latest_s else 30
            is_od    = 1 if p_stat == "OVERDUE" else 0
            consec   = sum(1 for s in c_stmts if s.get("_pay_stat") == "OVERDUE")
            fraud_al = sum(1 for t in c_txns if t["is_fraud"])
            a = c["_age"]
            sem_c360_rows.append((
                TODAY, c["customer_id"], cc, COUNTRY_CONF[cc]["legal_entity"],
                f"{c['first_name']} {c['last_name']}", c["first_name"], c["last_name"],
                c["_seg"], c["risk_rating"], c["kyc_status"],
                a, age_band(a), c["credit_score"], credit_band(c["credit_score"]),
                prim["account_id"], "CREDIT_CARD",
                prim["current_balance"], prim["available_balance"], prim["_credit_limit"],
                round(prim["current_balance"] / prim["_credit_limit"] if prim["_credit_limit"] > 0 else 0, 4),
                len(c_accts), mtd, prev, chg, top_cat, p_stat, t_due, dtd,
                is_od, consec, fraud_al, COUNTRY_CONF[cc]["currency"], NOW,
            ))
    sem_c360_cols = ["as_of_date","customer_id","country_code","legal_entity",
                     "full_name","first_name","last_name","customer_segment","risk_rating","kyc_status",
                     "age","age_band","credit_score","credit_band",
                     "primary_account_id","account_type","current_balance","available_balance",
                     "credit_limit","utilization_pct","total_accounts",
                     "mtd_spend","last_month_spend","spend_change_pct","top_spend_category",
                     "payment_status","total_due","days_to_due","is_overdue",
                     "consecutive_late","active_fraud_alerts","currency_code","created_at"]
    n = bulk_insert(cur, conn, "semantic_customer_360", sem_c360_cols, sem_c360_rows)
    print(f"  semantic_customer_360: {n} rows")

    # semantic_transaction_summary
    sem_txn_rows = []
    for cc, txns in all_txns.items():
        for t in txns:
            c = cust_lookup.get(t["customer_id"], {})
            sem_txn_rows.append((
                t["transaction_id"], t["account_id"], t["customer_id"], cc,
                COUNTRY_CONF[cc]["legal_entity"],
                f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg","MASS"),
                t["transaction_date"], t["transaction_date"].strftime("%Y-%m"),
                t["amount"], COUNTRY_CONF[cc]["currency"],
                t["transaction_type"], t["channel"],
                t["merchant_name"], t["merchant_category"], t["_merchant_risk"],
                t["auth_status"], t["decline_reason"],
                int(t["auth_status"] == "APPROVED"), int(t["auth_status"] == "DECLINED"),
                t["is_fraud"], t["fraud_score"], t["_is_suspicious"], t["is_international"],
                t["created_at"],
            ))
    sem_txn_cols = ["transaction_id","account_id","customer_id","country_code","legal_entity",
                    "full_name","customer_segment","transaction_date","txn_year_month",
                    "amount","currency_code","transaction_type","channel",
                    "merchant_name","merchant_category","merchant_risk_tier",
                    "auth_status","decline_reason","is_approved","is_declined",
                    "is_fraud","fraud_score","is_suspicious","is_international","created_at"]
    n = bulk_insert(cur, conn, "semantic_transaction_summary", sem_txn_cols, sem_txn_rows)
    print(f"  semantic_transaction_summary: {n} rows")

    # semantic_spend_metrics (from dp_spend_rows data)
    sem_spend_rows = []
    prev_spend = {}  # (cid, month) → spend
    for row in dp_spend_rows:
        (mth,cid,cc,le,seg,total,food,retail,travel,health,ent,util,groc,hotel,fuel,other,cnt,avg_t,top_m,top_c,cur_c,cat) = row
        prev_key_month = (date(int(mth[:4]), int(mth[5:7]), 1) - timedelta(days=1)).strftime("%Y-%m")
        prev = prev_spend.get((cid, prev_key_month), 0)
        mom  = round((total - prev) / prev, 4) if prev > 0 else 0
        prev_spend[(cid, mth)] = total
        c = cust_lookup.get(cid, {})
        sem_spend_rows.append((
            mth, cid, cc, le,
            f"{c.get('first_name','')} {c.get('last_name','')}", seg,
            total, food, retail, travel, health, ent, util, groc, hotel, fuel, other,
            cnt, avg_t, top_c, top_m, mom, cur_c, cat,
        ))
    sem_spend_cols = ["spend_month","customer_id","country_code","legal_entity","full_name","customer_segment",
                      "total_spend","food_dining","retail_shopping","travel_transport","healthcare",
                      "entertainment","utilities","grocery","hotel","fuel","other_spend",
                      "transaction_count","avg_txn_amount","top_category","top_merchant",
                      "mom_spend_change_pct","currency_code","created_at"]
    n = bulk_insert(cur, conn, "semantic_spend_metrics", sem_spend_cols, sem_spend_rows)
    print(f"  semantic_spend_metrics: {n} rows")

    # semantic_payment_status (from dp_pay_rows data)
    sem_pay_rows = []
    for row in dp_pay_rows:
        (aod,aid,cid,cc,le,fn,seg,smth,ddt,dtd,mnd,tdu,pamt,aout,pstat,ods,ob,consec,lf,iar,cur_c,cat) = row
        giro = int(random.random() < 0.4)
        method = random.choice(PAYMENT_METHODS[cc])
        sem_pay_rows.append((
            aod, aid, cid, cc, le, fn, seg,
            smth, ddt, dtd, mnd, tdu, pamt, aout,
            pstat, ods, ob, consec, lf, iar, giro, method, cur_c, cat,
        ))
    sem_pay_cols = ["as_of_date","account_id","customer_id","country_code","legal_entity",
                    "full_name","customer_segment","statement_month","due_date","days_to_due",
                    "minimum_due","total_due","amount_paid","amount_outstanding",
                    "payment_status","overdue_days","overdue_bucket","consecutive_late",
                    "late_fee","interest_at_risk","is_giro_enrolled","preferred_method",
                    "currency_code","created_at"]
    n = bulk_insert(cur, conn, "semantic_payment_status", sem_pay_cols, sem_pay_rows)
    print(f"  semantic_payment_status: {n} rows")

    # semantic_risk_metrics (from dp_risk_rows)
    sem_risk_rows = []
    for row in dp_risk_rows:
        (sd,cc,le,seg,tt,at,dt,ft,st,ta,fa,fr,dr,afs,hra,nfa,cur_c,cat) = row
        # derive delinquency bands from dp data
        d30  = round(random.uniform(0.02, 0.08), 4)
        d60  = round(d30 * random.uniform(0.3, 0.5), 4)
        d90  = round(d60 * random.uniform(0.2, 0.4), 4)
        d91p = round(d90 * random.uniform(0.1, 0.3), 4)
        sem_risk_rows.append((
            sd, cc, le, seg, tt, at, dt, ft, st, ta, fa, fr, dr, afs, d30, d60, d90, d91p, hra, cur_c, cat,
        ))
    sem_risk_cols = ["metric_date","country_code","legal_entity","customer_segment",
                     "total_txn","approved_txn","declined_txn","fraud_txn","suspicious_txn",
                     "total_amount","fraud_amount","fraud_rate","decline_rate","avg_fraud_score",
                     "delinquency_1_30","delinquency_31_60","delinquency_61_90","delinquency_91plus",
                     "high_risk_accounts","currency_code","created_at"]
    n = bulk_insert(cur, conn, "semantic_risk_metrics", sem_risk_cols, sem_risk_rows)
    print(f"  semantic_risk_metrics: {n} rows")

    # semantic_portfolio_kpis (from dp_port_rows)
    sem_port_rows = []
    for row in dp_port_rows:
        (km,cc,le,tc,ac,nc,chc,gp,cr,ta,aa,tcl,to,ts,sg,ab,au,fr,dr,dq,fp,npl,ii,cu,fx,cat) = row
        sem_port_rows.append((km,cc,le,tc,ac,nc,gp,cr,ts,sg,ab,au,fr,dr,dq,fp,npl,ii,cu,fx,cat))
    sem_port_cols = ["kpi_month","country_code","legal_entity","total_customers","active_customers",
                     "new_customers","customer_growth_pct","churn_rate",
                     "total_spend","spend_growth_pct","avg_balance","avg_utilization",
                     "fraud_rate","decline_rate","delinquency_rate","full_payment_rate","npl_rate",
                     "est_interest_income","currency_code","fx_rate_to_usd","created_at"]
    n = bulk_insert(cur, conn, "semantic_portfolio_kpis", sem_port_cols, sem_port_rows)
    print(f"  semantic_portfolio_kpis: {n} rows")

    # ── STEP 8: dp_transaction_enriched ───────────────────────────
    print("[9/9] Building enriched transactions...")
    dp_txn_enr_rows = []
    for cc, txns in all_txns.items():
        for t in txns:
            c = cust_lookup.get(t["customer_id"], {})
            dp_txn_enr_rows.append((
                t["transaction_id"], t["account_id"], t["customer_id"], cc,
                COUNTRY_CONF[cc]["legal_entity"],
                f"{c.get('first_name','')} {c.get('last_name','')}", c.get("_seg","MASS"),
                t["transaction_date"], t["transaction_date"].strftime("%Y-%m"),
                t["amount"], COUNTRY_CONF[cc]["currency"],
                t["transaction_type"], t["channel"],
                t["merchant_name"], t["merchant_category"], t["_merchant_risk"],
                t["auth_status"], t["decline_reason"],
                t["is_fraud"], t["fraud_score"], t["_is_suspicious"], t["is_international"],
                t["created_at"],
            ))
    dp_enr_cols = ["transaction_id","account_id","customer_id","country_code","legal_entity",
                   "full_name","customer_segment","transaction_date","txn_year_month",
                   "amount","currency_code","transaction_type","channel",
                   "merchant_name","merchant_category","merchant_risk_tier",
                   "auth_status","decline_reason","is_fraud","fraud_score",
                   "is_suspicious","is_international","created_at"]
    n = bulk_insert(cur, conn, "dp_transaction_enriched", dp_enr_cols, dp_txn_enr_rows)
    print(f"  dp_transaction_enriched: {n} rows")

    cur.close()
    conn.close()
    print("\n✓ All data generated and loaded successfully!")

    # Summary
    total_c = sum(cfg["n"] for cfg in COUNTRY_CONF.values())
    print(f"\nSummary:")
    ctry_summary = ', '.join(f'{cc}:{cfg["n"]}' for cc, cfg in COUNTRY_CONF.items())
    print(f"  Customers:    {total_c} ({ctry_summary})")
    print(f"  Merchants:    {sum(len(v) for v in MERCHANT_DATA.values())}")
    print(f"  Transactions: {sum(N_TXN_PER_COUNTRY for _ in COUNTRY_CONF)}")
    print(f"  Statements:   ~{total_c * 15} (15 months × accounts)")


if __name__ == "__main__":
    N_TXN_PER_COUNTRY = 3500
    main()
