# Spec: Post-Implement Lint Auto-Fix Gate

## Problem

Many verify failures originate from lint errors (E701, E741, etc.) that could
have been caught and auto-fixed right after the IMPLEMENT phase, before the
code enters REVIEW and VERIFY. Currently, `ruff check --fix` is only run as
part of `verify_mechanical`, which is too late — the lint errors are already
in the committed diff and can cause pre-check failures during VERIFY.

## ADDED Requirements

### Requirement: Post-IMPLEMENT lint auto-fix gate

After the IMPLEMENT agent finishes and the post-impl checkpoint commit is made,
the orchestrator SHALL run `ruff check --fix` on all changed files, followed by
`ruff check` to detect any remaining unfixable errors. If unfixable errors
remain, the orchestrator SHALL attempt one targeted fix before proceeding to
REVIEW.

#### Scenario: Auto-fixable lint errors are corrected before REVIEW

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** an IMPLEMENT phase that produces files with E701 (multiple statements on one line) and trailing whitespace
- **When** the post-IMPLEMENT lint auto-fix gate runs
- **Then** `ruff check --fix` SHALL be invoked on the changed files, and the trailing whitespace SHALL be removed automatically, resulting in zero lint errors for that category

#### Scenario: Unfixable lint errors trigger a targeted fix attempt

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** an IMPLEMENT phase that produces files with E741 (ambiguous variable name `l`) which `ruff check --fix` cannot auto-fix
- **When** the post-IMPLEMENT lint auto-fix gate detects remaining errors after `--fix`
- **Then** the orchestrator SHALL invoke the fix agent with a prompt containing the specific lint error lines, targeting only the files with errors
- **And** after the fix attempt, the orchestrator SHALL re-run `ruff check` on the changed files
- **And** if lint still fails, the change SHALL be reverted (same as current implement-phase lint failure behavior)

#### Scenario: Clean IMPLEMENT passes through without extra LLM call

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::ZsigaOrchestrator._run_phases
- **Given** an IMPLEMENT phase that produces files with no lint errors
- **When** the post-IMPLEMENT lint auto-fix gate runs
- **Then** no LLM fix agent SHALL be invoked, and the pipeline proceeds directly to REVIEW
