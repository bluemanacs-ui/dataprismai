"""
Raw pipeline – assembles raw_* DataFrames from generators.
"""
import pandas as pd

from generators.customer_gen  import generate_customers
from generators.account_gen   import generate_accounts
from generators.card_gen       import generate_cards
from generators.merchant_gen   import generate_merchants
from generators.transaction_gen import generate_transactions
from generators.payment_gen    import generate_statements_and_payments

from config import (
    COUNTRIES, SEGMENTS, SEGMENT_WEIGHTS, RISK_RATINGS, RISK_WEIGHTS,
    KYC_STATUSES, KYC_WEIGHTS, OCCUPATIONS, ACQUISITION_CHANNELS, ACQ_WEIGHTS,
    PRODUCTS, MERCHANT_CATEGORIES, CAT_NAMES, CAT_WEIGHTS,
    CATEGORY_AMOUNT_SGD, SEGMENT_TXN_FREQ, APPROVE_RATES, FRAUD_RATES,
    CHANNELS, CHAN_W, TXN_TYPES, TXN_W, DECLINE_REASONS,
    PAYMENT_PROFILES, DATA_MONTHS,
)


def build_raw() -> dict[str, pd.DataFrame]:
    print("→ Generating customers …")
    cust_rows = generate_customers(
        COUNTRIES, SEGMENTS, SEGMENT_WEIGHTS, RISK_RATINGS, RISK_WEIGHTS,
        KYC_STATUSES, KYC_WEIGHTS, OCCUPATIONS, ACQUISITION_CHANNELS, ACQ_WEIGHTS,
    )
    df_customer = pd.DataFrame(cust_rows)
    customers_by_id = {r["customer_id"]: r for r in cust_rows}
    print(f"   {len(df_customer):,} customers")

    print("→ Generating accounts …")
    acc_rows = generate_accounts(cust_rows, PRODUCTS)
    df_account = pd.DataFrame(acc_rows)
    print(f"   {len(df_account):,} accounts")

    print("→ Generating cards …")
    card_rows = generate_cards(acc_rows, customers_by_id, PRODUCTS)
    df_card = pd.DataFrame(card_rows)
    cards_by_account = {r["account_id"]: r for r in card_rows}
    print(f"   {len(df_card):,} cards")

    print("→ Generating merchants …")
    merch_rows = generate_merchants()
    df_merchant = pd.DataFrame(merch_rows)
    # Segment merchants by country_code
    merchants_by_cc  = {}
    global_merchants = []
    for m in merch_rows:
        if m["country_code"] == "GL":
            global_merchants.append(m)
        else:
            merchants_by_cc.setdefault(m["country_code"], []).append(m)
    print(f"   {len(df_merchant):,} merchants")

    print("→ Generating transactions …")
    txn_rows = generate_transactions(
        acc_rows, customers_by_id, cards_by_account,
        merch_rows, merchants_by_cc, global_merchants,
        DATA_MONTHS, SEGMENT_TXN_FREQ, APPROVE_RATES, FRAUD_RATES,
        CAT_NAMES, CAT_WEIGHTS, CATEGORY_AMOUNT_SGD, COUNTRIES,
        CHANNELS, CHAN_W, TXN_TYPES, TXN_W, DECLINE_REASONS,
    )
    df_transaction = pd.DataFrame(txn_rows)
    print(f"   {len(df_transaction):,} transactions")

    print("→ Generating statements & payments …")
    stmt_rows, pay_rows = generate_statements_and_payments(
        acc_rows, customers_by_id, txn_rows, DATA_MONTHS, PAYMENT_PROFILES, COUNTRIES,
    )
    df_statement = pd.DataFrame(stmt_rows)
    df_payment   = pd.DataFrame(pay_rows)
    print(f"   {len(df_statement):,} statements, {len(df_payment):,} payments")

    return {
        "raw_customer":    df_customer,
        "raw_account":     df_account,
        "raw_card":        df_card,
        "raw_merchant":    df_merchant,
        "raw_transaction": df_transaction,
        "raw_statement":   df_statement,
        "raw_payment":     df_payment,
        # pass-through for downstream pipelines
        "_customers_by_id": customers_by_id,
        "_txn_rows":         txn_rows,
    }
