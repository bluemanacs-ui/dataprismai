#!/usr/bin/env python3
"""
Synthetic Credit Card Data Generator for DataPrismAI

Generates realistic synthetic data for credit card analytics including:
- Customers
- Card accounts
- Cards
- Merchants
- Transactions
- Authorizations
- Settlements
- Statements
- Payments
- Fees
- Disputes
- Fraud alerts
- Rewards events
- Delinquency snapshots

Usage:
    python generate_synthetic_data.py --output-dir ./data/synthetic/raw --format csv
    python generate_synthetic_data.py --output-dir ./data/synthetic/parquet --format parquet
"""

import argparse
import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from faker import Faker
import numpy as np

fake = Faker()

# Configuration
NUM_CUSTOMERS = 1000  # Reduced for testing
NUM_ACCOUNTS = 1200  # ~1.2 accounts per customer
NUM_CARDS = 1200  # Most accounts have 1 card
NUM_MERCHANTS = 200  # Reduced for testing
NUM_TRANSACTIONS = 50000  # Reduced for testing
NUM_PAYMENTS = 1000  # Reduced for testing
NUM_STATEMENTS = 2400  # 24 months * 100 accounts
NUM_DISPUTES = 50  # Reduced for testing
NUM_FRAUD_ALERTS = 100  # Reduced for testing

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 3, 1)

class CreditCardDataGenerator:
    def __init__(self, output_dir, format_type='csv'):
        self.output_dir = output_dir
        self.format_type = format_type
        os.makedirs(output_dir, exist_ok=True)

        # Pre-generate reference data
        self.customers = []
        self.accounts = []
        self.cards = []
        self.merchants = []
        self.transactions = []
        self.payments = []
        self.statements = []
        self.disputes = []
        self.fraud_alerts = []

    def generate_customers(self):
        """Generate customer data"""
        print("Generating customers...")
        segments = ['Platinum', 'Gold', 'Silver', 'Bronze']
        income_bands = ['<25k', '25-50k', '50-75k', '75-100k', '100-150k', '150k+']
        age_bands = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']

        for i in range(NUM_CUSTOMERS):
            customer = {
                'customer_id': f"CUST_{i:06d}",
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.email(),
                'phone': fake.phone_number(),
                'address_line1': fake.street_address(),
                'address_line2': fake.secondary_address() if random.random() < 0.3 else '',
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'country': 'US',
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
                'ssn_last4': fake.ssn()[-4:],
                'income_band': random.choice(income_bands),
                'customer_segment': random.choice(segments),
                'credit_score': random.randint(300, 850),
                'created_at': fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
            }
            self.customers.append(customer)

    def generate_merchants(self):
        """Generate merchant data"""
        print("Generating merchants...")
        categories = {
            '5411': 'Grocery Stores',
            '5812': 'Eating Places',
            '5541': 'Service Stations',
            '5912': 'Drug Stores',
            '5311': 'Department Stores',
            '4814': 'Telecommunication Services',
            '4121': 'Taxicabs',
            '5814': 'Fast Food Restaurants',
            '5999': 'Miscellaneous Retail',
            '6011': 'Financial Institutions'
        }

        for i in range(NUM_MERCHANTS):
            category_code = random.choice(list(categories.keys()))
            merchant = {
                'merchant_id': f"MERCH_{i:06d}",
                'merchant_name': fake.company(),
                'merchant_category_code': category_code,
                'address_line1': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'country': 'US',
                'online_offline_flag': random.choice(['online', 'offline']),
                'created_at': fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
            }
            self.merchants.append(merchant)

    def generate_accounts_and_cards(self):
        """Generate card accounts and cards"""
        print("Generating accounts and cards...")
        products = [
            {'id': 'PLATINUM', 'name': 'Platinum Rewards', 'type': 'rewards', 'fee': 695.00},
            {'id': 'GOLD', 'name': 'Gold Cash Back', 'type': 'cashback', 'fee': 250.00},
            {'id': 'SILVER', 'name': 'Silver Everyday', 'type': 'basic', 'fee': 95.00},
            {'id': 'BUSINESS', 'name': 'Business Plus', 'type': 'business', 'fee': 0.00}
        ]

        for i in range(NUM_ACCOUNTS):
            customer = random.choice(self.customers)
            product = random.choice(products)

            account = {
                'account_id': f"ACC_{i:06d}",
                'customer_id': customer['customer_id'],
                'product_id': product['id'],
                'credit_limit': random.choice([500, 1000, 2500, 5000, 10000, 15000, 25000]),
                'apr': Decimal(str(random.uniform(0.15, 0.25))).quantize(Decimal('0.0001')),
                'cycle_day': random.randint(1, 28),
                'open_date': fake.date_between(start_date=START_DATE, end_date=END_DATE - timedelta(days=365)),
                'close_date': None if random.random() < 0.95 else fake.date_between(start_date=START_DATE, end_date=END_DATE),
                'status': 'active' if random.random() < 0.95 else 'closed',
                'created_at': fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
            }
            self.accounts.append(account)

            # Generate card for account
            card = {
                'card_id': f"CARD_{i:06d}",
                'account_id': account['account_id'],
                'card_number_hash': fake.sha256()[:16].upper(),
                'expiration_date': fake.date_between(start_date=END_DATE, end_date=END_DATE + timedelta(days=1460)),
                'cvv_hash': fake.sha256()[:8].upper(),
                'issued_date': account['open_date'],
                'status': 'active' if account['status'] == 'active' else 'inactive',
                'created_at': account['created_at']
            }
            self.cards.append(card)

    def generate_transactions(self):
        """Generate transaction data"""
        print("Generating transactions...")
        channels = ['online', 'instore', 'atm', 'contactless']
        devices = ['mobile', 'desktop', 'pos_terminal', 'atm_machine']

        for i in range(NUM_TRANSACTIONS):
            account = random.choice(self.accounts)
            merchant = random.choice(self.merchants)

            # Generate transaction date with some seasonality
            base_date = fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
            # Add some weekend/holiday uplift
            if base_date.weekday() >= 5:  # Weekend
                amount_multiplier = random.uniform(1.1, 1.5)
            else:
                amount_multiplier = 1.0

            # Category-based amount ranges
            category_amounts = {
                '5411': (10, 200),    # Grocery
                '5812': (15, 150),    # Restaurants
                '5541': (20, 100),    # Gas
                '5912': (5, 100),     # Pharmacy
                '5311': (25, 500),    # Department
                '4814': (20, 200),    # Telecom
                '4121': (10, 50),     # Taxi
                '5814': (5, 25),      # Fast food
                '5999': (10, 300),    # Misc retail
                '6011': (100, 1000)   # Financial
            }

            min_amt, max_amt = category_amounts.get(merchant['merchant_category_code'], (10, 100))
            base_amount = random.uniform(min_amt, max_amt)
            amount = base_amount * amount_multiplier

            transaction = {
                'transaction_id': f"TXN_{i:08d}",
                'account_id': account['account_id'],
                'card_id': random.choice([c['card_id'] for c in self.cards if c['account_id'] == account['account_id']]),
                'merchant_id': merchant['merchant_id'],
                'transaction_date': base_date,
                'amount': Decimal(str(amount)).quantize(Decimal('0.01')),
                'currency': 'USD',
                'auth_status': random.choice(['approved', 'approved', 'approved', 'declined']),
                'settlement_status': 'settled' if random.random() < 0.98 else 'pending',
                'interchange_fee': Decimal(str(amount * random.uniform(0.01, 0.03))).quantize(Decimal('0.01')),
                'fraud_score': Decimal(str(random.uniform(0.0, 1.0))).quantize(Decimal('0.0001')),
                'dispute_flag': random.random() < 0.005,  # 0.5% dispute rate
                'created_at': base_date
            }
            self.transactions.append(transaction)

    def generate_payments(self):
        """Generate payment data"""
        print("Generating payments...")
        payment_types = ['online', 'check', 'ach', 'wire']

        for i in range(NUM_PAYMENTS):
            account = random.choice(self.accounts)
            payment_date = fake.date_between(start_date=START_DATE, end_date=END_DATE)

            payment = {
                'payment_id': f"PAY_{i:07d}",
                'account_id': account['account_id'],
                'payment_date': payment_date,
                'amount': Decimal(str(random.uniform(50, 2000))).quantize(Decimal('0.01')),
                'payment_type': random.choice(payment_types),
                'autopay_flag': random.random() < 0.3,
                'created_at': payment_date
            }
            self.payments.append(payment)

    def generate_statements(self):
        """Generate statement snapshots"""
        print("Generating statements...")
        for account in self.accounts:
            # Generate monthly statements for 24 months
            for months_back in range(24):
                statement_date = (END_DATE - timedelta(days=30 * months_back)).date()  # Convert to date
                if statement_date < account['open_date']:
                    continue

                statement = {
                    'statement_id': f"STMT_{account['account_id']}_{statement_date.strftime('%Y%m')}",
                    'account_id': account['account_id'],
                    'statement_date': statement_date,
                    'ending_balance': Decimal(str(random.uniform(0, account['credit_limit'] * 0.8))).quantize(Decimal('0.01')),
                    'minimum_due': Decimal(str(random.uniform(25, 100))).quantize(Decimal('0.01')),
                    'payment_due_date': statement_date + timedelta(days=25),
                    'delinquency_bucket': random.choice(['current', 'current', 'current', '1-30', '31-60', '61-90', '91+']),
                    'revolving_flag': random.random() < 0.4,
                    'utilization_rate': Decimal(str(random.uniform(0.0, 0.8))).quantize(Decimal('0.0001')),
                    'created_at': statement_date
                }
                self.statements.append(statement)

    def generate_disputes_and_fraud(self):
        """Generate disputes and fraud alerts"""
        print("Generating disputes and fraud alerts...")

        # Disputes
        disputed_txns = random.sample(self.transactions, NUM_DISPUTES)
        for i, txn in enumerate(disputed_txns):
            dispute = {
                'dispute_id': f"DISP_{i:06d}",
                'transaction_id': txn['transaction_id'],
                'account_id': txn['account_id'],
                'dispute_date': txn['transaction_date'] + timedelta(days=random.randint(1, 30)),
                'dispute_reason': random.choice(['fraud', 'unauthorized', 'not_recognized', 'duplicate', 'quality']),
                'amount': txn['amount'],
                'status': random.choice(['open', 'won', 'lost', 'closed']),
                'created_at': txn['transaction_date'] + timedelta(days=random.randint(1, 30))
            }
            self.disputes.append(dispute)

        # Fraud alerts
        for i in range(NUM_FRAUD_ALERTS):
            txn = random.choice(self.transactions)
            alert = {
                'alert_id': f"ALERT_{i:07d}",
                'transaction_id': txn['transaction_id'],
                'account_id': txn['account_id'],
                'alert_date': txn['transaction_date'],
                'fraud_score': Decimal(str(random.uniform(0.7, 1.0))).quantize(Decimal('0.0001')),
                'alert_type': random.choice(['velocity', 'location', 'amount', 'merchant', 'device']),
                'confirmed_fraud': random.random() < 0.1,
                'created_at': txn['transaction_date']
            }
            self.fraud_alerts.append(alert)

    def save_to_csv(self, data, filename):
        """Save data to CSV file"""
        if not data:
            return

        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"Saved {len(data)} records to {filepath}")

    def save_to_parquet(self, data, filename):
        """Save data to Parquet file"""
        if not data:
            return

        df = pd.DataFrame(data)
        filepath = os.path.join(self.output_dir, f"{filename}.parquet")
        df.to_parquet(filepath, index=False)
        print(f"Saved {len(data)} records to {filepath}")

    def save_data(self):
        """Save all generated data"""
        print("Saving data...")

        datasets = [
            (self.customers, 'customers'),
            (self.accounts, 'card_accounts'),
            (self.cards, 'cards'),
            (self.merchants, 'merchants'),
            (self.transactions, 'transactions'),
            (self.payments, 'payments'),
            (self.statements, 'statements'),
            (self.disputes, 'disputes'),
            (self.fraud_alerts, 'fraud_alerts')
        ]

        for data, filename in datasets:
            if self.format_type == 'csv':
                self.save_to_csv(data, filename)
            elif self.format_type == 'parquet':
                self.save_to_parquet(data, filename)

    def generate_all(self):
        """Generate all synthetic data"""
        print("Starting synthetic data generation...")

        self.generate_customers()
        self.generate_merchants()
        self.generate_accounts_and_cards()
        self.generate_transactions()
        self.generate_payments()
        self.generate_statements()
        self.generate_disputes_and_fraud()

        self.save_data()

        print("Synthetic data generation complete!")
        print(f"Generated:")
        print(f"  - {len(self.customers)} customers")
        print(f"  - {len(self.accounts)} accounts")
        print(f"  - {len(self.cards)} cards")
        print(f"  - {len(self.merchants)} merchants")
        print(f"  - {len(self.transactions)} transactions")
        print(f"  - {len(self.payments)} payments")
        print(f"  - {len(self.statements)} statements")
        print(f"  - {len(self.disputes)} disputes")
        print(f"  - {len(self.fraud_alerts)} fraud alerts")


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic credit card data')
    parser.add_argument('--output-dir', default='./data/synthetic/raw',
                       help='Output directory for generated data')
    parser.add_argument('--format', choices=['csv', 'parquet'], default='csv',
                       help='Output format')

    args = parser.parse_args()

    generator = CreditCardDataGenerator(args.output_dir, args.format)
    generator.generate_all()


if __name__ == '__main__':
    main()
