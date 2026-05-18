# Proposal: upgrade intent_router.py from keyword regex to LLM-based classification: keep keyword as fast-path fallback, add classify_with_llm function that sends user message to LLM with a structured prompt asking for intent type + confidence + verbalization + reasoning in JSON format, integrate into classify() as primary path with keyword as fallback when LLM unavailable

## Summary
upgrade intent_router.py from keyword regex to LLM-based classification: keep keyword as fast-path fallback, add classify_with_llm function that sends user message to LLM with a structured prompt asking for intent type + confidence + verbalization + reasoning in JSON format, integrate into classify() as primary path with keyword as fallback when LLM unavailable

## Motivation

## Expected Behavior

