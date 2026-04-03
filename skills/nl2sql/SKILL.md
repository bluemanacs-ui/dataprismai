# Skill: nl2sql

## Purpose
Convert governed business questions into SQL using approved semantic context.

## Inputs
- user_question
- semantic_context
- target_engine

## Outputs
- sql
- assumptions
- confidence

## Guardrails
- read-only SQL only
- use approved semantic mappings
- prefer governed joins
- do not invent metrics

## Success Criteria
- SQL is syntactically valid
- SQL matches the semantic context
- output is explainable
