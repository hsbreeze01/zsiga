# Spec: Self-Assessment Reflect Write

Ensures REFLECT phase executes and writes self-assessment records for **all**
pipeline outcomes, not only for successful changes.

## MODIFIED Requirements

### Requirement: REFLECT phase executes on reverted changes

The pipeline orchestrator's `_run_phases()` method SHALL invoke
`phase_reflect()` before returning `False` on any reverted path.  Currently
REFLECT is only called after a successful VERIFY; reverted changes skip
REFLECT entirely, which is why the `self_assessment` table has near-zero rows.

This applies to both the IMPLEMENT-failure revert path and the
VERIFY-failure revert path.

#### Scenario: reflect-called-on-verify-fail

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator.phase_reflect

- **Given** a `ChangeRecord` whose `outcome` is `Outcome.REVERTED`, with an
  IMPLEMENT `PhaseRecord` (`fix_attempts=3`) and a VERIFY `PhaseRecord`
  (`fix_attempts=2`)
- **When** `phase_reflect(rec, change_name, project_name, task_type,
  change_dir, transport)` is called
- **Then** a row is inserted into the `self_assessment` SQLite table with
  `outcome="reverted"` and `self_rating="poor"`
- **And** `rec.phases` has an appended `PhaseRecord` with
  `phase=Phase.REFLECT`

#### Scenario: reflect-md-written-on-reverted

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator.phase_reflect

- **Given** a `ChangeRecord` with `outcome=Outcome.REVERTED`
- **When** `phase_reflect()` is called with a mock transport
- **Then** a file `reflect.md` is written to the change directory via
  `transport.run_shell`
- **And** the content contains `## Self-Rating`, `**poor**`, and
  `## Weaknesses`

#### Scenario: reflect-called-on-implement-fail

- **testable**: false

- **Given** a change where IMPLEMENT fails mechanical verification and the
  fix-loop exhausts all attempts
- **When** the orchestrator reverts the commit
- **Then** `phase_reflect()` is called before `return False`
- **And** a self-assessment row with `outcome="reverted"` exists in the DB

> Note: this is an integration scenario exercising the full `_run_phases`
> method; verified by LLM judge rather than a mechanical unit test.

### Requirement: phase_reflect handles reverted outcome metrics

`phase_reflect()` SHALL compute correct metrics (total_fix, actual_tokens,
actual_steps, self_rating) when `rec.outcome` is `Outcome.REVERTED`.

- `self_rating` MUST be `"poor"` when outcome is reverted
- `weaknesses` list SHALL include `"Task exceeded recovery capacity"`
- `lessons` list SHALL include `"Change reverted — review failure pattern"`

#### Scenario: reverted-assessment-fields

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator.phase_reflect

- **Given** a `ChangeRecord` with `outcome=Outcome.REVERTED`, phases
  containing IMPLEMENT (`fix_attempts=2`) and VERIFY (`fix_attempts=1`)
- **When** `phase_reflect()` is called
- **Then** the DB row has `self_rating="poor"`, `outcome="reverted"`
- **And** the `weaknesses` JSON includes `"Task exceeded recovery capacity"`
- **And** the `lessons` JSON includes `"Change reverted — review failure pattern"`

## Constraints

- `phase_reflect()` SHALL NOT raise exceptions that prevent the orchestrator
  from continuing; errors SHALL be logged and the method SHALL return a
  fallback elapsed time.
- The existing DB schema (`self_assessment` table) SHALL NOT be modified.
