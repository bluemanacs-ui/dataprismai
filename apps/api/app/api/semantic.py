import logging
from fastapi import APIRouter
from app.semantic.catalog import SEMANTIC_CATALOG
from app.schemas.semantic import SemanticCatalogResponse
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/semantic", tags=["semantic"])

# ── Canonical table schema (static fallback when StarRocks is unreachable) ────
# Format: {name, columns:[{name,type,nullable,key}], row_count}
# Derived from DDL files: 10_banking_raw_ddm.sql, 11_banking_dp_semantic.sql,
#   01_data_products.sql, 12_banking_mapping.sql, 13_banking_audit.sql
_STATIC_EXPLORER_TABLES = [
    # ── Raw Layer ─────────────────────────────────────────────────────────────
    {"name":"raw_customer","row_count":0,"columns":[
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"legal_entity","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"first_name","type":"VARCHAR(60)","nullable":"YES","key":""},
        {"name":"last_name","type":"VARCHAR(60)","nullable":"YES","key":""},
        {"name":"email","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"phone","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"date_of_birth","type":"DATE","nullable":"YES","key":""},
        {"name":"nationality","type":"VARCHAR(3)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"income_band","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"credit_score","type":"INT","nullable":"YES","key":""},
        {"name":"credit_band","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"kyc_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"risk_rating","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"onboard_date","type":"DATE","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"raw_account","row_count":0,"columns":[
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"product_code","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"open_date","type":"DATE","nullable":"YES","key":""},
        {"name":"current_balance","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"credit_limit","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"interest_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"account_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"currency_code","type":"VARCHAR(3)","nullable":"YES","key":""},
    ]},
    {"name":"raw_card","row_count":0,"columns":[
        {"name":"card_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"card_type","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"card_network","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"issue_date","type":"DATE","nullable":"YES","key":""},
        {"name":"expiry_date","type":"DATE","nullable":"YES","key":""},
        {"name":"card_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_contactless","type":"TINYINT","nullable":"YES","key":""},
        {"name":"is_virtual","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"raw_transaction","row_count":0,"columns":[
        {"name":"transaction_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"card_id","type":"VARCHAR(20)","nullable":"YES","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"merchant_id","type":"VARCHAR(20)","nullable":"YES","key":"MUL"},
        {"name":"transaction_date","type":"DATE","nullable":"NO","key":""},
        {"name":"amount","type":"DECIMAL(15,2)","nullable":"NO","key":""},
        {"name":"currency_code","type":"VARCHAR(3)","nullable":"YES","key":""},
        {"name":"merchant_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"transaction_type","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"channel","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"auth_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_fraud","type":"TINYINT","nullable":"YES","key":""},
        {"name":"fraud_score","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"is_international","type":"TINYINT","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"raw_payment","row_count":0,"columns":[
        {"name":"payment_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"statement_id","type":"VARCHAR(30)","nullable":"YES","key":"MUL"},
        {"name":"payment_date","type":"DATE","nullable":"NO","key":""},
        {"name":"payment_amount","type":"DECIMAL(15,2)","nullable":"NO","key":""},
        {"name":"payment_method","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"raw_statement","row_count":0,"columns":[
        {"name":"statement_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"statement_month","type":"VARCHAR(7)","nullable":"NO","key":""},
        {"name":"closing_balance","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"total_spend","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"total_due","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"minimum_due","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"payment_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"raw_merchant","row_count":0,"columns":[
        {"name":"merchant_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"merchant_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"merchant_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"mcc_code","type":"VARCHAR(4)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
        {"name":"risk_tier","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"fraud_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"decline_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
    ]},
    # ── Deposit & Loan Raw ─────────────────────────────────────────────────────
    {"name":"raw_deposit_account","row_count":0,"columns":[
        {"name":"deposit_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"true"},
        {"name":"legal_entity","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"deposit_type","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"deposit_category","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"product_code","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"product_name","type":"VARCHAR(100)","nullable":"YES","key":"false"},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":"false"},
        {"name":"current_balance","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"minimum_balance","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"interest_rate","type":"DECIMAL(8,4)","nullable":"YES","key":"false"},
        {"name":"interest_earned_ytd","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"tenor_months","type":"INT","nullable":"YES","key":"false"},
        {"name":"deposit_amount","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"maturity_date","type":"DATE","nullable":"YES","key":"false"},
        {"name":"has_salary_credit","type":"TINYINT","nullable":"YES","key":"false"},
        {"name":"status","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"open_date","type":"DATE","nullable":"YES","key":"false"},
        {"name":"created_at","type":"DATETIME","nullable":"YES","key":"false"},
        {"name":"updated_at","type":"DATETIME","nullable":"YES","key":"false"},
    ]},
    {"name":"raw_deposit_transaction","row_count":0,"columns":[
        {"name":"txn_id","type":"VARCHAR(30)","nullable":"NO","key":"true"},
        {"name":"deposit_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"false"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"false"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"false"},
        {"name":"txn_date","type":"DATETIME","nullable":"NO","key":"false"},
        {"name":"amount","type":"DECIMAL(20,2)","nullable":"NO","key":"false"},
        {"name":"txn_direction","type":"VARCHAR(10)","nullable":"YES","key":"false"},
        {"name":"txn_type","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"txn_category","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"channel","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"description","type":"VARCHAR(200)","nullable":"YES","key":"false"},
        {"name":"balance_after","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"status","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"created_at","type":"DATETIME","nullable":"YES","key":"false"},
    ]},
    {"name":"raw_loan","row_count":0,"columns":[
        {"name":"loan_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"true"},
        {"name":"legal_entity","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"loan_type","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"loan_category","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":"false"},
        {"name":"loan_amount","type":"DECIMAL(20,2)","nullable":"NO","key":"false"},
        {"name":"disbursement_date","type":"DATE","nullable":"YES","key":"false"},
        {"name":"loan_term_months","type":"INT","nullable":"YES","key":"false"},
        {"name":"annual_interest_rate","type":"DECIMAL(8,4)","nullable":"YES","key":"false"},
        {"name":"emi_amount","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"outstanding_balance","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":"false"},
        {"name":"dpd_bucket","type":"VARCHAR(15)","nullable":"YES","key":"false"},
        {"name":"npa_flag","type":"TINYINT","nullable":"YES","key":"false"},
        {"name":"loan_status","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"created_at","type":"DATETIME","nullable":"YES","key":"false"},
    ]},
    {"name":"raw_loan_repayment","row_count":0,"columns":[
        {"name":"repayment_id","type":"VARCHAR(30)","nullable":"NO","key":"true"},
        {"name":"loan_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"true"},
        {"name":"installment_number","type":"INT","nullable":"NO","key":"false"},
        {"name":"due_date","type":"DATE","nullable":"NO","key":"false"},
        {"name":"payment_date","type":"DATE","nullable":"YES","key":"false"},
        {"name":"emi_due","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"amount_paid","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"outstanding_principal","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":"false"},
        {"name":"payment_status","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"payment_method","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"created_at","type":"DATETIME","nullable":"YES","key":"false"},
    ]},
    # ── DDM Layer ─────────────────────────────────────────────────────────────
    {"name":"ddm_customer","row_count":0,"columns":[
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"legal_entity","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"income_band","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"credit_score","type":"INT","nullable":"YES","key":""},
        {"name":"credit_band","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"kyc_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"risk_rating","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"customer_age","type":"INT","nullable":"YES","key":""},
        {"name":"tenure_months","type":"INT","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"ddm_account","row_count":0,"columns":[
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"current_balance","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"credit_limit","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"utilization_pct","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"utilization_band","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"account_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"product_code","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"account_age_months","type":"INT","nullable":"YES","key":""},
    ]},
    {"name":"ddm_card","row_count":0,"columns":[
        {"name":"card_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"card_type","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"card_network","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"card_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"ddm_transaction","row_count":0,"columns":[
        {"name":"transaction_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"merchant_id","type":"VARCHAR(20)","nullable":"YES","key":"MUL"},
        {"name":"transaction_date","type":"DATE","nullable":"NO","key":""},
        {"name":"amount","type":"DECIMAL(15,2)","nullable":"NO","key":""},
        {"name":"merchant_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"channel","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"auth_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_fraud","type":"TINYINT","nullable":"YES","key":""},
        {"name":"fraud_score","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"fraud_tier","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"ddm_payment","row_count":0,"columns":[
        {"name":"payment_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"statement_id","type":"VARCHAR(30)","nullable":"YES","key":"MUL"},
        {"name":"payment_date","type":"DATE","nullable":"NO","key":""},
        {"name":"payment_amount","type":"DECIMAL(15,2)","nullable":"NO","key":""},
        {"name":"payment_method","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"payment_type","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"ddm_statement","row_count":0,"columns":[
        {"name":"statement_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"statement_month","type":"VARCHAR(7)","nullable":"NO","key":""},
        {"name":"closing_balance","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"total_spend","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"total_due","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"amount_paid","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"payment_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"ddm_merchant","row_count":0,"columns":[
        {"name":"merchant_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"merchant_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"merchant_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"mcc_code","type":"VARCHAR(4)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
        {"name":"risk_tier","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"fraud_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"decline_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
    ]},
    # ── Deposit & Loan DDM ─────────────────────────────────────────────────────
    {"name":"ddm_deposit_account","row_count":0,"columns":[
        {"name":"deposit_key","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"deposit_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"PRI"},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"deposit_type","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"deposit_category","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":""},
        {"name":"current_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"interest_rate","type":"DECIMAL(8,4)","nullable":"YES","key":""},
        {"name":"tenor_months","type":"INT","nullable":"YES","key":""},
        {"name":"balance_band","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_fd","type":"TINYINT","nullable":"YES","key":""},
        {"name":"status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"open_date","type":"DATE","nullable":"YES","key":""},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":""},
    ]},
    {"name":"ddm_loan","row_count":0,"columns":[
        {"name":"loan_key","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"loan_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":""},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":""},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":""},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"loan_type","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"loan_category","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":""},
        {"name":"loan_amount","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"outstanding_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"interest_rate","type":"DECIMAL(8,4)","nullable":"YES","key":""},
        {"name":"emi_amount","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"loan_term_months","type":"INT","nullable":"YES","key":""},
        {"name":"loan_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"dpd_bucket","type":"VARCHAR(15)","nullable":"YES","key":""},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"npa_flag","type":"TINYINT","nullable":"YES","key":""},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":""},
    ]},
    {"name":"ddm_loan_repayment","row_count":0,"columns":[
        {"name":"repayment_key","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"repayment_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"loan_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"PRI"},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"loan_type","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"installment_number","type":"INT","nullable":"YES","key":""},
        {"name":"due_date","type":"DATE","nullable":"YES","key":""},
        {"name":"payment_date","type":"DATE","nullable":"YES","key":""},
        {"name":"emi_due","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"amount_paid","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"outstanding_principal","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"payment_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_late","type":"TINYINT","nullable":"YES","key":""},
        {"name":"delay_days","type":"INT","nullable":"YES","key":""},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":""},
    ]},
    # ── Data Products (DP) ─────────────────────────────────────────────────────
    {"name":"dp_customer_balance_snapshot","row_count":0,"columns":[
        {"name":"snapshot_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"total_credit_limit","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"total_outstanding","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"utilization_pct","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
    ]},
    {"name":"dp_customer_spend_monthly","row_count":0,"columns":[
        {"name":"spend_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"total_spend","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"food_dining","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"retail_shopping","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"travel_transport","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"transaction_count","type":"INT","nullable":"YES","key":""},
        {"name":"top_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"mom_spend_change_pct","type":"DECIMAL(5,4)","nullable":"YES","key":""},
    ]},
    {"name":"dp_transaction_enriched","row_count":0,"columns":[
        {"name":"transaction_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"transaction_date","type":"DATE","nullable":"NO","key":""},
        {"name":"amount","type":"DECIMAL(15,2)","nullable":"NO","key":""},
        {"name":"merchant_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"channel","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"auth_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_fraud","type":"TINYINT","nullable":"YES","key":""},
        {"name":"fraud_score","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"merchant_risk_tier","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"dp_payment_status","row_count":0,"columns":[
        {"name":"as_of_date","type":"DATE","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"payment_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"overdue_bucket","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"total_due","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"amount_paid","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"late_fee","type":"DECIMAL(10,2)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"dp_risk_signals","row_count":0,"columns":[
        {"name":"signal_date","type":"DATE","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":"PRI"},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"fraud_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"decline_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"fraud_amount","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"delinquency_1_30","type":"INT","nullable":"YES","key":""},
        {"name":"delinquency_31_60","type":"INT","nullable":"YES","key":""},
        {"name":"high_risk_accounts","type":"INT","nullable":"YES","key":""},
    ]},
    {"name":"dp_portfolio_kpis","row_count":0,"columns":[
        {"name":"kpi_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":"PRI"},
        {"name":"total_customers","type":"INT","nullable":"YES","key":""},
        {"name":"total_spend","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"spend_growth_pct","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"avg_utilization","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"fraud_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"delinquency_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"npl_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"est_interest_income","type":"DECIMAL(15,2)","nullable":"YES","key":""},
    ]},
    {"name":"dp_deposit_portfolio","row_count":0,"columns":[
        {"name":"snapshot_month","type":"VARCHAR(7)","nullable":"NO","key":"true"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"true"},
        {"name":"legal_entity","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":"false"},
        {"name":"savings_balance","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"savings_account_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"savings_interest_rate","type":"DECIMAL(8,4)","nullable":"YES","key":"false"},
        {"name":"savings_interest_earned","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"current_balance","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"current_account_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"fd_balance","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"fd_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"fd_avg_rate","type":"DECIMAL(8,4)","nullable":"YES","key":"false"},
        {"name":"fd_maturing_next_30d","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"fd_maturing_next_90d","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"total_deposit_balance","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"total_deposit_accounts","type":"INT","nullable":"YES","key":"false"},
        {"name":"total_interest_earned_ytd","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"avg_monthly_credits","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"avg_monthly_debits","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"monthly_credit_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"monthly_debit_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"has_salary_credit","type":"TINYINT","nullable":"YES","key":"false"},
        {"name":"salary_credit_amount","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"deposit_balance_mom_change","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"deposit_balance_mom_pct","type":"DECIMAL(8,4)","nullable":"YES","key":"false"},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":"false"},
    ]},
    {"name":"dp_loan_portfolio","row_count":0,"columns":[
        {"name":"snapshot_month","type":"VARCHAR(7)","nullable":"NO","key":"true"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"true"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"true"},
        {"name":"legal_entity","type":"VARCHAR(20)","nullable":"YES","key":"false"},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":"false"},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":"false"},
        {"name":"annual_income","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"personal_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"personal_loan_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"personal_loan_emi","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"home_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"home_loan_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"home_loan_emi","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"auto_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"auto_loan_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"auto_loan_emi","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"business_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"business_loan_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"business_loan_emi","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"education_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"education_loan_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"total_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"total_loan_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"total_monthly_emi","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"max_overdue_days","type":"INT","nullable":"YES","key":"false"},
        {"name":"overdue_loan_count","type":"INT","nullable":"YES","key":"false"},
        {"name":"is_npa","type":"TINYINT","nullable":"YES","key":"false"},
        {"name":"npa_amount","type":"DECIMAL(20,2)","nullable":"YES","key":"false"},
        {"name":"dpd_bucket","type":"VARCHAR(15)","nullable":"YES","key":"false"},
        {"name":"debt_to_income_ratio","type":"DECIMAL(8,4)","nullable":"YES","key":"false"},
        {"name":"debt_service_ratio","type":"DECIMAL(8,4)","nullable":"YES","key":"false"},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":"false"},
    ]},
    # ── Semantic Layer ─────────────────────────────────────────────────────────
    {"name":"semantic_customer_360","row_count":0,"columns":[
        {"name":"as_of_date","type":"DATE","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"legal_entity","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"credit_score","type":"INT","nullable":"YES","key":""},
        {"name":"credit_band","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"kyc_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"risk_rating","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"current_balance","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"credit_limit","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"utilization_pct","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"mtd_spend","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"payment_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_overdue","type":"TINYINT","nullable":"YES","key":""},
        {"name":"active_fraud_alerts","type":"INT","nullable":"YES","key":""},
    ]},
    {"name":"semantic_transaction_summary","row_count":0,"columns":[
        {"name":"transaction_id","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"transaction_date","type":"DATE","nullable":"NO","key":""},
        {"name":"amount","type":"DECIMAL(15,2)","nullable":"NO","key":""},
        {"name":"merchant_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"channel","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"auth_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_fraud","type":"TINYINT","nullable":"YES","key":""},
        {"name":"fraud_score","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
    ]},
    {"name":"semantic_spend_metrics","row_count":0,"columns":[
        {"name":"spend_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":""},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"total_spend","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"food_dining","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"retail_shopping","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"travel_transport","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"top_category","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"transaction_count","type":"INT","nullable":"YES","key":""},
        {"name":"mom_spend_change_pct","type":"DECIMAL(5,4)","nullable":"YES","key":""},
    ]},
    {"name":"semantic_payment_status","row_count":0,"columns":[
        {"name":"as_of_date","type":"DATE","nullable":"NO","key":"PRI"},
        {"name":"account_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"MUL"},
        {"name":"payment_status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"overdue_bucket","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"consecutive_late","type":"INT","nullable":"YES","key":""},
        {"name":"total_due","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"amount_paid","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"late_fee","type":"DECIMAL(10,2)","nullable":"YES","key":""},
        {"name":"interest_at_risk","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
    ]},
    {"name":"semantic_risk_metrics","row_count":0,"columns":[
        {"name":"metric_date","type":"DATE","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":"PRI"},
        {"name":"customer_segment","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"fraud_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"decline_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"fraud_amount","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"delinquency_1_30","type":"INT","nullable":"YES","key":""},
        {"name":"delinquency_31_60","type":"INT","nullable":"YES","key":""},
        {"name":"high_risk_accounts","type":"INT","nullable":"YES","key":""},
    ]},
    {"name":"semantic_portfolio_kpis","row_count":0,"columns":[
        {"name":"kpi_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"NO","key":"PRI"},
        {"name":"total_customers","type":"INT","nullable":"YES","key":""},
        {"name":"total_spend","type":"DECIMAL(15,2)","nullable":"YES","key":""},
        {"name":"spend_growth_pct","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"avg_utilization","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"fraud_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"delinquency_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"npl_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"est_interest_income","type":"DECIMAL(15,2)","nullable":"YES","key":""},
    ]},
    {"name":"semantic_glossary_metrics","row_count":0,"columns":[
        {"name":"metric_name","type":"VARCHAR(60)","nullable":"NO","key":"PRI"},
        {"name":"domain","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"definition","type":"VARCHAR(300)","nullable":"YES","key":""},
        {"name":"sql_expression","type":"VARCHAR(500)","nullable":"YES","key":""},
        {"name":"grain","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"source_table","type":"VARCHAR(60)","nullable":"YES","key":""},
    ]},
    {"name":"semantic_dimension_mapping","row_count":0,"columns":[
        {"name":"domain","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"dimension_name","type":"VARCHAR(60)","nullable":"NO","key":"PRI"},
        {"name":"column_name","type":"VARCHAR(60)","nullable":"YES","key":""},
        {"name":"source_table","type":"VARCHAR(60)","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    # ── Semantic — Deposit & Loan ──────────────────────────────────────────────
    {"name":"semantic_deposit_portfolio","row_count":0,"columns":[
        {"name":"snapshot_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"PRI"},
        {"name":"customer_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":""},
        {"name":"savings_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_fd_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_deposit_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"fd_count","type":"INT","nullable":"YES","key":""},
        {"name":"fd_avg_rate","type":"DECIMAL(8,4)","nullable":"YES","key":""},
        {"name":"fd_maturing_next_30d","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"has_salary_credit","type":"TINYINT","nullable":"YES","key":""},
        {"name":"avg_monthly_credit","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"deposit_mom_change_pct","type":"DECIMAL(8,4)","nullable":"YES","key":""},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":""},
    ]},
    {"name":"semantic_loan_portfolio","row_count":0,"columns":[
        {"name":"snapshot_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"PRI"},
        {"name":"customer_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"currency_code","type":"VARCHAR(5)","nullable":"YES","key":""},
        {"name":"annual_income","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_loan_count","type":"INT","nullable":"YES","key":""},
        {"name":"total_monthly_emi","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"max_overdue_days","type":"INT","nullable":"YES","key":""},
        {"name":"overdue_bucket","type":"VARCHAR(15)","nullable":"YES","key":""},
        {"name":"is_npa","type":"TINYINT","nullable":"YES","key":""},
        {"name":"loan_to_income_ratio","type":"DECIMAL(8,4)","nullable":"YES","key":""},
        {"name":"debt_service_ratio","type":"DECIMAL(8,4)","nullable":"YES","key":""},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":""},
    ]},
    {"name":"semantic_customer_product_mix","row_count":0,"columns":[
        {"name":"snapshot_month","type":"VARCHAR(7)","nullable":"NO","key":"PRI"},
        {"name":"customer_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"country_code","type":"VARCHAR(5)","nullable":"NO","key":"PRI"},
        {"name":"customer_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"customer_segment","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"annual_income","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_product_count","type":"INT","nullable":"YES","key":""},
        {"name":"has_credit_card","type":"TINYINT","nullable":"YES","key":""},
        {"name":"has_savings","type":"TINYINT","nullable":"YES","key":""},
        {"name":"has_fd","type":"TINYINT","nullable":"YES","key":""},
        {"name":"has_loan","type":"TINYINT","nullable":"YES","key":""},
        {"name":"total_asset_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_liability_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"net_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_deposit_balance","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"total_loan_outstanding","type":"DECIMAL(20,2)","nullable":"YES","key":""},
        {"name":"wallet_share_score","type":"DECIMAL(8,4)","nullable":"YES","key":""},
        {"name":"dw_refreshed_at","type":"DATETIME","nullable":"YES","key":""},
    ]},
    # ── Config & Mapping ──────────────────────────────────────────────────────
    {"name":"intent_domain_mapping","row_count":0,"columns":[
        {"name":"intent_keyword","type":"VARCHAR(50)","nullable":"NO","key":"PRI"},
        {"name":"domain","type":"VARCHAR(30)","nullable":"NO","key":""},
        {"name":"priority","type":"INT","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"domain_semantic_mapping","row_count":0,"columns":[
        {"name":"domain","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"semantic_table","type":"VARCHAR(60)","nullable":"NO","key":"PRI"},
        {"name":"priority","type":"INT","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"semantic_metric_mapping","row_count":0,"columns":[
        {"name":"metric_name","type":"VARCHAR(60)","nullable":"NO","key":"PRI"},
        {"name":"domain","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"sql_expression","type":"VARCHAR(300)","nullable":"YES","key":""},
        {"name":"source_table","type":"VARCHAR(60)","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"semantic_access_control","row_count":0,"columns":[
        {"name":"persona","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"allowed_domain","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"allowed_countries","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"user_domain_mapping","row_count":0,"columns":[
        {"name":"user_id","type":"VARCHAR(20)","nullable":"NO","key":"PRI"},
        {"name":"domain","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"country_codes","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"domain_grain_mapping","row_count":0,"columns":[
        {"name":"domain","type":"VARCHAR(30)","nullable":"NO","key":"PRI"},
        {"name":"default_grain","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"allowed_grains","type":"VARCHAR(50)","nullable":"YES","key":""},
    ]},
    # ── Audit ─────────────────────────────────────────────────────────────────
    {"name":"audit_data_quality","row_count":0,"columns":[
        {"name":"check_id","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"check_timestamp","type":"DATETIME","nullable":"NO","key":"PRI"},
        {"name":"table_name","type":"VARCHAR(100)","nullable":"NO","key":""},
        {"name":"layer","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
        {"name":"check_type","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"check_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"severity","type":"VARCHAR(10)","nullable":"YES","key":""},
        {"name":"null_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
    ]},
    {"name":"audit_data_profile","row_count":0,"columns":[
        {"name":"profile_id","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"profile_date","type":"DATE","nullable":"NO","key":"PRI"},
        {"name":"table_name","type":"VARCHAR(100)","nullable":"NO","key":""},
        {"name":"column_name","type":"VARCHAR(100)","nullable":"NO","key":""},
        {"name":"data_type","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"total_rows","type":"BIGINT","nullable":"YES","key":""},
        {"name":"null_rate","type":"DECIMAL(5,4)","nullable":"YES","key":""},
        {"name":"distinct_count","type":"BIGINT","nullable":"YES","key":""},
        {"name":"min_value","type":"VARCHAR(200)","nullable":"YES","key":""},
        {"name":"max_value","type":"VARCHAR(200)","nullable":"YES","key":""},
    ]},
    {"name":"audit_pipeline_runs","row_count":0,"columns":[
        {"name":"run_id","type":"VARCHAR(50)","nullable":"NO","key":"PRI"},
        {"name":"pipeline_name","type":"VARCHAR(100)","nullable":"NO","key":""},
        {"name":"source_layer","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"target_layer","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"source_table","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"target_table","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
        {"name":"start_time","type":"DATETIME","nullable":"NO","key":""},
        {"name":"end_time","type":"DATETIME","nullable":"YES","key":""},
        {"name":"status","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"rows_inserted","type":"BIGINT","nullable":"YES","key":""},
        {"name":"error_message","type":"VARCHAR(500)","nullable":"YES","key":""},
    ]},
    {"name":"audit_query_log","row_count":0,"columns":[
        {"name":"log_id","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"log_date","type":"DATE","nullable":"NO","key":"PRI"},
        {"name":"user_id","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"query_text","type":"VARCHAR(1000)","nullable":"YES","key":""},
        {"name":"sql_generated","type":"VARCHAR(2000)","nullable":"YES","key":""},
        {"name":"execution_time_ms","type":"INT","nullable":"YES","key":""},
        {"name":"rows_returned","type":"INT","nullable":"YES","key":""},
        {"name":"status","type":"VARCHAR(20)","nullable":"YES","key":""},
    ]},
    {"name":"audit_user_activity","row_count":0,"columns":[
        {"name":"activity_id","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"activity_timestamp","type":"DATETIME","nullable":"NO","key":"PRI"},
        {"name":"user_id","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"user_role","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"persona","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"country_code","type":"VARCHAR(2)","nullable":"YES","key":""},
        {"name":"activity_type","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"query_text","type":"VARCHAR(1000)","nullable":"YES","key":""},
        {"name":"tables_accessed","type":"VARCHAR(300)","nullable":"YES","key":""},
        {"name":"rows_returned","type":"INT","nullable":"YES","key":""},
        {"name":"status","type":"VARCHAR(20)","nullable":"YES","key":""},
    ]},
    {"name":"audit_access_denied","row_count":0,"columns":[
        {"name":"denial_id","type":"BIGINT","nullable":"NO","key":"PRI"},
        {"name":"denial_timestamp","type":"DATETIME","nullable":"NO","key":"PRI"},
        {"name":"user_id","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"user_role","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"requested_table","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"requested_domain","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"requested_country","type":"VARCHAR(2)","nullable":"YES","key":""},
        {"name":"deny_reason","type":"VARCHAR(200)","nullable":"YES","key":""},
        {"name":"query_text","type":"VARCHAR(1000)","nullable":"YES","key":""},
    ]},
    # ── Dictionary / Metadata ─────────────────────────────────────────────────
    {"name":"dic_tables","row_count":0,"columns":[
        {"name":"table_id","type":"INT","nullable":"NO","key":"PRI"},
        {"name":"table_name","type":"VARCHAR(60)","nullable":"NO","key":""},
        {"name":"display_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"layer","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"domain","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"description","type":"VARCHAR(300)","nullable":"YES","key":""},
        {"name":"row_count_approx","type":"BIGINT","nullable":"YES","key":""},
        {"name":"owner","type":"VARCHAR(50)","nullable":"YES","key":""},
        {"name":"refresh_cadence","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"is_active","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"dic_columns","row_count":0,"columns":[
        {"name":"column_id","type":"INT","nullable":"NO","key":"PRI"},
        {"name":"table_name","type":"VARCHAR(60)","nullable":"NO","key":"MUL"},
        {"name":"column_name","type":"VARCHAR(60)","nullable":"NO","key":""},
        {"name":"display_name","type":"VARCHAR(100)","nullable":"YES","key":""},
        {"name":"data_type","type":"VARCHAR(30)","nullable":"YES","key":""},
        {"name":"description","type":"VARCHAR(300)","nullable":"YES","key":""},
        {"name":"is_primary_key","type":"TINYINT","nullable":"YES","key":""},
        {"name":"is_nullable","type":"TINYINT","nullable":"YES","key":""},
    ]},
    {"name":"dic_relationships","row_count":0,"columns":[
        {"name":"rel_id","type":"INT","nullable":"NO","key":"PRI"},
        {"name":"from_table","type":"VARCHAR(60)","nullable":"NO","key":""},
        {"name":"from_column","type":"VARCHAR(60)","nullable":"NO","key":""},
        {"name":"to_table","type":"VARCHAR(60)","nullable":"NO","key":""},
        {"name":"to_column","type":"VARCHAR(60)","nullable":"NO","key":""},
        {"name":"relationship_type","type":"VARCHAR(20)","nullable":"YES","key":""},
        {"name":"description","type":"VARCHAR(200)","nullable":"YES","key":""},
    ]},
]


def _sr_connect():
    import mysql.connector
    return mysql.connector.connect(
        host=settings.starrocks_host,
        port=settings.starrocks_port,
        user=settings.starrocks_user,
        password=settings.starrocks_password,
        database=settings.starrocks_database,
        connection_timeout=5,
    )


@router.get("/catalog", response_model=SemanticCatalogResponse)
def get_semantic_catalog() -> SemanticCatalogResponse:
    return SemanticCatalogResponse(
        metrics=SEMANTIC_CATALOG["metrics"],
        dimensions=SEMANTIC_CATALOG["dimensions"],
    )


@router.get("/tables")
def get_tables() -> dict:
    """Return StarRocks table metadata for the Data Explorer.

    Always returns the full canonical 50-table list so all tabs are consistent.
    When StarRocks is reachable, live row counts and column definitions are merged
    in for tables that physically exist; canonical tables not yet created in StarRocks
    are still returned with static column definitions and row_count=0.
    """
    # Index static tables by name so live data can be merged in-place
    static_by_name: dict = {t["name"]: dict(t) for t in _STATIC_EXPLORER_TABLES}
    try:
        conn = _sr_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES")
        raw = cursor.fetchall()
        table_names = [list(row.values())[0] for row in raw]
        for tname in table_names:
            try:
                cursor.execute(f"DESCRIBE `{tname}`")
                cols = [{"name": r.get("Field", ""), "type": r.get("Type", ""), "nullable": r.get("Null", ""), "key": r.get("Key", "")} for r in cursor.fetchall()]
                cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{tname}`")
                row_count = (cursor.fetchone() or {}).get("cnt", 0)
                # Overwrite static entry with live data (or add if not in static list)
                static_by_name[tname] = {"name": tname, "columns": cols, "row_count": row_count}
            except Exception:
                if tname not in static_by_name:
                    static_by_name[tname] = {"name": tname, "columns": [], "row_count": 0}
        conn.close()
        # Return in canonical order first, then any live-only extras appended at end
        static_names = {t["name"] for t in _STATIC_EXPLORER_TABLES}
        tables = (
            [static_by_name[t["name"]] for t in _STATIC_EXPLORER_TABLES]
            + [v for k, v in static_by_name.items() if k not in static_names]
        )
        return {"tables": tables, "database": settings.starrocks_database, "source": "live+static"}
    except Exception as e:
        logger.warning("StarRocks unreachable, serving static table schema: %s", e)
        return {"tables": _STATIC_EXPLORER_TABLES, "database": settings.starrocks_database, "source": "static"}


@router.get("/profiling/{table_name}")
def get_table_profiling(table_name: str) -> dict:
    """Return full column-level profiling statistics for a table.

    Per column: null_count, null_pct, distinct_count, min_val, max_val, avg_val (numeric).
    For low-cardinality columns (distinct <= 50): top 10 value frequencies.
    """
    import re as _re
    # Sanitize table name — only allow alphanumeric and underscores
    if not _re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        return {"error": "Invalid table name", "table": table_name}
    try:
        conn = _sr_connect()
        cursor = conn.cursor(dictionary=True)

        # 1. Get columns and types via DESCRIBE
        cursor.execute(f"DESCRIBE `{table_name}`")
        desc_rows = cursor.fetchall()
        if not desc_rows:
            conn.close()
            return {"error": f"Table '{table_name}' not found or has no columns", "table": table_name}

        cols = [{"name": r["Field"], "type": r.get("Type", ""), "nullable": r.get("Null", "YES")} for r in desc_rows]

        # 2. Build one aggregate query to get null/distinct/min/max for all columns at once
        _NUMERIC_PREFIXES = ("int", "bigint", "smallint", "tinyint", "decimal", "double", "float", "numeric")
        _DATE_PREFIXES = ("date", "datetime", "timestamp")

        agg_parts = ["COUNT(*) AS _total_rows"]
        for c in cols:
            cname = c["name"]
            ctype = c["type"].lower()
            safe = f"`{cname}`"
            agg_parts.append(f"(COUNT(*) - COUNT({safe})) AS `_null_{cname}`")
            agg_parts.append(f"COUNT(DISTINCT {safe}) AS `_dist_{cname}`")
            is_numeric = any(ctype.startswith(p) for p in _NUMERIC_PREFIXES)
            is_date = any(ctype.startswith(p) for p in _DATE_PREFIXES)
            if is_numeric or is_date:
                agg_parts.append(f"MIN({safe}) AS `_min_{cname}`")
                agg_parts.append(f"MAX({safe}) AS `_max_{cname}`")
                if is_numeric:
                    agg_parts.append(f"ROUND(AVG({safe}), 4) AS `_avg_{cname}`")

        agg_sql = f"SELECT {', '.join(agg_parts)} FROM `{table_name}`"
        cursor.execute(agg_sql)
        agg = cursor.fetchone() or {}
        total_rows = int(agg.get("_total_rows") or 0)

        # 3. Build per-column profile from aggregate result
        col_profiles = []
        for c in cols:
            cname = c["name"]
            ctype = c["type"].lower()
            null_count = int(agg.get(f"_null_{cname}") or 0)
            null_pct = round(100.0 * null_count / total_rows, 2) if total_rows > 0 else 0.0
            distinct_count = int(agg.get(f"_dist_{cname}") or 0)
            is_numeric = any(ctype.startswith(p) for p in _NUMERIC_PREFIXES)
            is_date = any(ctype.startswith(p) for p in _DATE_PREFIXES)

            profile: dict = {
                "name": cname,
                "type": c["type"],
                "nullable": c["nullable"],
                "null_count": null_count,
                "null_pct": null_pct,
                "distinct_count": distinct_count,
                "fill_pct": round(100.0 - null_pct, 2),
            }
            if is_numeric or is_date:
                min_v = agg.get(f"_min_{cname}")
                max_v = agg.get(f"_max_{cname}")
                profile["min_val"] = str(min_v) if min_v is not None else None
                profile["max_val"] = str(max_v) if max_v is not None else None
                if is_numeric:
                    avg_v = agg.get(f"_avg_{cname}")
                    profile["avg_val"] = str(avg_v) if avg_v is not None else None

            col_profiles.append(profile)

        # 4. For low-cardinality columns (distinct <= 50, non-date, not ID-like columns):
        #    fetch top-10 value frequencies
        for cp in col_profiles:
            cname = cp["name"]
            # Skip columns where top-values are not meaningful
            if cp["distinct_count"] == 0 or cp["distinct_count"] > 50:
                continue
            if cname.endswith("_id") or cname in ("transaction_id", "account_id", "customer_id", "payment_id", "statement_id", "merchant_id"):
                continue
            try:
                tv_sql = (
                    f"SELECT `{cname}` AS val, COUNT(*) AS cnt "
                    f"FROM `{table_name}` "
                    f"WHERE `{cname}` IS NOT NULL "
                    f"GROUP BY `{cname}` "
                    f"ORDER BY cnt DESC "
                    f"LIMIT 10"
                )
                cursor.execute(tv_sql)
                top_vals = [{"value": str(r["val"]), "count": int(r["cnt"]),
                              "pct": round(100.0 * int(r["cnt"]) / total_rows, 1) if total_rows > 0 else 0}
                             for r in cursor.fetchall()]
                cp["top_values"] = top_vals
            except Exception:
                pass

        conn.close()
        return {
            "table": table_name,
            "total_rows": total_rows,
            "total_columns": len(col_profiles),
            "null_columns": sum(1 for c in col_profiles if c["null_count"] > 0),
            "columns": col_profiles,
        }
    except Exception as e:
        return {"table": table_name, "total_rows": 0, "total_columns": 0, "null_columns": 0, "columns": [], "error": str(e)}


@router.get("/sample/{table_name}")
def get_table_sample(table_name: str, limit: int = 10, offset: int = 0) -> dict:
    """Return up to `limit` rows from `offset` for paginated sample data."""
    try:
        conn = _sr_connect()
        cursor = conn.cursor(dictionary=True)
        safe_limit = max(1, min(int(limit), 20))
        safe_offset = max(0, int(offset))
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {safe_limit} OFFSET {safe_offset}")
        rows = cursor.fetchall()
        conn.close()
        serialisable = []
        for row in rows:
            serialisable.append({k: (str(v) if v is not None else None) for k, v in row.items()})
        return {"rows": serialisable, "table": table_name, "offset": safe_offset, "limit": safe_limit}
    except Exception as e:
        return {"rows": [], "table": table_name, "offset": 0, "limit": limit, "error": str(e)}


@router.get("/user-context/{user_id}")
def get_user_context(user_id: str) -> dict:
    """Return domain, allowed semantic tables, and access info for a user."""
    try:
        conn = _sr_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT domain, access_level, country_code FROM user_domain_mapping WHERE user_id = %s", (user_id,))
        domain_rows = cursor.fetchall()
        allowed_domains = list({r["domain"] for r in domain_rows})
        conn.close()
        return {"user_id": user_id, "allowed_domains": allowed_domains, "domain_rows": [
            {k: v for k, v in r.items()} for r in domain_rows
        ]}
    except Exception as e:
        return {"user_id": user_id, "allowed_domains": [], "error": str(e)}
