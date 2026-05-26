# Spec: Phase Token Cap — Orchestrator Phase Injection

## MODIFIED Requirements

### Requirement: Phase cap injection before each phase

The orchestrator SHALL set `self.agent.budget.phase_cap` after each call to
`self.agent.set_phase(phase_name)` but before the phase's main work begins.
The cap value SHALL be obtained from
`self.config.pipeline.get_phase_cap(phase_name)`.

**Phase name mapping.** The orchestrator uses internal labels that differ
from `PHASE_TOKEN_CAPS` keys in one case:

| Orchestrator label | PHASE_TOKEN_CAPS key |
|--------------------|----------------------|
| `"clarify"`        | `"clarify"`          |
| `"enrich"`         | `"enrich"`           |
| `"impl"`           | `"implement"`        |
| `"verify"`         | `"verify"`           |
| `"optimize"`       | `"optimize"`         |
| `"reflect"`        | `"reflect"`          |
| `"deliver"`        | `"deliver"`          |

The orchestrator SHALL apply this mapping so that `get_phase_cap()` is
called with the correct `PHASE_TOKEN_CAPS` key.  For example, before the
implement phase (`set_phase("impl")`), the cap SHALL be obtained via
`get_phase_cap("implement")`.

Note: `set_phase()` already resets `_used` to zero, so a separate call to
`reset_phase()` is not required at phase boundaries.  The orchestrator
SHALL only set `phase_cap` after `set_phase()`.

#### Scenario: Orchestrator sets phase_cap before clarify phase

- **testable**: false
- **Given** an orchestrator with a `PipelineConfig` containing default
  `PHASE_TOKEN_CAPS`
- **When** the clarify phase is about to start
- **Then** `self.agent.budget.phase_cap` SHALL be set to `200000`

#### Scenario: Orchestrator sets phase_cap before implement phase

- **testable**: false
- **Given** an orchestrator with a default `PipelineConfig`
- **When** the implement phase (labelled `"impl"` internally) is about to
  start
- **Then** `self.agent.budget.phase_cap` SHALL be set to `800000`

#### Scenario: Orchestrator sets phase_cap before verify phase

- **testable**: false
- **Given** an orchestrator with a default `PipelineConfig`
- **When** the verify phase is about to start
- **Then** `self.agent.budget.phase_cap` SHALL be set to `150000`

#### Scenario: Orchestrator sets phase_cap before enrich phase

- **testable**: false
- **Given** an orchestrator with a default `PipelineConfig`
- **When** the enrich phase is about to start
- **Then** `self.agent.budget.phase_cap` SHALL be set to `400000`

### Requirement: CAP_EXCEEDED graceful handling

When a phase returns a `RunResult` with `content="CAP_EXCEEDED"`, the
orchestrator SHALL log a WARNING message and proceed to the next phase.
It SHALL NOT revert, retry, or treat the phase as a hard failure.

The phase record for the exceeded phase SHALL be recorded with
`outcome=Outcome.FAIL` and a `detail` field containing the string
`"CAP_EXCEEDED"`, consistent with the existing `BUDGET_EXCEEDED` handling
pattern (e.g., the enrich and implement phases already record
`Outcome.FAIL` with `detail="BUDGET_EXCEEDED"` when budget is exceeded).

#### Scenario: CAP_EXCEEDED triggers warning log and continues

- **testable**: false
- **Given** the enrich phase returns `content="CAP_EXCEEDED"`
- **When** the orchestrator processes the result
- **Then** a WARNING SHALL be logged mentioning the phase name and token
  usage
- And the orchestrator SHALL proceed to the next phase without revert or
  retry

#### Scenario: CAP_EXCEEDED phase record has correct detail

- **testable**: false
- **Given** the implement phase returns `content="CAP_EXCEEDED"`
- **When** the phase record is appended
- **Then** `detail` SHALL contain the string `"CAP_EXCEEDED"`
- And `outcome` SHALL be `Outcome.FAIL`

### Requirement: CAP_EXCEEDED does not trigger revert

Unlike `BUDGET_EXCEEDED` which can lead to `git_ops.reset_hard()` and
rollback, `CAP_EXCEEDED` SHALL NOT cause any rollback of the working tree.
The phase's partial work SHALL be preserved for subsequent phases (review,
verify, etc.) to evaluate.

#### Scenario: No revert after CAP_EXCEEDED in implement phase

- **testable**: false
- **Given** the implement phase returns `content="CAP_EXCEEDED"`
- **When** the orchestrator processes the result
- **Then** `git_ops.reset_hard()` SHALL NOT be called
- And the review/verify phases SHALL proceed with the working tree as-is

#### Scenario: No revert after CAP_EXCEEDED in enrich phase

- **testable**: false
- **Given** the enrich phase returns `content="CAP_EXCEEDED"`
- **When** the orchestrator processes the result
- **Then** the orchestrator SHALL continue to the implement phase
- And no git rollback SHALL occur
