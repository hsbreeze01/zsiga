# Tasks: Multi-Model Config & LLM-Based Intent Classification

## Group 1: Configuration Layer

- [x] 1.1 Add `LLMFastConfig` class and `llm_fast` field to `ZsigaConfig` in `config.py`
  - Add `LLMFastConfig(api_key, model="glm-4-flash", base_url="https://open.bigmodel.cn/api/paas/v4")`
  - Add `llm_fast: LLMFastConfig | None` parameter to `ZsigaConfig.__init__()`
  - Parse `agent.llm_fast` section in `load_config()` with defaults; inherit `api_key` from main `llm` when omitted; set `None` when section absent

- [x] 1.2 Add `LLMFastConfig` validation and config tests
  - Add tests for default model/base_url values, api_key inheritance from main llm, None when absent
  - Add tests to `tests/test_config_validation.py` covering parse, defaults, and inheritance scenarios

## Group 2: LLM-Based Intent Classification

- [ ] 2.1 Implement `_classify_via_llm()` and upgrade `classify()` in `intent_router.py`
  - Add `_classify_via_llm(message, config, timeout=3.0) -> Intent | None` using `ZaiClient` for single-turn chat completion
  - Build structured JSON prompt listing the 6 intent types and requesting `intent_type`/`confidence`/`verbalization`/`reasoning`
  - Parse JSON response, validate `intent_type` against `IntentType` enum, return `Intent` or `None`
  - Modify `classify()` signature to accept optional `llm_fast_config` parameter; try LLM first, fall back to keyword on any failure

- [ ] 2.2 Add LLM classification path tests in `tests/test_intent_router.py`
  - Mock `ZaiClient` to test: successful LLM response, invalid JSON fallback, timeout fallback, unknown intent_type fallback, no-config direct keyword path
  - Verify `Intent` fields are correctly populated from LLM response
  - Verify fallback `reasoning` indicates keyword fallback occurred
