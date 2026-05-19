# Delta Spec: OpenSpec Source Awareness (Verification Spec)

## MODIFIED Requirements

### Requirement: OpenSpec Source Parameter on classify()

The `classify()` function SHALL accept an optional `source` parameter.
When `source="openspec"`, the function MUST return an IMPLEMENTATION intent
immediately, bypassing all keyword matching and LLM classification.

#### Scenario: classify() called with source="openspec"

- **Given** a non-empty message string
- **When** `classify(message, source="openspec")` is called
- **Then** the returned Intent SHALL have `intent_type=IMPLEMENTATION`
- **And** `confidence` SHALL be 0.95
- **And** `reasoning` SHALL reference the OpenSpec source
- **And** no keyword matching or LLM calls SHALL be performed

#### Scenario: classify() called with source=None (default)

- **Given** a non-empty message string
- **When** `classify(message)` is called (no source argument)
- **Then** the function SHALL proceed through the normal keyword/LLM classification path
- **And** the source parameter SHALL have no effect on the result

#### Scenario: orchestrator passes source="openspec" for proposals

- **Given** the orchestrator reads a proposal from `openspec/changes/` directory
- **When** it calls `classify(proposal_text, source="openspec")`
- **Then** the intent SHALL always be IMPLEMENTATION regardless of proposal content
