#!/usr/bin/env python3
"""
Fast batch loader for StarRocks using executemany() with chunked inserts.
100-500x faster than single-row inserts.
"""
import os, csv, sys, time
from decimal import Decimal
from datetime import datetime, date
import mysql.connector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'raw')
CHUNK_SIZE = 500  # rows per executemany batch


def connect():
    return mysql.connector.connect(
        host='127.0.0.1', port=9030, user='root', password='',
        database='cc_analytics', connection_timeout=30,
    )


DATE_COLS = {'statement_date', 'open_date', 'close_date', 'issued_date',
             'expiration_date', 'payment_due_date', 'date_of_birth',
             'event_date', 'payment_date'}

DATETIME_COLS = {'transaction_date', 'alert_date', 'created_at', 'dispute_date'}
INT_COLS = {'credit_score', 'points_earned', 'points_redeemed', 'cycle_day', 'ssn_last4'}
BOOL_COLS = {'dispute_flag', 'autopay_flag', 'revolving_flag', 'confirmed_fraud'}
DECIMAL_COLS = {'apr', 'fraud_score', 'utilization_rate', 'credit_limit', 'amount',
                'ending_balance', 'minimum_due', 'interchange_fee', 'payment_amount'}


def coerce(col, val):
    if val in ('None', '', None):
        return None
    if col in DATETIME_COLS:
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
            try:
                return datetime.strptime(val[:19], fmt[:len(val)])
            except Exception:
                pass
        try:
            return datetime.strptime(val[:19], '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None
    if col in DATE_COLS:
        try:
            return datetime.strptime(val[:10], '%Y-%m-%d').date()
        except Exception:
            return None
    if col in INT_COLS:
        try:
            return int(float(val))
        except Exception:
            return 0
    if col in BOOL_COLS:
        return 1 if str(val).lower() in ('true', '1', 'yes') else 0
    if col in DECIMAL_COLS:
        try:
            return Decimal(val)
        except Exception:
            return Decimal('0')
    return val


def load_table(table, csv_file, truncate=False):
    if not os.path.exists(csv_file):
        print(f'  SKIP: {csv_file} not found')
        return 0

    conn = connect()
    cur = conn.cursor()

    if truncate:
        cur.execute(f'TRUNCATE TABLE {table}')
        conn.commit()

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        placeholders = ','.join(['%s'] * len(columns))
        sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"

        chunk = []
        total = 0
        t0 = time.time()
        for row in reader:
            chunk.append(tuple(coerce(c, row[c]) for c in columns))
            if len(chunk) >= CHUNK_SIZE:
                cur.executemany(sql, chunk)
                conn.commit()
                total += len(chunk)
                chunk = []

        if chunk:
            cur.executemany(sql, chunk)
            conn.commit()
            total += len(chunk)

    elapsed = time.time() - t0
    cur.close()
    conn.close()
    print(f'  {table}: {total} rows in {elapsed:.1f}s ({total/elapsed:.0f} rows/s)')
    return total


TABLE_FILES = [
    ('cc_analytics.raw_transactions',  'transactions.csv',  True),
    ('cc_analytics.raw_payments',      'payments.csv',      False),
    ('cc_analytics.raw_disputes',      'disputes.csv',      False),
    ('cc_analytics.raw_fraud_alerts',  'fraud_alerts.csv',  False),
    ('cc_analytics.raw_statements',    'statements.csv',    False),
]

# If specific tables passed as args, only load those
requested = set(sys.argv[1:])

print('Fast-loading StarRocks...')
total = 0
for table, fname, truncate in TABLE_FILES:
    short = table.split('.')[1]
    if requested and short not in requested and table not in requested:
        continue
    total += load_table(table, os.path.join(RAW_DIR, fname), truncate)

print(f'\nDone. Total rows: {total}')
