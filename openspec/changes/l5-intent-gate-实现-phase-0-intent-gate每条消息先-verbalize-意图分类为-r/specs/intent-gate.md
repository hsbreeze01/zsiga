# Delta Spec: Intent Gate (Phase 0)

## MODIFIED Requirements

### REQ-IG-01: Intent Classification — Six Categories

The system SHALL classify every incoming user message into exactly one of six intent categories **before** any pipeline routing occurs:

| Category | Description |
|---|---|
| `research` | User wants to explore, understand, or analyze existing code/data without making changes |
| `implementation` | User wants to build, add, modify, or create new functionality |
| `investigation` | User wants to debug, diagnose, or trace a specific problem or error |
| `evaluation` | User wants to review, assess quality, or compare alternatives |
| `fix` | User wants to repair a known defect, test failure, or lint error |
| `open-ended` | Ambiguous or conversational input that does not fit the above categories |

#### Scenario: Classify a research request
- **Given** a user message containing "分析一下" / "explain" / "how does X work"
- **When** the intent gate processes the message
- **Then** the system SHALL return `IntentType.RESEARCH` with confidence ≥ 0.6

#### Scenario: Classify an implementation request
- **Given** a user message containing "实现" / "添加" / "create" / "build"
- **When** the intent gate processes the message
- **Then** the system SHALL return `IntentType.IMPLEMENTATION` with confidence ≥ 0.6

#### Scenario: Classify an investigation request
- **Given** a user message containing "排查" / "为什么报错" / "debug" / "trace"
- **When** the intent gate processes the message
- **Then** the system SHALL return `IntentType.INVESTIGATION` with confidence ≥ 0.6

#### Scenario: Classify an evaluation request
- **Given** a user message containing "评估" / "review" / "compare" / "quality"
- **When** the intent gate processes the message
- **Then** the system SHALL return `IntentType.EVALUATION` with confidence ≥ 0.6

#### Scenario: Classify a fix request
- **Given** a user message containing "修复" / "fix" / "修bug" / "failed"
- **When** the intent gate processes the message
- **Then** the system SHALL return `IntentType.FIX` with confidence ≥ 0.6

#### Scenario: Classify ambiguous input
- **Given** a user message that matches no strong category keywords
- **When** the intent gate processes the message
- **Then** the system SHALL return `IntentType.OPEN_ENDED` with a verbalization noting the ambiguity

---

### REQ-IG-02: Verbalization — Pre-classification Intent Summary

Before classification, the system SHALL produce a **verbalization**: a one-sentence summary of what the user is asking, written in the same language as the input.

#### Scenario: Verbalization of a research message
- **Given** user input "这个模块的职责是什么"
- **When** the intent gate verbalizes
- **Then** the verbalization SHALL be a concise statement like "用户想了解某模块的职责（研究性质）"

#### Scenario: Verbalization of a fix message
- **Given** user input "pytest 跑不过了，帮我修一下"
- **When** the intent gate verbalizes
- **Then** the verbalization SHALL be a concise statement like "用户希望修复 pytest 失败问题"

#### Scenario: Verbalization of empty input
- **Given** an empty or whitespace-only message
- **When** the intent gate verbalizes
- **Then** the verbalization SHALL be "空消息，无法判断意图"

---

### REQ-IG-03: Routing Map — Intent to Execution Path

After verbalization and classification, the system SHALL route to the corresponding execution path:

| Intent | Route Target |
|---|---|
| `research` | `dispatch_explore` — read-only sub-agent with explore role |
| `implementation` | `pipeline` — full ENRICH → IMPLEMENT → VERIFY → DELIVER |
| `investigation` | `dispatch_diagnoser` — read-only sub-agent with diagnoser role |
| `evaluation` | `dispatch_review` — read-only sub-agent with review role |
| `fix` | `pipeline_fix` — shortened pipeline: IMPLEMENT (fix only) → VERIFY |
| `open-ended` | `ask_user` — ask for clarification |

#### Scenario: Research routes to explore agent
- **Given** an intent classified as `RESEARCH`
- **When** the orchestrator processes the route
- **Then** the system SHALL dispatch an explore-role sub-agent with read-only tools

#### Scenario: Implementation routes to full pipeline
- **Given** an intent classified as `IMPLEMENTATION`
- **When** the orchestrator processes the route
- **Then** the system SHALL execute the full pipeline (ENRICH → IMPLEMENT → VERIFY → DELIVER)

#### Scenario: Investigation routes to diagnoser
- **Given** an intent classified as `INVESTIGATION`
- **When** the orchestrator processes the route
- **Then** the system SHALL dispatch a diagnoser-role sub-agent

#### Scenario: Fix routes to shortened pipeline
- **Given** an intent classified as `FIX`
- **When** the orchestrator processes the route
- **Then** the system SHALL skip ENRICH and go directly to IMPLEMENT → VERIFY

#### Scenario: Open-ended asks user
- **Given** an intent classified as `OPEN_ENDED`
- **When** the orchestrator processes the route
- **Then** the system SHALL respond asking for clarification

---

### REQ-IG-04: Intent Data Model

The `Intent` dataclass SHALL carry the following fields:

| Field | Type | Description |
|---|---|---|
| `verbalization` | `str` | One-sentence summary of user intent |
| `intent_type` | `IntentType` | One of the six enum values |
| `confidence` | `float` | 0.0–1.0 classification confidence |
| `reasoning` | `str` | Why this category was chosen |
| `suggested_action` | `str` | Human-readable action description |

#### Scenario: Intent object has verbalization
- **Given** any non-empty user message
- **When** `classify()` is called
- **Then** the returned `Intent.verbalization` SHALL be a non-empty string

#### Scenario: Intent object has valid confidence
- **Given** any user message
- **When** `classify()` is called
- **Then** `Intent.confidence` SHALL be between 0.0 and 1.0 inclusive

---

### REQ-IG-05: Logging — Intent Gate Decision

Every intent gate decision SHALL be logged with the verbalization, category, confidence, and route target.

#### Scenario: Intent decision is logged
- **Given** a user message processed by the intent gate
- **When** classification completes
- **Then** the system SHALL print a log line containing the verbalization, intent type, confidence, and route target
