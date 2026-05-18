# Spec: Intent Router LLM Classification with Keyword Fallback

## MODIFIED Requirements

### REQ-IRLC-01: classify() SHALL attempt LLM classification before keyword matching

The `classify()` function in `intent_router.py` SHALL first attempt to classify the user message using a fast LLM model. If the LLM call succeeds and returns a valid `Intent`, that result SHALL be returned. If the LLM call fails (timeout, parse error, invalid intent_type, network error), the function SHALL fall back to the existing keyword-based classification logic.

#### Scenario: LLM returns a valid classification

- **Given** the `llm_fast` config is present in `zsiga.yaml`
- **When** `classify()` is called with a user message
- **And** the LLM returns valid JSON with a recognized `intent_type`
- **Then** the returned `Intent` SHALL use the LLM's `intent_type`, `confidence`, `verbalization`, and `reasoning`

#### Scenario: LLM fails, keyword fallback is used

- **Given** the `llm_fast` config is present in `zsiga.yaml`
- **When** `classify()` is called with a user message
- **And** the LLM call times out, returns invalid JSON, or returns an unrecognized `intent_type`
- **Then** the function SHALL fall back to keyword-based classification
- **And** the returned `Intent` SHALL be identical to the current keyword-only result

#### Scenario: LLM config is absent

- **Given** the `llm_fast` config is NOT present in `zsiga.yaml`
- **When** `classify()` is called with a user message
- **Then** the function SHALL skip the LLM call entirely and proceed directly to keyword-based classification

### REQ-IRLC-02: classify() SHALL accept an optional config parameter

The `classify()` function SHALL accept an optional `config` parameter of type `ZsigaConfig` (or `None`). When provided, it SHALL use `config.llm_fast` to configure the LLM client. When `None`, it SHALL attempt to load the global config.

#### Scenario: classify called with explicit config

- **Given** a `ZsigaConfig` with a valid `llm_fast` section
- **When** `classify(message, config=config)` is called
- **Then** the LLM client SHALL use the provided `config.llm_fast` settings

#### Scenario: classify called without config

- **Given** no `config` argument is passed
- **When** `classify(message)` is called
- **Then** the function SHALL attempt to load config via `load_config()`
- **And** if loading fails, SHALL fall back to keyword-only classification silently

### REQ-IRLC-03: LLM classification timeout SHALL be bounded at 3 seconds

The LLM classification call SHALL have a maximum timeout of 3 seconds. If the LLM does not respond within this time, the function SHALL fall back to keyword matching.

#### Scenario: LLM response exceeds timeout

- **Given** the LLM service is slow or unreachable
- **When** the LLM call exceeds 3 seconds
- **Then** the function SHALL abort the LLM call and return keyword-based classification result

### REQ-IRLC-04: zsiga.yaml SHALL include llm_fast configuration section

The `zsiga.yaml` configuration file SHALL include an `llm_fast` section under `agent` with `model` set to `glm-4-flash` and `base_url` set to the appropriate API endpoint.

#### Scenario: llm_fast config is parsed correctly

- **Given** `zsiga.yaml` contains `agent.llm_fast` with `api_key`, `model`, and `base_url`
- **When** `load_config()` is called
- **Then** `config.llm_fast` SHALL be a `LLMFastConfig` instance with the specified values

### REQ-IRLC-05: Existing keyword-based tests SHALL continue to pass

All existing tests in `tests/test_intent_router.py` SHALL pass without modification when `llm_fast` config is absent or when LLM calls fail (i.e., keyword fallback MUST produce the same results as before).

#### Scenario: All existing tests pass with keyword-only fallback

- **Given** the LLM is unavailable or returns errors
- **When** the existing test suite runs
- **Then** every test case SHALL produce the same `Intent` as before this change
