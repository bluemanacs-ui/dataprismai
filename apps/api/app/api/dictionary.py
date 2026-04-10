# =============================================================================
# DataPrismAI — /dictionary API Router
# =============================================================================
# Serves data dictionary metadata from the dic_* tables in StarRocks:
#   GET /dictionary/tables              — all table definitions
#   GET /dictionary/tables/{table_name} — single table + its columns
#   GET /dictionary/columns/{table_name}— columns for a table
#   GET /dictionary/relationships       — all FK/join relationships
#   GET /dictionary/search?q=...        — search across tables + columns
# =============================================================================
import logging
from fastapi import APIRouter, Query
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dictionary", tags=["dictionary"])

# ── Static fallback dictionary (used when StarRocks is unreachable) ──────────
_STATIC_TABLES = [
  # ── Semantic Layer ─────────────────────────────────────────────────────────
  {"table_id":1,  "table_name":"semantic_customer_360",       "display_name":"Customer 360",           "layer":"semantic","domain":"customer",    "description":"Full customer profile with balances, spend, payment status and risk flags","owner":"data-team","refresh_cadence":"daily",   "is_active":1},
  {"table_id":2,  "table_name":"semantic_transaction_summary","display_name":"Transaction Summary",     "layer":"semantic","domain":"transaction","description":"Enriched transaction ledger with fraud, channel, merchant and customer attributes","owner":"data-team","refresh_cadence":"daily",   "is_active":1},
  {"table_id":3,  "table_name":"semantic_spend_metrics",      "display_name":"Spend Metrics",          "layer":"semantic","domain":"spend",       "description":"Monthly per-customer spend by category with MoM change","owner":"data-team","refresh_cadence":"monthly","is_active":1},
  {"table_id":4,  "table_name":"semantic_payment_status",     "display_name":"Payment Status",         "layer":"semantic","domain":"payment",     "description":"Account-level payment behavior, overdue buckets, and late-fee exposure","owner":"data-team","refresh_cadence":"daily",   "is_active":1},
  {"table_id":5,  "table_name":"semantic_risk_metrics",       "display_name":"Risk Metrics",           "layer":"semantic","domain":"risk",        "description":"Daily fraud rates, decline rates, and delinquency bands by country/segment","owner":"risk-team","refresh_cadence":"daily",   "is_active":1},
  {"table_id":6,  "table_name":"semantic_portfolio_kpis",     "display_name":"Portfolio KPIs",         "layer":"semantic","domain":"portfolio",   "description":"Monthly portfolio roll-up: customers, spend growth, utilization, fraud rate, NPL rate","owner":"data-team","refresh_cadence":"monthly","is_active":1},
  {"table_id":7,  "table_name":"semantic_glossary_metrics",   "display_name":"Glossary Metrics",       "layer":"semantic","domain":"catalog",     "description":"Semantic metric definitions, SQL expressions, and grain metadata","owner":"data-team","refresh_cadence":"on-demand","is_active":1},
  # ── Data Products (DP) ─────────────────────────────────────────────────────
  {"table_id":11, "table_name":"dp_customer_balance_snapshot","display_name":"Customer Balance Snapshot","layer":"dp",    "domain":"customer",    "description":"Monthly snapshot of total credit limit, outstanding balance, utilization per customer","owner":"data-team","refresh_cadence":"monthly","is_active":1},
  {"table_id":12, "table_name":"dp_customer_spend_monthly",   "display_name":"Customer Monthly Spend", "layer":"dp",     "domain":"spend",       "description":"Monthly per-customer spend across 11 merchant categories with totals","owner":"data-team","refresh_cadence":"monthly","is_active":1},
  {"table_id":13, "table_name":"dp_transaction_enriched",     "display_name":"Enriched Transactions",  "layer":"dp",     "domain":"transaction","description":"Transaction ledger enriched with customer/merchant context, fraud scoring, and segment","owner":"data-team","refresh_cadence":"daily",   "is_active":1},
  {"table_id":14, "table_name":"dp_payment_status",           "display_name":"Payment Status",         "layer":"dp",     "domain":"payment",     "description":"Daily account-level payment status with overdue buckets, late fees, interest at risk","owner":"data-team","refresh_cadence":"daily",   "is_active":1},
  {"table_id":15, "table_name":"dp_risk_signals",             "display_name":"Risk Signals",           "layer":"dp",     "domain":"risk",        "description":"Daily aggregated fraud/decline/delinquency risk signals by country and segment","owner":"risk-team","refresh_cadence":"daily",   "is_active":1},
  {"table_id":16, "table_name":"dp_portfolio_kpis",           "display_name":"Portfolio KPIs",         "layer":"dp",     "domain":"portfolio",   "description":"Monthly portfolio health KPIs: customers, spend, utilization, fraud, NPL, churn","owner":"data-team","refresh_cadence":"monthly","is_active":1},
  {"table_id":17, "table_name":"dp_account_health_monthly",   "display_name":"Account Health Monthly",  "layer":"dp",     "domain":"account",     "description":"Monthly account health: revolving balance, payment rate, min-due coverage, delinquency bucket","owner":"data-eng","refresh_cadence":"monthly","is_active":1},
  {"table_id":18, "table_name":"dp_customer_value_cohort",    "display_name":"Customer Value Cohort",   "layer":"dp",     "domain":"customer",    "description":"Customer lifetime value cohort analysis: retention, avg spend, avg balance, delinquency rate by segment","owner":"data-eng","refresh_cadence":"monthly","is_active":1},
  {"table_id":19, "table_name":"dp_fraud_monitoring_hourly",  "display_name":"Fraud Monitoring (Hourly)","layer":"dp",    "domain":"risk",        "description":"Hourly fraud alert counts and flagged amounts by category, channel, and region","owner":"risk-team","refresh_cadence":"hourly","is_active":1},
  {"table_id":20, "table_name":"dp_rewards_profitability_monthly","display_name":"Rewards Profitability","layer":"dp",   "domain":"portfolio",   "description":"Monthly rewards cost vs interchange/fee revenue by product and segment","owner":"data-eng","refresh_cadence":"monthly","is_active":1},
  {"table_id":28, "table_name":"dp_spend_trend_daily",        "display_name":"Daily Spend Trend",       "layer":"dp",     "domain":"spend",       "description":"Daily spend aggregates by geography, merchant category, and product","owner":"data-eng","refresh_cadence":"daily","is_active":1},
  # ── Domain Data Model (DDM) ────────────────────────────────────────────────
  {"table_id":21, "table_name":"ddm_customer",                "display_name":"DDM Customer",           "layer":"ddm",    "domain":"customer",    "description":"Conformed customer dimension: demographics, KYC, risk, income band, credit band","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":22, "table_name":"ddm_account",                 "display_name":"DDM Account",            "layer":"ddm",    "domain":"account",     "description":"Conformed account dimension: balance, credit limit, utilization band, product info","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":23, "table_name":"ddm_card",                    "display_name":"DDM Card",               "layer":"ddm",    "domain":"card",        "description":"Conformed card dimension: card type, expiry, status, linked account and customer","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":24, "table_name":"ddm_transaction",             "display_name":"DDM Transaction",        "layer":"ddm",    "domain":"transaction","description":"Conformed transaction fact: enriched with segment, fraud tier, merchant risk tier","owner":"data-eng","refresh_cadence":"realtime","is_active":1},
  {"table_id":25, "table_name":"ddm_payment",                 "display_name":"DDM Payment",            "layer":"ddm",    "domain":"payment",     "description":"Conformed payment fact: payment method, amount, overdue days, linked statement","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":26, "table_name":"ddm_statement",               "display_name":"DDM Statement",          "layer":"ddm",    "domain":"statement",   "description":"Conformed monthly statement: closing balance, spend, minimum due, payment status","owner":"data-eng","refresh_cadence":"monthly","is_active":1},
  {"table_id":27, "table_name":"ddm_merchant",                "display_name":"DDM Merchant",           "layer":"ddm",    "domain":"merchant",    "description":"Conformed merchant dimension: MCC, risk tier, historical fraud/decline rates","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  # ── Raw Layer ──────────────────────────────────────────────────────────────
  {"table_id":31, "table_name":"raw_customer",                "display_name":"Raw Customers",          "layer":"raw",    "domain":"customer",    "description":"Source customer master — demographics, KYC, risk rating, credit score","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":32, "table_name":"raw_transaction",             "display_name":"Raw Transactions",       "layer":"raw",    "domain":"transaction","description":"Source transaction ledger with auth status, fraud score and channel","owner":"data-eng","refresh_cadence":"realtime","is_active":1},
  {"table_id":33, "table_name":"raw_account",                 "display_name":"Raw Accounts",           "layer":"raw",    "domain":"account",     "description":"Credit card accounts — balance, credit limit, interest rate, status","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":34, "table_name":"raw_card",                    "display_name":"Raw Cards",              "layer":"raw",    "domain":"card",        "description":"Physical card records — card type, expiry, linked account","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":35, "table_name":"raw_statement",               "display_name":"Raw Statements",         "layer":"raw",    "domain":"statement",   "description":"Monthly statements — closing balance, total spend, minimum due, payment status","owner":"data-eng","refresh_cadence":"monthly","is_active":1},
  {"table_id":36, "table_name":"raw_payment",                 "display_name":"Raw Payments",           "layer":"raw",    "domain":"payment",     "description":"Payment records — amount paid, method, overdue days","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":37, "table_name":"raw_merchant",                "display_name":"Raw Merchants",          "layer":"raw",    "domain":"merchant",    "description":"Merchant master — category, MCC, risk tier, fraud/decline rate","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  # ── Audit ──────────────────────────────────────────────────────────────────
  {"table_id":41, "table_name":"audit_data_quality",          "display_name":"Data Quality Audit",     "layer":"audit",  "domain":"ops",         "description":"Row-level data quality check results per table and rule","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":42, "table_name":"audit_data_profile",          "display_name":"Data Profile Audit",     "layer":"audit",  "domain":"ops",         "description":"Column-level profile statistics: null%, distinct count, min, max","owner":"data-eng","refresh_cadence":"daily",   "is_active":1},
  {"table_id":43, "table_name":"audit_pipeline_runs",         "display_name":"Pipeline Run Audit",     "layer":"audit",  "domain":"ops",         "description":"ETL pipeline execution log: status, rows loaded, duration, errors","owner":"data-eng","refresh_cadence":"realtime","is_active":1},
  {"table_id":44, "table_name":"audit_query_log",             "display_name":"Query Audit Log",        "layer":"audit",  "domain":"ops",         "description":"GenBI query audit: SQL generated, engine used, row count, execution time","owner":"platform","refresh_cadence":"realtime","is_active":1},
  {"table_id":45, "table_name":"audit_user_activity",         "display_name":"User Activity Audit",     "layer":"audit",  "domain":"ops",         "description":"User login, query, and export activity audit trail — compliance log","owner":"platform","refresh_cadence":"realtime","is_active":1},
  {"table_id":46, "table_name":"audit_access_denied",         "display_name":"Access Denied Audit",     "layer":"audit",  "domain":"ops",         "description":"Log of denied access attempts by user, table, domain, and reason","owner":"platform","refresh_cadence":"realtime","is_active":1},
  # ── Config & Mapping ───────────────────────────────────────────────────────
  {"table_id":51, "table_name":"intent_domain_mapping",       "display_name":"Intent→Domain Mapping",  "layer":"config", "domain":"routing",     "description":"Maps LLM-detected intent keywords to business domains for query routing","owner":"platform","refresh_cadence":"on-demand","is_active":1},
  {"table_id":52, "table_name":"domain_semantic_mapping",     "display_name":"Domain→Semantic Mapping","layer":"config", "domain":"routing",     "description":"Maps business domains to semantic table names for SQL generation","owner":"platform","refresh_cadence":"on-demand","is_active":1},
  {"table_id":53, "table_name":"semantic_metric_mapping",     "display_name":"Metric Mapping",         "layer":"config", "domain":"catalog",     "description":"Maps metric names to SQL expressions and source tables","owner":"platform","refresh_cadence":"on-demand","is_active":1},
  {"table_id":54, "table_name":"semantic_dimension_mapping",  "display_name":"Dimension Mapping",      "layer":"config", "domain":"catalog",     "description":"Allowed dimension breakdowns per metric/domain","owner":"platform","refresh_cadence":"on-demand","is_active":1},
  {"table_id":55, "table_name":"semantic_access_control",     "display_name":"Semantic Access Control","layer":"config", "domain":"security",    "description":"Row-level access: which domains/tables a persona/role may query","owner":"platform","refresh_cadence":"on-demand","is_active":1},
  {"table_id":56, "table_name":"user_domain_mapping",         "display_name":"User→Domain Mapping",    "layer":"config", "domain":"security",    "description":"Maps user IDs to allowed business domains and country codes","owner":"platform","refresh_cadence":"on-demand","is_active":1},
  {"table_id":57, "table_name":"domain_grain_mapping",        "display_name":"Domain Grain Mapping",   "layer":"config", "domain":"catalog",     "description":"Default grain (daily/monthly/all-time) for each business domain","owner":"platform","refresh_cadence":"on-demand","is_active":1},
]

_STATIC_COLUMNS: dict[str, list] = {
  "semantic_customer_360": [
    {"column_name":"as_of_date","display_name":"As-of Date","data_type":"DATE","description":"Snapshot date"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Unique customer identifier"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN","enum_values":"SG,MY,IN"},
    {"column_name":"legal_entity","display_name":"Legal Entity","data_type":"VARCHAR","description":"SG_BANK / MY_BANK / IN_BANK"},
    {"column_name":"full_name","display_name":"Full Name","data_type":"VARCHAR","description":"Customer full name"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"Customer segment","enum_values":"mass,affluent,premium"},
    {"column_name":"risk_rating","display_name":"Risk Rating","data_type":"VARCHAR","description":"Risk classification","enum_values":"low,medium,high"},
    {"column_name":"kyc_status","display_name":"KYC Status","data_type":"VARCHAR","description":"KYC verification status","enum_values":"verified,pending,enhanced_dd"},
    {"column_name":"credit_score","display_name":"Credit Score","data_type":"INT","description":"Numeric credit score"},
    {"column_name":"credit_band","display_name":"Credit Band","data_type":"VARCHAR","description":"Credit quality band","enum_values":"poor,fair,good,very_good,excellent"},
    {"column_name":"current_balance","display_name":"Current Balance","data_type":"DECIMAL","description":"Current outstanding balance"},
    {"column_name":"credit_limit","display_name":"Credit Limit","data_type":"DECIMAL","description":"Approved credit limit"},
    {"column_name":"utilization_pct","display_name":"Utilization %","data_type":"DECIMAL","description":"Balance / credit limit ratio"},
    {"column_name":"mtd_spend","display_name":"MTD Spend","data_type":"DECIMAL","description":"Month-to-date spend"},
    {"column_name":"payment_status","display_name":"Payment Status","data_type":"VARCHAR","description":"Latest payment status","enum_values":"paid_full,paid_partial,paid_minimum,overdue,pending"},
    {"column_name":"is_overdue","display_name":"Is Overdue","data_type":"BOOLEAN","description":"True if account is overdue"},
    {"column_name":"active_fraud_alerts","display_name":"Active Fraud Alerts","data_type":"INT","description":"Number of open fraud alerts"},
    {"column_name":"currency_code","display_name":"Currency","data_type":"VARCHAR","description":"Account currency"},
  ],
  "semantic_transaction_summary": [
    {"column_name":"transaction_id","display_name":"Transaction ID","data_type":"VARCHAR","description":"Unique transaction identifier"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Associated account"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Account owner"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"transaction_date","display_name":"Transaction Date","data_type":"DATE","description":"Date of transaction"},
    {"column_name":"amount","display_name":"Amount","data_type":"DECIMAL","description":"Transaction value"},
    {"column_name":"transaction_type","display_name":"Type","data_type":"VARCHAR","description":"purchase or declined","enum_values":"purchase,declined"},
    {"column_name":"channel","display_name":"Channel","data_type":"VARCHAR","description":"Purchase channel","enum_values":"online,pos,contactless,mobile,atm"},
    {"column_name":"merchant_name","display_name":"Merchant","data_type":"VARCHAR","description":"Merchant name"},
    {"column_name":"merchant_category","display_name":"Category","data_type":"VARCHAR","description":"Merchant category"},
    {"column_name":"auth_status","display_name":"Auth Status","data_type":"VARCHAR","description":"approved or declined","enum_values":"approved,declined"},
    {"column_name":"is_fraud","display_name":"Is Fraud","data_type":"BOOLEAN","description":"Confirmed fraud flag"},
    {"column_name":"fraud_score","display_name":"Fraud Score","data_type":"DECIMAL","description":"ML fraud probability 0-1"},
    {"column_name":"is_international","display_name":"International","data_type":"BOOLEAN","description":"Cross-border transaction flag"},
  ],
  "semantic_spend_metrics": [
    {"column_name":"spend_month","display_name":"Spend Month","data_type":"VARCHAR","description":"YYYY-MM month key"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Customer identifier"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"mass,affluent,premium"},
    {"column_name":"total_spend","display_name":"Total Spend","data_type":"DECIMAL","description":"Total spend in month"},
    {"column_name":"food_dining","display_name":"Food & Dining","data_type":"DECIMAL","description":"Spend at food/restaurant merchants"},
    {"column_name":"retail_shopping","display_name":"Retail Shopping","data_type":"DECIMAL","description":"Retail merchant spend"},
    {"column_name":"travel_transport","display_name":"Travel & Transport","data_type":"DECIMAL","description":"Travel and transport spend"},
    {"column_name":"top_category","display_name":"Top Category","data_type":"VARCHAR","description":"Highest-spend category for month"},
    {"column_name":"transaction_count","display_name":"Txn Count","data_type":"INT","description":"Number of transactions in month"},
    {"column_name":"mom_spend_change_pct","display_name":"MoM Change %","data_type":"DECIMAL","description":"Month-over-month spend % change"},
  ],
  "semantic_payment_status": [
    {"column_name":"as_of_date","display_name":"As-of Date","data_type":"DATE","description":"Snapshot date"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Account identifier"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Customer identifier"},
    {"column_name":"payment_status","display_name":"Payment Status","data_type":"VARCHAR","description":"paid_full,paid_partial,paid_minimum,overdue,pending"},
    {"column_name":"overdue_days","display_name":"Overdue Days","data_type":"INT","description":"Days past due date"},
    {"column_name":"overdue_bucket","display_name":"Overdue Bucket","data_type":"VARCHAR","description":"current,1-30 days,31-60 days"},
    {"column_name":"consecutive_late","display_name":"Consecutive Late","data_type":"INT","description":"Consecutive months with late payment"},
    {"column_name":"total_due","display_name":"Total Due","data_type":"DECIMAL","description":"Total amount due"},
    {"column_name":"amount_paid","display_name":"Amount Paid","data_type":"DECIMAL","description":"Amount actually paid"},
    {"column_name":"late_fee","display_name":"Late Fee","data_type":"DECIMAL","description":"Late fee assessed"},
    {"column_name":"interest_at_risk","display_name":"Interest at Risk","data_type":"DECIMAL","description":"Interest income at risk from late accounts"},
  ],
  "semantic_risk_metrics": [
    {"column_name":"metric_date","display_name":"Metric Date","data_type":"DATE","description":"Date of risk snapshot"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"mass,affluent,premium"},
    {"column_name":"fraud_rate","display_name":"Fraud Rate","data_type":"DECIMAL","description":"Fraud transactions / total transactions"},
    {"column_name":"decline_rate","display_name":"Decline Rate","data_type":"DECIMAL","description":"Declined transactions / total transactions"},
    {"column_name":"fraud_amount","display_name":"Fraud Amount","data_type":"DECIMAL","description":"Total value of fraud transactions"},
    {"column_name":"delinquency_1_30","display_name":"Delinquency 1-30d","data_type":"INT","description":"Accounts 1-30 days past due"},
    {"column_name":"delinquency_31_60","display_name":"Delinquency 31-60d","data_type":"INT","description":"Accounts 31-60 days past due"},
    {"column_name":"high_risk_accounts","display_name":"High Risk Accounts","data_type":"INT","description":"Count of high-risk rated accounts"},
  ],
  "semantic_portfolio_kpis": [
    {"column_name":"kpi_month","display_name":"KPI Month","data_type":"VARCHAR","description":"YYYY-MM month key"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"total_customers","display_name":"Total Customers","data_type":"INT","description":"Total active customers"},
    {"column_name":"total_spend","display_name":"Total Spend","data_type":"DECIMAL","description":"Portfolio total spend"},
    {"column_name":"spend_growth_pct","display_name":"Spend Growth %","data_type":"DECIMAL","description":"YoY spend growth"},
    {"column_name":"avg_utilization","display_name":"Avg Utilization","data_type":"DECIMAL","description":"Average credit utilization across portfolio"},
    {"column_name":"fraud_rate","display_name":"Fraud Rate","data_type":"DECIMAL","description":"Portfolio-level fraud rate"},
    {"column_name":"delinquency_rate","display_name":"Delinquency Rate","data_type":"DECIMAL","description":"% accounts with overdue payments"},
    {"column_name":"npl_rate","display_name":"NPL Rate","data_type":"DECIMAL","description":"Non-performing loan rate"},
    {"column_name":"est_interest_income","display_name":"Est. Interest Income","data_type":"DECIMAL","description":"Estimated interest income"},
  ],
  "raw_customer": [
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Unique customer ID"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG/MY/IN"},
    {"column_name":"first_name","display_name":"First Name","data_type":"VARCHAR","description":"Customer first name"},
    {"column_name":"last_name","display_name":"Last Name","data_type":"VARCHAR","description":"Customer last name"},
    {"column_name":"email","display_name":"Email","data_type":"VARCHAR","description":"Customer email address"},
    {"column_name":"phone","display_name":"Phone","data_type":"VARCHAR","description":"Contact phone number"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"mass,affluent,premium"},
    {"column_name":"credit_score","display_name":"Credit Score","data_type":"INT","description":"Credit score"},
    {"column_name":"kyc_status","display_name":"KYC Status","data_type":"VARCHAR","description":"verified,pending,enhanced_dd"},
    {"column_name":"risk_rating","display_name":"Risk Rating","data_type":"VARCHAR","description":"low,medium,high"},
  ],
  "raw_transaction": [
    {"column_name":"transaction_id","display_name":"Transaction ID","data_type":"VARCHAR","description":"Unique transaction ID"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Account identifier"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Customer identifier"},
    {"column_name":"transaction_date","display_name":"Date","data_type":"DATE","description":"Transaction date"},
    {"column_name":"amount","display_name":"Amount","data_type":"DECIMAL","description":"Transaction amount"},
    {"column_name":"merchant_category","display_name":"Category","data_type":"VARCHAR","description":"Merchant category"},
    {"column_name":"auth_status","display_name":"Auth Status","data_type":"VARCHAR","description":"approved,declined"},
    {"column_name":"is_fraud","display_name":"Is Fraud","data_type":"BOOLEAN","description":"Fraud flag"},
    {"column_name":"channel","display_name":"Channel","data_type":"VARCHAR","description":"online,pos,contactless,mobile,atm"},
  ],
  "raw_account": [
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Unique account ID"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Account owner"},
    {"column_name":"current_balance","display_name":"Balance","data_type":"DECIMAL","description":"Current outstanding balance"},
    {"column_name":"credit_limit","display_name":"Credit Limit","data_type":"DECIMAL","description":"Approved credit limit"},
    {"column_name":"account_status","display_name":"Status","data_type":"VARCHAR","description":"Account status"},
    {"column_name":"open_date","display_name":"Open Date","data_type":"DATE","description":"Account open date"},
  ],
  "raw_statement": [
    {"column_name":"statement_id","display_name":"Statement ID","data_type":"VARCHAR","description":"Unique statement ID"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Account identifier"},
    {"column_name":"statement_month","display_name":"Statement Month","data_type":"VARCHAR","description":"YYYY-MM"},
    {"column_name":"closing_balance","display_name":"Closing Balance","data_type":"DECIMAL","description":"End-of-month balance"},
    {"column_name":"total_spend","display_name":"Total Spend","data_type":"DECIMAL","description":"Month spend"},
    {"column_name":"total_due","display_name":"Total Due","data_type":"DECIMAL","description":"Amount due"},
    {"column_name":"payment_status","display_name":"Payment Status","data_type":"VARCHAR","description":"paid_full,paid_partial,paid_minimum,overdue,pending"},
  ],
  "raw_payment": [
    {"column_name":"payment_id","display_name":"Payment ID","data_type":"VARCHAR","description":"Unique payment ID"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Account identifier"},
    {"column_name":"payment_date","display_name":"Payment Date","data_type":"DATE","description":"Date payment received"},
    {"column_name":"payment_amount","display_name":"Amount Paid","data_type":"DECIMAL","description":"Payment amount"},
    {"column_name":"payment_method","display_name":"Method","data_type":"VARCHAR","description":"Payment method"},
    {"column_name":"overdue_days","display_name":"Overdue Days","data_type":"INT","description":"Days past due"},
  ],
  "raw_merchant": [
    {"column_name":"merchant_id","display_name":"Merchant ID","data_type":"VARCHAR","description":"Unique merchant ID"},
    {"column_name":"merchant_name","display_name":"Merchant Name","data_type":"VARCHAR","description":"Merchant name"},
    {"column_name":"merchant_category","display_name":"Category","data_type":"VARCHAR","description":"Merchant category code description"},
    {"column_name":"risk_tier","display_name":"Risk Tier","data_type":"VARCHAR","description":"low,medium"},
    {"column_name":"fraud_rate","display_name":"Fraud Rate","data_type":"DECIMAL","description":"Historical fraud rate at merchant"},
    {"column_name":"decline_rate","display_name":"Decline Rate","data_type":"DECIMAL","description":"Historical decline rate at merchant"},
  ],
  # ── DDM Layer ──────────────────────────────────────────────────────────────
  "ddm_customer": [
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Unique customer identifier"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN","enum_values":"SG,MY,IN"},
    {"column_name":"legal_entity","display_name":"Legal Entity","data_type":"VARCHAR","description":"SG_BANK / MY_BANK / IN_BANK"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"Customer value segment","enum_values":"mass,affluent,premium"},
    {"column_name":"income_band","display_name":"Income Band","data_type":"VARCHAR","description":"Income classification: low,medium,high"},
    {"column_name":"credit_score","display_name":"Credit Score","data_type":"INT","description":"Numeric credit score"},
    {"column_name":"credit_band","display_name":"Credit Band","data_type":"VARCHAR","description":"Credit quality band","enum_values":"poor,fair,good,very_good,excellent"},
    {"column_name":"kyc_status","display_name":"KYC Status","data_type":"VARCHAR","description":"KYC verification state","enum_values":"verified,pending,enhanced_dd"},
    {"column_name":"risk_rating","display_name":"Risk Rating","data_type":"VARCHAR","description":"Risk classification","enum_values":"low,medium,high"},
    {"column_name":"customer_age","display_name":"Customer Age","data_type":"INT","description":"Age in years"},
    {"column_name":"tenure_months","display_name":"Tenure (months)","data_type":"INT","description":"Months since account opened"},
    {"column_name":"is_active","display_name":"Is Active","data_type":"BOOLEAN","description":"Active customer flag"},
  ],
  "ddm_account": [
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Unique account identifier"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Foreign key to ddm_customer"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"current_balance","display_name":"Current Balance","data_type":"DECIMAL","description":"Current outstanding balance"},
    {"column_name":"credit_limit","display_name":"Credit Limit","data_type":"DECIMAL","description":"Approved credit limit"},
    {"column_name":"utilization_pct","display_name":"Utilization %","data_type":"DECIMAL","description":"Balance / credit limit ratio (0-1)"},
    {"column_name":"utilization_band","display_name":"Utilization Band","data_type":"VARCHAR","description":"low,medium,high,over_limit"},
    {"column_name":"account_status","display_name":"Account Status","data_type":"VARCHAR","description":"active,frozen,closed,default"},
    {"column_name":"product_code","display_name":"Product Code","data_type":"VARCHAR","description":"Card product identifier"},
    {"column_name":"account_age_months","display_name":"Account Age (months)","data_type":"INT","description":"Months since account opening"},
  ],
  "ddm_card": [
    {"column_name":"card_id","display_name":"Card ID","data_type":"VARCHAR","description":"Unique card identifier"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Linked account"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Card holder"},
    {"column_name":"card_type","display_name":"Card Type","data_type":"VARCHAR","description":"credit,debit,prepaid"},
    {"column_name":"card_network","display_name":"Network","data_type":"VARCHAR","description":"VISA,MASTERCARD,AMEX"},
    {"column_name":"card_status","display_name":"Card Status","data_type":"VARCHAR","description":"active,blocked,expired,cancelled"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
  ],
  "ddm_transaction": [
    {"column_name":"transaction_id","display_name":"Transaction ID","data_type":"VARCHAR","description":"Unique transaction identifier"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Transacting account"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Account owner"},
    {"column_name":"merchant_id","display_name":"Merchant ID","data_type":"VARCHAR","description":"Transacted merchant"},
    {"column_name":"transaction_date","display_name":"Transaction Date","data_type":"DATE","description":"Date of transaction"},
    {"column_name":"amount","display_name":"Amount","data_type":"DECIMAL","description":"Transaction value"},
    {"column_name":"merchant_category","display_name":"Category","data_type":"VARCHAR","description":"Merchant category group"},
    {"column_name":"channel","display_name":"Channel","data_type":"VARCHAR","description":"online,pos,contactless,mobile,atm"},
    {"column_name":"auth_status","display_name":"Auth Status","data_type":"VARCHAR","description":"approved,declined"},
    {"column_name":"is_fraud","display_name":"Is Fraud","data_type":"BOOLEAN","description":"Confirmed fraud flag"},
    {"column_name":"fraud_score","display_name":"Fraud Score","data_type":"DECIMAL","description":"ML fraud probability 0-1"},
    {"column_name":"fraud_tier","display_name":"Fraud Tier","data_type":"VARCHAR","description":"none,low,medium,high,confirmed"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"Customer's segment at transaction time"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
  ],
  "ddm_payment": [
    {"column_name":"payment_id","display_name":"Payment ID","data_type":"VARCHAR","description":"Unique payment identifier"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Account that made payment"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Customer identifier"},
    {"column_name":"statement_id","display_name":"Statement ID","data_type":"VARCHAR","description":"Statement being paid"},
    {"column_name":"payment_date","display_name":"Payment Date","data_type":"DATE","description":"Date payment received"},
    {"column_name":"payment_amount","display_name":"Amount Paid","data_type":"DECIMAL","description":"Amount of payment"},
    {"column_name":"payment_method","display_name":"Method","data_type":"VARCHAR","description":"online_banking,giro,cheque,cash"},
    {"column_name":"overdue_days","display_name":"Overdue Days","data_type":"INT","description":"Days past statement due date (negative = early)"},
    {"column_name":"payment_type","display_name":"Payment Type","data_type":"VARCHAR","description":"full,partial,minimum,overlimit"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
  ],
  "ddm_statement": [
    {"column_name":"statement_id","display_name":"Statement ID","data_type":"VARCHAR","description":"Unique statement identifier"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Account identifier"},
    {"column_name":"statement_month","display_name":"Statement Month","data_type":"VARCHAR","description":"YYYY-MM billing month"},
    {"column_name":"closing_balance","display_name":"Closing Balance","data_type":"DECIMAL","description":"End-of-month outstanding balance"},
    {"column_name":"total_spend","display_name":"Total Spend","data_type":"DECIMAL","description":"Total spend in billing month"},
    {"column_name":"total_due","display_name":"Total Due","data_type":"DECIMAL","description":"Full amount owed"},
    {"column_name":"amount_paid","display_name":"Amount Paid","data_type":"DECIMAL","description":"Payment received against statement"},
    {"column_name":"payment_status","display_name":"Payment Status","data_type":"VARCHAR","description":"paid_full,paid_partial,paid_minimum,overdue,pending"},
    {"column_name":"overdue_days","display_name":"Overdue Days","data_type":"INT","description":"Days past due date"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
  ],
  "ddm_merchant": [
    {"column_name":"merchant_id","display_name":"Merchant ID","data_type":"VARCHAR","description":"Unique merchant identifier"},
    {"column_name":"merchant_name","display_name":"Merchant Name","data_type":"VARCHAR","description":"Merchant display name"},
    {"column_name":"merchant_category","display_name":"Category","data_type":"VARCHAR","description":"Merchant category group"},
    {"column_name":"mcc_code","display_name":"MCC Code","data_type":"VARCHAR","description":"ISO merchant category code"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"risk_tier","display_name":"Risk Tier","data_type":"VARCHAR","description":"low,medium,high"},
    {"column_name":"fraud_rate","display_name":"Fraud Rate","data_type":"DECIMAL","description":"Historical fraud rate at this merchant"},
    {"column_name":"decline_rate","display_name":"Decline Rate","data_type":"DECIMAL","description":"Historical decline rate at this merchant"},
  ],
  # ── Data Products ──────────────────────────────────────────────────────────
  "dp_customer_balance_snapshot": [
    {"column_name":"snapshot_month","display_name":"Snapshot Month","data_type":"VARCHAR","description":"YYYY-MM snapshot period"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Customer identifier"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"total_credit_limit","display_name":"Total Credit Limit","data_type":"DECIMAL","description":"Sum of credit limits across all accounts"},
    {"column_name":"total_outstanding","display_name":"Total Outstanding","data_type":"DECIMAL","description":"Total balance across all accounts"},
    {"column_name":"utilization_pct","display_name":"Utilization %","data_type":"DECIMAL","description":"Outstanding / credit limit ratio (0-1)"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"mass,affluent,premium"},
  ],
  "dp_customer_spend_monthly": [
    {"column_name":"spend_month","display_name":"Spend Month","data_type":"VARCHAR","description":"YYYY-MM billing month"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Customer identifier"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"total_spend","display_name":"Total Spend","data_type":"DECIMAL","description":"Total spend across all categories"},
    {"column_name":"food_dining","display_name":"Food & Dining","data_type":"DECIMAL","description":"Spend at food/restaurant merchants"},
    {"column_name":"retail_shopping","display_name":"Retail Shopping","data_type":"DECIMAL","description":"Retail merchant spend"},
    {"column_name":"travel_transport","display_name":"Travel & Transport","data_type":"DECIMAL","description":"Travel and transport spend"},
    {"column_name":"transaction_count","display_name":"Transaction Count","data_type":"INT","description":"Number of transactions in month"},
    {"column_name":"top_category","display_name":"Top Category","data_type":"VARCHAR","description":"Highest-spend category for month"},
    {"column_name":"mom_spend_change_pct","display_name":"MoM Change %","data_type":"DECIMAL","description":"Month-over-month spend % change"},
  ],
  "dp_transaction_enriched": [
    {"column_name":"transaction_id","display_name":"Transaction ID","data_type":"VARCHAR","description":"Unique transaction identifier"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Transacting account"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Account owner"},
    {"column_name":"transaction_date","display_name":"Transaction Date","data_type":"DATE","description":"Date of transaction"},
    {"column_name":"amount","display_name":"Amount","data_type":"DECIMAL","description":"Transaction value"},
    {"column_name":"merchant_category","display_name":"Category","data_type":"VARCHAR","description":"Merchant category group"},
    {"column_name":"channel","display_name":"Channel","data_type":"VARCHAR","description":"online,pos,contactless,mobile,atm"},
    {"column_name":"auth_status","display_name":"Auth Status","data_type":"VARCHAR","description":"approved,declined"},
    {"column_name":"is_fraud","display_name":"Is Fraud","data_type":"BOOLEAN","description":"Confirmed fraud flag"},
    {"column_name":"fraud_score","display_name":"Fraud Score","data_type":"DECIMAL","description":"ML fraud probability 0-1"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"Customer segment at transaction time"},
    {"column_name":"merchant_risk_tier","display_name":"Merchant Risk Tier","data_type":"VARCHAR","description":"none,low,medium,high"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
  ],
  "dp_payment_status": [
    {"column_name":"as_of_date","display_name":"As-of Date","data_type":"DATE","description":"Snapshot date"},
    {"column_name":"account_id","display_name":"Account ID","data_type":"VARCHAR","description":"Account identifier"},
    {"column_name":"customer_id","display_name":"Customer ID","data_type":"VARCHAR","description":"Customer identifier"},
    {"column_name":"payment_status","display_name":"Payment Status","data_type":"VARCHAR","description":"paid_full,paid_partial,paid_minimum,overdue,pending"},
    {"column_name":"overdue_days","display_name":"Overdue Days","data_type":"INT","description":"Days past due date (0 = current)"},
    {"column_name":"overdue_bucket","display_name":"Overdue Bucket","data_type":"VARCHAR","description":"current,1-30,31-60,61-90,90+"},
    {"column_name":"total_due","display_name":"Total Due","data_type":"DECIMAL","description":"Total amount due on account"},
    {"column_name":"amount_paid","display_name":"Amount Paid","data_type":"DECIMAL","description":"Amount actually paid"},
    {"column_name":"late_fee","display_name":"Late Fee","data_type":"DECIMAL","description":"Late fee assessed"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
  ],
  "dp_risk_signals": [
    {"column_name":"signal_date","display_name":"Signal Date","data_type":"DATE","description":"Date of risk snapshot"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"customer_segment","display_name":"Segment","data_type":"VARCHAR","description":"mass,affluent,premium"},
    {"column_name":"fraud_rate","display_name":"Fraud Rate","data_type":"DECIMAL","description":"Fraud transactions / total transactions"},
    {"column_name":"decline_rate","display_name":"Decline Rate","data_type":"DECIMAL","description":"Declined / total transactions"},
    {"column_name":"fraud_amount","display_name":"Fraud Amount","data_type":"DECIMAL","description":"Total value of fraud transactions"},
    {"column_name":"delinquency_1_30","display_name":"Delinquency 1-30d","data_type":"INT","description":"Accounts 1-30 days past due"},
    {"column_name":"delinquency_31_60","display_name":"Delinquency 31-60d","data_type":"INT","description":"Accounts 31-60 days past due"},
    {"column_name":"high_risk_accounts","display_name":"High Risk Accounts","data_type":"INT","description":"Count of high-risk rated accounts"},
  ],
  "dp_portfolio_kpis": [
    {"column_name":"kpi_month","display_name":"KPI Month","data_type":"VARCHAR","description":"YYYY-MM reporting month"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"total_customers","display_name":"Total Customers","data_type":"INT","description":"Total active customers in portfolio"},
    {"column_name":"total_spend","display_name":"Total Spend","data_type":"DECIMAL","description":"Portfolio total spend"},
    {"column_name":"spend_growth_pct","display_name":"Spend Growth %","data_type":"DECIMAL","description":"YoY spend growth rate"},
    {"column_name":"avg_utilization","display_name":"Avg Utilization","data_type":"DECIMAL","description":"Average credit utilization across portfolio"},
    {"column_name":"fraud_rate","display_name":"Fraud Rate","data_type":"DECIMAL","description":"Portfolio-level fraud rate"},
    {"column_name":"delinquency_rate","display_name":"Delinquency Rate","data_type":"DECIMAL","description":"% accounts with overdue payments"},
    {"column_name":"npl_rate","display_name":"NPL Rate","data_type":"DECIMAL","description":"Non-performing loan rate"},
    {"column_name":"est_interest_income","display_name":"Est. Interest Income","data_type":"DECIMAL","description":"Estimated interest income"},
  ],
  "dp_account_health_monthly": [
    {"column_name":"month_key","display_name":"Month Key","data_type":"INT","description":"YYYYMM integer month key"},
    {"column_name":"account_key","display_name":"Account Key","data_type":"INT","description":"Account surrogate key"},
    {"column_name":"segment_key","display_name":"Segment Key","data_type":"INT","description":"Customer segment surrogate key"},
    {"column_name":"ending_balance","display_name":"Ending Balance","data_type":"DECIMAL","description":"Month-end outstanding balance"},
    {"column_name":"utilization_rate","display_name":"Utilization Rate","data_type":"DECIMAL","description":"Balance / credit limit (0-1)"},
    {"column_name":"payment_rate","display_name":"Payment Rate","data_type":"DECIMAL","description":"Amount paid / total due (0-1)"},
    {"column_name":"min_due_ratio","display_name":"Min Due Ratio","data_type":"DECIMAL","description":"Amount paid / minimum due (≥1 = no late fee)"},
    {"column_name":"delinquency_bucket","display_name":"Delinquency Bucket","data_type":"VARCHAR","description":"current,1-30,31-60,61-90,90+"},
    {"column_name":"chargeoff_risk_score","display_name":"Chargeoff Risk Score","data_type":"DECIMAL","description":"ML probability of chargeoff (0-1)"},
  ],
  "dp_customer_value_cohort": [
    {"column_name":"cohort_month_key","display_name":"Cohort Month","data_type":"INT","description":"YYYYMM cohort entry month"},
    {"column_name":"customer_segment_key","display_name":"Segment Key","data_type":"INT","description":"Customer segment surrogate key"},
    {"column_name":"product_key","display_name":"Product Key","data_type":"INT","description":"Card product surrogate key"},
    {"column_name":"active_accounts","display_name":"Active Accounts","data_type":"BIGINT","description":"Number of active accounts in cohort"},
    {"column_name":"retained_accounts","display_name":"Retained Accounts","data_type":"BIGINT","description":"Accounts still active in current month"},
    {"column_name":"avg_spend","display_name":"Avg Monthly Spend","data_type":"DECIMAL","description":"Average spend per account in cohort"},
    {"column_name":"avg_balance","display_name":"Avg Balance","data_type":"DECIMAL","description":"Average outstanding balance"},
    {"column_name":"delinquency_rate","display_name":"Delinquency Rate","data_type":"DECIMAL","description":"% accounts past due in cohort"},
  ],
  "dp_fraud_monitoring_hourly": [
    {"column_name":"hour_key","display_name":"Hour Key","data_type":"BIGINT","description":"YYYYMMDDHH integer hour key"},
    {"column_name":"merchant_category_key","display_name":"Category Key","data_type":"INT","description":"Merchant category surrogate key"},
    {"column_name":"channel_key","display_name":"Channel Key","data_type":"INT","description":"Transaction channel surrogate key"},
    {"column_name":"region_key","display_name":"Region Key","data_type":"INT","description":"Geographic region surrogate key"},
    {"column_name":"flagged_txn_count","display_name":"Flagged Transactions","data_type":"BIGINT","description":"Count of fraud-flagged transactions in hour"},
    {"column_name":"flagged_amount","display_name":"Flagged Amount","data_type":"DECIMAL","description":"Total value of flagged transactions"},
    {"column_name":"avg_fraud_score","display_name":"Avg Fraud Score","data_type":"DECIMAL","description":"Mean ML fraud score across flagged transactions"},
    {"column_name":"confirmed_fraud_count","display_name":"Confirmed Fraud","data_type":"BIGINT","description":"Count of confirmed fraud cases"},
  ],
  "dp_rewards_profitability_monthly": [
    {"column_name":"month_key","display_name":"Month Key","data_type":"INT","description":"YYYYMM integer month key"},
    {"column_name":"product_key","display_name":"Product Key","data_type":"INT","description":"Card product surrogate key"},
    {"column_name":"segment_key","display_name":"Segment Key","data_type":"INT","description":"Customer segment surrogate key"},
    {"column_name":"total_spend","display_name":"Total Spend","data_type":"DECIMAL","description":"Total cardholder spend generating interchange"},
    {"column_name":"interchange_revenue","display_name":"Interchange Revenue","data_type":"DECIMAL","description":"Revenue from merchant interchange fees"},
    {"column_name":"annual_fee_revenue","display_name":"Annual Fee Revenue","data_type":"DECIMAL","description":"Annualised annual fee contribution"},
    {"column_name":"rewards_cost","display_name":"Rewards Cost","data_type":"DECIMAL","description":"Cost of rewards redeemed / accrued"},
    {"column_name":"net_profitability","display_name":"Net Profitability","data_type":"DECIMAL","description":"Interchange + fees − rewards cost"},
  ],
  "dp_spend_trend_daily": [
    {"column_name":"date_key","display_name":"Date Key","data_type":"INT","description":"YYYYMMDD integer date key"},
    {"column_name":"geography_key","display_name":"Geography Key","data_type":"INT","description":"Country/region surrogate key"},
    {"column_name":"merchant_category_key","display_name":"Category Key","data_type":"INT","description":"Merchant category surrogate key"},
    {"column_name":"product_key","display_name":"Product Key","data_type":"INT","description":"Card product surrogate key"},
    {"column_name":"gross_spend","display_name":"Gross Spend","data_type":"DECIMAL","description":"Total spend value for day/category/product"},
    {"column_name":"txn_count","display_name":"Transaction Count","data_type":"BIGINT","description":"Number of transactions"},
    {"column_name":"avg_ticket","display_name":"Avg Ticket","data_type":"DECIMAL","description":"Average spend per transaction"},
    {"column_name":"fraud_flagged_amount","display_name":"Fraud Flagged Amount","data_type":"DECIMAL","description":"Amount from fraud-flagged transactions"},
    {"column_name":"dispute_amount","display_name":"Dispute Amount","data_type":"DECIMAL","description":"Amount under disputed transactions"},
  ],
  # ── Audit Layer ────────────────────────────────────────────────────────────
  "audit_data_quality": [
    {"column_name":"check_id","display_name":"Check ID","data_type":"BIGINT","description":"Unique check run identifier"},
    {"column_name":"check_timestamp","display_name":"Check Timestamp","data_type":"DATETIME","description":"When the quality check ran"},
    {"column_name":"table_name","display_name":"Table Name","data_type":"VARCHAR","description":"Table that was checked"},
    {"column_name":"layer","display_name":"Layer","data_type":"VARCHAR","description":"RAW,DDM,DP,SEMANTIC"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"check_type","display_name":"Check Type","data_type":"VARCHAR","description":"ROW_COUNT,NULL_RATE,DUPLICATE,FRESHNESS"},
    {"column_name":"check_name","display_name":"Check Name","data_type":"VARCHAR","description":"Human-readable check description"},
    {"column_name":"status","display_name":"Status","data_type":"VARCHAR","description":"PASS,FAIL,WARNING"},
    {"column_name":"severity","display_name":"Severity","data_type":"VARCHAR","description":"INFO,LOW,MEDIUM,HIGH,CRITICAL"},
    {"column_name":"null_rate","display_name":"Null Rate","data_type":"DECIMAL","description":"Proportion of NULL values (0-1)"},
  ],
  "audit_data_profile": [
    {"column_name":"profile_id","display_name":"Profile ID","data_type":"BIGINT","description":"Unique profile run identifier"},
    {"column_name":"profile_date","display_name":"Profile Date","data_type":"DATE","description":"Date profiling ran"},
    {"column_name":"table_name","display_name":"Table Name","data_type":"VARCHAR","description":"Table that was profiled"},
    {"column_name":"column_name","display_name":"Column Name","data_type":"VARCHAR","description":"Column profiled"},
    {"column_name":"data_type","display_name":"Data Type","data_type":"VARCHAR","description":"Column data type"},
    {"column_name":"total_rows","display_name":"Total Rows","data_type":"BIGINT","description":"Total rows in table at profile time"},
    {"column_name":"null_rate","display_name":"Null Rate","data_type":"DECIMAL","description":"Proportion of NULL values"},
    {"column_name":"distinct_count","display_name":"Distinct Count","data_type":"BIGINT","description":"Number of distinct values"},
    {"column_name":"min_value","display_name":"Min Value","data_type":"VARCHAR","description":"Minimum observed value (as string)"},
    {"column_name":"max_value","display_name":"Max Value","data_type":"VARCHAR","description":"Maximum observed value (as string)"},
  ],
  "audit_pipeline_runs": [
    {"column_name":"run_id","display_name":"Run ID","data_type":"VARCHAR","description":"Unique pipeline run identifier"},
    {"column_name":"pipeline_name","display_name":"Pipeline Name","data_type":"VARCHAR","description":"ETL pipeline name"},
    {"column_name":"source_layer","display_name":"Source Layer","data_type":"VARCHAR","description":"RAW,DDM,DP,SEMANTIC"},
    {"column_name":"target_layer","display_name":"Target Layer","data_type":"VARCHAR","description":"RAW,DDM,DP,SEMANTIC"},
    {"column_name":"source_table","display_name":"Source Table","data_type":"VARCHAR","description":"Input table"},
    {"column_name":"target_table","display_name":"Target Table","data_type":"VARCHAR","description":"Output table"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"start_time","display_name":"Start Time","data_type":"DATETIME","description":"Pipeline start timestamp"},
    {"column_name":"status","display_name":"Status","data_type":"VARCHAR","description":"RUNNING,SUCCESS,FAILED,PARTIAL,SKIPPED"},
    {"column_name":"rows_inserted","display_name":"Rows Inserted","data_type":"BIGINT","description":"Rows written to target table"},
    {"column_name":"error_message","display_name":"Error Message","data_type":"VARCHAR","description":"Error details if status=FAILED"},
  ],
  "audit_query_log": [
    {"column_name":"log_id","display_name":"Log ID","data_type":"BIGINT","description":"Unique query log entry"},
    {"column_name":"log_date","display_name":"Log Date","data_type":"DATE","description":"Date of query"},
    {"column_name":"user_id","display_name":"User ID","data_type":"VARCHAR","description":"User who ran the query"},
    {"column_name":"query_text","display_name":"Query Text","data_type":"VARCHAR","description":"Natural language query (may be masked)"},
    {"column_name":"sql_generated","display_name":"SQL Generated","data_type":"VARCHAR","description":"SQL that was executed"},
    {"column_name":"execution_time_ms","display_name":"Execution Time (ms)","data_type":"INT","description":"Query execution duration"},
    {"column_name":"rows_returned","display_name":"Rows Returned","data_type":"INT","description":"Number of rows in result"},
    {"column_name":"status","display_name":"Status","data_type":"VARCHAR","description":"SUCCESS,DENIED,ERROR"},
  ],
  "audit_user_activity": [
    {"column_name":"activity_id","display_name":"Activity ID","data_type":"BIGINT","description":"Unique activity log entry"},
    {"column_name":"activity_timestamp","display_name":"Timestamp","data_type":"DATETIME","description":"Activity datetime"},
    {"column_name":"user_id","display_name":"User ID","data_type":"VARCHAR","description":"Platform user"},
    {"column_name":"user_role","display_name":"Role","data_type":"VARCHAR","description":"analyst,manager,risk_officer,admin"},
    {"column_name":"persona","display_name":"Persona","data_type":"VARCHAR","description":"Active persona during query"},
    {"column_name":"country_code","display_name":"Country","data_type":"VARCHAR","description":"SG / MY / IN"},
    {"column_name":"activity_type","display_name":"Activity Type","data_type":"VARCHAR","description":"LOGIN,LOGOUT,QUERY,EXPORT,VIEW"},
    {"column_name":"query_text","display_name":"Query Text","data_type":"VARCHAR","description":"NL query text (masked if PII detected)"},
    {"column_name":"tables_accessed","display_name":"Tables Accessed","data_type":"VARCHAR","description":"Comma-separated list of queried tables"},
    {"column_name":"rows_returned","display_name":"Rows Returned","data_type":"INT","description":"Result row count"},
    {"column_name":"status","display_name":"Status","data_type":"VARCHAR","description":"SUCCESS,DENIED,ERROR"},
  ],
  "audit_access_denied": [
    {"column_name":"denial_id","display_name":"Denial ID","data_type":"BIGINT","description":"Unique denial log entry"},
    {"column_name":"denial_timestamp","display_name":"Timestamp","data_type":"DATETIME","description":"Denial datetime"},
    {"column_name":"user_id","display_name":"User ID","data_type":"VARCHAR","description":"User whose access was denied"},
    {"column_name":"user_role","display_name":"Role","data_type":"VARCHAR","description":"User role at time of denial"},
    {"column_name":"requested_table","display_name":"Requested Table","data_type":"VARCHAR","description":"Table the user attempted to access"},
    {"column_name":"requested_domain","display_name":"Requested Domain","data_type":"VARCHAR","description":"Business domain requested"},
    {"column_name":"requested_country","display_name":"Requested Country","data_type":"VARCHAR","description":"Country scope requested"},
    {"column_name":"deny_reason","display_name":"Deny Reason","data_type":"VARCHAR","description":"Rule or policy that blocked access"},
    {"column_name":"query_text","display_name":"Query Text","data_type":"VARCHAR","description":"NL query that triggered denial"},
  ],
}

_STATIC_RELATIONSHIPS = [
  {"from_table":"semantic_customer_360","from_column":"customer_id","to_table":"semantic_spend_metrics","to_column":"customer_id","join_type":"LEFT"},
  {"from_table":"semantic_customer_360","from_column":"customer_id","to_table":"semantic_payment_status","to_column":"customer_id","join_type":"LEFT"},
  {"from_table":"semantic_customer_360","from_column":"primary_account_id","to_table":"semantic_payment_status","to_column":"account_id","join_type":"LEFT"},
  {"from_table":"semantic_transaction_summary","from_column":"country_code","to_table":"semantic_risk_metrics","to_column":"country_code","join_type":"LEFT"},
  {"from_table":"semantic_portfolio_kpis","from_column":"country_code","to_table":"semantic_risk_metrics","to_column":"country_code","join_type":"LEFT"},
  {"from_table":"raw_account","from_column":"customer_id","to_table":"raw_customer","to_column":"customer_id","join_type":"INNER"},
  {"from_table":"raw_transaction","from_column":"account_id","to_table":"raw_account","to_column":"account_id","join_type":"INNER"},
  {"from_table":"raw_transaction","from_column":"merchant_id","to_table":"raw_merchant","to_column":"merchant_id","join_type":"LEFT"},
]


def _connect():
    import mysql.connector
    return mysql.connector.connect(
        host=settings.starrocks_host,
        port=settings.starrocks_port,
        user=settings.starrocks_user,
        password=settings.starrocks_password,
        database=settings.starrocks_database,
        connection_timeout=5,
    )


@router.get("/tables")
def get_dictionary_tables(layer: str = "", domain: str = "") -> dict:
    """Return all table entries from dic_tables, optionally filtered by layer/domain."""
    try:
        conn = _connect()
        cur = conn.cursor(dictionary=True)
        sql = "SELECT * FROM dic_tables WHERE is_active = 1"
        params: list = []
        if layer:
            sql += " AND layer = %s"
            params.append(layer)
        if domain:
            sql += " AND domain = %s"
            params.append(domain)
        sql += " ORDER BY layer, table_name"
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        if rows:
            return {"tables": [dict(r) for r in rows]}
        # No rows in StarRocks — fall through to static
        raise Exception("empty dic_tables")
    except Exception as e:
        logger.warning("dictionary/tables StarRocks unavailable (%s) — returning static dictionary", e)
        tables = _STATIC_TABLES
        if layer:
            tables = [t for t in tables if t["layer"] == layer]
        if domain:
            tables = [t for t in tables if t["domain"] == domain]
        return {"tables": tables, "source": "static"}


@router.get("/tables/{table_name}")
def get_dictionary_table_detail(table_name: str) -> dict:
    """Return table metadata + all its column definitions."""
    try:
        conn = _connect()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM dic_tables WHERE table_name = %s", (table_name,))
        table = cur.fetchone()
        if not table:
            raise Exception("not in StarRocks dic_tables")

        cur.execute(
            "SELECT * FROM dic_columns WHERE table_name = %s ORDER BY column_id",
            (table_name,),
        )
        columns = [dict(r) for r in cur.fetchall()]

        # Enrich columns: prefer _STATIC_COLUMNS (have business descriptions), then DESCRIBE
        if not columns:
            if table_name in _STATIC_COLUMNS:
                columns = _STATIC_COLUMNS[table_name]
            else:
                try:
                    cur.execute(f"DESCRIBE `{table_name}`")
                    columns = [
                        {
                            "column_name": r.get("Field", ""),
                            "display_name": r.get("Field", "").replace("_", " ").title(),
                            "data_type": r.get("Type", ""),
                            "description": "",
                            "is_nullable": 1 if r.get("Null") == "YES" else 0,
                            "is_primary_key": 1 if r.get("Key") == "PRI" else 0,
                            "is_pii": 0,
                            "enum_values": None,
                            "business_rule": None,
                            "example_values": None,
                        }
                        for r in cur.fetchall()
                    ]
                except Exception:
                    pass

        cur.execute(
            "SELECT * FROM dic_relationships WHERE from_table = %s OR to_table = %s",
            (table_name, table_name),
        )
        relationships = [dict(r) for r in cur.fetchall()]
        conn.close()

        return {
            "table": dict(table),
            "columns": columns,
            "relationships": relationships,
        }
    except Exception as e:
        logger.warning("dictionary/table_detail StarRocks unavailable (%s) — returning static", e)
        tbl_meta = next((t for t in _STATIC_TABLES if t["table_name"] == table_name), None)
        if not tbl_meta:
            return {"error": f"Table '{table_name}' not found in data dictionary"}
        cols = _STATIC_COLUMNS.get(table_name, [])
        rels = [r for r in _STATIC_RELATIONSHIPS if r["from_table"] == table_name or r["to_table"] == table_name]
        return {"table": tbl_meta, "columns": cols, "relationships": rels, "source": "static"}


@router.get("/columns/{table_name}")
def get_dictionary_columns(table_name: str) -> dict:
    """Return column definitions for a specific table."""
    try:
        conn = _connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM dic_columns WHERE table_name = %s ORDER BY column_id",
            (table_name,),
        )
        rows = cur.fetchall()
        conn.close()
        if rows:
            return {"columns": [dict(r) for r in rows], "table": table_name}
        raise Exception("empty")
    except Exception as e:
        cols = _STATIC_COLUMNS.get(table_name, [])
        return {"columns": cols, "table": table_name, "source": "static"}


@router.get("/relationships")
def get_dictionary_relationships() -> dict:
    """Return all table relationships."""
    try:
        conn = _connect()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM dic_relationships ORDER BY from_table")
        rows = cur.fetchall()
        conn.close()
        if rows:
            return {"relationships": [dict(r) for r in rows]}
        raise Exception("empty")
    except Exception as e:
        return {"relationships": _STATIC_RELATIONSHIPS, "source": "static"}


@router.get("/search")
def search_dictionary(q: str = Query(default="", min_length=1)) -> dict:
    """Full-text search across table names, display names, and column descriptions."""
    try:
        conn = _connect()
        cur = conn.cursor(dictionary=True)
        like = f"%{q}%"

        cur.execute(
            "SELECT table_name, display_name, layer, domain, description "
            "FROM dic_tables "
            "WHERE is_active = 1 AND (table_name LIKE %s OR display_name LIKE %s OR description LIKE %s) "
            "ORDER BY layer, table_name LIMIT 20",
            (like, like, like),
        )
        tables = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT table_name, column_name, display_name, description, data_type "
            "FROM dic_columns "
            "WHERE column_name LIKE %s OR display_name LIKE %s OR description LIKE %s "
            "ORDER BY table_name, column_name LIMIT 40",
            (like, like, like),
        )
        columns = [dict(r) for r in cur.fetchall()]
        conn.close()

        if tables or columns:
            return {"query": q, "tables": tables, "columns": columns}
        raise Exception("empty results from StarRocks")
    except Exception as e:
        ql = q.lower()
        tables = [t for t in _STATIC_TABLES if ql in t["table_name"] or ql in t.get("display_name", "").lower() or ql in t.get("description", "").lower()]
        columns = [
            {**c, "table_name": tname}
            for tname, cols in _STATIC_COLUMNS.items()
            for c in cols
            if ql in c["column_name"] or ql in c.get("display_name", "").lower() or ql in c.get("description", "").lower()
        ]
        return {"query": q, "tables": tables[:20], "columns": columns[:40], "source": "static"}
