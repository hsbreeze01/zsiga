# Delta Spec: Intent Routing in Orchestrator

## ADDED Requirements

### REQ-IR-01: Pre-pipeline Intent Classification

The orchestrator SHALL classify the intent of each proposal before entering the pipeline phases.

#### Scenario: Implementation intent proceeds through full pipeline

- **Given** a proposal with content containing implementation keywords (e.g. "添加", "实现", "create", "fix")
- **When** the orchestrator processes the change
- **Then** it SHALL call `intent_router.classify()` on the proposal content
- **And** the classified intent type SHALL be `IMPLEMENTATION`
- **And** the routing path SHALL be `"pipeline"`
- **And** processing SHALL continue through ENRICH → IMPLEMENT → VERIFY → DELIVER phases

#### Scenario: Exploration intent skips pipeline

- **Given** a proposal with content containing exploration keywords (e.g. "如何", "how", "explore")
- **When** the orchestrator processes the change
- **Then** it SHALL classify the intent as `EXPLORATION`
- **And** the routing path SHALL be `"dispatch_explore"`
- **And** the orchestrator SHALL skip the standard pipeline phases and return `False`

#### Scenario: Trivial intent responds directly

- **Given** a proposal with content matching trivial patterns (short greetings)
- **When** the orchestrator processes the change
- **Then** it SHALL classify the intent as `TRIVIAL`
- **And** the routing path SHALL be `"respond_directly"`
- **And** the orchestrator SHALL skip the pipeline and return `False`

### REQ-IR-02: Intent Classification Logging

The orchestrator SHALL log the intent classification result for observability.

#### Scenario: Intent classification is logged

- **Given** any proposal being processed
- **When** the orchestrator classifies the proposal intent
- **Then** it SHALL print the intent type, confidence, and routing path to stdout
- **And** the `PhaseRecord.detail` for the phase SHALL include the intent classification summary

### REQ-IR-03: Ambiguous Intent Fallback

The orchestrator SHALL treat ambiguous intents as implementation by default, preserving backward compatibility.

#### Scenario: Ambiguous intent falls through to pipeline

- **Given** a proposal with content that matches no clear intent pattern
- **When** the orchestrator classifies the intent
- **Then** the intent type SHALL be `AMBIGUOUS`
- **And** the orchestrator SHALL proceed with the standard pipeline as a safe default
