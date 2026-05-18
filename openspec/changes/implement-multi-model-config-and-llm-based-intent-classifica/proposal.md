# Proposal: implement multi-model config and LLM-based intent classification: 1) add llm_fast section to config.py with separate api_key/model/base_url fields, defaulting to glm-4-flash on open.bigmodel.cn/api/paas/v4, 2) upgrade intent_router.py classify() to try LLM classification first using the fast model with a structured JSON prompt, fall back to keyword matching if LLM fails or times out, 3) LLM prompt should output JSON with intent_type/confidence/verbalization/reasoning fields

## Summary
implement multi-model config and LLM-based intent classification: 1) add llm_fast section to config.py with separate api_key/model/base_url fields, defaulting to glm-4-flash on open.bigmodel.cn/api/paas/v4, 2) upgrade intent_router.py classify() to try LLM classification first using the fast model with a structured JSON prompt, fall back to keyword matching if LLM fails or times out, 3) LLM prompt should output JSON with intent_type/confidence/verbalization/reasoning fields

## Motivation

## Expected Behavior

