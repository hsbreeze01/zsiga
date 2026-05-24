# Spec: SRE Intent Routing

## ADDED Requirements

### Requirement: SRE Intent Type

The `IntentType` enum SHALL include a new value `SRE = "sre"` representing infrastructure operations intent. The `route()` function SHALL map `IntentType.SRE` to `"dispatch_sre"`.

#### Scenario: Route returns dispatch_sre for SRE intent type

- **testable**: true
- **target**: zsiga.agent.intent_router::route
- **Given** an `Intent` object with `intent_type=IntentType.SRE`
- **When** `route(intent)` is called
- **Then** the return value SHALL be `"dispatch_sre"`

#### Scenario: SRE value in IntentType enum

- **testable**: true
- **target**: zsiga.agent.intent_router::IntentType
- **Given** the `IntentType` enum
- **When** `IntentType("sre")` is called
- **Then** it SHALL return `IntentType.SRE`

### Requirement: SRE Keyword Detection

The `classify()` function SHALL detect SRE intent when the user message contains any of the following keywords (Chinese or English): 服务, 重启, 健康检测, 清理, 磁盘, 宕机, 日志, 进程, 监控, systemctl, service, restart, health, cleanup, disk, downtime, log, process, monitor, nginx, apache, docker, container, deploy, deployment, uptime, load, memory, cpu, swap, zombie, oom, kill, port, socket, tunnel, ssh, cron, journalctl, dmesg.

SRE keyword detection SHALL take priority over IMPLEMENTATION and RESEARCH keyword matches when both are present. SRE detection MUST NOT override FIX intent (fix/修复 keywords remain highest priority for bug fixing).

#### Scenario: Chinese SRE keywords classified as SRE intent

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** a user message containing "服务重启，磁盘满了"
- **When** `classify(message)` is called without LLM config (keyword-only)
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.SRE`

#### Scenario: English SRE keywords classified as SRE intent

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** a user message containing "restart the nginx service and check health"
- **When** `classify(message)` is called without LLM config
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.SRE`

#### Scenario: SRE intent takes priority over implementation keywords

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** a user message containing "清理磁盘空间" (cleanup + disk, both SRE and implementation keywords)
- **When** `classify(message)` is called without LLM config
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.SRE`

#### Scenario: FIX intent is not overridden by SRE keywords

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** a user message containing "修复日志错误" (fix + log keywords)
- **When** `classify(message)` is called without LLM config
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.FIX`

#### Scenario: Pure implementation message not misclassified as SRE

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** a user message containing "实现一个新功能模块" (only implementation keywords)
- **When** `classify(message)` is called without LLM config
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.IMPLEMENTATION`

#### Scenario: Empty message does not produce SRE intent

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** an empty user message
- **When** `classify("")` is called
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.OPEN_ENDED`

### Requirement: SRE Verbalization

When SRE intent is detected via keywords, the `_verbalize()` function SHALL return a verbalization that identifies the intent as infrastructure operations.

#### Scenario: Chinese SRE verbalization

- **testable**: true
- **target**: zsiga.agent.intent_router::_verbalize
- **Given** a message containing SRE keywords in Chinese
- **When** `_verbalize(message)` is called
- **Then** the verbalization SHALL contain "运维" or "基础设施" or "SRE"

#### Scenario: English SRE verbalization

- **testable**: true
- **target**: zsiga.agent.intent_router::_verbalize
- **Given** a message containing SRE keywords in English
- **When** `_verbalize(message)` is called
- **Then** the verbalization SHALL contain "infrastructure" or "SRE" or "operations"

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
