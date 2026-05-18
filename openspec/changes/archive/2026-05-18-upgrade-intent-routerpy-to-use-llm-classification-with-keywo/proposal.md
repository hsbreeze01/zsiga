# Proposal: upgrade intent_router.py to use LLM classification with keyword fallback: add classify_with_llm function that sends a structured JSON prompt to the fast model requesting intent_type/confidence/verbalization/reasoning, modify classify() to try LLM first and fall back to existing keyword logic if LLM fails or returns invalid JSON, add llm_fast config section to zsiga.yaml with glm-4-flash model on open.bigmodel.cn/api/paas/v4 endpoint

## Summary
upgrade intent_router.py to use LLM classification with keyword fallback: add classify_with_llm function that sends a structured JSON prompt to the fast model requesting intent_type/confidence/verbalization/reasoning, modify classify() to try LLM first and fall back to existing keyword logic if LLM fails or returns invalid JSON, add llm_fast config section to zsiga.yaml with glm-4-flash model on open.bigmodel.cn/api/paas/v4 endpoint

## Motivation

## Expected Behavior

