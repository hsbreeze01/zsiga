# Tasks: Intent Router LLM Classification

## Group 1: Core Logic

- [x] **1.1** Modify `classify()` in `intent_router.py` to accept optional `config` parameter and call `_classify_via_llm()` first with keyword fallback
- [x] **1.2** Add `llm_fast` section to `zsiga.yaml` with glm-4-flash model config

## Group 2: Tests

- [x] **2.1** Add LLM classification tests: mock `_classify_via_llm` returning valid Intent, returning None (fallback), and config=None path — ensuring existing tests still pass
