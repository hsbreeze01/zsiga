# Spec: Confidence Gate for Low-Confidence Classifications

## ADDED Requirements

### Requirement: Low-Confidence Explore Gate

When the intent classifier returns confidence below the threshold (0.6),
the orchestrator SHALL dispatch an explore sub-agent to gather additional
context before making a final routing decision.

#### Scenario: Low confidence triggers explore-first

- **Given** a proposal classified with `confidence < 0.6`
- **And** the classified intent_type is not `OPEN_ENDED`
- **When** the orchestrator evaluates the confidence gate
- **Then** an explore sub-agent SHALL be dispatched with the proposal text
- **And** the sub-agent result SHALL be appended to the proposal context
- **And** the proposal SHALL be re-classified with the enriched context
- **And** the reclassification SHALL be recorded via `update_intent_reclassification()`

#### Scenario: High confidence bypasses gate

- **Given** a proposal classified with `confidence >= 0.6`
- **When** the orchestrator evaluates the confidence gate
- **Then** no explore sub-agent SHALL be dispatched
- **And** the original classification SHALL be used for routing

#### Scenario: Open-ended intent skips gate

- **Given** a proposal classified as `OPEN_ENDED`
- **When** the orchestrator evaluates the confidence gate
- **Then** the confidence gate SHALL be skipped
- **And** the `ask_user` route SHALL be used directly

#### Scenario: Explore fails — use original classification

- **Given** a proposal with `confidence < 0.6`
- **And** the explore sub-agent fails or returns no useful content
- **When** reclassification is attempted
- **Then** the original classification SHALL be used as fallback
- **And** the confidence SHALL remain unchanged

#### Scenario: Reclassification changes intent type

- **Given** a proposal originally classified as `research` with confidence 0.5
- **When** the explore sub-agent returns context revealing this is an implementation task
- **And** reclassification returns `implementation` with confidence 0.8
- **Then** the new intent SHALL be used for routing
- **And** `reclassified_from` = `"research"`, `reclassified_to` = `"implementation"` SHALL be recorded
