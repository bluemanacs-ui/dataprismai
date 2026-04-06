"""
Card generator – one card per account.
card_number_hash is SHA-256 of a synthetic PAN so it is 64 hex chars.
"""
import random
import hashlib
from datetime import date


_CARD_STATUSES = ["active", "active", "active", "active", "blocked", "expired"]


def generate_cards(accounts: list[dict],
                   customers_by_id: dict,
                   products: dict) -> list[dict]:
    """Return list of raw_card dicts."""
    rows    = []
    counter = 1

    for acc in accounts:
        cid = acc["customer_id"]
        cust = customers_by_id[cid]

        prod   = random.choice(products[cust["customer_segment"]])
        issued = acc["open_date"]          # same as account open date
        # Expiry: 3 or 5 years after issuance
        iss_yr = int(issued[:4])
        iss_mo = int(issued[5:7])
        exp_yr = iss_yr + random.choice([3, 5])
        exp_dt = date(exp_yr, iss_mo, 28).strftime("%Y-%m-%d")

        # Synthetic PAN hash
        fake_pan = f"4{random.randint(100_000_000_000_000, 999_999_999_999_999)}"
        pan_hash = hashlib.sha256(fake_pan.encode()).hexdigest()

        status = "active" if exp_yr > 2025 else "expired"

        rows.append({
            "card_id":               f"CRD_{counter:07d}",
            "account_id":            acc["account_id"],
            "customer_id":           cid,
            "country_code":          acc["country_code"],
            "legal_entity":          acc["legal_entity"],
            "card_type":             "credit",
            "card_scheme":           prod["card_scheme"],
            "card_number_hash":      pan_hash,
            "card_tier":             prod["card_tier"],
            "issued_date":           issued,
            "expiry_date":           exp_dt,
            "card_status":           status,
            "is_primary_card":       1,
            "daily_limit":           round(acc["credit_limit"] * 0.30, 2),
            "international_enabled": 1 if cust["customer_segment"] != "mass" else random.choice([0, 1]),
            "contactless_enabled":   1,
            "created_at":            f"{issued} 09:00:00",
            "updated_at":            "2025-12-31 23:59:59",
        })
        counter += 1

    return rows
