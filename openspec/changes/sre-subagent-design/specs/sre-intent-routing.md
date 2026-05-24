# Spec: SRE Intent Routing

## ADDED Requirements

### Requirement: SRE Intent Type in Intent Router

The intent router SHALL recognize a new `sre` intent type for infrastructure operations messages. The `IntentType` enum MUST include an `SRE` member with value `"sre"`.

#### Scenario: SRE value in IntentType enum

- **testable**: true
- **target**: zsiga/agent/intent_router.py::IntentType
- **Given** the `IntentType` enum is loaded
- **When** accessing `IntentType("sre")` and `IntentType.SRE.value`
- **Then** `IntentType("sre")` SHALL be `IntentType.SRE` and `.value` SHALL equal `"sre"`

---

### Requirement: SRE Keyword Classification

The `classify()` function SHALL detect SRE keywords in both Chinese and English and return an `Intent` with `intent_type == IntentType.SRE`. Chinese keywords: 服务、重启、健康、清理、磁盘、宕机、日志、进程、监控. English keywords: restart, service, health, cleanup, disk, down, log, process, monitor.

#### Scenario: Chinese SRE keywords classified as SRE intent

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message containing Chinese SRE keywords (e.g., "服务重启，磁盘满了")
- **When** `classify(msg)` is called
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.SRE`

#### Scenario: English SRE keywords classified as SRE intent

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message containing English SRE keywords (e.g., "restart the nginx service and check health")
- **When** `classify(msg)` is called
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.SRE`

---

### Requirement: SRE Priority Over Implementation Keywords

When a message contains SRE keywords but no FIX keywords, `classify()` SHALL return `IntentType.SRE` rather than `IntentType.IMPLEMENTATION`.

#### Scenario: SRE intent takes priority over implementation keywords

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message like "清理磁盘空间" containing SRE keywords but no FIX keywords
- **When** `classify(msg)` is called
- **Then** `result.intent_type` SHALL be `IntentType.SRE`

---

### Requirement: FIX Intent Preserves Priority Over SRE

When a message contains FIX keywords (修复, fix, bug), `classify()` MUST return `IntentType.FIX` even if SRE keywords are also present. FIX intent takes precedence over SRE.

#### Scenario: FIX intent is not overridden by SRE keywords

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message like "修复日志错误" containing both FIX and SRE keywords
- **When** `classify(msg)` is called
- **Then** `result.intent_type` SHALL be `IntentType.FIX`

---

### Requirement: Non-SRE Messages Not Misclassified

Messages that do not contain SRE or FIX keywords SHALL NOT be classified as `IntentType.SRE`. Pure implementation messages SHALL remain `IntentType.IMPLEMENTATION`. Empty messages SHALL be `IntentType.OPEN_ENDED`.

#### Scenario: Pure implementation message not misclassified as SRE

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** a message like "实现一个新功能模块"
- **When** `classify(msg)` is called
- **Then** `result.intent_type` SHALL be `IntentType.IMPLEMENTATION`

#### Scenario: Empty message does not produce SRE intent

- **testable**: true
- **target**: zsiga/agent/intent_router.py::classify
- **Given** an empty string message
- **When** `classify("")` is called
- **Then** `result.intent_type` SHALL be `IntentType.OPEN_ENDED`

---

### Requirement: SRE Intent Route Dispatch

The `route()` function SHALL return `"dispatch_sre"` when given an `Intent` with `intent_type == IntentType.SRE`.

#### Scenario: Route returns dispatch_sre for SRE intent type

- **testable**: true
- **target**: zsiga/agent/intent_router.py::route
- **Given** an `Intent` with `intent_type=IntentType.SRE`
- **When** `route(intent)` is called
- **Then** the return value SHALL be `"dispatch_sre"`

---

### Requirement: SRE Verbalization

The `_verbalize()` function SHALL produce a verbalization containing SRE-related terms (运维, 基础设施, SRE, infrastructure, operations) when the input message contains SRE keywords.

#### Scenario: Chinese SRE verbalization

- **testable**: true
- **target**: zsiga/agent/intent_router.py::_verbalize
- **Given** a message like "重启服务检查健康状态"
- **When** `_verbalize(msg)` is called
- **Then** the result SHALL contain at least one of: "运维", "基础设施", or "SRE"

#### Scenario: English SRE verbalization

- **testable**: true
- **target**: zsiga/agent/intent_router.py::_verbalize
- **Given** a message like "restart service and check health status"
- **When** `_verbalize(msg)` is called
- **Then** the result SHALL contain at least one of: "infrastructure", "SRE", or "operations"

---

### Requirement: SRE and Implementation Intent Mutual Exclusion

A single message SHALL NOT be classified as both SRE and IMPLEMENTATION. When SRE keywords dominate, the result MUST be `IntentType.SRE`; when implementation keywords dominate without SRE keywords, the result MUST be `IntentType.IMPLEMENTATION`.

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
