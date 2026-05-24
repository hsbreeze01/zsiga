# Gate Runtime Behavior

> **⚠️ Critical dependency**: These requirements describe the **intended**
> runtime behavior when `proposal_gate` and `design_gate` are enabled.
> Their fulfillment depends on Python code that **reads** the gate
> configuration and **enforces** gate logic. The clarify phase confirmed
> that consuming Python code for gate enforcement must already exist in
> the daemon/pipeline modules. These requirements define the behavioral
> contract that the enabled gates SHALL satisfy when the daemon processes
> proposals.

## ADDED Requirements

### Requirement: Proposal Gate Execution Before Pipeline

When `pipeline.proposal_gate.enabled` is `true`, every new proposal
(non-FIX intent) SHALL pass through the Proposal Gate (Steward role)
before any pipeline phase executes. The Steward evaluates the proposal
against historical lessons and codebase facts, producing a verdict.

#### Scenario: new-proposal-intercepted-by-steward

- **testable**: false
- **Given** `pipeline.proposal_gate.enabled` is `true` in zsiga.yaml
- **When** a new non-FIX proposal enters the daemon cycle
- **Then** the Proposal Gate (Steward) SHALL evaluate the proposal before
  the ENRICH phase begins
- **And** the Steward SHALL produce an accept / pushback / reject verdict
  with a numeric score

#### Scenario: proposal-gate-rejects-below-threshold

- **testable**: false
- **Given** `pipeline.proposal_gate.enabled` is `true` in zsiga.yaml
- **And** a proposal scores below `score_pushback` (3)
- **When** the Steward evaluates the proposal
- **Then** the proposal SHALL be rejected with a diagnostic reason
- **And** the cycle SHALL NOT proceed to ENRICH

#### Scenario: proposal-gate-pushback-mid-range

- **testable**: false
- **Given** `pipeline.proposal_gate.enabled` is `true` in zsiga.yaml
- **And** a proposal scores between `score_pushback` (3) and
  `score_accept` (6) inclusive
- **When** the Steward evaluates the proposal
- **Then** the proposal SHALL receive a pushback verdict with improvement
  suggestions
- **And** the cycle MAY retry up to `max_retries` (1) times

---

### Requirement: Design Gate Execution After ENRICH

When `pipeline.design_gate.enabled` is `true`, the Design Gate (Judge role)
SHALL evaluate the design/spec artifacts produced by the ENRICH phase
before the IMPLEMENT phase begins.

#### Scenario: enrich-output-reviewed-by-judge

- **testable**: false
- **Given** `pipeline.design_gate.enabled` is `true` in zsiga.yaml
- **When** the ENRICH phase completes successfully
- **Then** the Design Gate (Judge) SHALL evaluate the design artifacts
- **And** the Judge SHALL produce an accept / pushback / reject verdict

#### Scenario: design-gate-rejects-poor-design

- **testable**: false
- **Given** `pipeline.design_gate.enabled` is `true` in zsiga.yaml
- **And** ENRICH produces a design with quality below the accept threshold
- **When** the Judge evaluates the design
- **Then** the design SHALL be rejected
- **And** the cycle SHALL NOT proceed to IMPLEMENT

---

### Requirement: Gate Toggle Immediate Effect

Changing `proposal_gate.enabled` or `design_gate.enabled` in zsiga.yaml
SHALL take effect on the next daemon cycle without requiring code changes
or daemon restart (if the daemon reloads config per cycle).

#### Scenario: disabling-gate-takes-effect-next-cycle

- **testable**: false
- **Given** `pipeline.proposal_gate.enabled` is `true`
- **When** the value is changed to `false` in zsiga.yaml
- **Then** the next daemon cycle SHALL skip the Proposal Gate entirely

---

### Requirement: FIX Intent Fast Pipeline Unaffected

The FIX intent fast pipeline (which skips CLARIFY/ENRICH) SHALL NOT be
affected by gate configuration. Gates apply only to the full pipeline
path for non-FIX intents.

#### Scenario: fix-intent-bypasses-all-gates

- **testable**: false
- **Given** `pipeline.proposal_gate.enabled` is `true` and
  `pipeline.design_gate.enabled` is `true`
- **When** a FIX intent is processed
- **Then** neither the Proposal Gate nor the Design Gate SHALL be invoked
- **And** the FIX pipeline SHALL proceed directly to IMPLEMENT as before
