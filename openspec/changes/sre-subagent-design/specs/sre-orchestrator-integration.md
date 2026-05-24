# Spec: SRE Orchestrator Integration

## ADDED Requirements

### Requirement: SRE Intent Routing Mutual Exclusion with Implementation

The orchestrator SHALL route SRE-intent messages to the SRE pipeline and NOT to the code pipeline. Messages classified as `IntentType.SRE` SHALL NOT be simultaneously classified as `IntentType.IMPLEMENTATION`.

#### Scenario: SRE intent not also classified as implementation

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message like "检查服务健康状态"
- **When** `classify(msg)` is called
- **Then** `result.intent_type` SHALL be `IntentType.SRE` and SHALL NOT be `IntentType.IMPLEMENTATION`

#### Scenario: Implementation intent not classified as SRE

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message like "实现用户登录模块"
- **When** `classify(msg)` is called
- **Then** `result.intent_type` SHALL be `IntentType.IMPLEMENTATION` and SHALL NOT be `IntentType.SRE`

---

### Requirement: FIX Intent Priority Over SRE in Orchestrator

When a message contains both FIX and SRE keywords, the intent classifier MUST classify it as `IntentType.FIX`. FIX intent has higher priority than SRE in the routing hierarchy.

#### Scenario: SRE mutual exclusion — fix has priority over SRE

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message like "修复服务启动失败的问题" containing both FIX and SRE keywords
- **When** `classify(msg)` is called
- **Then** `result.intent_type` SHALL be `IntentType.FIX`

---

### Requirement: Mixed SRE and Research Keywords Resolved to SRE

When a message contains both SRE and research keywords (查看, 分析) without FIX keywords, the classifier SHALL classify it as `IntentType.SRE`. SRE keywords dominate research intent.

#### Scenario: Mixed SRE + research keywords resolved to SRE

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message like "查看日志分析磁盘问题" containing both research and SRE keywords
- **When** `classify(msg)` is called
- **Then** `result.intent_type` SHALL be `IntentType.SRE`

---

### Requirement: SRE Pipeline Bypasses Code Pipeline Phases

When the orchestrator routes to the SRE pipeline, it SHALL NOT enter the code pipeline's ENRICH → IMPLEMENT → VERIFY flow. The SRE pipeline follows its own DIAGNOSE → PLAN → EXECUTE → VERIFY → REPORT phases.

#### Scenario: SRE pipeline does not enter code phases

- **testable**: false
- **Given** an SRE-intent message dispatched by the orchestrator
- **When** the SRE pipeline runs to completion
- **Then** no ENRICH, IMPLEMENT, or code-VERIFY phases SHALL be invoked
