# Design: Multi-Model Config & LLM-Based Intent Classification

## Architecture Decision

**Separate fast model config** — The `llm_fast` section is intentionally decoupled from the main `llm` config. This allows using a cheap, low-latency model (e.g., `glm-4-flash`) for classification while reserving the powerful model (e.g., `glm-5.1`) for actual code generation. The fast model config is minimal (3 fields) since it only needs connection details, not generation parameters like temperature or max_tokens.

**LLM-first with graceful fallback** — The `classify()` function gains an optional `llm_fast_config` parameter. When provided, it attempts LLM classification first. Any failure (timeout, parse error, invalid intent_type) transparently falls back to the existing keyword matcher. This preserves backward compatibility — all existing tests pass without modification since keyword matching remains the fallback.

**Direct ZaiClient usage** — For the classification call, we create a lightweight `ZaiClient` instance directly in `intent_router.py` rather than using the full `AgentLoop`. Classification is a single-turn chat completion with no tool calls, so the agent loop machinery is unnecessary overhead.

## Data Flow

```
User message
    │
    ▼
classify(message, llm_fast_config=LLMFastConfig | None)
    │
    ├─ llm_fast_config is None? ──Yes──► _classify_keywords(message) ──► Intent
    │
    ├─ llm_fast_config present ──► _classify_via_llm(message, config)
    │       │
    │       ├─ ZaiClient.chat.completions.create(prompt)
    │       │       │
    │       │       ├─ Success + valid JSON ──► Intent (LLM result)
    │       │       │
    │       │       ├─ Timeout / network error ──► fallback
    │       │       │
    │       │       └─ Invalid JSON / unknown intent_type ──► fallback
    │       │
    │       └─ fallback ──► _classify_keywords(message) ──► Intent
    │
    ▼
Intent(verbalization, intent_type, confidence, reasoning, suggested_action)
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/config.py` | Add `LLMFastConfig` class; add `llm_fast` field to `ZsigaConfig`; parse `agent.llm_fast` in `load_config()` with defaults |
| `zsiga/agent/intent_router.py` | Add `_classify_via_llm()` function; modify `classify()` to accept optional `llm_fast_config` parameter and try LLM first |
| `tests/test_config_validation.py` | Add tests for `LLMFastConfig` parsing, defaults, and inheritance from main `llm` api_key |
| `tests/test_intent_router.py` | Add tests for LLM classification path (mocked), timeout fallback, invalid JSON fallback, no-config path |

## Detailed Design

### 1. LLMFastConfig (config.py)

```python
class LLMFastConfig:
    def __init__(self, api_key: str, model: str = "glm-4-flash",
                 base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
```

Minimal — only connection parameters. No temperature/max_tokens since classification uses defaults.

### 2. load_config() changes (config.py)

Parse `agent.llm_fast` section:
- If `agent.llm_fast` exists: build `LLMFastConfig` with provided values + defaults
- If `api_key` not in `llm_fast`: inherit from `agent.llm.api_key`
- If `agent.llm_fast` absent entirely: `llm_fast = None`

### 3. _classify_via_llm() (intent_router.py)

```python
def _classify_via_llm(message: str, config: LLMFastConfig,
                       timeout: float = 3.0) -> Intent | None:
```

- Creates a `ZaiClient(api_key=config.api_key, base_url=config.base_url)`
- Sends a single chat completion with a system prompt listing the 6 intent types and requesting JSON output
- Parses the response JSON, validates `intent_type` against `IntentType` enum
- Returns `Intent` on success, `None` on any failure (caller falls back)

### 4. classify() modification (intent_router.py)

```python
def classify(message: str, llm_fast_config: LLMFastConfig = None) -> Intent:
```

- If `llm_fast_config` is not None: try `_classify_via_llm()`
- If LLM returns None (any failure): fall through to keyword classification
- Keyword classification logic unchanged

### 5. Timeout handling

Use `httpx` timeout passed through `ZaiClient` or wrap the LLM call in a `threading.Timer`-based timeout. The simplest approach: pass `timeout=httpx.Timeout(3.0)` when creating the ZaiClient for classification.

## Backward Compatibility

- All existing `classify(msg)` calls work unchanged (default `llm_fast_config=None`)
- All existing tests pass without modification
- Keyword classification is never removed, only augmented
