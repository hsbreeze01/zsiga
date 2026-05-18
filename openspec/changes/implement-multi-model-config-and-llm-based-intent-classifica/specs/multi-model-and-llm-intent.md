# Delta Spec: Multi-Model Config & LLM-Based Intent Classification

## ADDED Requirements

### Requirement: llm_fast Configuration Section

The system SHALL support an optional `llm_fast` configuration section under `agent` in `zsiga.yaml`, providing a separate fast/cheap LLM endpoint for latency-sensitive operations (e.g., intent classification).

#### Scenario: User configures a dedicated fast model for lightweight operations

- **Given** a `zsiga.yaml` with an `agent.llm_fast` section specifying `api_key`, `model`, and `base_url`
- **When** the configuration is loaded
- **Then** the system SHALL parse `llm_fast` into an `LLMFastConfig` object with fields: `api_key`, `model`, `base_url`
- **And** `model` SHALL default to `"glm-4-flash"`
- **And** `base_url` SHALL default to `"https://open.bigmodel.cn/api/paas/v4"`

#### Scenario: llm_fast section is absent from config

- **Given** a `zsiga.yaml` without an `agent.llm_fast` section
- **When** the configuration is loaded
- **Then** `ZsigaConfig.llm_fast` SHALL be `None`
- **And** the system SHALL still function using keyword-only intent classification

#### Scenario: llm_fast inherits api_key from main llm when omitted

- **Given** a `zsiga.yaml` with `agent.llm.api_key` set but `agent.llm_fast.api_key` omitted
- **When** the configuration is loaded
- **Then** the system SHALL use the main `llm.api_key` as the `llm_fast.api_key` default

---

### Requirement: LLM-Based Intent Classification with Keyword Fallback

The `classify()` function in `intent_router.py` SHALL attempt LLM-based classification first when `llm_fast` is configured, and fall back to keyword matching on any LLM failure or timeout.

#### Scenario: LLM returns a valid structured JSON response

- **Given** `llm_fast` is configured and reachable
- **When** `classify("修复一下这个登录 bug")` is called
- **Then** the system SHALL call the fast LLM with a structured prompt requesting JSON output with fields: `intent_type`, `confidence`, `verbalization`, `reasoning`
- **And** the returned `Intent` SHALL use values from the LLM response
- **And** `intent_type` SHALL be one of the six valid `IntentType` enum values

#### Scenario: LLM returns invalid or unexpected JSON

- **Given** `llm_fast` is configured
- **When** the LLM response cannot be parsed into the expected JSON structure
- **Then** the system SHALL fall back to the existing keyword-based classification
- **And** the `Intent.reasoning` field SHALL indicate fallback occurred

#### Scenario: LLM call times out

- **Given** `llm_fast` is configured
- **When** the LLM call exceeds the configured timeout (default 3 seconds)
- **Then** the system SHALL fall back to keyword-based classification
- **And** no unhandled exception SHALL propagate to the caller

#### Scenario: LLM returns an intent_type not in the valid enum

- **Given** `llm_fast` is configured and returns a response
- **When** the `intent_type` field in the JSON does not match any `IntentType` enum value
- **Then** the system SHALL fall back to keyword-based classification

#### Scenario: LLM is not configured (llm_fast is None)

- **Given** `llm_fast` is `None` in the config
- **When** `classify()` is called
- **Then** the system SHALL use keyword-based classification directly without any LLM call

---

### Requirement: Structured JSON Prompt for Intent Classification

The LLM prompt for intent classification SHALL request a specific JSON output format to ensure parseable and consistent responses.

#### Scenario: Prompt construction for classification

- **Given** the system is preparing an LLM call for intent classification
- **When** the prompt is constructed
- **Then** it SHALL include the user message and a list of the six valid intent types
- **And** it SHALL request JSON output with exactly these fields: `intent_type` (string), `confidence` (float 0-1), `verbalization` (string), `reasoning` (string)
- **And** the prompt SHALL instruct the LLM to output ONLY valid JSON with no additional text

---

## MODIFIED Requirements

### Requirement: ZsigaConfig Data Model

The `ZsigaConfig` class SHALL be extended to include an optional `llm_fast` field.

#### Scenario: ZsigaConfig with llm_fast

- **Given** a valid configuration with both `llm` and `llm_fast` sections
- **When** `ZsigaConfig` is instantiated
- **Then** `config.llm_fast` SHALL be an `LLMFastConfig` instance
- **And** `config.llm` SHALL remain unchanged

#### Scenario: ZsigaConfig without llm_fast

- **Given** a valid configuration with only `llm` section
- **When** `ZsigaConfig` is instantiated
- **Then** `config.llm_fast` SHALL be `None`
