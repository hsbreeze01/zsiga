# Spec: Verify Failure Observability

## Problem

All verify-phase failures in the zsiga project record `detail: ""`, making it
impossible to diagnose *why* verify failed. The `PhaseRecord.detail` field is
set for `implement` and `review` failures but left empty for `verify` failures.

## ADDED Requirements

### Requirement: Verify PhaseRecord MUST capture failure diagnostic

The pipeline SHALL write meaningful content into `PhaseRecord.detail` for every
verify phase, regardless of outcome (success, fail, or reverted).

#### Scenario: Verify fail with verdict detail captured

- **testable**: true
- **target**: zsiga/metrics/types.py::PhaseRecord
- **Given** a verify `PhaseRecord` with outcome=FAIL and `detail="verdict=FAIL; Layer 1: FAIL — 2 testable scenarios"`
- **When** the record is inspected
- **Then** `detail` SHALL be non-empty and contain the string `"FAIL"`

#### Scenario: Verify revert captures eval-fix failure reason

- **testable**: true
- **target**: zsiga/metrics/types.py::PhaseRecord
- **Given** a verify `PhaseRecord` with outcome=FAIL, `fix_attempts=3`, and `detail="eval-fix exhausted 3 attempts"`
- **When** the record is inspected
- **Then** `detail` SHALL be non-empty and contain both `"eval-fix"` and `"3"`

#### Scenario: Verify precheck failure captures error type and file

- **testable**: true
- **target**: zsiga/metrics/types.py::PhaseRecord
- **Given** a verify `PhaseRecord` with outcome=FAIL and `detail="pre-check: import in zsiga/foo.py"`
- **When** the record is inspected
- **Then** `detail` SHALL contain both `"import"` and `"zsiga/foo.py"`

#### Scenario: Verify success records verdict and layer-1 summary

- **testable**: true
- **target**: zsiga/metrics/types.py::PhaseRecord
- **Given** a verify `PhaseRecord` with outcome=SUCCESS and `detail="verdict=PASS; Layer 1: PASS — 3 testable scenarios"`
- **When** the record is inspected
- **Then** `detail` SHALL contain the string `"PASS"`

### Requirement: PhaseRecord detail SHALL survive ChangeRecord serialization

The `detail` field SHALL be preserved when a `PhaseRecord` is embedded in a
`ChangeRecord` and serialized via `to_dict()`.

#### Scenario: PhaseRecord detail preserved through ChangeRecord.to_dict()

- **testable**: true
- **target**: zsiga/metrics/types.py::ChangeRecord
- **Given** a `ChangeRecord` containing a verify `PhaseRecord` with `detail="lint: E701 in foo.py"`
- **When** `ChangeRecord.to_dict()` is called
- **Then** the serialized phases list SHALL contain the entry with `"detail": "lint: E701 in foo.py"`

### Requirement: read_verdict SHALL parse verify.md verdicts

The `read_verdict` function SHALL read the `verify.md` file in a change
directory and extract the verdict string.

#### Scenario: read_verdict returns PASS from properly formatted verify.md

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::read_verdict
- **Given** a directory containing `verify.md` with content "Verdict: PASS\nLayer 1: PASS — 1 testable scenario\n"
- **When** `read_verdict` is called on that directory
- **Then** it SHALL return `"PASS"`

#### Scenario: read_verdict returns FAIL from properly formatted verify.md

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::read_verdict
- **Given** a directory containing `verify.md` with content "Verdict: FAIL\nLayer 1: FAIL — 2 testable scenarios failed\n"
- **When** `read_verdict` is called on that directory
- **Then** it SHALL return `"FAIL"`

#### Scenario: read_verdict returns UNKNOWN when verify.md does not exist

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::read_verdict
- **Given** a directory with no `verify.md` file
- **When** `read_verdict` is called on that directory
- **Then** it SHALL return `"UNKNOWN"`
