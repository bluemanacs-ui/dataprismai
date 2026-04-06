"""
DataPrism Synthetic Data Program Pack – Configuration
All constants consumed by generators and pipelines.
"""

RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Country definitions
# ---------------------------------------------------------------------------
COUNTRIES = {
    "SG": {
        "currency": "SGD",
        "legal_entity": "SG_BANK",
        "fx_to_usd": 0.7400,
        "avg_monthly_income": 8000,
        "income_std": 3000,
        "cities": ["Singapore"],
        "state_province": "Singapore",
        "postal_prefix": "0",
        "phone_prefix": "+65-9",
        "id_type": "NRIC",
        "nationality": "Singaporean",
        "n_customers": 150,
        # Amount scale: 1 SGD = 1x
        "amount_scale": 1.0,
        # Minimum payment floor in local currency
        "min_payment_floor": 50.0,
    },
    "MY": {
        "currency": "MYR",
        "legal_entity": "MY_BANK",
        "fx_to_usd": 0.2150,
        "avg_monthly_income": 5000,
        "income_std": 2000,
        "cities": ["Kuala Lumpur", "Petaling Jaya", "Shah Alam", "Johor Bahru", "Penang", "Ipoh"],
        "state_province": "Selangor",
        "postal_prefix": "5",
        "phone_prefix": "+60-1",
        "id_type": "MyKad",
        "nationality": "Malaysian",
        "n_customers": 200,
        "amount_scale": 3.50,
        "min_payment_floor": 50.0,
    },
    "IN": {
        "currency": "INR",
        "legal_entity": "IN_BANK",
        "fx_to_usd": 0.0120,
        "avg_monthly_income": 80000,
        "income_std": 30000,
        "cities": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata"],
        "state_province": "Maharashtra",
        "postal_prefix": "4",
        "phone_prefix": "+91-9",
        "id_type": "PAN",
        "nationality": "Indian",
        "n_customers": 150,
        "amount_scale": 62.0,
        "min_payment_floor": 500.0,
    },
}

# ---------------------------------------------------------------------------
# Demographic distributions
# ---------------------------------------------------------------------------
SEGMENTS        = ["mass", "affluent", "premium"]
SEGMENT_WEIGHTS = [0.50,   0.35,       0.15]

RISK_RATINGS    = ["low",  "medium", "high"]
RISK_WEIGHTS    = [0.60,   0.30,     0.10]

KYC_STATUSES    = ["verified", "pending", "enhanced_dd"]
KYC_WEIGHTS     = [0.82,       0.12,      0.06]

GENDERS         = ["Male", "Female"]
GENDER_WEIGHTS  = [0.52,   0.48]

OCCUPATIONS = [
    "Software Engineer", "Doctor", "Accountant", "Teacher", "Lawyer",
    "Business Owner", "Sales Manager", "Marketing Executive", "Engineer",
    "Nurse", "Financial Analyst", "HR Manager", "Consultant", "Entrepreneur",
    "Civil Servant", "Retired", "Self-employed", "Banking Professional",
    "Operations Manager", "Data Analyst",
]

ACQUISITION_CHANNELS = ["branch", "online", "referral", "campaign", "partnership"]
ACQ_WEIGHTS          = [0.30,     0.35,     0.15,       0.12,       0.08]

# ---------------------------------------------------------------------------
# Product catalogue (per segment)
# ---------------------------------------------------------------------------
PRODUCTS = {
    "mass": [
        {"product_code": "CC_VISA_CLASSIC",  "product_name": "Visa Classic Card",
         "card_tier": "Classic",  "card_scheme": "VISA",       "interest_rate": 0.2400,
         "credit_mult_low": 1.5,  "credit_mult_high": 4.0},
        {"product_code": "CC_MC_STANDARD",   "product_name": "Mastercard Standard",
         "card_tier": "Standard", "card_scheme": "MASTERCARD", "interest_rate": 0.2200,
         "credit_mult_low": 1.5,  "credit_mult_high": 4.0},
    ],
    "affluent": [
        {"product_code": "CC_VISA_GOLD",     "product_name": "Visa Gold Card",
         "card_tier": "Gold",     "card_scheme": "VISA",       "interest_rate": 0.1800,
         "credit_mult_low": 4.0,  "credit_mult_high": 10.0},
        {"product_code": "CC_MC_GOLD",       "product_name": "Mastercard Gold",
         "card_tier": "Gold",     "card_scheme": "MASTERCARD", "interest_rate": 0.1800,
         "credit_mult_low": 4.0,  "credit_mult_high": 10.0},
    ],
    "premium": [
        {"product_code": "CC_VISA_PLATINUM", "product_name": "Visa Platinum Card",
         "card_tier": "Platinum", "card_scheme": "VISA",       "interest_rate": 0.1500,
         "credit_mult_low": 10.0, "credit_mult_high": 25.0},
        {"product_code": "CC_MC_WORLD",      "product_name": "Mastercard World",
         "card_tier": "World",    "card_scheme": "MASTERCARD", "interest_rate": 0.1500,
         "credit_mult_low": 10.0, "credit_mult_high": 25.0},
    ],
}

# ---------------------------------------------------------------------------
# Merchant categories (name, MCC, label, spend_weight)
# ---------------------------------------------------------------------------
MERCHANT_CATEGORIES = [
    ("food_dining",      "5812", "Food & Dining",       0.25),
    ("retail_shopping",  "5999", "Retail Shopping",     0.20),
    ("travel_transport", "4511", "Travel & Transport",  0.15),
    ("healthcare",       "8011", "Healthcare",          0.05),
    ("entertainment",    "7832", "Entertainment",       0.08),
    ("utilities",        "4900", "Utilities",           0.07),
    ("grocery",          "5411", "Grocery",             0.10),
    ("hotel",            "7011", "Hotel",               0.03),
    ("fuel",             "5541", "Fuel",                0.04),
    ("other",            "9999", "Other",               0.03),
]
CAT_NAMES   = [c[0] for c in MERCHANT_CATEGORIES]
CAT_WEIGHTS = [c[3] for c in MERCHANT_CATEGORIES]

# Amount ranges per category in SGD-equivalent; scaled × COUNTRIES[cc]["amount_scale"]
CATEGORY_AMOUNT_SGD = {
    "food_dining":      (5,   80),
    "retail_shopping":  (20,  600),
    "travel_transport": (10,  800),
    "healthcare":       (20,  500),
    "entertainment":    (8,   200),
    "utilities":        (50,  350),
    "grocery":          (20,  300),
    "hotel":            (100, 1000),
    "fuel":             (30,  150),
    "other":            (5,   150),
}

# ---------------------------------------------------------------------------
# Transaction generation parameters
# ---------------------------------------------------------------------------
SEGMENT_TXN_FREQ = {"mass": 5, "affluent": 12, "premium": 25}  # Poisson λ/month

# Auth outcomes
APPROVE_RATES = {"low": 0.96, "medium": 0.93, "high": 0.88}  # by risk_rating
FRAUD_RATES   = {"low": 0.003, "medium": 0.012, "high": 0.040}

DECLINE_REASONS = [
    "insufficient_funds", "risk_block", "card_expired",
    "international_block", "daily_limit_exceeded", "merchant_blocked",
]

CHANNELS  = ["online", "pos", "contactless", "atm", "mobile"]
CHAN_W    = [0.35,      0.30,  0.20,          0.05,  0.10]

TXN_TYPES = ["purchase", "purchase", "purchase", "refund", "cash_advance"]
TXN_W     = [0.80,       0.10,       0.05,       0.03,     0.02]

# ---------------------------------------------------------------------------
# Payment behaviour profiles (by risk_rating)
# ---------------------------------------------------------------------------
PAYMENT_PROFILES = {
    "low":    {"full": 0.55, "partial": 0.30, "minimum": 0.10, "late": 0.05},
    "medium": {"full": 0.35, "partial": 0.35, "minimum": 0.20, "late": 0.10},
    "high":   {"full": 0.15, "partial": 0.30, "minimum": 0.25, "late": 0.30},
}

# ---------------------------------------------------------------------------
# Date range
# ---------------------------------------------------------------------------
DATA_MONTHS = [
    "2025-01", "2025-02", "2025-03", "2025-04",
    "2025-05", "2025-06", "2025-07", "2025-08",
    "2025-09", "2025-10", "2025-11", "2025-12",
]
AS_OF_DATE   = "2025-12-31"
CREATED_AT   = "2025-12-31 23:59:59"
STARROCKS_DB = "cc_analytics"
