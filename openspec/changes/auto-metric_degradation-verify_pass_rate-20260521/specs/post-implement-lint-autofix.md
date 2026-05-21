# Spec: Post-Implement Lint Auto-Fix Gate

## Problem

Many verify failures originate from lint errors (E701, E741, W291, etc.) that
could have been caught and auto-fixed right after the IMPLEMENT phase, before
the code enters REVIEW and VERIFY. Currently, `ruff check --fix` is only run
as part of `verify_mechanical`, which is too late — the lint errors are already
in the committed diff and can cause pre-check failures during VERIFY.

## ADDED Requirements

### Requirement: Post-IMPLEMENT lint auto-fix SHALL correct auto-fixable errors

After the IMPLEMENT phase finishes, the pipeline SHALL run `ruff check --fix`
on all changed files. Auto-fixable lint errors (trailing whitespace, unused
imports, E701 multiple-statements-on-one-line, etc.) SHALL be silently
corrected.

#### Scenario: Auto-fixable lint errors are corrected by ruff --fix

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** a Python file containing trailing whitespace (`W291`) after code lines
- **When** `ruff check --fix` is invoked on that file
- **Then** the trailing whitespace SHALL be removed and a subsequent `ruff check` SHALL report zero `W291` errors

#### Scenario: Unfixable lint errors remain after --fix

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** a Python file containing `E741` (ambiguous variable name `l`)
- **When** `ruff check --fix` is invoked on that file
- **Then** `E741` SHALL still be reported by a subsequent `ruff check --select E741`

#### Scenario: Clean file passes without any fix

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** a Python file with no lint errors
- **When** `ruff check` is invoked on that file
- **Then** the exit code SHALL be 0 and no errors SHALL be reported

### Requirement: verify_mechanical SHALL pass on clean code changes

The `verify_mechanical` function SHALL return `(True, [])` when the changed
files have no lint or test errors.

#### Scenario: verify_mechanical returns True for clean changes

- **testable**: true
- **target**: zsiga/pipeline/utils.py::verify_mechanical
- **Given** a git repository with a clean Python file change (no lint errors, tests pass)
- **When** `verify_mechanical` is called with the repo path and since_sha
- **Then** the function SHALL return `(True, [])`
