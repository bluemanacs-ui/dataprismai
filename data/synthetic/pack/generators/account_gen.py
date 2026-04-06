"""
Account generator – produces raw_account rows.
Each customer gets 1 account (75 %) or 2 accounts (25 %).
"""
import random
import numpy as np
from datetime import date, datetime, timedelta


def _credit_limit(monthly_income: float, segment: str, products: dict) -> float:
    prod = random.choice(products[segment])
    lo   = prod["credit_mult_low"]  * monthly_income
    hi   = prod["credit_mult_high"] * monthly_income
    return round(random.uniform(lo, hi), -2)   # round to nearest 100


def generate_accounts(customers: list[dict], products: dict) -> list[dict]:
    """Return list of raw_account dicts, keyed to customer_ids."""
    rows    = []
    counter = 1

    for c in customers:
        n_accounts = 2 if random.random() < 0.25 else 1
        monthly_inc = c["annual_income"] / 12.0

        for i in range(n_accounts):
            aid     = f"ACC_{counter:07d}"
            counter += 1

            segment = c["customer_segment"]
            prod    = random.choice(products[segment])

            credit_limit = _credit_limit(monthly_inc, segment, products)
            # Starting balance = 20–70 % utilisation
            util_start   = random.uniform(0.20, 0.70)
            current_bal  = round(credit_limit * util_start, 2)
            avail_bal    = round(credit_limit - current_bal, 2)
            min_bal      = round(credit_limit * 0.05, 2)

            open_yr  = random.randint(2020, 2024)
            open_mo  = random.randint(1, 12)
            open_day = random.randint(1, 28)
            open_dt  = date(open_yr, open_mo, open_day)

            last_act = date(2025, random.randint(10, 12), random.randint(1, 28))

            # cycle_day: billing cycle cut-off day (1–28)
            cycle_day = random.randint(1, 28)

            rows.append({
                "account_id":         aid,
                "customer_id":        c["customer_id"],
                "country_code":       c["country_code"],
                "legal_entity":       c["legal_entity"],
                "account_type":       "credit_card",
                "product_code":       prod["product_code"],
                "currency_code":      c["currency_code"],
                "current_balance":    current_bal,
                "available_balance":  avail_bal,
                "credit_limit":       credit_limit,
                "minimum_balance":    min_bal,
                "interest_rate":      prod["interest_rate"],
                "account_status":     "active",
                "freeze_reason":      None,
                "branch_code":        f"BR{random.randint(100, 999)}",
                "product_name":       prod["product_name"],
                "open_date":          open_dt.strftime("%Y-%m-%d"),
                "close_date":         None,
                "last_activity_date": last_act.strftime("%Y-%m-%d"),
                "cycle_day":          cycle_day,
                "is_deleted":         0,
                "created_at":         f"{open_dt.strftime('%Y-%m-%d')} 09:00:00",
                "updated_at":         "2025-12-31 23:59:59",
            })

    return rows
