"""
Transaction generator.

For each account × month, generates N ≈ Poisson(λ) purchase transactions
plus a small share of declines and fraudulent transactions.
"""
import random
import hashlib
import numpy as np
from datetime import datetime, timedelta
from calendar import monthrange


def _random_dt(year: int, month: int) -> str:
    _, last = monthrange(year, month)
    day  = random.randint(1, last)
    hour = random.randint(7, 23)
    minu = random.randint(0, 59)
    sec  = random.randint(0, 59)
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minu:02d}:{sec:02d}"


def _settlement_dt(txn_dt: str, is_international: int) -> str:
    dt = datetime.strptime(txn_dt, "%Y-%m-%d %H:%M:%S")
    dt += timedelta(days=(2 if is_international else 1))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate_transactions(
    accounts:          list[dict],
    customers_by_id:   dict,
    cards_by_account:  dict,
    merchants:         list[dict],
    merchants_by_cc:   dict,      # {cc: [merchant_dicts]}
    global_merchants:  list[dict],
    data_months:       list[str],
    seg_txn_freq:      dict,
    approve_rates:     dict,
    fraud_rates:       dict,
    cat_names:         list,
    cat_weights:       list,
    cat_amount_sgd:    dict,
    country_cfg:       dict,
    channels:          list,
    chan_w:            list,
    txn_types:         list,
    txn_w:             list,
    decline_reasons:   list,
) -> list[dict]:

    rows    = []
    counter = 1

    for acc in accounts:
        cid       = acc["customer_id"]
        cust      = customers_by_id[cid]
        cc        = acc["country_code"]
        cfg       = country_cfg[cc]
        card      = cards_by_account.get(acc["account_id"])
        card_id   = card["card_id"] if card else None
        seg       = cust["customer_segment"]
        risk      = cust["risk_rating"]
        scale     = cfg["amount_scale"]
        currency  = acc["currency_code"]
        legal     = acc["legal_entity"]
        full_name = f"{cust['first_name']} {cust['last_name']}"

        lam       = seg_txn_freq[seg]
        apr_rate  = approve_rates[risk]
        frd_rate  = fraud_rates[risk]

        local_merchants = merchants_by_cc.get(cc, [])

        for ym in data_months:
            yr, mo = int(ym[:4]), int(ym[5:7])
            n_txn  = max(0, np.random.poisson(lam))

            for _ in range(n_txn):
                tid = f"TXN_{counter:09d}"
                counter += 1

                # Pick category and merchant
                cat = random.choices(cat_names, weights=cat_weights)[0]

                # 90 % local merchant, 5 % global, 5 % cross-country (international)
                r = random.random()
                is_international = 0
                if r < 0.90 and local_merchants:
                    pool = [m for m in local_merchants if m["merchant_category"] == cat]
                    if not pool:
                        pool = local_merchants
                    merch = random.choice(pool)
                elif r < 0.95 and global_merchants:
                    pool = [m for m in global_merchants if m["merchant_category"] == cat]
                    if not pool:
                        pool = global_merchants
                    merch = random.choice(pool)
                else:
                    other_ccs = [k for k in merchants_by_cc if k != cc]
                    if other_ccs:
                        pool = merchants_by_cc[random.choice(other_ccs)]
                        merch = random.choice(pool)
                        is_international = 1
                    else:
                        merch = random.choice(local_merchants) if local_merchants else None
                    if merch is None:
                        continue

                # Amount
                lo, hi = cat_amount_sgd[cat]
                amt    = round(random.uniform(lo * scale, hi * scale), 2)

                # Auth decision
                is_fraud = 1 if random.random() < frd_rate else 0
                approved = bool(random.random() < apr_rate) and not is_fraud
                if is_fraud:
                    approved = True   # fraud txns are approved before detected

                auth_status   = "approved" if approved else "declined"
                decline_reason= None if approved else random.choice(decline_reasons)

                # Fraud score
                if is_fraud:
                    fraud_score = round(random.uniform(0.80, 1.00), 4)
                elif not approved:
                    fraud_score = round(random.uniform(0.20, 0.65), 4)
                else:
                    fraud_score = round(random.uniform(0.00, 0.35), 4)

                fraud_tier    = (
                    "critical" if fraud_score >= 0.85 else
                    "high"     if fraud_score >= 0.60 else
                    "medium"   if fraud_score >= 0.30 else
                    "low"
                )

                channel       = random.choices(channels, weights=chan_w)[0]
                txn_type      = "purchase" if approved else "declined"
                is_contactless= 1 if channel == "contactless" else 0
                is_recurring  = 1 if cat == "utilities" and random.random() < 0.6 else 0

                txn_dt  = _random_dt(yr, mo)
                sett_dt = _settlement_dt(txn_dt, is_international) if approved else None

                ref_no  = f"REF{counter:012d}"
                desc    = f"{merch['merchant_name']} – {cat.replace('_', ' ').title()}"

                rows.append({
                    "transaction_id":    tid,
                    "account_id":        acc["account_id"],
                    "card_id":           card_id,
                    "customer_id":       cid,
                    "country_code":      cc,
                    "legal_entity":      legal,
                    "transaction_date":  txn_dt,
                    "settlement_date":   sett_dt,
                    "amount":            amt,
                    "currency_code":     currency,
                    "transaction_type":  txn_type,
                    "channel":           channel,
                    "merchant_id":       merch["merchant_id"],
                    "merchant_name":     merch["merchant_name"],
                    "merchant_category": cat,
                    "mcc_code":          merch["mcc_code"],
                    "auth_status":       auth_status,
                    "decline_reason":    decline_reason,
                    "is_fraud":          is_fraud,
                    "fraud_score":       fraud_score,
                    "fraud_tier":        fraud_tier,
                    "is_international":  is_international,
                    "is_recurring":      is_recurring,
                    "is_contactless":    is_contactless,
                    "reference_number":  ref_no,
                    "description":       desc,
                    "created_at":        txn_dt,
                })

    return rows
