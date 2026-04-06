"""
Merchant generator – curated lists per country + 5 global online merchants.
"""
import random
from datetime import datetime

# (name, category, mcc, business_type, is_online, risk_tier)
_MERCHANTS_SG = [
    ("NTUC FairPrice",          "grocery",          "5411", "supermarket",   0, "low"),
    ("Cold Storage",            "grocery",          "5411", "supermarket",   0, "low"),
    ("Sheng Siong",             "grocery",          "5411", "supermarket",   0, "low"),
    ("Grab Food SG",            "food_dining",      "5812", "food_delivery", 1, "low"),
    ("McDonald's Singapore",    "food_dining",      "5812", "fast_food",     0, "low"),
    ("Ya Kun Kaya Toast",       "food_dining",      "5812", "cafe",          0, "low"),
    ("TCC Coffee",              "food_dining",      "5812", "cafe",          0, "low"),
    ("Bengawan Solo",           "food_dining",      "5812", "bakery",        0, "low"),
    ("Old Chang Kee",           "food_dining",      "5812", "fast_food",     0, "low"),
    ("BreadTalk",               "food_dining",      "5812", "bakery",        0, "low"),
    ("Grab Transport SG",       "travel_transport", "4111", "ride_hailing",  1, "low"),
    ("ComfortDelGro",           "travel_transport", "4111", "taxi",          0, "low"),
    ("Singapore Airlines",      "travel_transport", "4511", "airline",       1, "low"),
    ("Scoot",                   "travel_transport", "4511", "airline",       1, "low"),
    ("SP Group",                "utilities",        "4900", "utility",       0, "low"),
    ("Singtel",                 "utilities",        "4814", "telco",         0, "low"),
    ("StarHub",                 "utilities",        "4814", "telco",         0, "low"),
    ("Raffles Medical Group",   "healthcare",       "8011", "clinic",        0, "low"),
    ("Mount Elizabeth Hospital","healthcare",       "8011", "hospital",      0, "low"),
    ("Parkway Health",          "healthcare",       "8011", "clinic",        0, "low"),
    ("Golden Village",          "entertainment",    "7832", "cinema",        0, "low"),
    ("Shaw Theatres",           "entertainment",    "7832", "cinema",        0, "low"),
    ("Charles & Keith",         "retail_shopping",  "5999", "fashion",       0, "low"),
    ("Uniqlo Singapore",        "retail_shopping",  "5999", "fashion",       0, "low"),
    ("ZALORA Singapore",        "retail_shopping",  "5999", "fashion",       1, "low"),
    ("Sephora Singapore",       "retail_shopping",  "5999", "beauty",        0, "low"),
    ("Shell Singapore",         "fuel",             "5541", "petrol_station",0, "low"),
    ("SPC Petrol",              "fuel",             "5541", "petrol_station",0, "low"),
    ("Marriott Singapore",      "hotel",            "7011", "hotel",         0, "low"),
    ("Pan Pacific Hotel",       "hotel",            "7011", "hotel",         0, "low"),
]

_MERCHANTS_MY = [
    ("Giant Malaysia",          "grocery",          "5411", "supermarket",   0, "low"),
    ("Jaya Grocer",             "grocery",          "5411", "supermarket",   0, "low"),
    ("Mydin",                   "grocery",          "5411", "supermarket",   0, "low"),
    ("Grab Food MY",            "food_dining",      "5812", "food_delivery", 1, "low"),
    ("McDonald's Malaysia",     "food_dining",      "5812", "fast_food",     0, "low"),
    ("Old Town White Coffee",   "food_dining",      "5812", "cafe",          0, "low"),
    ("Rotiboy",                 "food_dining",      "5812", "bakery",        0, "low"),
    ("Jollibee Malaysia",       "food_dining",      "5812", "fast_food",     0, "low"),
    ("Grab Transport MY",       "travel_transport", "4111", "ride_hailing",  1, "low"),
    ("AirAsia",                 "travel_transport", "4511", "airline",       1, "low"),
    ("Malaysia Airlines",       "travel_transport", "4511", "airline",       1, "low"),
    ("Rapid KL",                "travel_transport", "4111", "public_transit",0, "low"),
    ("Tenaga Nasional",         "utilities",        "4900", "utility",       0, "low"),
    ("Maxis",                   "utilities",        "4814", "telco",         0, "low"),
    ("Celcom",                  "utilities",        "4814", "telco",         0, "low"),
    ("KPJ Healthcare",          "healthcare",       "8011", "hospital",      0, "low"),
    ("Pantai Hospital",         "healthcare",       "8011", "hospital",      0, "low"),
    ("Columbia Asia",           "healthcare",       "8011", "clinic",        0, "low"),
    ("TGV Cinemas",             "entertainment",    "7832", "cinema",        0, "low"),
    ("GSC Cinemas",             "entertainment",    "7832", "cinema",        0, "low"),
    ("Padini",                  "retail_shopping",  "5999", "fashion",       0, "low"),
    ("Parkson",                 "retail_shopping",  "5999", "department",    0, "low"),
    ("ZALORA Malaysia",         "retail_shopping",  "5999", "fashion",       1, "low"),
    ("H&M Malaysia",            "retail_shopping",  "5999", "fashion",       0, "low"),
    ("Petronas Petrol",         "fuel",             "5541", "petrol_station",0, "low"),
    ("Shell Malaysia",          "fuel",             "5541", "petrol_station",0, "low"),
    ("Hilton Kuala Lumpur",     "hotel",            "7011", "hotel",         0, "low"),
    ("Sunway Hotel",            "hotel",            "7011", "hotel",         0, "low"),
    ("Lazada Malaysia",         "retail_shopping",  "5999", "ecommerce",     1, "medium"),
    ("Shopee Malaysia",         "retail_shopping",  "5999", "ecommerce",     1, "medium"),
]

_MERCHANTS_IN = [
    ("Reliance Fresh",          "grocery",          "5411", "supermarket",   0, "low"),
    ("Big Bazaar",              "grocery",          "5411", "supermarket",   0, "low"),
    ("DMart",                   "grocery",          "5411", "supermarket",   0, "low"),
    ("Swiggy",                  "food_dining",      "5812", "food_delivery", 1, "low"),
    ("Zomato",                  "food_dining",      "5812", "food_delivery", 1, "low"),
    ("McDonald's India",        "food_dining",      "5812", "fast_food",     0, "low"),
    ("Cafe Coffee Day",         "food_dining",      "5812", "cafe",          0, "low"),
    ("Haldiram's",              "food_dining",      "5812", "snacks",        0, "low"),
    ("Ola",                     "travel_transport", "4111", "ride_hailing",  1, "low"),
    ("Rapido",                  "travel_transport", "4111", "ride_hailing",  1, "low"),
    ("IndiGo",                  "travel_transport", "4511", "airline",       1, "low"),
    ("Air India",               "travel_transport", "4511", "airline",       1, "low"),
    ("IRCTC",                   "travel_transport", "4112", "rail",          1, "low"),
    ("BSES Delhi",              "utilities",        "4900", "utility",       0, "low"),
    ("BESCOM",                  "utilities",        "4900", "utility",       0, "low"),
    ("Airtel",                  "utilities",        "4814", "telco",         0, "low"),
    ("Jio",                     "utilities",        "4814", "telco",         1, "low"),
    ("Apollo Hospitals",        "healthcare",       "8011", "hospital",      0, "low"),
    ("Fortis Healthcare",       "healthcare",       "8011", "hospital",      0, "low"),
    ("Max Healthcare",          "healthcare",       "8011", "clinic",        0, "low"),
    ("PVR Cinemas",             "entertainment",    "7832", "cinema",        0, "low"),
    ("INOX Leisure",            "entertainment",    "7832", "cinema",        0, "low"),
    ("Myntra",                  "retail_shopping",  "5999", "fashion",       1, "low"),
    ("Flipkart",                "retail_shopping",  "5999", "ecommerce",     1, "low"),
    ("H&M India",               "retail_shopping",  "5999", "fashion",       0, "low"),
    ("Nykaa",                   "retail_shopping",  "5999", "beauty",        1, "medium"),
    ("Indian Oil",              "fuel",             "5541", "petrol_station",0, "low"),
    ("HPCL",                    "fuel",             "5541", "petrol_station",0, "low"),
    ("OYO Hotels",              "hotel",            "7011", "hotel",         0, "medium"),
    ("Taj Hotels",              "hotel",            "7011", "hotel",         0, "low"),
]

_GLOBAL_ONLINE = [
    ("Amazon",          "retail_shopping",  "5999", "ecommerce",      1, "low"),
    ("Netflix",         "entertainment",    "7841", "streaming",      1, "low"),
    ("Spotify",         "entertainment",    "7929", "streaming",      1, "low"),
    ("Agoda",           "hotel",            "7011", "travel_ota",     1, "low"),
    ("Booking.com",     "hotel",            "7011", "travel_ota",     1, "low"),
]


def generate_merchants() -> list[dict]:
    rows    = []
    counter = 1

    def _add(merch_list, country_code):
        nonlocal counter
        for name, cat, mcc, btype, is_online, risk_tier in merch_list:
            fraud_base  = {"low": 0.002, "medium": 0.008, "high": 0.025}[risk_tier]
            decline_base= {"low": 0.030, "medium": 0.060, "high": 0.100}[risk_tier]
            rows.append({
                "merchant_id":       f"MCH_{counter:05d}",
                "country_code":      country_code,
                "merchant_name":     name,
                "merchant_category": cat,
                "mcc_code":          mcc,
                "business_type":     btype,
                "address":           f"{random.randint(1, 200)} Main St",
                "city":              {"SG": "Singapore", "MY": "Kuala Lumpur",
                                      "IN": "Mumbai", "GL": "Online"}[country_code],
                "is_online":         is_online,
                "risk_tier":         risk_tier,
                "fraud_rate":        round(fraud_base + random.uniform(0, 0.002), 4),
                "decline_rate":      round(decline_base + random.uniform(0, 0.01), 4),
                "created_at":        "2024-01-01 00:00:00",
                "updated_at":        "2025-12-31 23:59:59",
            })
            counter += 1

    _add(_MERCHANTS_SG,   "SG")
    _add(_MERCHANTS_MY,   "MY")
    _add(_MERCHANTS_IN,   "IN")
    _add(_GLOBAL_ONLINE,  "GL")

    return rows
