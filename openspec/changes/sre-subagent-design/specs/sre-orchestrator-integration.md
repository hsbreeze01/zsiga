# Spec: SRE Pipeline Orchestrator Integration

## ADDED Requirements

### Requirement: SRE Dispatch in Orchestrator

The `ZsigaOrchestrator._process_change()` method SHALL handle `route_path == "dispatch_sre"` by dispatching to the SRE pipeline instead of the code pipeline. When dispatched to SRE, the orchestrator SHALL NOT create a `ChangeRecord`, SHALL NOT run the ENRICH→IMPLEMENT→VERIFY→DELIVER phases, and SHALL NOT perform git operations (feature branch, commit, tag, push).

#### Scenario: SRE intent routes to dispatch_sre in orchestrator

- **testable**: true
- **target**: zsiga.pipeline.orchestrator::ZsigaOrchestrator._process_change
- **Given** a proposal with intent classified as `IntentType.SRE` and `route_path == "dispatch_sre"`
- **When** `_process_change(prop)` is called
- **Then** the SRE pipeline SHALL be invoked
- **And** the code pipeline phases SHALL NOT execute

### Requirement: SRE and Code Pipeline Mutual Exclusion

When an intent is classified as `IntentType.SRE`, it SHALL NOT simultaneously be classified as `IntentType.IMPLEMENTATION` or `IntentType.FIX`. The `classify()` function SHALL return exactly one `IntentType` value. The orchestrator SHALL dispatch to exactly one pipeline based on the route.

#### Scenario: SRE intent not also classified as implementation

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** a message containing only SRE keywords (e.g., "检查服务健康状态")
- **When** `classify(message)` is called without LLM config
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.SRE`
- **And** SHALL NOT be `IntentType.IMPLEMENTATION`

#### Scenario: Implementation intent not classified as SRE

- **testable**: true
- **target**: zsiga.agent.intent_router::classify
- **Given** a message containing only implementation keywords (e.g., "实现用户登录模块")
- **When** `classify(message)` is called without LLM config
- **Then** the returned `Intent.intent_type` SHALL be `IntentType.IMPLEMENTATION`
- **And** SHALL NOT be `IntentType.SRE`

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
