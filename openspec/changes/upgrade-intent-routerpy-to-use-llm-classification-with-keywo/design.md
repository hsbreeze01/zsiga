# Design: Intent Router LLM Classification with Keyword Fallback

## Architecture Decision

The `intent_router.py` already has `_classify_via_llm()` implemented with proper error handling (returns `None` on any failure). The change is minimal: wire it into `classify()` as the first attempt, with keyword matching as the fallback.

**Why LLM-first, keyword-fallback (not keyword-first):**
- LLM provides better classification for ambiguous inputs that keyword matching mishandles
- Keyword matching is deterministic and fast — perfect as a reliable fallback
- The 3-second timeout ensures LLM failure doesn't block the pipeline

**Why optional config parameter:**
- Production usage passes config from the pipeline context
- Tests can pass `None` or a mock config to control behavior
- Backward compatible — existing callers pass no config and get keyword-only behavior if `load_config()` fails

## Data Flow

```
User message
    │
    ▼
classify(message, config=None)
    │
    ├── config is None? → load_config() → get llm_fast
    │
    ├── llm_fast present?
    │   ├── YES → _classify_via_llm(message, config.llm_fast, timeout=3.0)
    │   │         ├── Success → return LLM Intent
    │   │         └── Failure (None) → fall through
    │   └── NO → fall through
    │
    ▼
Keyword-based classification (existing logic, unchanged)
    │
    ▼
Return keyword Intent
```

## Files to Modify

### 1. `zsiga/agent/intent_router.py`
- Modify `classify()` signature: add optional `config: ZsigaConfig | None = None` parameter
- Add LLM-first logic: attempt `_classify_via_llm()` before keyword matching
- Import `load_config` lazily inside the function to avoid circular imports at module level
- Empty/whitespace messages skip LLM and go directly to keyword path (already handled)

### 2. `zsiga.yaml`
- Add `llm_fast` section under `agent`:
  ```yaml
  agent:
    llm_fast:
      api_key: <same as main llm>
      model: glm-4-flash
      base_url: https://open.bigmodel.cn/api/paas/v4
  ```

### 3. `tests/test_intent_router.py`
- Add new test class `TestClassifyWithLLM` with mocked `_classify_via_llm`
- Add test for fallback when LLM returns `None`
- Add test for behavior when config is `None`
- All existing tests remain unchanged — they call `classify()` without config, and since LLM will likely fail/timeout in test environment, keyword fallback ensures they pass

## No New Files

All changes are modifications to existing files. No new modules or packages needed.
