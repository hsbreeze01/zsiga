# Spec: Verify Failure Observability

## Problem

All 44 verify-phase failures in the zsiga project record `detail: ""`, making it
impossible to diagnose *why* verify failed. The `PhaseRecord.detail` field is
set for `implement` and `review` failures but left empty for `verify` failures
in two code paths:

1. **REVERTED path** — when `_eval_fix_loop` exhausts retries and calls
   `git_ops.reset_hard`, the verify `PhaseRecord` captures `detail` from the
   precheck error type but not from the eval-fix failure reason.
2. **SUCCESS path** — the verify `PhaseRecord` written on success never captures
   the actual `read_verdict()` result, and on failure the verdict content from
   `verify.md` is not persisted into `detail`.

## ADDED Requirements

### Requirement: Verify PhaseRecord MUST capture failure diagnostic

The orchestrator SHALL write the content of `verify.md` (or a 200-char excerpt)
into `PhaseRecord.detail` for every verify phase, regardless of outcome
(success, fail, or reverted).

#### Scenario: Verify fail with verdict detail captured

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** a change whose verify phase results in `verdict == "FAIL"` and `verify.md` containing "Layer 1: FAIL — 2 testable scenarios"
- **When** the orchestrator appends the verify `PhaseRecord` to `rec.phases`
- **Then** the `detail` field of that `PhaseRecord` SHALL contain the string "FAIL" (from the verdict) and at least 50 characters of the `verify.md` content

#### Scenario: Verify revert captures eval-fix failure reason

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** a change where `_eval_fix_loop` returns `(False, attempts)` and the verify phase reverts
- **When** the orchestrator writes the REVERTED verify `PhaseRecord`
- **Then** `detail` SHALL be a non-empty string containing at minimum the word "eval-fix" and the number of fix attempts

#### Scenario: Verify precheck failure captures error type and file

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** a change where `verify_precheck` fails with `error_type="import"` and `file_path="zsiga/foo.py"`
- **When** the orchestrator writes the pre-check-failure verify `PhaseRecord`
- **Then** `detail` SHALL contain both "import" and "zsiga/foo.py"

### Requirement: Verify PhaseRecord MUST capture the actual verdict string on success

#### Scenario: Verify success records verdict and layer-1 summary

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** a change where `verdict == "PASS"` and `verify.md` contains "Layer 1: PASS — 3 testable scenarios"
- **When** the orchestrator appends the verify `PhaseRecord`
- **Then** `detail` SHALL contain the string "PASS"
