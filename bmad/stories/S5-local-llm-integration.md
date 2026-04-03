# Story S5: Local LLM Integration

## Goal
Replace mock backend response generation with a real local LLM using Ollama.

## Scope
- install and configure Ollama
- add backend config for local model host and model name
- create prompt builder
- add Ollama service wrapper
- connect chat service to local LLM

## Files likely impacted
- apps/api/app/core/config.py
- apps/api/app/prompts/prompt_builder.py
- apps/api/app/services/llm_service.py
- apps/api/app/services/chat_service.py
- apps/api/main.py
- apps/api/requirements.txt
- apps/api/.env

## Out of scope
- real NL-to-SQL
- chart rendering
- semantic retrieval
- query execution

## Acceptance Criteria
- Ollama runs locally
- API can call local model
- chat endpoint returns model-generated text
- persona-aware prompt flow remains intact
