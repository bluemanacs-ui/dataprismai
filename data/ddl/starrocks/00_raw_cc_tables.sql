-- =============================================================================
-- LEGACY raw tables — SUPERSEDED by 10_banking_raw_ddm.sql
-- These are dropped here to prevent duplicate table names in cc_analytics.
-- Canonical raw tables are: raw_customer, raw_account, raw_card,
--   raw_transaction, raw_payment, raw_statement, raw_merchant
-- =============================================================================

DROP TABLE IF EXISTS raw_customers;
DROP TABLE IF EXISTS raw_card_accounts;
DROP TABLE IF EXISTS raw_cards;
DROP TABLE IF EXISTS raw_transactions;
DROP TABLE IF EXISTS raw_payments;
DROP TABLE IF EXISTS raw_statements;
DROP TABLE IF EXISTS raw_merchants;
DROP TABLE IF EXISTS raw_disputes;
DROP TABLE IF EXISTS raw_fraud_alerts;
DROP TABLE IF EXISTS query_audit_log;
