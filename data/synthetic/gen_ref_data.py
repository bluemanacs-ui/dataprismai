"""
DataPrismAI — Reference / configuration data shared across all generator modules.
Import this from gen_customers.py, gen_accounts.py, etc.
"""
from datetime import date, datetime
from decimal import Decimal

random_seed = 42

# ── Date range ────────────────────────────────────────────────────────────────
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2026, 3, 31)
TODAY      = date(2026, 4, 7)
NOW        = datetime(2026, 4, 7, 10, 0, 0)

# ── Country configuration ─────────────────────────────────────────────────────
COUNTRY_CONF = {
    "SG": {
        "legal_entity": "SG_BANK", "currency": "SGD", "n_customers": 200,
        "cities": ["Singapore", "Jurong East", "Tampines", "Bishan", "Clementi",
                   "Bedok", "Punggol", "Woodlands", "Buona Vista", "Orchard"],
        "states": ["Central Region", "East Region", "North Region", "West Region", "North-East Region"],
        "m_names": ["Wei", "Ahmad", "Brendan", "Marcus", "Kai", "Jun", "Ethan", "Leon",
                    "Ryan", "Aaron", "Daryl", "Ivan", "Ravi", "Vijay", "Hari"],
        "f_names": ["Priya", "Siti", "Emily", "Grace", "Cheryl", "Mei", "Nadia", "Sharon",
                    "Karen", "Nicole", "Jasmine", "Belle", "Deepa", "Kavya", "Aisyah"],
        "surnames": ["Tan", "Lee", "Lim", "Wong", "Ng", "Ridzwan", "Kumar", "Singh",
                     "Ong", "Koh", "Ho", "Chua", "Chan", "Goh", "Teo", "Patel"],
        "id_type": "NRIC",
        "phone_prefix": "+65",
        "postal_format": "6-digit",
        "credit_limits": {
            "MASS":     (3000,   10000),
            "AFFLUENT": (10000,  50000),
            "PRIORITY": (50000,  150000),
            "HNW":      (150000, 500000),
        },
        "incomes": {
            "MASS":     (36000,  80000),
            "AFFLUENT": (80000,  250000),
            "PRIORITY": (250000, 700000),
            "HNW":      (700000, 5000000),
        },
        "avg_cc_txn": 120, "avg_deposit_bal": 25000, "avg_loan": 80000,
        "fx_to_usd": Decimal("0.748"),
    },
    "MY": {
        "legal_entity": "MY_BANK", "currency": "MYR", "n_customers": 200,
        "cities": ["Kuala Lumpur", "Petaling Jaya", "Penang", "Johor Bahru",
                   "Subang Jaya", "Shah Alam", "Cyberjaya", "Ipoh", "Kota Kinabalu", "Kuching"],
        "states": ["Kuala Lumpur", "Selangor", "Penang", "Johor", "Sabah", "Sarawak", "Perak"],
        "m_names": ["Raj", "David", "Ahmad", "Chong", "Muthu", "Faisal", "Darren",
                    "Jason", "Kevin", "Daniel", "Azman", "Hakim", "Weng", "Bala"],
        "f_names": ["Siti", "Amy", "Priya", "Mei Ling", "Nora", "Jasmine", "Kelly",
                    "Sarah", "Kavya", "Diana", "Aishah", "Farah", "Lim Wei", "Rani"],
        "surnames": ["Kumar", "Lim", "Abdullah", "Tan", "Krishnan", "Yong", "Hassan",
                     "Singh", "Ng", "Chan", "Ibrahim", "Rahman", "Chew", "Yin"],
        "id_type": "MYKAD",
        "phone_prefix": "+60",
        "postal_format": "5-digit",
        "credit_limits": {
            "MASS":     (5000,   15000),
            "AFFLUENT": (15000,  80000),
            "PRIORITY": (80000,  300000),
            "HNW":      (300000, 1000000),
        },
        "incomes": {
            "MASS":     (24000,  72000),
            "AFFLUENT": (72000,  240000),
            "PRIORITY": (240000, 700000),
            "HNW":      (700000, 5000000),
        },
        "avg_cc_txn": 200, "avg_deposit_bal": 15000, "avg_loan": 120000,
        "fx_to_usd": Decimal("0.223"),
    },
    "IN": {
        "legal_entity": "IN_BANK", "currency": "INR", "n_customers": 200,
        "cities": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
                   "Pune", "Ahmedabad", "Kolkata", "Jaipur", "Surat"],
        "states": ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana",
                   "Gujarat", "West Bengal", "Rajasthan"],
        "m_names": ["Ravi", "Vikram", "Arjun", "Rohit", "Suresh", "Pradeep", "Nitin",
                    "Arun", "Sanjay", "Mahesh", "Rajesh", "Dinesh", "Kiran", "Anand"],
        "f_names": ["Anita", "Priya", "Deepa", "Kavya", "Sunita", "Rekha", "Nisha",
                    "Pooja", "Divya", "Smita", "Geeta", "Meena", "Sneha", "Ritu"],
        "surnames": ["Sharma", "Patel", "Kumar", "Singh", "Gupta", "Nair", "Iyer",
                     "Mehta", "Desai", "Joshi", "Verma", "Pillai", "Rao", "Bose"],
        "id_type": "AADHAR",
        "phone_prefix": "+91",
        "postal_format": "6-digit",
        "credit_limits": {
            "MASS":     (50000,   200000),
            "AFFLUENT": (200000,  800000),
            "PRIORITY": (800000,  3000000),
            "HNW":      (3000000, 15000000),
        },
        "incomes": {
            "MASS":     (240000,  800000),
            "AFFLUENT": (800000,  3000000),
            "PRIORITY": (3000000, 10000000),
            "HNW":      (10000000, 50000000),
        },
        "avg_cc_txn": 2000, "avg_deposit_bal": 150000, "avg_loan": 1500000,
        "fx_to_usd": Decimal("0.012"),
    },
}

SEGMENT_POOL = ["MASS"] * 55 + ["AFFLUENT"] * 28 + ["PRIORITY"] * 13 + ["HNW"] * 4

OCCUPATIONS = [
    "Software Engineer", "Doctor", "Teacher", "Business Owner", "Senior Manager",
    "Accountant", "Lawyer", "Civil Engineer", "Nurse", "Management Consultant",
    "IT Professional", "Investment Banker", "Entrepreneur", "Government Officer",
    "Freelance Designer", "Architect", "Executive Chef", "Pharmacist",
    "Data Scientist", "Marketing Director", "Financial Analyst", "HR Manager",
    "Operations Manager", "Product Manager", "Sales Director",
]

PAYMENT_METHODS = {
    "SG": ["GIRO", "PAYNOW", "BANK_TRANSFER", "DEBIT_CARD", "INTERNET_BANKING"],
    "MY": ["BANK_TRANSFER", "FPX", "INTERNET_BANKING", "CHEQUE", "DEBIT_CARD"],
    "IN": ["UPI", "NEFT", "IMPS", "NETBANKING", "DEBIT_CARD"],
}

CHANNELS_CC   = ["POS"] * 3 + ["POS"] * 2 + ["ONLINE"] * 3 + ["CONTACTLESS"] * 4 + ["MOBILE"] * 2 + ["ATM"]
TXN_TYPES_CC  = ["PURCHASE"] * 8 + ["REFUND"] + ["WITHDRAWAL"] + ["FEE"]
AUTH_STATUSES = ["APPROVED"] * 85 + ["DECLINED"] * 10 + ["REVERSED"] * 5
DECLINE_REASONS = [
    "INSUFFICIENT_FUNDS", "LIMIT_EXCEEDED", "FRAUD_SUSPECT",
    "INVALID_CVV", "CARD_BLOCKED", "EXPIRED_CARD", "DO_NOT_HONOUR",
]

CARD_SCHEMES = {
    "MASS":     ["VISA", "MASTERCARD"],
    "AFFLUENT": ["VISA", "MASTERCARD"],
    "PRIORITY": ["VISA_SIGNATURE", "MASTERCARD_WORLD"],
    "HNW":      ["VISA_INFINITE", "MASTERCARD_WORLD_ELITE", "AMEX_PLATINUM"],
}

MERCHANT_DATA = {
    "SG": [
        # (merchant_id, name, category, mcc, is_online, risk_tier, city)
        ("SG_M_001", "Crystal Jade Restaurant",    "FOOD_DINING",        "5812", False, "LOW",    "Singapore"),
        ("SG_M_002", "NTUC FairPrice",              "GROCERY",            "5411", False, "LOW",    "Singapore"),
        ("SG_M_003", "Singapore Airlines",          "TRAVEL_TRANSPORT",   "4511", True,  "LOW",    "Singapore"),
        ("SG_M_004", "Grab Singapore",              "TRAVEL_TRANSPORT",   "7299", True,  "LOW",    "Singapore"),
        ("SG_M_005", "Raffles Medical Group",       "HEALTHCARE",         "8099", False, "LOW",    "Singapore"),
        ("SG_M_006", "Golden Village Cinemas",      "ENTERTAINMENT",      "7832", False, "LOW",    "Singapore"),
        ("SG_M_007", "SP Services",                 "UTILITIES",          "4900", True,  "LOW",    "Singapore"),
        ("SG_M_008", "Marina Bay Sands",            "HOTEL_LODGING",      "7011", False, "LOW",    "Singapore"),
        ("SG_M_009", "Shell Singapore",             "FUEL_PETROL",        "5541", False, "LOW",    "Singapore"),
        ("SG_M_010", "Uniqlo Singapore",            "RETAIL_SHOPPING",    "5999", False, "LOW",    "Orchard"),
        ("SG_M_011", "Din Tai Fung",                "FOOD_DINING",        "5812", False, "LOW",    "Orchard"),
        ("SG_M_012", "Cold Storage",                "GROCERY",            "5411", False, "LOW",    "Singapore"),
        ("SG_M_013", "Lazada Singapore",            "RETAIL_SHOPPING",    "5999", True,  "MEDIUM", "Singapore"),
        ("SG_M_014", "ComfortDelGro Taxi",          "TRAVEL_TRANSPORT",   "4121", False, "LOW",    "Singapore"),
        ("SG_M_015", "Singtel",                     "UTILITIES",          "4813", True,  "LOW",    "Singapore"),
        ("SG_M_016", "Ion Orchard Mall",            "RETAIL_SHOPPING",    "5311", False, "LOW",    "Orchard"),
        ("SG_M_017", "Grand Hyatt Singapore",       "HOTEL_LODGING",      "7011", False, "LOW",    "Orchard"),
        ("SG_M_018", "Caltex Singapore",            "FUEL_PETROL",        "5541", False, "LOW",    "Singapore"),
        ("SG_M_019", "Kaplan Singapore",            "EDUCATION",          "8299", True,  "LOW",    "Singapore"),
        ("SG_M_020", "Amazon Singapore",            "RETAIL_SHOPPING",    "5999", True,  "LOW",    "Singapore"),
        ("SG_M_021", "Guardian Pharmacy",           "HEALTHCARE",         "5912", False, "LOW",    "Singapore"),
        ("SG_M_022", "IKEA Singapore",              "RETAIL_SHOPPING",    "5712", False, "LOW",    "Tampines"),
        ("SG_M_023", "Food Republic",               "FOOD_DINING",        "5812", False, "LOW",    "Orchard"),
        ("SG_M_024", "Starbucks Singapore",         "FOOD_DINING",        "5814", False, "LOW",    "Singapore"),
        ("SG_M_025", "Capital Tower Carpark",       "TRAVEL_TRANSPORT",   "7523", False, "LOW",    "Singapore"),
    ],
    "MY": [
        ("MY_M_001", "PappaRich",                   "FOOD_DINING",        "5812", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_002", "Giant Hypermarket",           "GROCERY",            "5411", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_003", "AirAsia",                     "TRAVEL_TRANSPORT",   "4511", True,  "LOW",    "Kuala Lumpur"),
        ("MY_M_004", "Grab Malaysia",               "TRAVEL_TRANSPORT",   "7299", True,  "LOW",    "Kuala Lumpur"),
        ("MY_M_005", "Pantai Hospital KL",          "HEALTHCARE",         "8062", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_006", "GSC Cinemas",                 "ENTERTAINMENT",      "7832", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_007", "Telekom Malaysia",            "UTILITIES",          "4813", True,  "LOW",    "Kuala Lumpur"),
        ("MY_M_008", "Mandarin Oriental KL",        "HOTEL_LODGING",      "7011", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_009", "Petronas Station",            "FUEL_PETROL",        "5541", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_010", "Pavilion KL Mall",            "RETAIL_SHOPPING",    "5311", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_011", "OldTown White Coffee",        "FOOD_DINING",        "5812", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_012", "Village Grocer",              "GROCERY",            "5411", False, "LOW",    "Petaling Jaya"),
        ("MY_M_013", "Shopee Malaysia",             "RETAIL_SHOPPING",    "5999", True,  "MEDIUM", "Kuala Lumpur"),
        ("MY_M_014", "Rapid KL Transit",            "TRAVEL_TRANSPORT",   "4111", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_015", "Maxis Berhad",                "UTILITIES",          "4813", True,  "LOW",    "Kuala Lumpur"),
        ("MY_M_016", "AEON Mall",                   "RETAIL_SHOPPING",    "5311", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_017", "JW Marriott KL",              "HOTEL_LODGING",      "7011", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_018", "Petron Malaysia",             "FUEL_PETROL",        "5541", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_019", "Taylor's University",         "EDUCATION",          "8299", False, "LOW",    "Subang Jaya"),
        ("MY_M_020", "Lazada Malaysia",             "RETAIL_SHOPPING",    "5999", True,  "LOW",    "Kuala Lumpur"),
        ("MY_M_021", "Watson's Malaysia",           "HEALTHCARE",         "5912", False, "LOW",    "Penang"),
        ("MY_M_022", "McDonald's Malaysia",         "FOOD_DINING",        "5814", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_023", "Caring Pharmacy",             "HEALTHCARE",         "5912", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_024", "MyNews Holdings",             "RETAIL_SHOPPING",    "5999", False, "LOW",    "Kuala Lumpur"),
        ("MY_M_025", "Shell Malaysia",              "FUEL_PETROL",        "5541", False, "LOW",    "Johor Bahru"),
    ],
    "IN": [
        ("IN_M_001", "Swiggy",                      "FOOD_DINING",        "5812", True,  "LOW",    "Mumbai"),
        ("IN_M_002", "BigBasket",                   "GROCERY",            "5411", True,  "LOW",    "Bangalore"),
        ("IN_M_003", "IndiGo Airlines",             "TRAVEL_TRANSPORT",   "4511", True,  "LOW",    "Delhi"),
        ("IN_M_004", "Ola Cabs",                    "TRAVEL_TRANSPORT",   "7299", True,  "LOW",    "Mumbai"),
        ("IN_M_005", "Apollo Hospitals",            "HEALTHCARE",         "8062", False, "LOW",    "Chennai"),
        ("IN_M_006", "PVR Cinemas",                 "ENTERTAINMENT",      "7832", False, "LOW",    "Mumbai"),
        ("IN_M_007", "Reliance Jio",                "UTILITIES",          "4813", True,  "LOW",    "Mumbai"),
        ("IN_M_008", "Taj Hotels",                  "HOTEL_LODGING",      "7011", False, "LOW",    "Mumbai"),
        ("IN_M_009", "Indian Oil Corporation",      "FUEL_PETROL",        "5541", False, "LOW",    "Delhi"),
        ("IN_M_010", "Flipkart",                    "RETAIL_SHOPPING",    "5999", True,  "MEDIUM", "Bangalore"),
        ("IN_M_011", "Zomato",                      "FOOD_DINING",        "5812", True,  "LOW",    "Delhi"),
        ("IN_M_012", "DMart",                       "GROCERY",            "5411", False, "LOW",    "Mumbai"),
        ("IN_M_013", "Amazon India",                "RETAIL_SHOPPING",    "5999", True,  "MEDIUM", "Bangalore"),
        ("IN_M_014", "IRCTC Rail",                  "TRAVEL_TRANSPORT",   "4111", True,  "LOW",    "Delhi"),
        ("IN_M_015", "Airtel",                      "UTILITIES",          "4813", True,  "LOW",    "Delhi"),
        ("IN_M_016", "Myntra",                      "RETAIL_SHOPPING",    "5311", True,  "LOW",    "Bangalore"),
        ("IN_M_017", "ITC Maurya Hotel",            "HOTEL_LODGING",      "7011", False, "LOW",    "Delhi"),
        ("IN_M_018", "HPCL Fuel Station",           "FUEL_PETROL",        "5541", False, "LOW",    "Chennai"),
        ("IN_M_019", "Byju's Learning",             "EDUCATION",          "8299", True,  "LOW",    "Bangalore"),
        ("IN_M_020", "Nykaa Beauty",                "RETAIL_SHOPPING",    "5999", True,  "LOW",    "Mumbai"),
        ("IN_M_021", "Apollo Pharmacy",             "HEALTHCARE",         "5912", False, "LOW",    "Chennai"),
        ("IN_M_022", "Domino's India",              "FOOD_DINING",        "5814", False, "LOW",    "Mumbai"),
        ("IN_M_023", "MakeMyTrip",                  "TRAVEL_TRANSPORT",   "4722", True,  "LOW",    "Delhi"),
        ("IN_M_024", "Tanishq Jewellery",           "RETAIL_SHOPPING",    "5944", False, "LOW",    "Mumbai"),
        ("IN_M_025", "HP Petrol Bunk",              "FUEL_PETROL",        "5541", False, "LOW",    "Hyderabad"),
    ],
}

# Deposit products per country
DEPOSIT_PRODUCTS = {
    "SG": [
        # (product_code, product_name, type, category, rate_range)
        ("SG_SAV_001", "eSavings Account",         "SAVINGS",       "SAVINGS",      (0.0020, 0.0080)),
        ("SG_SAV_002", "MySavings Plus",           "SAVINGS_PLUS",  "SAVINGS",      (0.0050, 0.0200)),
        ("SG_CUR_001", "BusinessCurrent Account",  "CURRENT",       "CURRENT",      (0.0000, 0.0010)),
        ("SG_CUR_002", "PersonalCurrent Account",  "CURRENT_PLUS",  "CURRENT",      (0.0005, 0.0015)),
        ("SG_FD_001",  "Fixed Deposit 3M",         "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0320, 0.0380)),
        ("SG_FD_002",  "Fixed Deposit 6M",         "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0360, 0.0420)),
        ("SG_FD_003",  "Fixed Deposit 12M",        "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0380, 0.0450)),
    ],
    "MY": [
        ("MY_SAV_001", "Simpanan Biasa",            "SAVINGS",       "SAVINGS",      (0.0020, 0.0060)),
        ("MY_SAV_002", "Simpanan Premium",          "SAVINGS_PLUS",  "SAVINGS",      (0.0040, 0.0150)),
        ("MY_CUR_001", "Current Account",           "CURRENT",       "CURRENT",      (0.0000, 0.0008)),
        ("MY_CUR_002", "Current Account Plus",      "CURRENT_PLUS",  "CURRENT",      (0.0005, 0.0012)),
        ("MY_FD_001",  "Fixed Deposit 3M",          "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0280, 0.0350)),
        ("MY_FD_002",  "Fixed Deposit 6M",          "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0310, 0.0380)),
        ("MY_FD_003",  "Fixed Deposit 12M",         "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0340, 0.0410)),
    ],
    "IN": [
        ("IN_SAV_001", "Savings Account",           "SAVINGS",       "SAVINGS",      (0.0250, 0.0400)),
        ("IN_SAV_002", "Savings Max",               "SAVINGS_PLUS",  "SAVINGS",      (0.0350, 0.0500)),
        ("IN_CUR_001", "Current Account",           "CURRENT",       "CURRENT",      (0.0000, 0.0000)),
        ("IN_CUR_002", "Current Plus Account",      "CURRENT_PLUS",  "CURRENT",      (0.0000, 0.0050)),
        ("IN_FD_001",  "Fixed Deposit 3M",          "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0575, 0.0650)),
        ("IN_FD_002",  "Fixed Deposit 6M",          "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0625, 0.0700)),
        ("IN_FD_003",  "Fixed Deposit 12M",         "FIXED_DEPOSIT", "TERM_DEPOSIT", (0.0650, 0.0725)),
    ],
}

# Loan products per country
LOAN_PRODUCTS = {
    "SG": [
        # (product_code, product_name, loan_type, category, rate_range, max_term_months, collateral)
        ("SG_PL_001", "Personal Loan",          "PERSONAL",   "UNSECURED", (0.0388, 0.0799), 60,  "NONE"),
        ("SG_HL_001", "Home Loan (HDB)",        "HOME",       "SECURED",   (0.0268, 0.0350), 300, "PROPERTY"),
        ("SG_HL_002", "Home Loan (Private)",    "HOME",       "SECURED",   (0.0290, 0.0380), 300, "PROPERTY"),
        ("SG_AL_001", "Car Loan",               "AUTO",       "SECURED",   (0.0245, 0.0350), 84,  "VEHICLE"),
        ("SG_BL_001", "SME Business Loan",      "BUSINESS",   "UNSECURED", (0.0450, 0.0899), 60,  "NONE"),
        ("SG_EL_001", "Study Loan",             "EDUCATION",  "UNSECURED", (0.0425, 0.0550), 120, "NONE"),
    ],
    "MY": [
        ("MY_PL_001", "Personal Financing-i",   "PERSONAL",   "UNSECURED", (0.0399, 0.0699), 60,  "NONE"),
        ("MY_HL_001", "Home Financing",         "HOME",       "SECURED",   (0.0320, 0.0420), 360, "PROPERTY"),
        ("MY_AL_001", "Hire Purchase",          "AUTO",       "SECURED",   (0.0275, 0.0380), 84,  "VEHICLE"),
        ("MY_BL_001", "SME Financing",          "BUSINESS",   "UNSECURED", (0.0480, 0.0899), 60,  "NONE"),
        ("MY_EL_001", "Education Financing",    "EDUCATION",  "UNSECURED", (0.0400, 0.0599), 120, "NONE"),
        ("MY_RL_001", "Renovation Loan",        "RENOVATION", "UNSECURED", (0.0350, 0.0550), 60,  "NONE"),
    ],
    "IN": [
        ("IN_PL_001", "Personal Loan",          "PERSONAL",   "UNSECURED", (0.1050, 0.1800), 60,  "NONE"),
        ("IN_HL_001", "Home Loan",              "HOME",       "SECURED",   (0.0825, 0.0950), 300, "PROPERTY"),
        ("IN_AL_001", "Auto Loan (Car)",        "AUTO",       "SECURED",   (0.0875, 0.1050), 84,  "VEHICLE"),
        ("IN_BL_001", "Business Loan (MSME)",   "BUSINESS",   "UNSECURED", (0.1100, 0.1650), 60,  "NONE"),
        ("IN_EL_001", "Education Loan",         "EDUCATION",  "SECURED",   (0.0850, 0.1050), 120, "NONE"),
        ("IN_GL_001", "Gold Loan",              "PERSONAL",   "SECURED",   (0.0750, 0.0950), 24,  "GOLD"),
    ],
}

FD_TENORS = [3, 6, 12, 24, 36]  # months

DEPOSIT_TXN_TYPES = [
    "SALARY_CREDIT", "TRANSFER_IN", "TRANSFER_OUT", "ATM_WITHDRAWAL",
    "UPI_PAYMENT", "NEFT", "IMPS", "PAYNOW", "FPS", "INTEREST_CREDIT",
    "STANDING_ORDER", "CASH_DEPOSIT", "UTILITY_PAYMENT", "FD_ROLLOVER",
    "FD_MATURITY", "FEE_DEBIT", "GIRO", "CHEQUE",
]

DEPOSIT_CHANNELS = ["MOBILE", "INTERNET", "ATM", "BRANCH", "STANDING_ORDER", "INTER_BANK", "SYSTEM"]

LOAN_PURPOSES = {
    "PERSONAL":   ["Debt Consolidation", "Medical Expenses", "Wedding", "Home Renovation",
                   "Vacation", "Electronics Purchase", "Emergency Fund", "Other"],
    "HOME":       ["Property Purchase", "Construction", "Home Improvement", "Balance Transfer"],
    "AUTO":       ["New Car Purchase", "Used Car Purchase", "Commercial Vehicle"],
    "BUSINESS":   ["Working Capital", "Equipment Purchase", "Business Expansion",
                   "Invoice Financing", "Trade Finance"],
    "EDUCATION":  ["Undergraduate Studies", "Postgraduate Studies", "Professional Course",
                   "Overseas Education"],
    "RENOVATION": ["Kitchen Renovation", "Bathroom Upgrade", "Full Renovation", "Furniture"],
}
