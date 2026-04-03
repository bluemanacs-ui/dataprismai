# Skill: sql-validator

## Purpose
Validate generated SQL before execution.

## Inputs
- sql
- target_engine
- semantic_context

## Outputs
- is_valid
- rewritten_sql
- issues

## Guardrails
- block DDL/DML
- enforce row limit
- reject unapproved schemas
- reject unsafe patterns

## Success Criteria
- unsafe SQL is blocked
- valid SQL is preserved or safely rewritten
