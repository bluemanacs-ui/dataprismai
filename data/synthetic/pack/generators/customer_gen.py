"""
Customer generator – produces raw_customer rows.
"""
import random
import numpy as np
from datetime import date, datetime

from faker import Faker

_fake = Faker("en_US")

# ---------------------------------------------------------------------------
# Curated name pools for realism
# ---------------------------------------------------------------------------
_SG_MY_MALAY_M  = ["Ahmad","Muhammad","Rizal","Faizal","Hafiz","Iskandar",
                    "Kasim","Nordin","Omar","Rashid","Suhaimi","Azrul","Irfan","Fadzli"]
_SG_MY_MALAY_F  = ["Aisha","Farah","Hana","Izzati","Liyana","Nadia","Nurulain",
                    "Putri","Siti","Rohani","Wani","Zuraidah","Fatin","Hanis","Nurul"]
_SG_MY_MALAY_SN = ["Abdullah","Ahmad","Ismail","Hassan","Mohamed","Ibrahim",
                    "Othman","Rahman","Salleh","Yahya","Aziz","Bakar","Daud","Ghani"]
_SG_MY_CHN_M    = ["Wei","Ming","Jun","Hao","Jian","Kai","Cheng","Bin","Sheng","Yong","Feng"]
_SG_MY_CHN_F    = ["Ying","Hui","Mei","Fang","Xin","Lin","Jing","Na","Yan","Ling","Hong"]
_SG_MY_CHN_SN   = ["Tan","Lim","Lee","Ng","Wong","Chen","Goh","Chua","Koh",
                    "Teo","Ong","Ho","Tay","Lau","Yeo","Sim","Heng","Phua"]
_IN_M           = ["Arjun","Rahul","Vikram","Aditya","Rohit","Amit","Raj","Suresh",
                    "Pradeep","Nikhil","Vivek","Deepak","Sanjay","Karan","Rohan"]
_IN_F           = ["Priya","Neha","Anjali","Shreya","Kavya","Ananya","Pooja","Sunita",
                    "Meera","Lakshmi","Divya","Swati","Ritu","Asha","Sonal"]
_IN_SN          = ["Kumar","Singh","Sharma","Patel","Gupta","Nair","Reddy","Verma",
                    "Mehta","Joshi","Kapoor","Shah","Iyer","Pillai","Bhat","Rao"]


def _pick_name(country_code: str, gender: str):
    """Return (first_name, last_name) based on country."""
    if country_code == "IN":
        fn = random.choice(_IN_M if gender == "Male" else _IN_F)
        ln = random.choice(_IN_SN)
        return fn, ln
    # SG or MY – 45 % Malay, 55 % Chinese
    if random.random() < 0.45:
        fn = random.choice(_SG_MY_MALAY_M if gender == "Male" else _SG_MY_MALAY_F)
        bin_ = "bin" if gender == "Male" else "binte"
        ln = f"{bin_} {random.choice(_SG_MY_MALAY_SN)}"
    else:
        fn = random.choice(_SG_MY_CHN_M if gender == "Male" else _SG_MY_CHN_F)
        ln = random.choice(_SG_MY_CHN_SN)
    return fn, ln


def generate_customers(countries: dict, segments: list, seg_w: list,
                        risk_ratings: list, risk_w: list,
                        kyc_statuses: list, kyc_w: list,
                        occupations: list,
                        acq_channels: list, acq_w: list) -> list[dict]:
    """Return list of raw_customer dicts."""
    rows = []
    counter = 1

    for cc, cfg in countries.items():
        for _ in range(cfg["n_customers"]):
            cid = f"CUST_{counter:06d}"
            counter += 1

            gender  = random.choices(["Male", "Female"], weights=[0.52, 0.48])[0]
            fn, ln  = _pick_name(cc, gender)

            age  = random.randint(22, 68)
            dob  = date(2025 - age, random.randint(1, 12), random.randint(1, 28))

            segment     = random.choices(segments, weights=seg_w)[0]
            risk_rating = random.choices(risk_ratings, weights=risk_w)[0]
            kyc_status  = random.choices(kyc_statuses, weights=kyc_w)[0]

            monthly_inc = max(1000.0, np.random.normal(cfg["avg_monthly_income"], cfg["income_std"]))
            annual_inc  = round(monthly_inc * 12, 2)

            credit_score = {
                "low":    random.randint(680, 850),
                "medium": random.randint(560, 720),
                "high":   random.randint(300, 600),
            }[risk_rating]

            phone  = cfg["phone_prefix"] + str(random.randint(10000000, 99999999))
            ln_key = ln.replace("bin ", "").replace("binte ", "").replace(" ", "")
            email  = f"{fn.lower()}.{ln_key.lower()}{random.randint(10, 99)}@gmail.com"
            id_no  = f"{cid[:2]}{random.randint(1000000, 9999999)}{random.choice('ABCDEFGHJKLMNPRSTUWXYZ')}"

            city        = random.choice(cfg["cities"])
            postal_code = str(cfg["postal_prefix"]) + str(random.randint(10000, 99999))
            addr        = f"{random.randint(1, 200)} {_fake.street_name()}"

            created = datetime(
                random.randint(2021, 2024),
                random.randint(1, 12),
                random.randint(1, 28),
                random.randint(8, 18), 0, 0,
            )

            rows.append({
                "customer_id":        cid,
                "country_code":       cc,
                "legal_entity":       cfg["legal_entity"],
                "first_name":         fn,
                "last_name":          ln,
                "date_of_birth":      dob.strftime("%Y-%m-%d"),
                "gender":             gender,
                "email":              email,
                "phone":              phone,
                "address_line1":      addr,
                "city":               city,
                "state_province":     cfg["state_province"],
                "postal_code":        postal_code,
                "nationality":        cfg["nationality"],
                "id_type":            cfg["id_type"],
                "id_number":          id_no,
                "customer_segment":   segment,
                "kyc_status":         kyc_status,
                "risk_rating":        risk_rating,
                "annual_income":      annual_inc,
                "currency_code":      cfg["currency"],
                "occupation":         random.choice(occupations),
                "acquisition_channel": random.choices(acq_channels, weights=acq_w)[0],
                "credit_score":       credit_score,
                "is_deleted":         0,
                "created_at":         created.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at":         created.strftime("%Y-%m-%d %H:%M:%S"),
            })

    return rows
