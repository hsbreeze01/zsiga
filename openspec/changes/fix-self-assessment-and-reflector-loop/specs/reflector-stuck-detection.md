# Spec: Reflector Stuck Detection

Adds auto-proposal stuck detection to the Reflector.  When the same
auto-proposal pattern has failed VERIFY three or more consecutive times,
the Reflector SHALL stop generating new proposals for that pattern and
instead produce a `diagnosis.md` for human inspection.

## ADDED Requirements

### Requirement: _is_stuck stuck detection method

The `Reflector` class SHALL expose a method `_is_stuck(base: Path,
signal: Signal) -> bool` that returns `True` when the last 3 (or more)
auto-generated proposals whose directory name contains the sanitized
`signal.pattern_key` all have outcome `"reverted"` in the changes history.

#### Scenario: stuck-when-three-consecutive-fails

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._is_stuck

- **Given** a base directory with `_load_recent_changes` returning a list
  of change dicts where the last 3 changes whose `change_name` contains the
  sanitized pattern_key all have `outcome="reverted"`
- **When** `_is_stuck(base, signal)` is called with a Signal whose
  `pattern_key` matches those changes
- **Then** the method returns `True`

#### Scenario: not-stuck-when-fewer-than-three-fails

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._is_stuck

- **Given** a base directory with `_load_recent_changes` returning only 2
  reverted changes matching the pattern_key
- **When** `_is_stuck(base, signal)` is called
- **Then** the method returns `False`

#### Scenario: not-stuck-when-mixed-outcomes

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._is_stuck

- **Given** a base directory with 3 matching changes but one has
  `outcome="success"`
- **When** `_is_stuck(base, signal)` is called
- **Then** the method returns `False`

### Requirement: stuck signal generates diagnosis.md instead of proposal

When `_is_stuck()` returns `True`, the Reflector SHALL NOT call
`generate_proposal()`.  Instead it SHALL create a directory named
`auto-stuck-{sanitized_pattern_key}-{date}` under `openspec/changes/`
containing a `diagnosis.md` file.

The `diagnosis.md` SHALL contain:
- A list of the failed proposal names
- The FAIL reason for each (extracted from the changes history phases)
- A section recommending human intervention

This directory SHALL NOT trigger pipeline execution (no `proposal.md`
with the standard template).

#### Scenario: diagnosis-md-created-on-stuck

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._generate_stuck_diagnosis

- **Given** a signal for which `_is_stuck()` returns `True`, and a base
  directory
- **When** `_generate_stuck_diagnosis(base, signal)` is called
- **Then** a directory `auto-stuck-{sanitized_key}-{date}/` exists under
  `openspec/changes/`
- **And** the directory contains `diagnosis.md` (not `proposal.md`)
- **And** `diagnosis.md` contains a header mentioning the pattern key

#### Scenario: diagnosis-md-lists-failed-changes

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._generate_stuck_diagnosis

- **Given** a stuck signal and recent changes data listing 3 failed change
  names with their failure details
- **When** `_generate_stuck_diagnosis(base, signal)` is called
- **Then** `diagnosis.md` contains each failed change name
- **And** `diagnosis.md` contains a `## Recommendation` section suggesting
  human intervention

### Requirement: should_propose integrates stuck check

`should_propose()` SHALL return `False` when `_is_stuck()` returns `True`,
in addition to existing dedup/rate-limit/external checks.

#### Scenario: should-propose-rejects-stuck-signal

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector.should_propose

- **Given** a signal whose pattern_key has 3 consecutive VERIFY-FAIL
  auto-proposals
- **When** `should_propose(signal, base)` is called
- **Then** it returns `False`

## Constraints

- `_is_stuck()` SHALL only inspect auto-generated proposals (directory name
  starts with `auto-`).
- Stuck detection window: consider only changes from the last 30 days to
  avoid false positives from ancient history.
- `_generate_stuck_diagnosis()` SHALL be a pure filesystem operation — no
  LLM calls.
