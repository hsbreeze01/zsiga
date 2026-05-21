# Spec: Reflector History Injection

Enhances `generate_proposal()` to inject recent failure history into the
proposal content, so that LLM-driven downstream phases can reference past
mistakes and avoid repeating the same strategy.

## ADDED Requirements

### Requirement: _load_recent_failures helper

The `Reflector` class SHALL expose a method
`_load_recent_failures(base: Path, pattern_key: str, limit: int = 3) -> list[dict]`
that returns up to `limit` recent change dicts whose `change_name` contains
the sanitized `pattern_key` and whose `outcome` is `"reverted"`.

Each returned dict SHALL contain at least:
- `change_name`: the change directory name
- `fail_reason`: extracted from `phases_json` (the `detail` field of the
  last VERIFY PhaseRecord, or `"unknown"` if unavailable)

#### Scenario: load-recent-failures-returns-reverted

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._load_recent_failures

- **Given** a base directory with `_load_recent_changes` returning a list
  where 3 changes match the pattern_key and have `outcome="reverted"`,
  each with phase records containing VERIFY `detail` strings
- **When** `_load_recent_failures(base, pattern_key, limit=3)` is called
- **Then** a list of 3 dicts is returned, each with a `change_name` and
  `fail_reason` key

#### Scenario: load-recent-failures-caps-at-limit

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._load_recent_failures

- **Given** 5 matching reverted changes
- **When** `_load_recent_failures(base, pattern_key, limit=3)` is called
- **Then** exactly 3 dicts are returned

#### Scenario: load-recent-failures-returns-empty-when-none

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector._load_recent_failures

- **Given** no reverted changes matching the pattern_key
- **When** `_load_recent_failures(base, pattern_key)` is called
- **Then** an empty list is returned

### Requirement: generate_proposal injects failure history

`generate_proposal()` SHALL call `_load_recent_failures()` and, when the
result is non-empty, append a `## Past Failures` section to the rendered
`proposal.md`.

The section SHALL list each past failure with its change name and fail
reason, formatted as bullet points.

#### Scenario: proposal-md-contains-past-failures-section

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector.generate_proposal

- **Given** a signal with `pattern_key="verify_pass_rate"` and a base
  directory where `_load_recent_failures` returns 2 past failures
- **When** `generate_proposal(signal, base)` is called (mocking
  `_load_recent_failures`)
- **Then** the generated `proposal.md` contains a `## Past Failures` section
- **And** each past failure's `change_name` appears in the content

#### Scenario: proposal-md-no-past-failures-when-clean

- **testable**: true
- **target**: zsiga/intake/reflector.py::Reflector.generate_proposal

- **Given** a signal and `_load_recent_failures` returning an empty list
- **When** `generate_proposal(signal, base)` is called
- **Then** the generated `proposal.md` does NOT contain `## Past Failures`

## Constraints

- The `## Past Failures` section SHALL appear after `## Motivation` and
  before `## Expected Behavior` in the proposal.md template.
- Each `fail_reason` SHALL be truncated to 200 characters to keep the
  prompt within token budget.
- `_load_recent_failures()` SHALL NOT call the LLM; it reads from the
  local metrics/changes data.
